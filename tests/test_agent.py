from fastapi.testclient import TestClient

from app.api.main import app
from app.services.agent import _pick_tool_from_query


def test_pick_tool_from_query():
    assert _pick_tool_from_query("玛丽港有哪些船只？")[0] == "find_vessels_by_port"
    assert _pick_tool_from_query("Turku 最近的船是哪一条？")[0] == "find_nearest_vessel"
    assert _pick_tool_from_query("Viking Line 的哪艘船在哪里？")[0] == "find_vessel_location"


def test_mcp_execute_route(monkeypatch):
    def fake_execute_tool(db, tool_name, params):
        return {
            "tool_name": tool_name,
            "status": "success",
            "tool_response": [],
            "meta": {"description": "fake"},
        }

    import app.services.mcp as mcp_module

    monkeypatch.setattr(mcp_module, "execute_tool", fake_execute_tool)

    client = TestClient(app)
    response = client.post(
        "/mcp/execute",
        json={"tool_name": "find_vessels_by_port", "params": {"port_name": "玛丽港"}},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["tool_name"] == "find_vessels_by_port"
    assert data["status"] == "success"
