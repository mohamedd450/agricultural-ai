from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from openai import OpenAI
from database import get_db
from models import Conversation, Message
from config import get_settings
from datetime import datetime

router = APIRouter(prefix="/api/chat", tags=["chat"])
settings = get_settings()


class ChatRequest(BaseModel):
    message: str
    conversation_id: int | None = None


class ChatResponse(BaseModel):
    reply: str
    conversation_id: int


def get_openai_client():
    return OpenAI(api_key=settings.openai_api_key)


@router.post("", response_model=ChatResponse)
def send_message(request: ChatRequest, db: Session = Depends(get_db)):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="الرسالة لا يمكن أن تكون فارغة")

    if request.conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == request.conversation_id
        ).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="المحادثة غير موجودة")
    else:
        title = request.message[:50] + "..." if len(request.message) > 50 else request.message
        conversation = Conversation(title=title)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    history = db.query(Message).filter(
        Message.conversation_id == conversation.id
    ).order_by(Message.created_at).all()

    messages = [{"role": "system", "content": settings.system_prompt}]
    for msg in history:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": request.message})

    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.message,
    )
    db.add(user_message)

    client = get_openai_client()
    try:
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            max_tokens=settings.max_tokens,
            temperature=0.7,
        )
        reply = response.choices[0].message.content
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=502, detail=f"خطأ في الاتصال بـ OpenAI: {str(e)}")

    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=reply,
    )
    db.add(assistant_message)

    conversation.updated_at = datetime.utcnow()
    db.commit()

    return ChatResponse(reply=reply, conversation_id=conversation.id)
