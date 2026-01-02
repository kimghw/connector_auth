# RAG System Architecture Diagrams
Generated from interface_spec.py

## 1. Class Diagram (클래스 다이어그램)
Shows the structure of data models, enums, and interfaces.

```mermaid

classDiagram
    %% Data Models
    class Document {
        +id: str
        +filename: str
        +file_path: str
        +file_size: int
        +upload_time: datetime
        +status: DocumentStatus
        +chunk_count: int
        +error_message: str?
        +to_dict() dict
    }

    class Chunk {
        +id: str
        +document_id: str
        +chunk_index: int
        +content: str
        +token_count: int
        +char_start: int
        +char_end: int
        +embedding_id: str?
        +to_dict() dict
    }

    class SearchResult {
        +chunk_id: str
        +document_id: str
        +document_name: str
        +content: str
        +similarity_score: float
        +chunk_index: int
        +to_dict() dict
    }

    class ProcessStatus {
        +doc_id: str
        +status: DocumentStatus
        +current_step: ProcessingStep
        +progress: int
        +error_message: str?
        +started_at: datetime
        +updated_at: datetime
        +to_dict() dict
    }

    %% Enums
    class DocumentStatus {
        <<enumeration>>
        PENDING
        PROCESSING
        COMPLETED
        ERROR
        DELETED
    }

    class ProcessingStep {
        <<enumeration>>
        UPLOAD
        EXTRACTION
        CHUNKING
        EMBEDDING
        INDEXING
        COMPLETED
    }

    %% Protocols (Interfaces)
    class IDocumentManager {
        <<interface>>
        +upload(file_path) str
        +list_all(status?) List~Document~
        +get_by_id(doc_id) Document
        +delete(doc_id) bool
    }

    class ITextProcessor {
        <<interface>>
        +extract_text(file_path) str
        +clean_text(text) str
        +normalize_text(text) str
    }

    class IChunker {
        <<interface>>
        +create_chunks(text, max_tokens, overlap) List~Dict~
        +count_tokens(text) int
    }

    class IEmbeddingGenerator {
        <<interface>>
        +generate_embedding(text) ndarray
        +generate_embeddings_batch(texts) List~ndarray~
        +dimension: int
    }

    class ISearchEngine {
        <<interface>>
        +search(query, top_k) List~SearchResult~
        +search_with_filter(query, filters) List~SearchResult~
    }

    class IVectorStore {
        <<interface>>
        +add_vector(chunk_id, vector) bool
        +search_vectors(query_vector, top_k) List~tuple~
        +delete_vector(chunk_id) bool
        +get_vector(chunk_id) ndarray?
        +rebuild_index() bool
    }

    %% Relationships
    Document "1" --> "*" Chunk : contains
    Chunk "1" --> "1" SearchResult : found in
    Document ..> DocumentStatus : uses
    ProcessStatus ..> DocumentStatus : uses
    ProcessStatus ..> ProcessingStep : uses

    IDocumentManager ..> Document : manages
    IChunker ..> Chunk : creates
    ISearchEngine ..> SearchResult : returns
    IVectorStore ..> ISearchEngine : used by
    IEmbeddingGenerator ..> IVectorStore : feeds
    
```

## 2. Sequence Diagram (시퀀스 다이어그램)
Shows the interaction flow for document processing and search.

```mermaid

sequenceDiagram
    participant User
    participant rag_service as RAG Service<br/>(Facade)
    participant DM as Document<br/>Manager
    participant TP as Text<br/>Processor
    participant CH as Chunker
    participant EG as Embedding<br/>Generator
    participant VS as Vector<br/>Store
    participant DB as Database

    %% Upload Document
    User->>rag_service: upload_document(file_path)
    rag_service->>DM: upload(file_path)
    DM->>DB: save_metadata()
    DM-->>rag_service: doc_id
    rag_service-->>User: doc_id

    %% Process Document
    User->>rag_service: process_document(doc_id)
    rag_service->>TP: extract_text(file_path)
    TP-->>rag_service: raw_text

    rag_service->>TP: clean_text(raw_text)
    TP-->>rag_service: clean_text

    rag_service->>CH: create_chunks(clean_text)
    CH-->>rag_service: chunks[]

    loop For each chunk
        rag_service->>EG: generate_embedding(chunk)
        EG-->>rag_service: embedding
        rag_service->>VS: add_vector(chunk_id, embedding)
        rag_service->>DB: save_chunk(chunk)
    end

    rag_service-->>User: ProcessStatus

    %% Search
    User->>rag_service: search(query)
    rag_service->>EG: generate_embedding(query)
    EG-->>rag_service: query_embedding

    rag_service->>VS: search_vectors(query_embedding)
    VS-->>rag_service: chunk_ids[]

    rag_service->>DB: get_chunks(chunk_ids)
    DB-->>rag_service: chunks[]

    rag_service-->>User: SearchResult[]
    
```

