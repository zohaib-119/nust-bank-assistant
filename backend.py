"""
FastAPI Backend for NUST Bank RAG Assistant

Provides REST API endpoints for:
- Chat queries (with source retrieval)
- Knowledge base management (upload, rebuild)
- Health checks
- Analytics
- Admin authentication and management
"""

import os
import sys
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import json
from datetime import datetime

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from src.rag_pipeline import RAGPipeline
from src.config import CONFIG
from src.guardrails import check_input, check_output

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="NUST Bank RAG Assistant API",
    description="REST API for the NUST Bank Customer Support Assistant",
    version="1.0.0"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global pipeline instance
pipeline: Optional[RAGPipeline] = None


def initialize_pipeline():
    """Initialize the RAG pipeline."""
    global pipeline
    if pipeline is None:
        data_dir = PROJECT_ROOT
        index_dir = os.path.join(PROJECT_ROOT, "index")
        pipeline = RAGPipeline(data_dir=data_dir, index_dir=index_dir, top_k=CONFIG.top_k)
        try:
            pipeline.initialize()
            logger.info("Pipeline initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize pipeline: {e}")
            raise
    return pipeline


# ==================== Pydantic Models ====================

class QueryRequest(BaseModel):
    """Request model for chat queries."""
    query: str


class QueryResponse(BaseModel):
    """Response model for chat queries."""
    answer: str
    sources: List[str] = []
    confidence: float = 1.0
    error: Optional[str] = None


class LoginRequest(BaseModel):
    """Request model for admin login."""
    username: str
    password: str


class LoginResponse(BaseModel):
    """Response model for admin login."""
    status: str
    message: str
    token: Optional[str] = None
    is_admin: bool = False


class AdminCheckResponse(BaseModel):
    """Response model for admin check."""
    is_admin: bool
    username: Optional[str] = None


class UploadResponse(BaseModel):
    """Response model for file uploads."""
    status: str
    message: str
    file_path: Optional[str] = None


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    pipeline_loaded: bool
    version: str


# ==================== Admin Credentials ====================
# Hardcoded admin user (in production, use environment variables)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "nustbank2026"
ADMIN_TOKEN = "admin_token_nustbank_2026"

# Active sessions
active_sessions = {}


# ==================== Endpoints ====================

