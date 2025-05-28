from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any
import uvicorn

from agents.classifier_agent import ClassifierAgent
from agents.json_agent import JSONAgent
from agents.email_parser_agent import EmailParserAgent
from agents.pdf_agent import PDFAgent
from memory.memory_manager import MemoryManager
from utility.file_handler import FileHandler

app = FastAPI(title="Multi-Format Intake Agent", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
memory_manager = MemoryManager()
classifier_agent = ClassifierAgent()
json_agent = JSONAgent(memory_manager)
email_agent = EmailParserAgent(memory_manager)
pdf_agent = PDFAgent(memory_manager)
file_handler = FileHandler()

@app.get("/")
async def root():
    return {"message": "Multi-Format Intake Agent is running!"}

@app.post("/process/file")
async def process_file(file: UploadFile = File(...)):
    """Process uploaded file (PDF, JSON, etc.)"""
    try:
        # Save uploaded file
        file_path = await file_handler.save_upload(file)
        
        # Read file content
        content = await file_handler.read_file(file_path, file.content_type)
        
        # Classify the input
        classification = await classifier_agent.classify(
            content=content,
            file_type=file.content_type,
            filename=file.filename
        )
        
        # Store initial metadata
        session_id = memory_manager.create_session(
            source=file.filename,
            input_type=classification["format"],
            intent=classification["intent"],
            timestamp=datetime.now()
        )
        
        # Route to appropriate agent
        result = await route_to_agent(classification, content, session_id)
        
        return {
            "session_id": session_id,
            "classification": classification,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process/email")
async def process_email(email_body: str = Form(...), subject: Optional[str] = Form(None)):
    """Process email content"""
    try:
        # Classify the email
        classification = await classifier_agent.classify(
            content=email_body,
            file_type="email",
            metadata={"subject": subject}
        )
        
        # Create session
        session_id = memory_manager.create_session(
            source="email",
            input_type="email",
            intent=classification["intent"],
            timestamp=datetime.now()
        )
        
        # Process with email agent
        result = await email_agent.process(email_body, subject, session_id)
        
        return {
            "session_id": session_id,
            "classification": classification,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process/json")
async def process_json(data: Dict[Any, Any]):
    """Process JSON data"""
    try:
        json_content = json.dumps(data)
        
        # Classify the JSON
        classification = await classifier_agent.classify(
            content=json_content,
            file_type="json"
        )
        
        # Create session
        session_id = memory_manager.create_session(
            source="api",
            input_type="json",
            intent=classification["intent"],
            timestamp=datetime.now()
        )
        
        # Process with JSON agent
        result = await json_agent.process(data, session_id)
        
        return {
            "session_id": session_id,
            "classification": classification,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memory/{session_id}")
async def get_session_memory(session_id: str):
    """Retrieve session memory"""
    try:
        memory = memory_manager.get_session(session_id)
        if not memory:
            raise HTTPException(status_code=404, detail="Session not found")
        return memory
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memory")
async def get_all_sessions():
    """Retrieve all sessions"""
    try:
        return memory_manager.get_all_sessions()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def route_to_agent(classification: Dict, content: Any, session_id: str):
    """Route content to appropriate agent based on classification"""
    format_type = classification["format"].lower()
    
    if format_type == "pdf":
        return await pdf_agent.process(content, session_id)
    elif format_type == "json":
        return await json_agent.process(json.loads(content) if isinstance(content, str) else content, session_id)
    elif format_type == "email":
        return await email_agent.process(content, None, session_id)
    else:
        raise ValueError(f"Unsupported format: {format_type}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)