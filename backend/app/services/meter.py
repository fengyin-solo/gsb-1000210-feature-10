"""关口计量业务规则：状态流转、字段校验与筛选口径都收在这里。"""
from __future__ import annotations

from datetime import date
from typing import Any

from app.store import store

MODULE = "meter"
REQUIRED_FIELDS = ["表计编号", "表计型号", "计量点位置"]
STATUS_ORDER = ["正常运行", "通讯中断", "示数异常", "待校验"]
ACTION_RULES = {"记录示数": "正常运行", "标记异常": "示数异常", "送检校验": "待校验"}
NEGATIVE_ACTIONS = []
VALIDITY_FIELD = "校验日期"


def _parse_validity(raw: str, label: str) -> date:
    """把检定有效期边界解析成日期；格式不对时抛出带说明的 ValueError。"""
    try:
        return date.fromisoformat(raw.strip())
    except ValueError:
        raise ValueError(f"{label}「{raw}」不是合法日期，请按 YYYY-MM-DD 填写") from None


def _in_validity(row: dict[str, Any], start: date | None, end: date | None) -> bool:
    """判断表计的校验日期是否落在检定有效期区间内；日期缺失的表计不计入。"""
    try:
        checked = date.fromisoformat(str(row.get(VALIDITY_FIELD) or "").strip())
    except ValueError:
        return False
    if start and checked < start:
        return False
    if end and checked > end:
        return False
    return True


class MeterService:
    def list_entries(
        self,
        *,
        keyword: str | None = None,
        status: str | None = None,
        location: str | None = None,
        valid_from: str | None = None,
        valid_to: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        rows = store.rows(MODULE)
        if keyword:
            rows = [row for row in rows if keyword in str(row.get("表计编号", ""))]
        if status:
            rows = [row for row in rows if row.get("status") == status]
        if location:
            rows = [row for row in rows if location in str(row.get("计量点位置", ""))]
        start = _parse_validity(valid_from, "检定有效期起") if valid_from else None
        end = _parse_validity(valid_to, "检定有效期止") if valid_to else None
        if start and end and start > end:
            raise ValueError("检定有效期起不能晚于检定有效期止，请调整后再查")
        if start or end:
            rows = [row for row in rows if _in_validity(row, start, end)]
        total = len(rows)
        offset = max(page - 1, 0) * size
        return rows[offset:offset + size], total

    def get_entry(self, entry_id: int) -> dict[str, Any] | None:
        return store.find(MODULE, entry_id)

    def create_entry(self, values: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
        missing = [field for field in REQUIRED_FIELDS if not str(values.get(field) or "").strip()]
        if missing:
            return None, missing
        rows = store.rows(MODULE)
        entry = {"id": max((int(row.get("id", 0)) for row in rows), default=0) + 1}
        entry.update({field: values.get(field) for field in REQUIRED_FIELDS})
        entry["status"] = STATUS_ORDER[0]
        entry["pending"] = True
        entry["abnormal"] = False
        rows.append(entry)
        return entry, []

    def run_action(self, entry_id: int, action: str) -> tuple[dict[str, Any] | None, str]:
        entry = store.find(MODULE, entry_id)
        if entry is None:
            return None, f"计量表计 {entry_id} 不存在或已归档"
        if action not in ACTION_RULES:
            return None, f"动作「{action}」不属于关口计量可执行范围"
        target = ACTION_RULES[action]
        if target not in STATUS_ORDER:
            return None, f"目标状态「{target}」不在允许的状态序列里"
        entry["status"] = target
        entry["pending"] = target != STATUS_ORDER[-1]
        entry["abnormal"] = action in NEGATIVE_ACTIONS
        return entry, f"计量表计已{action}"
