from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.services.toolkit import call_tool, get_tool


def execute_tool(db: Session, tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
    tool = get_tool(tool_name)
    if tool is None:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")

    try:
        result = call_tool(db, tool_name, params)
        return {
            "tool_name": tool_name,
            "status": "success",
            "tool_response": result["result"],
            "meta": {
                "description": tool["description"],
                "params": params,
            },
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
