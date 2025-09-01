from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import os
from ..services.chat_service import smart_librarian


# Pydantic models for API requests/responses
class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[Dict[str, str]]] = None


class ChatResponse(BaseModel):
    success: bool
    message: str
    filtered: bool
    function_calls: List[Dict[str, Any]]
    search_results: List[Dict[str, Any]]
    error: Optional[str] = None


class DatabaseInfo(BaseModel):
    collection_name: str
    document_count: int
    persist_directory: str


class BookListResponse(BaseModel):
    books: List[str]


# Initialize FastAPI app
app = FastAPI(
    title="Smart Librarian API",
    description="AI-powered book recommendation chatbot with RAG",
    version="1.0.0"
)

# Add CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080", "*"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if os.path.exists("frontend/build"):
    app.mount("/static", StaticFiles(directory="frontend/build/static"), name="static")


@app.on_event("startup")
async def startup_event():
    """Initialize the database on startup."""
    try:
        print("Initializing Smart Librarian database...")
        smart_librarian.initialize_database("data/book_summaries.txt")
        db_info = smart_librarian.get_database_info()
        print(f"Database initialized: {db_info['document_count']} books loaded")
    except Exception as e:
        print(f"Warning: Could not initialize database: {e}")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Smart Librarian API",
        "version": "1.0.0",
        "description": "AI-powered book recommendation chatbot",
        "endpoints": {
            "chat": "/chat",
            "books": "/books",
            "database": "/database/info",
            "health": "/health"
        }
    }


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main chat endpoint for book recommendations.

    Args:
        request (ChatRequest): Chat request with user message and optional history

    Returns:
        ChatResponse: AI response with recommendations
    """
    try:
        response = smart_librarian.chat(
            user_message=request.message,
            conversation_history=request.conversation_history
        )

        return ChatResponse(**response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat service error: {str(e)}")


@app.get("/books", response_model=BookListResponse)
async def get_books():
    """Get list of all available books in the database."""
    try:
        books = smart_librarian.get_available_books()
        return BookListResponse(books=books)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching books: {str(e)}")


@app.get("/database/info", response_model=DatabaseInfo)
async def get_database_info():
    """Get information about the vector database."""
    try:
        info = smart_librarian.get_database_info()
        return DatabaseInfo(**info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching database info: {str(e)}")


@app.post("/database/reinitialize")
async def reinitialize_database():
    """Reinitialize the vector database"""
    try:
        smart_librarian.vector_store.reset_database()
        smart_librarian.initialize_database("data/book_summaries.txt")
        info = smart_librarian.get_database_info()
        return {
            "message": "Database reinitialized successfully",
            "database_info": info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reinitializing database: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        db_info = smart_librarian.get_database_info()
        return {
            "status": "healthy",
            "database_status": "connected" if db_info.get('document_count', 0) > 0 else "empty",
            "database_info": db_info
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# Example endpoint for testing specific book summaries
@app.get("/book/{title}")
async def get_book_summary(title: str):
    """Get detailed summary for a specific book."""
    try:
        from ..database.book_summaries import get_summary_by_title
        summary = get_summary_by_title(title)

        if "Sorry, I don't have" in summary:
            raise HTTPException(status_code=404, detail=summary)

        return {
            "title": title,
            "summary": summary
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching book summary: {str(e)}")
