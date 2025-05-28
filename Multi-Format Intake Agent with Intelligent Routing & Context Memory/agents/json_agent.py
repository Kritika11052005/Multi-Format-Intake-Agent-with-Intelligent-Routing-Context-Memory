# agents/json_agent.py
from typing import Dict, Any
from memory.memory_manager import MemoryManager

class JSONAgent:
    """Agent for processing JSON data"""
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory = memory_manager
    
    async def process(self, data: Dict[Any, Any], session_id: str) -> Dict[str, Any]:
        """Process JSON data"""
        try:
            # Basic JSON processing logic
            result = {
                "status": "success",
                "data_type": "json",
                "keys_found": list(data.keys()) if isinstance(data, dict) else [],
                "total_fields": len(data) if isinstance(data, dict) else 0,
                "processed_data": data
            }
            
            # Store in memory
            self.memory.add_processing_step(session_id, "JSONAgent", result)
            self.memory.store_extracted_data(session_id, "json_data", data)
            
            return result
            
        except Exception as e:
            error_result = {
                "status": "error",
                "error": str(e),
                "data_type": "json"
            }
            self.memory.add_processing_step(session_id, "JSONAgent", error_result)
            return error_result

# agents/email_parser_agent.py
from typing import Optional, Dict, Any
from memory.memory_manager import MemoryManager
import re

class EmailParserAgent:
    """Agent for parsing email content"""
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory = memory_manager
    
    async def process(self, email_body: str, subject: Optional[str], session_id: str) -> Dict[str, Any]:
        """Process email content"""
        try:
            # Extract email information
            extracted_data = {
                "subject": subject,
                "body_length": len(email_body),
                "emails_found": self._extract_emails(email_body),
                "urls_found": self._extract_urls(email_body),
                "phone_numbers": self._extract_phone_numbers(email_body)
            }
            
            result = {
                "status": "success",
                "data_type": "email",
                "extracted_data": extracted_data,
                "summary": f"Parsed email with {len(extracted_data['emails_found'])} email addresses found"
            }
            
            # Store in memory
            self.memory.add_processing_step(session_id, "EmailParserAgent", result)
            self.memory.store_extracted_data(session_id, "email_data", extracted_data)
            
            return result
            
        except Exception as e:
            error_result = {
                "status": "error",
                "error": str(e),
                "data_type": "email"
            }
            self.memory.add_processing_step(session_id, "EmailParserAgent", error_result)
            return error_result
    
    def _extract_emails(self, text: str) -> list:
        """Extract email addresses from text"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return list(set(re.findall(email_pattern, text)))
    
    def _extract_urls(self, text: str) -> list:
        """Extract URLs from text"""
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        return list(set(re.findall(url_pattern, text)))
    
    def _extract_phone_numbers(self, text: str) -> list:
        """Extract phone numbers from text"""
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        return list(set(re.findall(phone_pattern, text)))

# agents/pdf_agent.py
from typing import Dict, Any
from memory.memory_manager import MemoryManager

class PDFAgent:
    """Agent for processing PDF documents"""
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory = memory_manager
    
    async def process(self, content: str, session_id: str) -> Dict[str, Any]:
        """Process PDF content"""
        try:
            # Basic PDF text analysis
            word_count = len(content.split())
            char_count = len(content)
            
            # Simple keyword extraction (you can enhance this)
            keywords = self._extract_keywords(content)
            
            result = {
                "status": "success",
                "data_type": "pdf",
                "word_count": word_count,
                "character_count": char_count,
                "keywords": keywords[:10],  # Top 10 keywords
                "summary": f"Processed PDF with {word_count} words"
            }
            
            # Store in memory
            self.memory.add_processing_step(session_id, "PDFAgent", result)
            self.memory.store_extracted_data(session_id, "pdf_text", content)
            
            return result
            
        except Exception as e:
            error_result = {
                "status": "error",
                "error": str(e),
                "data_type": "pdf"
            }
            self.memory.add_processing_step(session_id, "PDFAgent", error_result)
            return error_result
    
    def _extract_keywords(self, text: str) -> list:
        """Simple keyword extraction"""
        # Remove common stop words and extract frequent words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = text.lower().split()
        
        # Count word frequency
        word_freq = {}
        for word in words:
            word = word.strip('.,!?;:"()[]{}')
            if len(word) > 3 and word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Return sorted by frequency
        return sorted(word_freq.keys(), key=lambda x: word_freq[x], reverse=True)