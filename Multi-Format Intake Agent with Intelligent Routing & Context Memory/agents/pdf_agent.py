import PyPDF2
import io
from typing import Dict, Any, List
from datetime import datetime
from memory.memory_manager import MemoryManager
from utility.llm_client import LLMClient

class PDFAgent:
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        self.llm_client = LLMClient()
        
    async def process(self, pdf_content: bytes, session_id: str) -> Dict[str, Any]:
        """Process PDF content and extract structured information"""
        
        # Extract text from PDF
        extracted_text = self._extract_text_from_pdf(pdf_content)
        
        # Analyze document structure
        document_analysis = await self._analyze_document(extracted_text)
        
        # Extract key information using LLM
        extracted_data = await self._extract_key_information(extracted_text, document_analysis)
        
        # Identify document type and extract specific fields
        document_classification = await self._classify_document_type(extracted_text)
        
        result = {
            "agent": "pdf_agent",
            "document_classification": document_classification,
            "extracted_text": extracted_text[:1000] + "..." if len(extracted_text) > 1000 else extracted_text,
            "document_analysis": document_analysis,
            "extracted_data": extracted_data,
            "processed_at": datetime.now().isoformat()
        }
        
        # Store in memory
        self.memory_manager.update_session(session_id, result)
        
        return result
    
    def _extract_text_from_pdf(self, pdf_content: bytes) -> str:
        """Extract text content from PDF"""
        try:
            pdf_file = io.BytesIO(pdf_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    text += f"\n--- Page {page_num + 1} ---\n{page_text}"
                except Exception as e:
                    text += f"\n--- Page {page_num + 1} (Error extracting text) ---\n"
            
            return text.strip()
            
        except Exception as e:
            return f"Error extracting PDF text: {str(e)}"
    
    async def _analyze_document(self, text: str) -> Dict[str, Any]:
        """Analyze document structure and characteristics"""
        
        lines = text.split('\n')
        words = text.split()
        
        # Basic statistics
        stats = {
            "total_lines": len(lines),
            "total_words": len(words),
            "total_characters": len(text),
            "avg_words_per_line": len(words) / len(lines) if lines else 0
        }
        
        # Look for structured elements
        structure_elements = {
            "has_tables": self._detect_tables(text),
            "has_headers": self._detect_headers(lines),
            "has_addresses": self._detect_addresses(text),
            "has_dates": self._detect_dates(text),
            "has_amounts": self._detect_amounts(text),
            "has_phone_numbers": self._detect_phone_numbers(text),
            "has_emails": self._detect_emails(text)
        }
        
        return {
            "statistics": stats,
            "structure_elements": structure_elements,
            "document_sections": self._identify_sections(lines)
        }
    
    def _detect_tables(self, text: str) -> bool:
        """Detect if document contains tables"""
        import re
        # Look for patterns that suggest tabular data
        table_patterns = [
            r'\|.*\|.*\|',  # Pipe-separated
            r'\t.*\t.*\t',  # Tab-separated
            r'^\s*\w+\s+\$?[\d,]+\.?\d*\s*$',  # Amount columns
        ]
        
        for pattern in table_patterns:
            if re.search(pattern, text, re.MULTILINE):
                return True
        return False
    
    def _detect_headers(self, lines: List[str]) -> bool:
        """Detect document headers"""
        # Look for lines that might be headers (short, all caps, etc.)
        for line in lines[:10]:  # Check first 10 lines
            if line.strip() and (line.isupper() or len(line.split()) <= 5):
                return True
        return False
    
    def _detect_addresses(self, text: str) -> bool:
        """Detect addresses in text"""
        import re
        address_patterns = [
            r'\d+\s+\w+\s+(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd)',
            r'\b\d{5}(-\d{4})?\b',  # ZIP codes
            r'\b[A-Z]{2}\s+\d{5}\b'  # State ZIP
        ]
        
        for pattern in address_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _detect_dates(self, text: str) -> bool:
        """Detect dates in text"""
        import re
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{2,4}',
            r'\d{1,2}-\d{1,2}-\d{2,4}',
            r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+\d{2,4}',
            r'\d{4}-\d{2}-\d{2}'
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _detect_amounts(self, text: str) -> bool:
        """Detect monetary amounts"""
        import re
        amount_patterns = [
            r'\$[\d,]+\.?\d*',
            r'USD\s*[\d,]+\.?\d*',
            r'Total:?\s*\$?[\d,]+\.?\d*'
        ]
        
        for pattern in amount_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _detect_phone_numbers(self, text: str) -> bool:
        """Detect phone numbers"""
        import re
        phone_patterns = [
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            r'\(\d{3}\)\s*\d{3}[-.]?\d{4}',
            r'\b\d{3}\s\d{3}\s\d{4}\b'
        ]
        
        for pattern in phone_patterns:
            if re.search(pattern, text):
                return True
        return False
    
    def _detect_emails(self, text: str) -> bool:
        """Detect email addresses"""
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return bool(re.search(email_pattern, text))
    
    def _identify_sections(self, lines: List[str]) -> List[str]:
        """Identify document sections"""
        sections = []
        current_section = []
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_section:
                    sections.append('\n'.join(current_section))
                    current_section = []
            else:
                current_section.append(line)
        
        if current_section:
            sections.append('\n'.join(current_section))
        
        return sections[:5]  # Return first 5 sections
    
    async def _extract_key_information(self, text: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key information using LLM"""
        
        prompt = f"""
        Extract key information from this document. Based on the document analysis, focus on:
        - Document title/header
        - Key dates
        - Names and contact information
        - Monetary amounts
        - Important numbers (invoice numbers, account numbers, etc.)
        - Addresses
        - Main content summary
        
        Document Analysis Context:
        - Has tables: {analysis['structure_elements']['has_tables']}
        - Has amounts: {analysis['structure_elements']['has_amounts']}
        - Has dates: {analysis['structure_elements']['has_dates']}
        - Has addresses: {analysis['structure_elements']['has_addresses']}
        
        Document Text (first 2000 chars):
        {text[:2000]}...
        
        Return extracted information in JSON format with clear field names.
        """
        
        try:
            response = await self.llm_client.generate(prompt)
            # Parse LLM response
            import json
            extracted = json.loads(response)
            return extracted
        except Exception as e:
            print(f"Error extracting information: {e}")
            return self._basic_extraction(text)
    
    def _basic_extraction(self, text: str) -> Dict[str, Any]:
        """Basic information extraction as fallback"""
        import re
        
        extracted = {}
        
        # Extract emails
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        if emails:
            extracted['emails'] = emails
        
        # Extract phone numbers
        phones = re.findall(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', text)
        if phones:
            extracted['phone_numbers'] = phones
        
        # Extract amounts
        amounts = re.findall(r'\$[\d,]+\.?\d*', text)
        if amounts:
            extracted['amounts'] = amounts
        
        # Extract dates
        dates = re.findall(r'\d{1,2}/\d{1,2}/\d{2,4}', text)
        if dates:
            extracted['dates'] = dates
        
        return extracted
    
    async def _classify_document_type(self, text: str) -> Dict[str, Any]:
        """Classify the type of PDF document"""
        
        prompt = f"""
        Classify this document type based on its content. 
        
        Common document types:
        - Invoice
        - Receipt
        - Contract
        - Report
        - Letter
        - Form
        - Certificate
        - Manual
        - Brochure
        
        Document content (first 1000 chars):
        {text[:1000]}...
        
        Respond with:
        {{
            "document_type": "...",
            "confidence": "high/medium/low",
            "key_indicators": ["...", "..."],
            "business_category": "..."
        }}
        """
        
        try:
            response = await self.llm_client.generate(prompt)
            import json
            classification = json.loads(response)
            return classification
        except Exception as e:
            print(f"Error classifying document: {e}")
            return {
                "document_type": "Unknown",
                "confidence": "low",
                "key_indicators": [],
                "business_category": "General"
            }
