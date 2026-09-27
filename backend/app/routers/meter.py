"""关口计量接口：维护计量表计，覆盖记录示数、标记异常、送检校验等动作。"""
from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.schemas import ActionResult, EntryPayload, PageResult
from app.services.meter import MeterService

router = APIRouter(prefix="/api/meter", tags=["关口计量"])

service = MeterService()

LIST_FIELDS = ["表计编号", "表计型号", "计量点位置", "倍率", "上次示数", "当前示数", "校验日期", "检定有效期", "表计状态"]
STATUSES = ["正常运行", "通讯中断", "示数异常", "待校验"]


def _validate_query_date(value: str | None, label: str) -> str | None:
    """日期类查询条件必须是 YYYY-MM-DD；不合法时让前端明确提示，而不是悄悄返回空结果。"""
    if value is None or not value.strip():
        return None
    value = value.strip()
    try:
        date.fromisoformat(value)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"{label}「{value}」不是合法日期，请按 YYYY-MM-DD 填写")
    return value


@router.get("", response_model=PageResult[dict])
def list_entries(
    keyword: str | None = Query(default=None, description="按表计编号检索"),
    location: str | None = Query(default=None, description="按计量点位置模糊检索"),
    expire_before: str | None = Query(default=None, description="检定有效期截止日（含当日），格式 YYYY-MM-DD"),
    status: str | None = Query(default=None, description="正常运行、通讯中断、示数异常、待校验"),
    page: int = 1,
    size: int = 20,
) -> PageResult[dict]:
    """按表计编号、计量点位置、检定有效期与状态过滤；没有匹配数据时返回空页，不报错。"""
    if size > 200:
        raise HTTPException(status_code=400, detail="每页最多 200 条，请缩小分页范围")
    if page < 1:
        raise HTTPException(status_code=400, detail="页码必须从 1 开始")
    if location is not None and len(location.strip()) > 50:
        raise HTTPException(status_code=400, detail="计量点位置最多 50 个字，请缩短后重试")
    expire_before = _validate_query_date(expire_before, "检定有效期")
    if status is not None and status.strip() and status not in STATUSES:
        raise HTTPException(status_code=400, detail=f"表计状态「{status}」不在可选范围：{'、'.join(STATUSES)}")
    items, total = service.list_entries(
        keyword=(keyword or "").strip() or None,
        location=(location or "").strip() or None,
        expire_before=expire_before,
        status=(status or "").strip() or None,
        page=page,
        size=size,
    )
    return PageResult(items=items, total=total, page=page, size=size)


@router.get("/export")
def export_entries() -> dict[str, Any]:
    """导出关口计量清单：返回全量数据。"""
    items, total = service.list_entries(page=1, size=10000)
    return {"module": "meter", "total": total, "items": items}


@router.get("/{entry_id}", response_model=dict)
def get_entry(entry_id: int) -> dict:
    """读取单条计量表计明细；不存在时给出可读的错误说明。"""
    entry = service.get_entry(entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"计量表计 {entry_id} 不存在或已归档")
    return entry


@router.post("", response_model=ActionResult)
def create_entry(payload: EntryPayload) -> ActionResult:
    """登记一条计量表计，缺字段时说明原因而不是静默丢弃。"""
    entry, missing = service.create_entry(payload.values)
    if missing:
        return ActionResult(ok=False, message=f"缺少必填字段：{'、'.join(missing)}")
    return ActionResult(ok=True, message="计量表计已登记", entry=entry)


@router.post("/{entry_id}/actions", response_model=ActionResult)
def run_action(entry_id: int, payload: EntryPayload) -> ActionResult:
    """对单条计量表计执行记录示数、标记异常、送检校验；不允许的动作会被拦下并说明原因。"""
    action = str(payload.values.get("action") or "").strip()
    entry, message = service.run_action(entry_id, action)
    if entry is None:
        return ActionResult(ok=False, message=message)
    return ActionResult(ok=True, message=message, entry=entry)
