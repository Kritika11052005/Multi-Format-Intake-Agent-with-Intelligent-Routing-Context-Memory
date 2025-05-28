import uuid
import redis
import json
from datetime import datetime
from typing import Dict, Any, Optional, List

class MemoryManager:
    """Manages session memory using Redis backend"""
    
    def __init__(self, redis_host: str = 'redis', redis_port: int = 6379):
        self.redis_client = redis.Redis(
            host=redis_host, 
            port=redis_port, 
            decode_responses=True
        )
        self.session_prefix = "session:"
        self.sessions_key = "active_sessions"
    
    def create_session(self, source: str, input_type: str, intent: str, 
                    timestamp: datetime) -> str:
        """Create a new session and return session ID"""
        session_id = str(uuid.uuid4())
        
        session_data = {
            "session_id": session_id,
            "source": source,
            "input_type": input_type,
            "intent": intent,
            "created_at": timestamp.isoformat(),
            "updated_at": timestamp.isoformat(),
            "status": "active",
            "processing_history": [],
            "extracted_data": {},
            "metadata": {}
        }
        
        # Store session data
        session_key = f"{self.session_prefix}{session_id}"
        self.redis_client.hset(session_key, mapping={
            k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) 
            for k, v in session_data.items()
        })
        
        # Add to active sessions set
        self.redis_client.sadd(self.sessions_key, session_id)
        
        # Set expiration (24 hours)
        self.redis_client.expire(session_key, 86400)
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data"""
        session_key = f"{self.session_prefix}{session_id}"
        
        if not self.redis_client.exists(session_key):
            return None
        
        raw_data = self.redis_client.hgetall(session_key)
        
        # Parse JSON fields back to objects
        session_data = {}
        for key, value in raw_data.items():
            try:
                # Try to parse as JSON first
                session_data[key] = json.loads(value)
            except:
                # If not JSON, keep as string
                session_data[key] = value
        
        return session_data
    
    def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session data"""
        session_key = f"{self.session_prefix}{session_id}"
        
        if not self.redis_client.exists(session_key):
            return False
        
        # Add timestamp
        updates["updated_at"] = datetime.now().isoformat()
        
        # Convert complex objects to JSON strings
        redis_updates = {
            k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
            for k, v in updates.items()
        }
        
        self.redis_client.hset(session_key, mapping=redis_updates)
        return True
    
    def add_processing_step(self, session_id: str, agent_name: str, 
                           result: Dict[str, Any]) -> bool:
        """Add a processing step to session history"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        processing_step = {
            "agent": agent_name,
            "timestamp": datetime.now().isoformat(),
            "result": result
        }
        
        session["processing_history"].append(processing_step)
        
        return self.update_session(session_id, {
            "processing_history": session["processing_history"]
        })
    
    def store_extracted_data(self, session_id: str, data_key: str, 
                            data_value: Any) -> bool:
        """Store extracted data in session"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session["extracted_data"][data_key] = data_value
        
        return self.update_session(session_id, {
            "extracted_data": session["extracted_data"]
        })
    
    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """Get all active sessions"""
        session_ids = self.redis_client.smembers(self.sessions_key)
        sessions = []
        
        for session_id in session_ids:
            session = self.get_session(session_id)
            if session:
                sessions.append(session)
        
        return sessions
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        session_key = f"{self.session_prefix}{session_id}"
        
        # Remove from active sessions
        self.redis_client.srem(self.sessions_key, session_id)
        
        # Delete session data
        return bool(self.redis_client.delete(session_key))
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions from the active sessions set"""
        session_ids = self.redis_client.smembers(self.sessions_key)
        
        for session_id in session_ids:
            session_key = f"{self.session_prefix}{session_id}"
            if not self.redis_client.exists(session_key):
                self.redis_client.srem(self.sessions_key, session_id)