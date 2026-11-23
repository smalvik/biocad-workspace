"""Deterministic HTTP provider for isolated regression ONLY, never deployed as an LLM."""

import json

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()


@app.get("/healthz")
async def health():
    return {"fixture": True}


@app.post("/v1/chat/completions")
async def completions(request: Request):
    body = await request.json()
    assert request.headers["authorization"] == "Bearer fixture-not-secret"
    assert body["model"] in {"test/scripted", "test/fallback"}
    assert body["provider"]["max_price"] == {"prompt": 0, "completion": 0, "request": 0}
    assert body["provider"]["allow_fallbacks"] is False
    messages = body["messages"]
    user = next(m["content"] for m in reversed(messages) if m["role"] == "user")
    if "сбой AI" in user:
        return JSONResponse({"error": "scripted provider outage"}, status_code=503)
    if "резерв AI" in user and body["model"] == "test/scripted":
        return JSONResponse({"error": "scripted primary outage"}, status_code=503)
    context = json.loads(messages[0]["content"].split("\nContext: ")[1])["selected"]
    start, end = context["start_at"], context["end_at"]
    tool_results = [json.loads(m["content"]) for m in messages if m["role"] == "tool"]
    if "предел раундов" in user:
        if len(tool_results) < 3:
            name, arguments = "search_employees", {"q": "Анна", "start_at": start, "end_at": end}
        else:
            name, arguments = (
                "get_availability",
                {"floor_id": context["floor_id"], "start_at": start, "end_at": end, "kind": "DESK"},
            )
    elif "уточни" in user:
        name, arguments = "ask_clarification", {"missing": ["date", "time"]}
    elif "несуществующее" in user:
        name, arguments = "propose_booking", {"space_id": "NO-SUCH-SPACE", "start_at": start, "end_at": end}
    elif "постоянное" in user:
        name, arguments = "propose_booking", {"space_id": "D-01", "start_at": start, "end_at": end}
    elif tool_results and tool_results[-1].get("items"):
        name, arguments = (
            "propose_booking",
            {"space_id": tool_results[-1]["items"][0]["id"], "start_at": start, "end_at": end},
        )
    else:
        name, arguments = (
            "get_availability",
            {
                "floor_id": context["floor_id"],
                "start_at": start,
                "end_at": end,
                "kind": "MEETING_ROOM" if "переговорную" in user else "DESK",
                "min_capacity": 6 if "переговорную" in user else 1,
            },
        )
    return {
        "model": body["model"],
        "usage": {"cost": 0},
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "fixture-call-" + str(len(messages)),
                            "type": "function",
                            "function": {"name": name, "arguments": json.dumps(arguments)},
                        }
                    ],
                }
            }
        ],
    }
