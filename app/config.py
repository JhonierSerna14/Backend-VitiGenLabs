"""
Application Configuration Module

This module defines the configuration settings for the VitiGenLabs backend application.
All settings are loaded from environment variables with appropriate defaults and validation.

Environment Variables Required:
- MONGODB_URL: MongoDB connection string
- MONGODB_DATABASE: MongoDB database name
- SECRET_KEY: JWT secret key for token generation
- RABBITMQ_HOST: RabbitMQ server host
- RABBITMQ_PORT: RabbitMQ server port
- UPLOAD_FOLDER: Directory for file uploads
- SENDGRID: SendGrid API key
- SENDGRID_EMAIL: SendGrid sender email
"""

import os
from typing import List
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    This class uses Pydantic for automatic validation and type conversion
    of configuration values from environment variables.
    """
    
    # Application Information
    PROJECT_NAME: str = "VitiGenLabs - Genetic Analysis Backend"
    PROJECT_VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", description="Application environment")
    
    # Database Configuration
    MONGODB_URL: str = Field(..., description="MongoDB connection URL")
    MONGODB_DATABASE: str = Field(..., description="MongoDB database name")
    
    # Security Configuration
    SECRET_KEY: str = Field(..., description="JWT secret key")
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30, 
        description="JWT token expiration time in minutes"
    )
    
    # RabbitMQ Configuration
    RABBITMQ_HOST: str = Field(..., description="RabbitMQ server host")
    RABBITMQ_PORT: int = Field(default=5672, description="RabbitMQ server port")
    RABBITMQ_USER: str = Field(default="guest", description="RabbitMQ username")
    RABBITMQ_PASSWORD: str = Field(default="guest", description="RabbitMQ password")
    RABBITMQ_QUEUE: str = Field(
        default="security_key_queue", 
        description="RabbitMQ queue name for security keys"
    )
    
    # File Upload Configuration
    UPLOAD_FOLDER: str = Field(..., description="File upload directory")
    MAX_FILE_SIZE: int = Field(
        default=5368709120,  # 5GB in bytes
        description="Maximum file size in bytes"
    )
    ALLOWED_FILE_EXTENSIONS: List[str] = Field(
        default=[".vcf", ".vcf.gz"],
        description="Allowed file extensions for upload"
    )
    
    # Email Configuration
    SENDGRID_API_KEY: str = Field(..., alias="SENDGRID", description="SendGrid API key")
    SENDGRID_EMAIL: str = Field(..., description="SendGrid sender email address")
    SENDGRID_TEMPLATE_ID: str = Field(
        default="d-9fce5a2cd717486995e8cc8c3249178b",
        description="SendGrid template ID for security key emails"
    )
    
    # Performance Configuration
    WORKER_PROCESSES: int = Field(
        default=1,
        description="Number of worker processes"
    )
    MAX_DB_CONNECTIONS: int = Field(
        default=100,
        description="Maximum database connections"
    )
    
    @validator("UPLOAD_FOLDER")
    def create_upload_folder(cls, v):
        """Ensure upload folder exists."""
        os.makedirs(v, exist_ok=True)
        return v
    
    @validator("SECRET_KEY")
    def validate_secret_key(cls, v):
        """Validate secret key length for security."""
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    @validator("MAX_FILE_SIZE")
    def validate_file_size(cls, v):
        """Validate maximum file size is reasonable."""
        if v > 10 * 1024 * 1024 * 1024:  # 10GB
            raise ValueError("MAX_FILE_SIZE cannot exceed 10GB")
        return v
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Get application settings instance.
    
    Returns:
        Settings: The application settings instance
    """
    return settings
