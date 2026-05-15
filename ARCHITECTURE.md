# Architecture Overview

## System Design Principles

This project follows **SOLID principles** and industry-standard design patterns:

### 1. Single Responsibility Principle (SRP)
- Each module has one clear purpose
- `document_processor.py` - Only handles document processing
- `retrieval.py` - Only handles vector search
- `draft_generator.py` - Only handles draft generation
- `improvement_engine.py` - Only handles learning from edits

### 2. Open/Closed Principle (OCP)
- **LLM Service**: Easy to add new providers (OpenAI, Groq, Anthropic) without modifying existing code
- **Repository Pattern**: Can swap database implementations without changing business logic
- **Workflow System**: LangGraph allows extending workflows without breaking existing ones

### 3. Liskov Substitution Principle (LSP)
- All LLM providers implement `BaseLLMService` interface
- Can swap OpenAI ↔ Groq seamlessly
- Repositories extend `BaseRepository` with consistent behavior

### 4. Interface Segregation Principle (ISP)
- Clean, minimal interfaces for each service
- LLM service exposes only `generate()` method
- Repositories expose only needed CRUD operations

### 5. Dependency Inversion Principle (DIP)
- High-level modules depend on abstractions, not concretions
- Draft generator depends on `BaseLLMService`, not specific implementation
- API layer depends on repository interfaces, not database details

---

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                     Presentation Layer                      │
│                  (React Frontend + FastAPI)                 │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                    Application Layer                        │
│              (LangGraph Workflows + Services)               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  DraftGenerationWorkflow (LangGraph)                 │   │
│  │  - Orchestrates entire pipeline                      │   │
│  │  - State management                                  │   │
│  │  - Error handling                                    │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                     Business Logic Layer                    │
│                        (Services)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ LLM Service  │  │  Document    │  │  Retrieval   │      │
│  │ (Pluggable)  │  │  Processor   │  │  Service     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │ Improvement  │  │  Draft       │                        │
│  │  Engine      │  │  Generator   │                        │
│  └──────────────┘  └──────────────┘                        │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                    Data Access Layer                        │
│                   (Repository Pattern)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Document    │  │    Draft     │  │   Pattern    │      │
│  │  Repository  │  │  Repository  │  │  Repository  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                    Persistence Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  PostgreSQL  │  │   ChromaDB   │  │  File System │      │
│  │  (Metadata)  │  │  (Vectors)   │  │  (Documents) │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Components

### 1. LLM Service (Abstraction Layer)

**Location**: `src/services/llm_service.py`

**Purpose**: Provides a unified interface for different LLM providers

**Design Pattern**: Strategy Pattern + Factory Pattern

```python
# Abstract interface
class BaseLLMService(ABC):
    @abstractmethod
    def generate(self, system_prompt, user_message, ...) -> LLMResponse:
        pass

# Concrete implementations
class OpenAILLMService(BaseLLMService): ...
class GroqLLMService(BaseLLMService): ...

# Factory for creation
class LLMServiceFactory:
    @staticmethod
    def create(provider, api_key, model) -> BaseLLMService:
        ...
```

**Benefits**:
- Easy to switch providers (OpenAI ↔ Groq)
- Easy to add new providers
- Consistent interface across the application
- Testable with mock implementations

### 2. Repository Pattern

**Location**: `src/repositories/`

**Purpose**: Abstracts data access logic from business logic

**Design Pattern**: Repository Pattern

```python
# Generic base repository
class BaseRepository(Generic[T]):
    def create(self, **kwargs) -> T: ...
    def get_by_id(self, id: str) -> Optional[T]: ...
    def get_all(self) -> List[T]: ...
    def update(self, id: str, **kwargs) -> Optional[T]: ...
    def delete(self, id: str) -> bool: ...

# Specialized repositories
class DocumentRepository(BaseRepository[Document]):
    def get_by_status(self, status) -> List[Document]: ...
    def get_ready_documents(self) -> List[Document]: ...
```

**Benefits**:
- Separation of concerns
- Easy to test (mock repositories)
- Can swap database implementations
- Reduces code duplication

### 3. LangGraph Workflows

**Location**: `src/workflows/draft_generation_workflow.py`

**Purpose**: Orchestrates complex multi-step processes

**Design Pattern**: State Machine + Pipeline Pattern

```python
class DraftGenerationWorkflow:
    def _build_graph(self):
        workflow = StateGraph(DraftGenerationState)
        
        # Define nodes (steps)
        workflow.add_node("validate_inputs", self._validate_inputs)
        workflow.add_node("fetch_documents", self._fetch_documents)
        workflow.add_node("retrieve_evidence", self._retrieve_evidence)
        workflow.add_node("generate_draft", self._generate_draft)
        
        # Define flow
        workflow.set_entry_point("validate_inputs")
        workflow.add_edge("validate_inputs", "fetch_documents")
        workflow.add_edge("fetch_documents", "retrieve_evidence")
        workflow.add_edge("retrieve_evidence", "generate_draft")
        
        return workflow.compile()
```

**Benefits**:
- Clear visualization of process flow
- Easy to add/remove steps
- Built-in state management
- Error handling at each step
- Testable individual steps

### 4. Database Layer

**Location**: `src/database/`

