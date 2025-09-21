"""
VitiGenLabs Backend Application Entry Point

This module serves as the main entry point for the VitiGenLabs backend application.
It starts both the FastAPI server and the RabbitMQ consumer for security key emails.
"""

import asyncio
import logging
import threading
from typing import NoReturn

import uvicorn

from app.services.security_key_consumer import start_consumer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def run_consumer() -> None:
    """
    Run the RabbitMQ consumer in a separate thread.
    
    This function is executed in a daemon thread to handle
    security key email notifications asynchronously.
    """
    try:
        asyncio.run(start_consumer())
    except Exception as e:
        logger.error(f"Error in consumer thread: {e}")


def main() -> NoReturn:
    """
    Main application entry point.
    
    Starts the RabbitMQ consumer in a daemon thread and then
    launches the FastAPI server with Uvicorn.
    """
    logger.info("Starting VitiGenLabs Backend Application")
    
    try:
        # Start the RabbitMQ consumer in a daemon thread
        consumer_thread = threading.Thread(target=run_consumer, daemon=True)
        consumer_thread.start()
        logger.info("RabbitMQ consumer thread started")
        
        # Start the FastAPI server
        logger.info("Starting FastAPI server")
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise


if __name__ == "__main__":
    main()
