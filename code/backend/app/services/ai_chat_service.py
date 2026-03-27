import json
from datetime import datetime

import requests
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.models import DutySchedule, ShiftChangeRecord, SystemSetting

SYSTEM_PROMPT = """
你是值班提醒系统中的AI助手。你必须严格遵守：
1) 仅回答值班系统相关问题。
2) 当用户意图为“查询数据”时，调用可用工具查询数据库后再回答。
3) 当用户意图为“换班/改班”时，必须调用换班工具执行，并返回执行结果。
4) 不得编造数据。如果工具返回为空，明确说明未找到。
5) 输出简洁中文。
""".strip()


def _get_setting(db: Session) -> SystemSetting:
    setting = db.query(SystemSetting).first()
    if not setting:
        raise HTTPException(status_code=400, detail="系统设置不存在，请先初始化")
    return setting


def _tool_list_schedule(db: Session, start_date: str | None = None, end_date: str | None = None, person: str | None = None):
    q = db.query(DutySchedule)
    if start_date:
        q = q.filter(DutySchedule.duty_date >= datetime.strptime(start_date, "%Y-%m-%d").date())
    if end_date:
        q = q.filter(DutySchedule.duty_date <= datetime.strptime(end_date, "%Y-%m-%d").date())
    if person:
        q = q.filter(DutySchedule.duty_person_name == person)
    items = q.order_by(DutySchedule.duty_date.asc()).all()
    return [
        {
            "id": x.id,
            "duty_date": str(x.duty_date),
            "weekday_text": x.weekday_text,
            "duty_person_name": x.duty_person_name,
            "source_sheet": x.source_sheet,
        }
        for x in items
    ]


def _tool_shift_change(
    db: Session,
    duty_date: str,
    new_person_name: str,
    reason: str = "",
    requested_by: str = "AI",
    source: str = "ai_chat",
):
    d = datetime.strptime(duty_date, "%Y-%m-%d").date()
    row = db.query(DutySchedule).filter(DutySchedule.duty_date == d).first()
    if not row:
        return {"ok": False, "message": "未找到该日期的值班记录"}

    old_name = row.duty_person_name
    row.duty_person_name = new_person_name

    record = ShiftChangeRecord(
        duty_date=d,
        old_person_name=old_name,
        new_person_name=new_person_name,
        reason=reason,
        requested_by=requested_by,
        source=source,
        status="done",
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "ok": True,
        "message": f"已将 {duty_date} 的值班人从 {old_name} 调整为 {new_person_name}",
        "record_id": record.id,
    }


def _parse_json_response(resp: requests.Response) -> dict:
    content_type = (resp.headers.get("Content-Type", "") or "").lower()
    text = (resp.text or "").strip()
    if not text:
        raise HTTPException(status_code=500, detail="AI 响应为空，请检查 Base URL 是否正确")

    # 某些兼容网关返回 text/plain 但内容依然是 JSON，这里做兼容解析
    if "application/json" in content_type:
        try:
            return resp.json()
        except Exception:
            raise HTTPException(status_code=500, detail=f"AI JSON 解析失败：{text[:300]}")

    if text.startswith("{") or text.startswith("["):
        try:
            return json.loads(text)
        except Exception:
            raise HTTPException(status_code=500, detail=f"AI JSON 解析失败：{text[:300]}")

    raise HTTPException(
        status_code=500,
        detail=f"AI 返回非 JSON 响应（{content_type or 'unknown'}）：{text[:300]}",
    )


def chat_with_openai_compatible(db: Session, message: str, history: list[dict]) -> str:
    setting = _get_setting(db)
    if not setting.ai_enabled:
        raise HTTPException(status_code=400, detail="AI 功能未启用，请在系统设置中启用")
    if not setting.ai_base_url or not setting.ai_api_key or not setting.ai_model:
        raise HTTPException(status_code=400, detail="AI 配置不完整，请在系统设置中填写 Base URL / API Key / Model")

    url = setting.ai_base_url.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {setting.ai_api_key}",
        "Content-Type": "application/json",
    }

    tools = [
        {
            "type": "function",
            "function": {
                "name": "list_schedule",
                "description": "按日期区间或值班人查询值班表",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "start_date": {"type": "string", "description": "开始日期, YYYY-MM-DD"},
                        "end_date": {"type": "string", "description": "结束日期, YYYY-MM-DD"},
                        "person": {"type": "string", "description": "值班人姓名"},
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "shift_change",
                "description": "执行换班：修改某天值班人并记录换班日志",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "duty_date": {"type": "string", "description": "值班日期, YYYY-MM-DD"},
                        "new_person_name": {"type": "string", "description": "新的值班人"},
                        "reason": {"type": "string", "description": "换班原因"},
                    },
                    "required": ["duty_date", "new_person_name"],
                },
            },
        },
    ]

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in history[-20:]:
        if m.get("role") in {"user", "assistant", "system"} and m.get("content"):
            messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": message})

    payload = {
        "model": setting.ai_model,
        "temperature": max(0.0, min(1.0, (setting.ai_temperature or 20) / 100)),
        "messages": messages,
        "tools": tools,
        "tool_choice": "auto",
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=45)
    if resp.status_code >= 400:
        raise HTTPException(status_code=500, detail=f"AI 请求失败: {resp.text[:300]}")

    data = _parse_json_response(resp)
    choice = data.get("choices", [{}])[0]
    msg = choice.get("message", {})

    tool_calls = msg.get("tool_calls") or []
    if not tool_calls:
        return msg.get("content") or "未获取到AI回复"

    tool_results = []
    for call in tool_calls:
        fn = call.get("function", {}).get("name")
        args_text = call.get("function", {}).get("arguments") or "{}"
        try:
            args = json.loads(args_text)
        except Exception:
            args = {}

        if fn == "list_schedule":
            result = _tool_list_schedule(
                db,
                start_date=args.get("start_date"),
                end_date=args.get("end_date"),
                person=args.get("person"),
            )
        elif fn == "shift_change":
            result = _tool_shift_change(
                db,
                duty_date=args.get("duty_date"),
                new_person_name=args.get("new_person_name"),
                reason=args.get("reason", ""),
                requested_by="AI",
                source="ai_chat",
            )
        else:
            result = {"ok": False, "message": f"unknown tool: {fn}"}

        tool_results.append(
            {
                "role": "tool",
                "tool_call_id": call.get("id"),
                "name": fn,
                "content": json.dumps(result, ensure_ascii=False),
            }
        )

    payload2 = {
        "model": setting.ai_model,
        "temperature": max(0.0, min(1.0, (setting.ai_temperature or 20) / 100)),
        "messages": messages + [msg] + tool_results,
    }
    resp2 = requests.post(url, headers=headers, json=payload2, timeout=45)
    if resp2.status_code >= 400:
        raise HTTPException(status_code=500, detail=f"AI 二次请求失败: {resp2.text[:300]}")

    data2 = _parse_json_response(resp2)
    final_msg = data2.get("choices", [{}])[0].get("message", {})
    return final_msg.get("content") or "操作已执行，但未获取到总结回复"
