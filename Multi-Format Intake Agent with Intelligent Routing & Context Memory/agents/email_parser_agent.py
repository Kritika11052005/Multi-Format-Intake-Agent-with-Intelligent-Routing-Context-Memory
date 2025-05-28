import re
import email
from email.parser import Parser
from typing import Dict, Any, Optional
from datetime import datetime
from memory.memory_manager import MemoryManager
from utility.llm_client import LLMClient

class EmailParserAgent:
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        self.llm_client = LLMClient()
        
    async def process(self, email_body: str, subject: Optional[str], session_id: str) -> Dict[str, Any]:
        """Process email content and extract structured information"""
        
        # Parse email components
        parsed_email = self._parse_email_structure(email_body)
        
        # Extract sender information
        sender_info = self._extract_sender_info(email_body, parsed_email)
        
        # Determine urgency and intent using LLM
        analysis = await self._analyze_email_content(email_body, subject)
        
        # Create CRM-style record
        crm_record = self._create_crm_record(sender_info, analysis, subject, email_body)
        
        # Generate conversation ID
        conversation_id = self._generate_conversation_id(sender_info, subject)
        
        result = {
            "agent": "email_parser_agent",
            "conversation_id": conversation_id,
            "sender_info": sender_info,
            "analysis": analysis,
            "crm_record": crm_record,
            "parsed_email": parsed_email,
            "processed_at": datetime.now().isoformat()
        }
        
        # Store in memory
        self.memory_manager.update_session(session_id, result)
        
        return result
    
    def _parse_email_structure(self, email_body: str) -> Dict[str, Any]:
        """Parse email structure to extract headers and content"""
        
        # Try to parse as proper email format
        try:
            msg = Parser().parsestr(email_body)
            return {
                "headers": dict(msg.items()),
                "subject": msg.get('Subject', ''),
                "from": msg.get('From', ''),
                "to": msg.get('To', ''),
                "date": msg.get('Date', ''),
                "body": msg.get_payload()
            }
        except Exception:
            # Fallback for plain text
            return self._parse_plain_text_email(email_body)
    
    def _parse_plain_text_email(self, email_body: str) -> Dict[str, Any]:
        """Parse plain text email"""
        lines = email_body.strip().split('\n')
        headers = {}
        body_start = 0
        
        # Look for header-like patterns
        for i, line in enumerate(lines):
            if ':' in line and len(line.split(':', 1)) == 2:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                if key.lower() in ['from', 'to', 'subject', 'date', 'cc', 'bcc']:
                    headers[key] = value
                    body_start = i + 1
            elif line.strip() == '':
                body_start = i + 1
                break
        
        body = '\n'.join(lines[body_start:]).strip()
        
        return {
            "headers": headers,
            "subject": headers.get('Subject', headers.get('subject', '')),
            "from": headers.get('From', headers.get('from', '')),
            "to": headers.get('To', headers.get('to', '')),
            "date": headers.get('Date', headers.get('date', '')),
            "body": body
        }
    
    def _extract_sender_info(self, email_body: str, parsed_email: Dict[str, Any]) -> Dict[str, Any]:
        """Extract sender information"""
        
        from_field = parsed_email.get('from', '')
        
        # Extract email address
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', from_field)
        email_address = email_match.group(0) if email_match else ''
        
        # Extract name
        name_match = re.search(r'^([^<]+)<', from_field)
        if name_match:
            name = name_match.group(1).strip().strip('"')
        else:
            # Try to extract name from email or content
            if email_address:
                name = email_address.split('@')[0].replace('.', ' ').replace('_', ' ').title()
            else:
                name = self._extract_name_from_content(email_body)
        
        # Extract company/domain
        company = ''
        if email_address:
            domain = email_address.split('@')[1]
            company = domain.split('.')[0].title()
        
        return {
            "name": name,
            "email": email_address,
            "company": company,
            "full_from_field": from_field
        }
    
    def _extract_name_from_content(self, content: str) -> str:
        """Try to extract name from email content"""
        
        # Look for signature patterns
        signature_patterns = [
            r'Best regards,\s*\n([^\n]+)',
            r'Sincerely,\s*\n([^\n]+)',
            r'Thanks,\s*\n([^\n]+)',
            r'Regards,\s*\n([^\n]+)',
        ]
        
        for pattern in signature_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1).strip()
        
        return "Unknown Sender"
    
    async def _analyze_email_content(self, email_body: str, subject: Optional[str]) -> Dict[str, Any]:
        """Analyze email content for intent and urgency using LLM"""
        
        prompt = f"""
        Analyze this email and provide:
        1. Intent/Purpose (RFQ, Support Request, Complaint, General Inquiry, etc.)
        2. Urgency Level (Low, Medium, High, Critical)
        3. Key Topics/Tags (up to 5 relevant keywords)
        4. Required Action (if any)
        5. Sentiment (Positive, Neutral, Negative)
        
        Subject: {subject or "No subject"}
        
        Email Content:
        {email_body[:1500]}...
        
        Please respond in JSON format:
        {{
            "intent": "...",
            "urgency": "...",
            "topics": [...],
            "required_action": "...",
            "sentiment": "...",
            "confidence": "..."
        }}
        """
        
        try:
            response = await self.llm_client.generate(prompt)
            analysis = eval(response)  # In production, use proper JSON parsing
            return analysis
        except Exception as e:
            print(f"Error analyzing email: {e}")
            return {
                "intent": "General Inquiry",
                "urgency": "Medium",
                "topics": ["general"],
                "required_action": "Review and respond",
                "sentiment": "Neutral",
                "confidence": "Low"
            }
    
    def _create_crm_record(self, sender_info: Dict[str, Any], analysis: Dict[str, Any], 
                          subject: Optional[str], email_body: str) -> Dict[str, Any]:
        """Create CRM-style record"""
        
        return {
            "contact": {
                "name": sender_info["name"],
                "email": sender_info["email"],
                "company": sender_info["company"]
            },
            "interaction": {
                "type": "email",
                "subject": subject or "No Subject",
                "intent": analysis.get("intent", "General"),
                "urgency": analysis.get("urgency", "Medium"),
                "sentiment": analysis.get("sentiment", "Neutral"),
                "topics": analysis.get("topics", []),
                "required_action": analysis.get("required_action", "Review"),
                "content_preview": email_body[:200] + "..." if len(email_body) > 200 else email_body,
                "timestamp": datetime.now().isoformat(),
                "status": "new"
            },
            "metadata": {
                "content_length": len(email_body),
                "has_attachments": "attachment" in email_body.lower(),
                "language": "en",  # Could be enhanced with language detection
                "source": "email_parser_agent"
            }
        }
    
    def _generate_conversation_id(self, sender_info: Dict[str, Any], subject: Optional[str]) -> str:
        """Generate unique conversation ID"""
        
        # Create ID based on sender email and subject
        base_string = f"{sender_info.get('email', 'unknown')}_{subject or 'no_subject'}"
        
        # Simple hash-like ID (in production, use proper hashing)
        import hashlib
        conversation_id = hashlib.md5(base_string.encode()).hexdigest()[:12]
        
        return f"conv_{conversation_id}"