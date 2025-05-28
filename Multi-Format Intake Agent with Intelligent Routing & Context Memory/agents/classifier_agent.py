from typing import Dict, Any, Optional
import json

class ClassifierAgent:
    """Agent responsible for classifying input content and determining intent"""
    
    def __init__(self):
        self.format_patterns = {
            'application/pdf': 'pdf',
            'application/json': 'json',
            'text/json': 'json',
            'message/rfc822': 'email',
            'text/plain': 'text',
            'text/html': 'html'
        }
    
    async def classify(self, content: Any, file_type: Optional[str] = None, 
                    filename: Optional[str] = None, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Classify the input content and determine format and intent"""
        
        # Determine format
        format_type = self._determine_format(content, file_type, filename)
        
        # Determine intent based on content analysis
        intent = await self._determine_intent(content, format_type, metadata)
        
        # Calculate confidence score
        confidence = self._calculate_confidence(content, format_type, intent)
        
        return {
            "format": format_type,
            "intent": intent,
            "confidence": confidence,
            "metadata": {
                "file_type": file_type,
                "filename": filename,
                "content_length": len(str(content)) if content else 0
            }
        }
    
    def _determine_format(self, content: Any, file_type: Optional[str] = None, 
                        filename: Optional[str] = None) -> str:
        """Determine the format of the input"""
        
        # Check file type first
        if file_type and file_type in self.format_patterns:
            return self.format_patterns[file_type]
        
        # Check filename extension
        if filename:
            extension = filename.lower().split('.')[-1]
            if extension == 'pdf':
                return 'pdf'
            elif extension in ['json', 'jsonl']:
                return 'json'
            elif extension in ['eml', 'msg']:
                return 'email'
            elif extension in ['txt', 'text']:
                return 'text'
            elif extension in ['html', 'htm']:
                return 'html'
        
        # Analyze content structure
        if isinstance(content, dict) or self._is_json_string(content):
            return 'json'
        elif isinstance(content, str):
            if content.strip().startswith('%PDF'):
                return 'pdf'
            elif self._looks_like_email(content):
                return 'email'
            elif content.strip().startswith('<html'):
                return 'html'
            else:
                return 'text'
        
        return 'unknown'
    
    async def _determine_intent(self, content: Any, format_type: str, 
                            metadata: Optional[Dict] = None) -> str:
        """Determine the intent/purpose of the content"""
        
        # Basic intent classification based on content analysis
        content_str = str(content).lower()
        
        # Check for common intents
        if any(word in content_str for word in ['invoice', 'bill', 'payment', 'charge']):
            return 'invoice_processing'
        elif any(word in content_str for word in ['resume', 'cv', 'experience', 'education']):
            return 'resume_parsing'
        elif any(word in content_str for word in ['order', 'purchase', 'buy', 'cart']):
            return 'order_processing'
        elif any(word in content_str for word in ['support', 'help', 'issue', 'problem']):
            return 'support_ticket'
        elif any(word in content_str for word in ['application', 'apply', 'form']):
            return 'form_processing'
        elif format_type == 'email':
            return 'email_processing'
        elif format_type == 'pdf':
            return 'document_processing'
        else:
            return 'general_processing'
    
    def _calculate_confidence(self, content: Any, format_type: str, intent: str) -> float:
        """Calculate confidence score for the classification"""
        base_confidence = 0.7
        
        # Boost confidence for clear format indicators
        if format_type in ['pdf', 'json', 'email']:
            base_confidence += 0.2
        
        # Boost confidence for clear intent indicators
        if intent != 'general_processing':
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)
    
    def _is_json_string(self, content: Any) -> bool:
        """Check if string content is valid JSON"""
        if not isinstance(content, str):
            return False
        try:
            json.loads(content)
            return True
        except:
            return False
    
    def _looks_like_email(self, content: str) -> bool:
        """Check if content looks like an email"""
        email_indicators = ['from:', 'to:', 'subject:', 'date:', '@']
        return any(indicator in content.lower() for indicator in email_indicators)