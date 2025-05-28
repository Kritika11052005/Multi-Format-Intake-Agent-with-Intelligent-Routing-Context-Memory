Multi-Format Intake Agent with Intelligent Routing & Context Memory
🎯 Objective
Build a multi-agent AI system that can accept data in PDF, JSON, or Email (text) format, intelligently classify the input type and purpose, and then route it to the right specialized agent for extraction. The system maintains context (e.g., sender, topic, last extracted fields) to support downstream chaining or audits.
🏗️ System Architecture
Core Components
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Input Data    │───▶│ Classifier Agent │───▶│ Routing Engine  │
│ (PDF/JSON/Email)│    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │ Shared Memory   │    │ Specialized     │
                       │   Module        │    │   Agents        │
                       └─────────────────┘    └─────────────────┘
                                                        │
                              ┌─────────────────────────┼─────────────────────────┐
                              │                         │                         │
                              ▼                         ▼                         ▼
                    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
                    │   PDF Agent     │    │   JSON Agent    │    │  Email Parser   │
                    │                 │    │                 │    │     Agent       │
                    └─────────────────┘    └─────────────────┘    └─────────────────┘
🤖 Agent Specifications
1. Classifier Agent
Responsibilities:

Receives raw input (file/email/JSON body)
Classifies format: PDF / JSON / Email
Determines intent: Invoice, RFQ, Complaint, Regulation, etc.
Routes to appropriate extraction agent
Adds format + intent to shared memory

Input: Raw data streams
Output: Classification metadata + routing decision
2. JSON Agent
Responsibilities:

Accepts arbitrary JSON (webhook payloads, APIs)
Extracts and re-formats data to defined FlowBit schema
Identifies anomalies or missing fields
Validates data integrity

Input: JSON objects
Output: Structured FlowBit schema + validation report
3. Email Parser Agent
Responsibilities:

Accepts email body text (plain or HTML)
Extracts sender name, request intent, urgency level
Returns formatted CRM-style record
Stores conversation ID + parsed metadata

Input: Email text/HTML
Output: CRM-formatted contact record + metadata
4. PDF Agent (Bonus)
Responsibilities:

Extracts text and structured data from PDF documents
Handles invoices, contracts, forms
OCR capabilities for scanned documents

Input: PDF files
Output: Extracted structured data
💾 Shared Memory Module
Storage Requirements

Input metadata: source, type, timestamp
Extracted fields: per agent output
Thread/conversation ID: if available
Processing history: audit trail

Implementation Options

Redis: For distributed systems
SQLite: For lightweight local deployment
In-memory store: For development/testing

Memory Schema
python{
    "session_id": "uuid",
    "timestamp": "2025-05-29T10:30:00Z",
    "input": {
        "type": "email|json|pdf",
        "source": "filename|sender|endpoint",
        "raw_data": "...",
        "size": 1024
    },
    "classification": {
        "format": "email",
        "intent": "rfq",
        "confidence": 0.95,
        "agent_assigned": "email_parser"
    },
    "extraction": {
        "agent": "email_parser",
        "fields": {...},
        "anomalies": [...],
        "status": "completed"
    },
    "context": {
        "conversation_id": "thread_123",
        "related_sessions": ["uuid1", "uuid2"],
        "priority": "high"
    }
}
📁 Project Structure
multi-format-intake-agent/
├── README.md
├── requirements.txt
├── docker-compose.yml
├── .env.example
├── main.py
├── agents/
│   ├── __init__.py
│   ├── classifier.py
│   ├── json_agent.py
│   ├── email_parser.py
│   └── pdf_agent.py
├── memory/
│   ├── __init__.py
│   ├── redis_store.py
│   ├── sqlite_store.py
│   └── in_memory_store.py
├── utils/
│   ├── __init__.py
│   ├── file_handlers.py
│   ├── schema_validator.py
│   └── logging_config.py
├── data/
│   ├── sample_inputs/
│   │   ├── emails/
│   │   ├── json/
│   │   └── pdfs/
│   └── schemas/
│       ├── flowbit_schema.json
│       └── crm_schema.json
├── tests/
│   ├── test_classifier.py
│   ├── test_agents.py
│   └── test_memory.py
├── api/
│   ├── __init__.py
│   ├── fastapi_server.py
│   └── routes/
│       ├── upload.py
│       ├── classify.py
│       └── extract.py
└── docs/
    ├── api_documentation.md
    ├── agent_specifications.md
    └── deployment_guide.md
🔄 End-to-End Flow Example
Scenario: RFQ Email with JSON Attachment

Input: User uploads email body containing RFQ request
Classifier: Detects "email + RFQ intent" (confidence: 0.92)
Routing: Routed to Email Parser Agent
Extraction:

