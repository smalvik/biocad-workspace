"""A real SDK MCP server over STDIO; all domain reads travel through RabbitMQ."""

import os
from typing import Any

from mcp.server import MCPServer

from app.errors import AssistantError
from app.proposals import Selection, propose
from app.rpc import RpcClient

server = MCPServer("BIOCAD demo booking tools", version="1.0", log_level="ERROR")


def rpc():
    return RpcClient(os.environ["RABBITMQ_URL"], os.environ["MCP_SESSION_TOKEN"])


async def read(operation, payload):
    try:
        return await rpc().call(operation, payload)
    except AssistantError as error:
        return {"error": {"code": error.code, "message": error.message}}


@server.tool(structured_output=True)
async def search_employees(q: str, start_at: str, end_at: str) -> dict[str, Any]:
    """Search fictional colleagues' assignments/reservations for an exact interval, not physical presence."""
    return await read("search_employees", {"q": q, "from": start_at, "to": end_at})


@server.tool(structured_output=True)
async def list_spaces(floor_id: str, start_at: str, end_at: str) -> dict[str, Any]:
    """List actual resources, including busy and dedicated, for this floor and time."""
    return await read("list_spaces", {"floor_id": floor_id, "from": start_at, "to": end_at})


@server.tool(structured_output=True)
async def get_availability(
    floor_id: str,
    start_at: str,
    end_at: str,
    kind: str = "",
    min_capacity: int = 1,
    near_employee_id: str = "",
) -> dict[str, Any]:
    """Find free spaces, optionally sorted by distance to a colleague's selected-time resource."""
    return await read(
        "get_availability",
        {
            "floor_id": floor_id,
            "from": start_at,
            "to": end_at,
            "kind": kind,
            "min_capacity": min_capacity,
            "near_employee_id": near_employee_id,
        },
    )


@server.tool(structured_output=True)
async def get_space_details(space_id: str, start_at: str, end_at: str) -> dict[str, Any]:
    """Recheck a real space and its exact interval. This never creates a booking."""
    return await read("get_space_details", {"space_id": space_id, "from": start_at, "to": end_at})


@server.tool(structured_output=True)
async def propose_booking(space_id: str, start_at: str, end_at: str) -> dict[str, Any]:
    """Validate availability and return a proposal only. The human must explicitly confirm in the UI."""
    try:
        selection = Selection(space_id=space_id, start_at=start_at, end_at=end_at)
        return {
            "proposal": await propose(
                rpc(), os.environ["MCP_USER_ID"], os.environ["ASSISTANT_PROPOSAL_SECRET"], selection
            )
        }
    except (ValueError, AssistantError) as error:
        message = (
            error.message
            if isinstance(error, AssistantError)
            else "Укажите корректный будущий интервал с часовым поясом, в пределах одного дня МСК"
        )
        return {"error": {"code": "PROPOSAL_INVALID", "message": message}}


@server.tool(structured_output=True)
async def ask_clarification(missing: list[str]) -> dict[str, Any]:
    """Ask for missing mandatory fields: date, time, type, capacity, employee. Never claim a booking."""
    labels = {
        "date": "дату",
        "time": "время начала и окончания (МСК)",
        "type": "рабочее место или переговорную",
        "capacity": "число участников",
        "employee": "имя сотрудника",
    }
    return {"clarification": [labels[key] for key in dict.fromkeys(missing) if key in labels]}


if __name__ == "__main__":
    server.run()
