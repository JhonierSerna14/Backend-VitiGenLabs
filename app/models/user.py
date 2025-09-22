"""
User Models Module

This module defines Pydantic models for user-related data structures
including user creation, authentication, and security key verification.
"""

import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserBase(BaseModel):
    """
    Base user model with common fields.
    
    Contains the fundamental user attributes that are shared
    across different user model variations.
    """
    email: EmailStr = Field(..., description="User's email address")
    is_active: bool = Field(default=True, description="Whether the user account is active")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the user was created"
    )
    last_login: Optional[datetime] = Field(
        default=None,
        description="Timestamp of the user's last login"
    )


class UserCreate(UserBase):
    """
    User creation model with password validation.
    
    Used when creating new user accounts. Includes comprehensive
    password validation to ensure security requirements are met.
    """
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="User's password (will be hashed)"
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, password: str) -> str:
        """
        Validate password complexity requirements.
        
        Args:
            password: The password to validate
            
        Returns:
            str: The validated password
            
        Raises:
            ValueError: If password doesn't meet security requirements
        """
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")

        if len(password) > 128:
            raise ValueError("Password must not exceed 128 characters")

        # Check for uppercase letter
        if not re.search(r"[A-Z]", password):
            raise ValueError("Password must contain at least one uppercase letter")

        # Check for lowercase letter
        if not re.search(r"[a-z]", password):
            raise ValueError("Password must contain at least one lowercase letter")

        # Check for digit
        if not re.search(r"\d", password):
            raise ValueError("Password must contain at least one number")

        # Check for special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValueError("Password must contain at least one special character")

        return password


class UserInDB(UserBase):
    """
    User model as stored in the database.
    
    Includes internal fields like hashed password and security keys
    that are not exposed in API responses.
    """
    id: str = Field(..., description="Unique user identifier")
    hashed_password: str = Field(..., description="Bcrypt hashed password")
    security_key: Optional[str] = Field(
        default=None,
        description="Temporary security key for email verification"
    )
    security_key_expires: Optional[datetime] = Field(
        default=None,
        description="Expiration timestamp for the security key"
    )
    is_verified: bool = Field(
        default=False,
        description="Whether the user has verified their security key"
    )


class UserResponse(UserBase):
    """
    User model for API responses.
    
    Contains only the information that should be exposed
    to clients, excluding sensitive data like passwords.
    """
    id: str = Field(..., description="Unique user identifier")

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class LoginRequest(BaseModel):
    """
    Login request model.
    
    Used for user authentication with username/email and password.
    """
    username: EmailStr = Field(
        ...,
        description="User's email address used as username"
    )
    password: str = Field(
        ...,
        min_length=1,
        description="User's password"
    )


class SecurityKeyRequest(BaseModel):
    """
    Security key request model.
    
    Used when requesting a new security key for email verification.
    """
    email: EmailStr = Field(
        ...,
        description="Email address to send the security key to"
    )


class SecurityKeyVerify(BaseModel):
    """
    Security key verification model.
    
    Used to verify a security key sent via email.
    """
    email: EmailStr = Field(
        ...,
        description="Email address associated with the security key"
    )
    security_key: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Security key received via email"
    )


class TokenResponse(BaseModel):
    """
    JWT token response model.
    
    Used for authentication token responses.
    """
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
