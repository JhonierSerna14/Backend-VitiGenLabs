"""
Authentication Service Module

This module provides comprehensive authentication services including:
- User creation and management
- Password hashing and verification
- JWT token generation and validation
- Security key management and email verification
- RabbitMQ integration for email notifications
"""

import json
import logging
import secrets
import threading
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
import pika
from bson import ObjectId
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from pydantic import EmailStr

from app.config import settings
from app.db.mongodb import get_async_database, connect_to_mongo
from app.models.user import UserCreate, UserInDB, UserResponse
from app.services.security_key_consumer import start_consumer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Silence pika logging
logging.getLogger("pika").setLevel(logging.WARNING)

# Security configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")


class AuthService:
    """
    Authentication service class.
    
    Handles all authentication-related operations including user management,
    password operations, JWT tokens, and security key verification.
    """

    def __init__(self):
        """Initialize the authentication service."""
        self.db = None
        self.users_collection = None

    async def get_database(self):
        """
        Get database connection with lazy initialization.
        
        Returns:
            Database: The async MongoDB database instance
        """
        if self.db is None:
            await connect_to_mongo()
            self.db = get_async_database()
            self.users_collection = self.db["users"]
        return self.db

    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """
        Retrieve a user by email address.
        
        Args:
            email: The user's email address
            
        Returns:
            UserInDB or None: The user if found, None otherwise
        """
        try:
            db = await self.get_database()
            user_dict = await db.users.find_one({"email": email})
            
            if user_dict:
                user_dict["id"] = str(user_dict.pop("_id"))
                return UserInDB(**user_dict)
                
        except Exception as e:
            logger.error(f"Error retrieving user {email}: {e}")
            
        return None

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            plain_password: The plain text password
            hashed_password: The hashed password
            
        Returns:
            bool: True if password matches, False otherwise
        """
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False

    def get_password_hash(self, password: str) -> str:
        """
        Generate a hash for a password.
        
        Args:
            password: The plain text password
            
        Returns:
            str: The hashed password
        """
        return pwd_context.hash(password)

    def generate_security_key(self) -> str:
        """
        Generate a random security key.
        
        Returns:
            str: A URL-safe random security key
        """
        return secrets.token_urlsafe(16)

    async def create_user(self, user: UserCreate) -> UserResponse:
        """
        Create a new user account.
        
        Args:
            user: User creation data
            
        Returns:
            UserResponse: The created user data
            
        Raises:
            ValueError: If user already exists or creation fails
        """
        try:
            # Check if user already exists
            existing_user = await self.get_user_by_email(user.email)
            if existing_user:
                raise ValueError("User already exists with this email")

            # Create user document
            hashed_password = self.get_password_hash(user.password)
            user_dict = user.model_dump(exclude={"password"})
            user_dict["hashed_password"] = hashed_password
            user_dict["created_at"] = datetime.now(tz=timezone.utc)

            # Generate security key
            security_key = self.generate_security_key()
            user_dict["security_key"] = security_key
            user_dict["security_key_expires"] = datetime.now(tz=timezone.utc) + timedelta(hours=24)

            # Insert user into database
            await self.get_database()  # Ensure database is initialized
            result = await self.users_collection.insert_one(user_dict)
            user_dict["id"] = str(result.inserted_id)

            # Start consumer thread and send security key email
            self._start_consumer_thread()
            self.publish_security_key_email(user.email, security_key)

            logger.info(f"User created successfully: {user.email}")
            return UserResponse(**user_dict)
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise ValueError(f"Failed to create user: {str(e)}")

    async def authenticate_user(self, email: str, password: str) -> Optional[UserInDB]:
        """
        Authenticate a user with email and password.
        
        Args:
            email: The user's email
            password: The user's password
            
        Returns:
            UserInDB or None: The authenticated user or None if authentication fails
        """
        try:
            user = await self.get_user_by_email(email)
            if not user:
                logger.warning(f"Authentication failed: user not found - {email}")
                return None
                
            if not self.verify_password(password, user.hashed_password):
                logger.warning(f"Authentication failed: invalid password - {email}")
                return None

            # Generate new security key on login
            new_security_key = self.generate_security_key()
            expires_at = datetime.now(tz=timezone.utc) + timedelta(hours=24)

            # Update user with new security key
            await self.users_collection.update_one(
                {"email": email},
                {
                    "$set": {
                        "security_key": new_security_key,
                        "security_key_expires": expires_at,
                        "last_login": datetime.now(tz=timezone.utc)
                    }
                },
            )

            # Send security key email
            self.publish_security_key_email(email, new_security_key)
            
            logger.info(f"User authenticated successfully: {email}")
            return user
            
        except Exception as e:
            logger.error(f"Error during authentication: {e}")
            return None

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT access token.
        
        Args:
            data: The data to encode in the token
            expires_delta: Token expiration time
            
        Returns:
            str: The encoded JWT token
        """
        try:
            to_encode = data.copy()
            expire = datetime.now(tz=timezone.utc) + (
                expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            )
            to_encode.update({"exp": expire})
            
            return jwt.encode(
                to_encode, 
                settings.SECRET_KEY, 
                algorithm=settings.ALGORITHM
            )
        except Exception as e:
            logger.error(f"Error creating access token: {e}")
            raise

    async def get_current_user(self, token: str) -> UserResponse:
        """
        Get the current user from a JWT token.
        
        Args:
            token: The JWT token
            
        Returns:
            UserResponse: The current user
            
        Raises:
            HTTPException: If token is invalid or user not found
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=[settings.ALGORITHM]
            )
            email: str = payload.get("sub")
            if email is None:
                raise credentials_exception
                
        except jwt.PyJWTError as e:
            logger.warning(f"JWT decode error: {e}")
            raise credentials_exception

        user = await self.get_user_by_email(email)
        if user is None:
            raise credentials_exception
            
        return UserResponse(**user.model_dump())

    async def verify_security_key(self, email: EmailStr, security_key: str) -> bool:
        """
        Verify a security key for a user.
        
        Args:
            email: The user's email
            security_key: The security key to verify
            
        Returns:
            bool: True if key is valid, False otherwise
            
        Raises:
            ValueError: If user not found or key is invalid/expired
        """
        try:
            user = await self.get_user_by_email(email)
            if not user:
                raise ValueError("User not found")

            if user.security_key != security_key:
                raise ValueError("Invalid security key")

            # Ensure security key expiration has timezone info
            if user.security_key_expires.tzinfo is None:
                user.security_key_expires = user.security_key_expires.replace(
                    tzinfo=timezone.utc
                )

            # Check if key has expired
            if user.security_key_expires < datetime.now(tz=timezone.utc):
                raise ValueError("Security key has expired")

            # Clear the security key after successful verification
            await self.users_collection.update_one(
                {"email": email},
                {
                    "$set": {
                        "security_key": None,
                        "security_key_expires": None,
                    }
                },
            )

            logger.info(f"Security key verified successfully for user: {email}")
            return True
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error verifying security key: {e}")
            raise ValueError("Security key verification failed")

    def publish_security_key_email(self, email: str, security_key: str) -> None:
        """
        Publish a security key email message to RabbitMQ.
        
        Args:
            email: The recipient email
            security_key: The security key to send
        """
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=settings.RABBITMQ_HOST,
                    port=settings.RABBITMQ_PORT,
                    credentials=pika.PlainCredentials(
                        settings.RABBITMQ_USER, 
                        settings.RABBITMQ_PASSWORD
                    )
                )
            )
            channel = connection.channel()
            channel.queue_declare(queue=settings.RABBITMQ_QUEUE, durable=True)

            message = {
                "email": email,
                "security_key": security_key,
                "timestamp": datetime.now(tz=timezone.utc).isoformat()
            }
            
            channel.basic_publish(
                exchange="",
                routing_key=settings.RABBITMQ_QUEUE,
                body=json.dumps(message),
                properties=pika.BasicProperties(delivery_mode=2)  # Make message persistent
            )
            
            connection.close()
            logger.info(f"Security key email queued for: {email}")
            
        except Exception as e:
            logger.error(f"Error publishing security key email: {e}")

    def _start_consumer_thread(self) -> None:
        """
        Start the RabbitMQ consumer thread if not already running.
        
        This method ensures that the email consumer is running to process
        security key email notifications.
        """
        try:
            consumer_thread = threading.Thread(target=start_consumer, daemon=True)
            consumer_thread.start()
            logger.info("RabbitMQ consumer thread started")
        except Exception as e:
            logger.error(f"Error starting consumer thread: {e}")


# Global service instance
auth_service = AuthService()


# Standalone functions for backward compatibility
async def create_user(user: UserCreate) -> UserResponse:
    """Create a new user account."""
    return await auth_service.create_user(user)


async def authenticate_user(email: str, password: str) -> Optional[UserInDB]:
    """Authenticate a user with email and password."""
    return await auth_service.authenticate_user(email, password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    return auth_service.create_access_token(data, expires_delta)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserResponse:
    """Get the current user from JWT token dependency."""
    return await auth_service.get_current_user(token)