## 3. Component Diagram (컴포넌트 다이어그램)
Shows the system architecture and dependencies.

```mermaid

graph TB
    subgraph "Client Layer"
        UI[User Interface]
        API[API Client]
    end

    subgraph "Facade Layer"
        RS[rag_service.py<br/>Public API]
    end

    subgraph "Core Layer (Private)"
        DM[Document Manager]
        TP[Text Processor]
        CH[Chunker]
        EG[Embedding Generator]
        SE[Search Engine]
    end

    subgraph "Storage Layer"
        VS[Vector Store<br/>FAISS]
        DB[(SQLite DB)]
        FS[File Storage]
    end

    subgraph "External Services"
        OAI[OpenAI API]
    end

    UI --> API
    API --> RS
    RS --> DM
    RS --> TP
    RS --> CH
    RS --> EG
    RS --> SE

    DM --> DB
    DM --> FS
    CH --> DB
    EG --> OAI
    EG --> VS
    SE --> VS
    SE --> DB

    style RS fill:#f9f,stroke:#333,stroke-width:4px
    style UI fill:#bbf,stroke:#333,stroke-width:2px
    style OAI fill:#fbf,stroke:#333,stroke-width:2px
    
```

## 4. State Diagram (상태 다이어그램)
Shows document processing states.

```mermaid

stateDiagram-v2
    [*] --> PENDING: Document Uploaded

    PENDING --> PROCESSING: Start Processing

    PROCESSING --> EXTRACTION: Extract Text
    EXTRACTION --> CHUNKING: Text Extracted
    CHUNKING --> EMBEDDING: Chunks Created
    EMBEDDING --> INDEXING: Embeddings Generated
    INDEXING --> COMPLETED: Index Updated

    EXTRACTION --> ERROR: Extraction Failed
    CHUNKING --> ERROR: Chunking Failed
    EMBEDDING --> ERROR: Embedding Failed
    INDEXING --> ERROR: Indexing Failed

    ERROR --> PROCESSING: Retry
    ERROR --> DELETED: Delete Document
    COMPLETED --> DELETED: Delete Document

    DELETED --> [*]
    COMPLETED --> [*]
    
```

## 5. Data Flow Diagram (데이터 플로우 다이어그램)
Shows how data flows through the system.

```mermaid

graph LR
    subgraph "Input"
        PDF[PDF File]
        TXT[TXT File]
        Query[Search Query]
    end

    subgraph "Processing Pipeline"
        Extract[Text<br/>Extraction]
        Clean[Text<br/>Cleaning]
        Chunk[Chunking<br/>512 tokens]
        Embed[Embedding<br/>Generation]
        Index[Vector<br/>Indexing]
    end

    subgraph "Storage"
        Meta[(Metadata)]
        Vectors[(Vectors)]
        Files[(Files)]
    end

    subgraph "Search Pipeline"
        QEmbed[Query<br/>Embedding]
        VSim[Vector<br/>Similarity]
        Rank[Re-ranking]
    end

    subgraph "Output"
        Results[Search<br/>Results]
    end

    PDF --> Extract
    TXT --> Extract
    Extract --> Clean
    Clean --> Chunk
    Chunk --> Embed
    Embed --> Index

    Extract --> Meta
    Chunk --> Meta
    Index --> Vectors
    PDF --> Files
    TXT --> Files

    Query --> QEmbed
    QEmbed --> VSim
    Vectors --> VSim
    VSim --> Rank
    Meta --> Rank
    Rank --> Results

    style Extract fill:#faa,stroke:#333,stroke-width:2px
    style Embed fill:#afa,stroke:#333,stroke-width:2px
    style VSim fill:#aaf,stroke:#333,stroke-width:2px
    
```

## How to View

### Option 1: GitHub
GitHub automatically renders Mermaid diagrams in markdown files.

### Option 2: Mermaid Live Editor
1. Go to https://mermaid.live/
2. Copy the diagram code
3. Paste and view

### Option 3: VS Code Extension
Install "Markdown Preview Mermaid Support" extension.

### Option 4: Generate Images
```bash
# Install mermaid-cli
npm install -g @mermaid-js/mermaid-cli

# Generate SVG/PNG
mmdc -i diagram.mmd -o output.svg
```