Sender: "john.doe@company.com"
Intent: "Request for Quote - Cloud Services"
Urgency: "High"
Deadline: "2025-06-15"


Memory Storage: Session metadata and extracted fields stored
Secondary Processing: If RFQ references attached JSON → also route to JSON Agent
Output: Combined structured output returned to mock CRM

Sample Flow Output
json{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "processing_chain": [
        {
            "agent": "classifier",
            "result": {
                "format": "email",
                "intent": "rfq",
                "confidence": 0.92
            }
        },
        {
            "agent": "email_parser",
            "result": {
                "sender": "john.doe@company.com",
                "company": "TechCorp Inc.",
                "intent": "Request for Quote - Cloud Services",
                "urgency": "high",
                "deadline": "2025-06-15",
                "requirements": ["AWS hosting", "24/7 support", "SLA 99.9%"]
            }
        }
    ],
    "crm_record": {
        "contact_id": "generated_uuid",
        "lead_source": "email_rfq",
        "priority": "high",
        "next_action": "prepare_quote",
        "estimated_value": "50000"
    }
}
🛠️ Tech Stack
Core Technologies

Python 3.9+
FastAPI: REST API framework
LangChain: LLM orchestration
Pydantic: Data validation

LLM Options

OpenAI GPT-4: Production-ready
Google Gemini: Cost-effective alternative
Ollama: Open-source local deployment

Memory Solutions

Redis: Distributed caching and persistence
SQLite: Lightweight embedded database
PostgreSQL: Full-featured database (optional)

Additional Tools

Docker: Containerization
PyPDF2/pdfplumber: PDF processing
BeautifulSoup: HTML email parsing
Pytest: Testing framework

🚀 Installation & Setup
Prerequisites
bash# Python 3.9+
python --version

# Docker (optional)
docker --version
Quick Start
bash# Clone repository
git clone https://github.com/your-org/multi-format-intake-agent.git
cd multi-format-intake-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys and configuration

# Initialize memory store
python -m memory.setup

# Run the application
python main.py
Docker Deployment
bash# Build and run with Docker Compose
docker-compose up --build

# API will be available at http://localhost:8000
📋 Environment Configuration
Required Environment Variables
bash# .env file
OPENAI_API_KEY=your_openai_api_key
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=sqlite:///./memory.db
LOG_LEVEL=INFO
MAX_FILE_SIZE=10485760  # 10MB
SUPPORTED_FORMATS=pdf,json,email
🧪 Testing
Sample Test Cases
bash# Run all tests
pytest tests/

# Test specific agent
pytest tests/test_email_parser.py -v

# Integration tests
pytest tests/test_integration.py -v
Sample Inputs Provided

Emails: RFQ requests, complaints, inquiries
JSON: Webhook payloads, API responses, structured data
PDFs: Invoices, contracts, forms

📊 API Endpoints
Core Endpoints
POST /api/v1/classify
POST /api/v1/extract
GET  /api/v1/memory/{session_id}
GET  /api/v1/health
Usage Examples
bash# Classify input
curl -X POST "http://localhost:8000/api/v1/classify" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample_email.txt"

# Extract data
curl -X POST "http://localhost:8000/api/v1/extract" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "uuid", "agent": "email_parser"}'
📈 Performance Metrics
Target Benchmarks

Classification Accuracy: >90%
Processing Time: <5 seconds per document
Memory Usage: <100MB per session
Throughput: 100 documents/minute

Monitoring

Processing time per agent
Classification confidence scores
Memory usage patterns
Error rates and types

🔧 Customization
Adding New Agents

Create agent class in agents/ directory
Implement required interface methods
Register with classifier routing logic
Add tests and documentation

Custom Schemas

Define JSON schema in data/schemas/
Update validation logic in utils
Configure agent output mapping

📝 Submission Requirements Checklist

 Working Video: Demonstration of full system flow
 GitHub Repository: Complete codebase with proper structure
 README.md: Comprehensive documentation (this file)
 Sample Input Files: PDFs, JSONs, emails in /data directory
 Folder Structure: Organized as specified
 Sample Output Logs: Processing results and screenshots
 Docker Support: Optional containerization
 Test Suite: Unit and integration tests

🤝 Contributing
Development Setup

Fork the repository
Create feature branch
Make changes with tests
Submit pull request

Code Standards

Follow PEP 8 style guide
Add docstrings to functions
Include type hints
Write unit tests for new features


🆘 Support
Common Issues

Memory store connection errors: Check Redis/SQLite configuration
LLM API failures: Verify API keys and rate limits
PDF processing errors: Ensure proper file permissions
