# Divorce Lawyer AI Assistant

## Project Overview

Divorce Lawyer AI Assistant is an intelligent assistant for family law attorneys, using artificial intelligence technologies to process and analyze legal documents related to divorce proceedings. The project is built on a RAG (Retrieval-Augmented Generation) architecture, allowing the system to find and use relevant information from a knowledge base when generating responses.

## Key Features

- Analysis of PDF documents with extraction of relevant information
- Creation and management of knowledge bases for RAG
- API for uploading, storing, and managing documents
- Integration with Google Cloud Storage for file storage
- Utilization of Pinecone for vector databases
- Integration with OpenAI for response generation and embeddings
- Document management through Firestore Database
- Hierarchical knowledge storage system with categories and subcategories
- Access a control system with different permission levels
- Smart document search with result ranking

   The ranking mechanism is implemented by generating vector embeddings for each document 
   using OpenAI’s models. When a search is performed, the query is converted into a vector, 
   and then using Pinecone’s vector database, each document is scored based on similarity 
   (e.g., cosine similarity) to the query. Additional factors such as document metadata 
   and keyword relevance help refine the final normalized ranking score, ensuring 
   the most relevant documents are returned first.

## Technology Stack

- Python 3.12
- FastAPI
- LangChain
- OpenAI
- Pinecone
- Google Cloud Storage
- Google Cloud Firestore
- PyMuPDF (for working with PDF documents)
- Jinja2 (for templates)
- Pydantic (for data validation)
- Poetry (dependency management)

## Requirements

- Python 3.12
- Poetry
- Google Cloud Storage credentials
- Google Cloud Firestore credentials
- API keys for OpenAI and Pinecone

## Installation and Setup

### Environment Configuration

1. Clone the repository
   ```bash
   git clone [repository URL]
   cd divorce-lawyer-ai-assistant
   ```

2. Install dependencies using Poetry
   ```bash
   poetry install
   ```

3. Create a `.env` file in the project root with the following variables:
   ```
   DEBUG=True
   BASE_AI_MODEL=gpt-4-turbo
   OPENAI_API_KEY=your_openai_api_key
   PINECONE_API_KEY=your_pinecone_api_key
   GOOGLE_CLOUD_PROJECT=your_google_cloud_project_id
   GOOGLE_APPLICATION_CREDENTIALS=path_to_your_credentials.json
   ```

### Running the Application

```bash
poetry run uvicorn src.main:app --reload
```

After starting, the application will be available at http://localhost:8000

## API Endpoints

### Knowledge Base
- `POST /api/v1/knowledge-base/` - Create new knowledge base
- `GET /api/v1/knowledge-base/{name_knowledge_base}` - Get information about knowledge base
- `PUT /api/v1/knowledge-base/` - Rename knowledge base
- `DELETE /api/v1/knowledge-base/` - Delete knowledge base

### Files
- `GET /api/v1/knowledge-base/files/{file_path:path}` - Get file information
- `GET /api/v1/knowledge-base/files` - List all files
- `POST /api/v1/knowledge-base/upload` - Upload a single file
- `POST /api/v1/knowledge-base/upload/multiple` - Upload multiple files
- `PUT /api/v1/knowledge-base/files/{file_path:path}` - Rename a file
- `DELETE /api/v1/knowledge-base/files/{file_path:path}` - Delete a file

### Folders
- `GET /api/v1/knowledge-base/folders` - List all folders
- `GET /api/v1/knowledge-base/folder/{folder_path:path}` - Get folder contents
- `POST /api/v1/knowledge-base/folders` - Create a new folder
- `PUT /api/v1/knowledge-base/folders/{folder_path:path}` - Rename a folder
- `DELETE /api/v1/knowledge-base/folders/{folder_path:path}` - Delete a folder

## UI Interfaces
- `/` - Main page
- `/data-for-rag` - Knowledge base management interface

## Development

### Testing
```bash
poetry run pytest
```

### Type Checking
```bash
poetry run mypy .
```

### Code Style Checking
```bash
poetry run black .
poetry run flake8
```

## Project Structure
- `src/` - Project source code
  - `api/` - API endpoint definitions
  - `core/` - Base configurations and constants
  - `services/` - Services for working with storage and external APIs
    - `document_database/` - Document management service using Firestore
    - `storage/` - Storage service implementation
    - `rag_service/` - RAG (Retrieval-Augmented Generation) service implementation
  - `knowledge_storage/` - Knowledge organization and storage system
  - `templates/` - HTML templates
  - `utils/` - Helper functions and utilities
  - `tests/` - Test suite
  - `main.py` - Application entry point

## License
This project is distributed under the Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0) license.

You can:
- Share — copy and redistribute the material in any medium or format
- Adapt — remix, transform, and build upon the material

Under the following conditions:
- Attribution — You must give appropriate credit, provide a link to the license, and indicate if changes were made
- NonCommercial — You may not use the material for commercial purposes

Full license text: https://creativecommons.org/licenses/by-nc/4.0/
