"""关口计量业务规则：状态流转、字段校验与筛选口径都收在这里。"""
from __future__ import annotations

from typing import Any

from app.store import store

MODULE = "meter"
REQUIRED_FIELDS = ["表计编号", "表计型号", "计量点位置"]
STATUS_ORDER = ["正常运行", "通讯中断", "示数异常", "待校验"]
ACTION_RULES = {"记录示数": "正常运行", "标记异常": "示数异常", "送检校验": "待校验"}
NEGATIVE_ACTIONS = ["标记异常"]


class MeterService:
    def list_entries(
        self,
        *,
        keyword: str | None = None,
        location: str | None = None,
        expire_before: str | None = None,
        status: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        rows = store.rows(MODULE)
        if keyword:
            rows = [row for row in rows if keyword in str(row.get("表计编号", ""))]
        if location:
            rows = [row for row in rows if location in str(row.get("计量点位置", ""))]
        if expire_before:
            # 检定有效期早于或等于查询日，即该日之前（含当日）已到期；
            # 未登记检定有效期的表计不参与有效期筛选，避免把脏数据静默算成结果。
            rows = [
                row
                for row in rows
                if str(row.get("检定有效期") or "") <= expire_before
                and bool(str(row.get("检定有效期") or "").strip())
            ]
        if status:
            rows = [row for row in rows if row.get("status") == status]
        total = len(rows)
        start = max(page - 1, 0) * size
        return rows[start:start + size], total

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
        # 列表里的「表计状态」列跟着动作同步，避免筛选项与展示列口径不一致。
        entry["表计状态"] = target
        return entry, f"计量表计已{action}"
