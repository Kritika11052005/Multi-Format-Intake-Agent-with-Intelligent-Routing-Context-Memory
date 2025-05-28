from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

class SessionCreate(BaseModel):
    source: str
    input_type: str
    intent: str
    timestamp: datetime

class SessionData(BaseModel):
    session_id: str
    source: str
    input_type: str
    intent: str
    timestamp: str
    data: Dict[str, Any]
    created_at: str
    updated_at: str

class FlowBitSchema(BaseModel):
    id: str
    timestamp: str
    source: str
    data: Dict[str, Any]

class CRMRecord(BaseModel):
    contact: Dict[str, Any]
    interaction: Dict[str, Any]
    metadata: Dict[str, Any]

class ConversationThread(BaseModel):
    thread_id: str
    conversation_id: str
    session_id: str
    message_data: Dict[str, Any]
    timestamp: str
