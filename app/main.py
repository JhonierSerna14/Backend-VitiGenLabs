from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import user, gene_search, file_upload

app = FastAPI(
    title="Gene Search Backend for Vineyard Research",
    description="Backend for searching and analyzing gene data from grape varieties",
    version="0.1.0",
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(user.router, prefix="/users", tags=["users"])
app.include_router(gene_search.router, prefix="/search", tags=["gene-search"])
app.include_router(file_upload.router, prefix="/upload", tags=["file-upload"])


@app.get("/")
async def root():
    return {"message": "Welcome to Gene Search Backend", "status": "operational"}

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routes import user, gene_search, file_upload
from app.db.mongodb import connect_to_mongo, close_mongo_connection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events for the FastAPI application,
    including database connections and cleanup.
    """
    # Startup
    logger.info("Starting VitiGenLabs Backend")
    try:
        await connect_to_mongo()
        logger.info("MongoDB connection established")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down VitiGenLabs Backend")
    try:
        await close_mongo_connection()
        logger.info("MongoDB connection closed")
    except Exception as e:
        logger.error(f"Error closing MongoDB connection: {e}")


app = FastAPI(
    title="VitiGenLabs - Genetic Analysis Backend",
    description="""
    Backend API for searching and analyzing gene data from grape varieties.
    
    This API provides endpoints for:
    - User authentication and authorization
    - VCF file upload and processing
    - Gene search and filtering
    - Security key verification via email
    
    Built with FastAPI, MongoDB, and RabbitMQ for scalable genetic data analysis.
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)


# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure specific origins in production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(
    user.router, 
    prefix="/api/v1/users", 
    tags=["Authentication"]
)
app.include_router(
    gene_search.router, 
    prefix="/api/v1/search", 
    tags=["Gene Search"]
)
app.include_router(
    file_upload.router, 
    prefix="/api/v1/upload", 
    tags=["File Processing"]
)


@app.get("/", tags=["Health Check"])
async def root():
    """
    Root endpoint providing basic API information and health status.
    
    Returns:
        dict: API status and basic information
    """
    return {
        "message": "VitiGenLabs - Genetic Analysis Backend",
        "status": "operational",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", tags=["Health Check"])
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    
    Returns:
        dict: Application health status
    """
    return {
        "status": "healthy",
        "service": "vitigenlabs-backend"
    }
