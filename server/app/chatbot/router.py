from fastapi import APIRouter, Depends, HTTPException, Request
from sse_starlette.sse import EventSourceResponse
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from app.core.config import settings
from app.chatbot.agent.graph import build_graph
from app.chatbot.models.schemas import ChatRequest
from app.dependencies import get_current_user
from app.models.user import User
import json

router = APIRouter()

def get_chatbot_graph(request: Request):
    graph = getattr(request.app.state, "chatbot_graph", None)

    if graph is None:
        raise HTTPException(
            status_code=503,
            detail="Chatbot graph is not initialized yet."
        )

    return graph


@router.post("/chat/stream")
async def chat_stream(
    chat_request: ChatRequest,
    fastapi_request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    SSE streaming endpoint. Requires JWT auth.

    Frontend usage:
        POST /chatbot/chat/stream
        Headers: Authorization: Bearer <jwt_token>
                 Content-Type: application/json
        Body: { "message": "...", "thread_id": "unique-session-id" }

    The frontend should:
    - Generate a UUID as thread_id when the chat opens
    - Store it in localStorage so the same conversation continues on refresh
    - Send it with every message
    """

    graph = get_chatbot_graph(fastapi_request)

    user_id = str(current_user.id)
    user_name = current_user.full_name or ""

    # Important: scope memory to the logged-in user
    thread_key = f"user:{user_id}:thread:{chat_request.thread_id}"

    async def generate():
        try:
                config = {
                    "configurable": {
                        "thread_id": thread_key
                    }
                }
                input_state = {
                    "messages": [HumanMessage(content=chat_request.message)],
                    "phase": "general",
                    "recommended_specialist": "",
                    "user_id": str(current_user.id),
                    "user_name": current_user.full_name,
                }
                async for event in graph.astream_events(
                    input_state,
                    config=config,
                    version="v2"
                ):
                    kind = event["event"]
                    if kind == "on_chat_model_stream":
                        chunk = event["data"]["chunk"]
                        if chunk.content:
                            yield {
                                "event": "message",
                                "data": json.dumps({
                                    "token": chunk.content,
                                    "done": False
                                })
                            }
                yield {
                    "event": "message",
                    "data": json.dumps({"token": "", "done": True})
                }


        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }
        finally:
            # Always send done — ensures frontend loading state is cleared
            yield {"event": "done", "data": ""}

    return EventSourceResponse(generate())


@router.post("/chat")
async def chat_simple(
    chat_request: ChatRequest,
    fastapi_request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Non-streaming endpoint. Use for testing with curl or FastAPI /docs.

    Test sequence (use the same thread_id across calls to verify memory):

    Call 1: {"message": "I have chest pain", "thread_id": "test-001"}
    Call 2: {"message": "show me doctors on Monday", "thread_id": "test-001"}
            → Bot should search for cardiologists without you repeating it.

    Direct booking test (no symptom phase):
    Call 1: {"message": "find me a dentist on tuesday and wednesday", "thread_id": "test-002"}
            → Bot should directly search for dentists on those two days.
    """
    try:
            graph = get_chatbot_graph(fastapi_request)

            user_id = str(current_user.id)
            user_name = current_user.full_name or ""

            # Important: scope memory to the logged-in user
            thread_key = f"user:{user_id}:thread:{chat_request.thread_id}"

            config = {"configurable": {"thread_id": thread_key}}

            input_state = {
                "messages": [HumanMessage(content=chat_request.message)],
                "phase": "general",
                "recommended_specialist": "",
                "user_id": str(current_user.id),
                "user_name": current_user.full_name,
            }

            result = await graph.ainvoke(input_state, config=config)

            ai_messages = [
                m for m in result["messages"]
                if hasattr(m, "content")
                and not isinstance(m, HumanMessage)
                and m.__class__.__name__ != "ToolMessage"
                and m.content
            ]

            last_response = ai_messages[-1].content if ai_messages else "No response generated."

            return {
                "response": last_response,
                "thread_id": chat_request.thread_id,
                "phase_detected": result.get("phase"),
                "recommended_specialist": result.get("recommended_specialist", ""),
                "user": current_user.full_name,
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))