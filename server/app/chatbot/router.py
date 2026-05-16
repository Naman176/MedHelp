from fastapi import APIRouter, Depends, HTTPException, Request
from langchain_core.messages import HumanMessage
from app.chatbot.models.schemas import ChatRequest
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter()

def get_chatbot_graph(request: Request):
    graph = getattr(request.app.state, "chatbot_graph", None)

    if graph is None:
        raise HTTPException(
            status_code=503,
            detail="Chatbot graph is not initialized yet."
        )

    return graph


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
            "user_id": user_id,
            "user_name": user_name,
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

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))