**Purpose**: Persistent storage for documents, drafts, edits, patterns

**Technology**: SQLAlchemy ORM + PostgreSQL/SQLite

**Models**:
- `Document` - Processed documents with metadata
- `Draft` - Generated drafts
- `OperatorEdit` - User edits to drafts
- `LearnedPattern` - Extracted improvement patterns

**Benefits**:
- Proper persistence (no data loss on restart)
- ACID transactions
- Relationships between entities
- Query optimization

---

## Data Flow

### Document Upload → Draft Generation

```
1. User uploads PDF/image
   ↓
2. DocumentProcessor extracts text + OCR
   ↓
3. Chunking + structured field extraction
   ↓
4. Store in PostgreSQL (metadata) + ChromaDB (vectors)
   ↓
5. User requests draft generation
   ↓
6. LangGraph Workflow starts:
   a. Validate inputs
   b. Fetch document metadata
   c. Build retrieval query
   d. Retrieve evidence from ChromaDB
   e. Load learned patterns
   f. Generate draft via LLM Service
   g. Build grounding map
   ↓
7. Return draft to user
```

### Improvement Loop

```
1. User edits draft
   ↓
2. Store edit in database
   ↓
3. After N edits, trigger pattern extraction
   ↓
4. LLM analyzes edits → extracts patterns
   ↓
5. Store patterns in database
   ↓
6. Next draft generation includes patterns
   ↓
7. Improved draft quality
```

---

## Technology Stack

### Backend
- **FastAPI** - Modern, fast web framework
- **SQLAlchemy** - ORM for database operations
- **PostgreSQL** - Primary database (SQLite for dev)
- **ChromaDB** - Vector database for embeddings
- **LangGraph** - Workflow orchestration
- **OpenAI/Groq** - LLM providers
- **PyMuPDF + Tesseract** - Document processing

### Frontend (Planned)
- **React** - UI framework
- **JavaScript** - Programming language
- **Axios** - HTTP client
- **TailwindCSS** - Styling

### DevOps
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **pytest** - Testing framework

---

## Design Patterns Used

1. **Strategy Pattern** - LLM service implementations
2. **Factory Pattern** - LLM service creation
3. **Repository Pattern** - Data access abstraction
4. **Singleton Pattern** - LLM service instance
5. **Dependency Injection** - Services injected into workflows
6. **State Machine** - LangGraph workflows
7. **Pipeline Pattern** - Document processing steps
8. **Observer Pattern** - Edit capture → pattern extraction

---

## Scalability Considerations

### Current Architecture
- Single server deployment
- SQLite/PostgreSQL for metadata
- ChromaDB for vectors
- In-process LLM calls

### Future Scaling Options

1. **Horizontal Scaling**
   - Load balancer → Multiple API servers
   - Shared PostgreSQL database
   - Shared ChromaDB cluster

2. **Async Processing**
   - Celery/RQ for background tasks
   - Pattern extraction as async job
   - Document processing queue

3. **Caching**
   - Redis for frequently accessed data
   - Cache retrieval results
   - Cache generated drafts

4. **Microservices** (if needed)
   - Document Processing Service
   - Retrieval Service
   - Draft Generation Service
   - Pattern Learning Service

---

## Testing Strategy

### Unit Tests
- Test individual functions in isolation
- Mock external dependencies (LLM, database)
- Fast execution

### Integration Tests
- Test component interactions
- Use test database
- Verify workflows end-to-end

### End-to-End Tests
- Test complete user flows
- Use real services (in test mode)
- Verify UI → API → Database

---

## Security Considerations

1. **API Keys** - Stored in environment variables, never in code
2. **Input Validation** - Pydantic models validate all inputs
3. **SQL Injection** - SQLAlchemy ORM prevents injection
4. **File Upload** - Validate file types and sizes
5. **CORS** - Configured for specific origins only
6. **Rate Limiting** - TODO: Add rate limiting middleware
7. **Authentication** - TODO: Add JWT-based auth

---

## Performance Optimizations

1. **Database Indexing** - Indexes on frequently queried fields
2. **Connection Pooling** - SQLAlchemy connection pool
3. **Batch Processing** - ChromaDB batch upserts
4. **Lazy Loading** - Load data only when needed
5. **Caching** - Cache LLM service instance
6. **Async Operations** - FastAPI async endpoints

---

## Monitoring & Logging

1. **Structured Logging** - JSON logs for easy parsing
2. **Log Levels** - DEBUG, INFO, WARNING, ERROR
3. **Error Tracking** - Log exceptions with stack traces
4. **Performance Metrics** - TODO: Add Prometheus metrics
5. **Health Checks** - `/health` endpoint for monitoring

---

## Future Enhancements

1. **Real-time Collaboration** - WebSocket for live editing
2. **Version Control** - Track draft versions
3. **User Management** - Multi-user support with permissions
4. **Audit Trail** - Log all user actions
5. **Advanced Analytics** - Dashboard for pattern insights
6. **Export Formats** - PDF, DOCX export
7. **Template System** - Customizable draft templates
8. **API Rate Limiting** - Protect against abuse
9. **Webhook Support** - Notify external systems
10. **Multi-language Support** - i18n for UI and documents
