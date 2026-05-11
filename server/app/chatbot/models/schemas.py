from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="The user's message to the chatbot")
    thread_id: str = Field(..., description="Unique session ID — same ID continues the same conversation")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "I have chest pain and shortness of breath",
                "thread_id": "user-session-abc123"
            }
        }