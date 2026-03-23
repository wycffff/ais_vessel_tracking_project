from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.settings import get_settings
from app.services.mcp import execute_tool

try:
    from llama_cpp import Llama
except ImportError:
    Llama = None  # type: ignore


class Agent:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.model = None
        if Llama is not None and self.settings.llm_model_path:
            try:
                self.model = Llama(model_path=self.settings.llm_model_path)
            except Exception:
                self.model = None

    def generate(self, prompt: str) -> str:
        if self.model is None:
            # Fallback: simple templated response
            return f"[LLM unavailable] 解析问题：{prompt}"
        resp = self.model(prompt=prompt, max_tokens=256, temperature=self.settings.llm_temperature)
        if isinstance(resp, dict) and "choices" in resp and len(resp["choices"]) > 0:
            return resp["choices"][0].get("text", "").strip()
        return ""


agent_instance = Agent()


def _pick_tool_from_query(query: str) -> tuple[str, dict[str, Any]]:
    q = query.strip().lower()
    if "玛丽港" in q or "mariehamn" in q:
        return "find_vessels_by_port", {"port_name": "玛丽港"}
    if "turku" in q or "图尔库" in q:
        return "find_nearest_vessel", {"city_name": "turku"}
    if "viking line" in q.lower() or "维京" in q:
        return "find_vessel_location", {"vessel_query": "Viking Line"}
    if "最近的船" in q or "nearest" in q:
        # 默认用图尔库
        return "find_nearest_vessel", {"city_name": "turku"}
    if "在哪" in q or "在哪里" in q:
        return "find_vessel_location", {"vessel_query": q}
    return "find_vessels_by_port", {"port_name": "玛丽港"}


def agent_handle_query(user_query: str, db: Session) -> Dict[str, Any]:
    tool_name, params = _pick_tool_from_query(user_query)
    tool_response = execute_tool(db, tool_name, params)

    # 来自tool的原始数据
    rows = tool_response.get("tool_response")
    if not rows:
        answer = f"我未能找到符合 '{user_query}' 的实时船只数据。"
    else:
        # 使用LLM总结内容
        prompt = (
            f"你是一个船舶问答助手。用户问题：{user_query}。\n"
            f"工具名称：{tool_name}。\n工具参数：{params}。\n"
            f"工具结果（JSON数组）：{rows[:5]}"  # 仅先简短
        )
        llm_answer = agent_instance.generate(prompt)
        if llm_answer.startswith("[LLM unavailable]"):
            # 本地不可用 fallback
            summary_items = []
            for vessel in rows[:3]:
                summary_items.append(f"{vessel.get('vessel_name') or vessel.get('mmsi')} 位于 ({vessel.get('lat')},{vessel.get('lon')})")
            answer = "；".join(summary_items) if summary_items else "没有找到相关船只。"
        else:
            answer = llm_answer

    return {
        "user_query": user_query,
        "tool_used": tool_name,
        "tool_params": params,
        "tool_result": rows,
        "answer": answer,
        "status": "success",
    }