@app.on_event("startup")
async def startup_event():
    """Initialize pipeline on server startup."""
    logger.info("Starting NUST Bank RAG Assistant API server...")
    initialize_pipeline()
    logger.info("API server started successfully")


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Check if the API and pipeline are healthy."""
    return HealthResponse(
        status="ok" if pipeline else "initializing",
        pipeline_loaded=pipeline is not None,
        version="1.0.0"
    )


# ==================== Authentication Endpoints ====================

@app.post("/api/auth/login", response_model=LoginResponse, tags=["Authentication"])
async def login(request: LoginRequest):
    """
    Admin login endpoint.
    Returns a token for authenticated admin access.
    """
    try:
        if request.username == ADMIN_USERNAME and request.password == ADMIN_PASSWORD:
            session_id = f"{ADMIN_USERNAME}_{datetime.now().timestamp()}"
            active_sessions[session_id] = {
                "username": ADMIN_USERNAME,
                "login_time": datetime.now().isoformat(),
                "is_admin": True
            }
            
            logger.info(f"Admin login successful: {ADMIN_USERNAME}")
            
            return LoginResponse(
                status="success",
                message="Admin login successful",
                token=session_id,
                is_admin=True
            )
        else:
            logger.warning(f"Failed login attempt for user: {request.username}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@app.post("/api/auth/logout", tags=["Authentication"])
async def logout(token: str = Header(..., alias="X-Auth-Token")):
    """
    Logout the current admin session.
    """
    try:
        if token in active_sessions:
            username = active_sessions[token]["username"]
            del active_sessions[token]
            logger.info(f"Admin logout: {username}")
            return {"status": "success", "message": "Logged out successfully"}
        else:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(status_code=500, detail=f"Logout failed: {str(e)}")


@app.get("/api/auth/check", response_model=AdminCheckResponse, tags=["Authentication"])
async def check_auth(token: str = Header(None, alias="X-Auth-Token")):
    """
    Check if the provided token is valid and user is admin.
    """
    try:
        if token and token in active_sessions:
            session = active_sessions[token]
            return AdminCheckResponse(
                is_admin=session.get("is_admin", False),
                username=session.get("username")
            )
        else:
            return AdminCheckResponse(is_admin=False, username=None)
    
    except Exception as e:
        logger.error(f"Auth check error: {e}")
        raise HTTPException(status_code=500, detail=f"Auth check failed: {str(e)}")


def verify_admin_token(token: Optional[str]):
    """Verify if the provided token belongs to an admin user."""
    if not token or token not in active_sessions:
        raise HTTPException(status_code=401, detail="Unauthorized: Admin access required")
    
    session = active_sessions.get(token)
    if not session or not session.get("is_admin"):
        raise HTTPException(status_code=403, detail="Forbidden: Admin access required")
    
    return session


@app.post("/api/query", response_model=QueryResponse, tags=["Chat"])
async def query(request: QueryRequest):
    """
    Process a user query through the RAG pipeline.
    
    Returns:
    - answer: Generated response from the LLM
    - confidence: Confidence score (0-1)
    """
    try:
        rag = initialize_pipeline()
        user_query = request.query.strip()
        
        if not user_query:
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Apply input guardrails
        if CONFIG.enable_guardrails:
            gi = check_input(user_query)
            if not gi.allowed:
                return QueryResponse(
                    answer="",
                    error=gi.message or "Query blocked by safety checks"
                )
            user_query = gi.sanitized_text or user_query
        
        # Process query through pipeline
        result = rag.query_with_sources(user_query)
        answer = result.get("answer", "")
        # Note: sources are retrieved but not returned in response per user request
        
        # Apply output guardrails
        if CONFIG.enable_guardrails:
            go = check_output(answer)
            answer = go.sanitized_text or answer
        
        logger.info(f"Query processed: {user_query[:50]}...")
        
        return QueryResponse(
            answer=answer,
            sources=[],  # Sources not displayed to users
            confidence=0.95
        )
    
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.post("/api/upload", response_model=UploadResponse, tags=["KnowledgeBase"])
async def upload_file(
    file: UploadFile = File(...),
    token: str = Header(None, alias="X-Auth-Token")
):
    """
    [ADMIN ONLY] Upload a knowledge base file and rebuild the index.
    Keeps existing data and adds newly uploaded documents.
    
    Supported formats:
    - Excel (.xlsx)
    - JSON (.json)
    - Text (.txt)
    - Markdown (.md)
    - PDF (.pdf)
    
    Requires admin authentication via X-Auth-Token header.
    """
    try:
        # Verify admin access
        session = verify_admin_token(token)
        
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Save uploaded file temporarily
        temp_path = f"/tmp/{file.filename}"
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        rag = initialize_pipeline()
        info = rag.add_upload_and_rebuild(temp_path)
        
        logger.info(f"[ADMIN {session['username']}] File uploaded and indexed: {file.filename}")
        
        return UploadResponse(
            status="success",
            message=f"File {file.filename} uploaded and indexed successfully",
            file_path=info.get("saved_path")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/api/rebuild", response_model=UploadResponse, tags=["KnowledgeBase"])
async def rebuild_index(token: str = Header(None, alias="X-Auth-Token")):
    """
    [ADMIN ONLY] Rebuild the FAISS index from existing knowledge base files.
    Reprocesses all existing data from scratch.
    
    Requires admin authentication via X-Auth-Token header.
    """
    try:
        # Verify admin access
        session = verify_admin_token(token)
        
        rag = initialize_pipeline()
        rag.rebuild_index()
        
        logger.info(f"[ADMIN {session['username']}] Index rebuilt successfully")
        
        return UploadResponse(
            status="success",
            message="Index rebuilt from existing knowledge base files"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rebuilding index: {e}")
        raise HTTPException(status_code=500, detail=f"Rebuild failed: {str(e)}")


@app.get("/api/stats", tags=["System"])
async def get_stats():
    """Get statistics about the knowledge base and system."""
    try:
        rag = initialize_pipeline()
        
        index_path = os.path.join(PROJECT_ROOT, "index", "metadata.json")
        num_vectors = 0
        
        if os.path.exists(index_path):
            import json
            with open(index_path) as f:
                metadata = json.load(f)
                num_vectors = len(metadata)
        
        return {
            "status": "ok",
            "vectors_in_index": num_vectors,
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "llm_model": CONFIG.ollama_model,
            "top_k_retrieval": CONFIG.top_k,
            "guardrails_enabled": CONFIG.enable_guardrails
        }
    
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting NUST Bank RAG Assistant FastAPI server...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
