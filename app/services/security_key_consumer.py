"""
Security Key Email Consumer Module

This module handles RabbitMQ message consumption for sending security key emails
via SendGrid. It processes authentication and verification email notifications.
"""

import json
import logging
from typing import Dict, Any

import pika
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from pika.exceptions import AMQPConnectionError, AMQPChannelError

from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Silence pika logging
logging.getLogger("pika").setLevel(logging.WARNING)


def send_security_key_email(email: str, code: str) -> bool:
    """
    Send security key email using SendGrid dynamic template.
    
    Args:
        email: Recipient email address
        code: Security key/code to send
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        logger.info(f"Sending security key email to: {email}")
        
        # Create mail object with dynamic template
        message = Mail(
            from_email=settings.SENDGRID_EMAIL,
            to_emails=email,
        )
        
        # Set dynamic template
        message.template_id = settings.SENDGRID_TEMPLATE_ID
        message.dynamic_template_data = {
            "code": code,
            "app_name": "VitiGenLabs",
            "timestamp": "now"
        }
        
        # Send email via SendGrid
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        
        if response.status_code in [200, 202]:
            logger.info(f"Security key email sent successfully to: {email}")
            return True
        else:
            logger.error(f"SendGrid returned status code: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending security key email to {email}: {e}")
        return False


def process_message(ch, method, properties, body: bytes) -> None:
    """
    Process incoming RabbitMQ message for security key emails.
    
    Args:
        ch: Channel object
        method: Method object
        properties: Properties object
        body: Message body as bytes
    """
    try:
        # Parse message
        message_data = json.loads(body.decode('utf-8'))
        email = message_data.get("email")
        security_key = message_data.get("security_key")
        
        if not email or not security_key:
            logger.error(f"Invalid message format: {message_data}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return
        
        # Send email
        success = send_security_key_email(email, security_key)
        
        if success:
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info(f"Message processed successfully for: {email}")
        else:
            # Reject and requeue for retry
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            logger.warning(f"Message processing failed for: {email}, requeuing")
            
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


def start_consumer() -> None:
    """
    Start the RabbitMQ consumer for security key emails.
    
    This function establishes a connection to RabbitMQ and starts consuming
    messages from the security key queue. It handles reconnection and error recovery.
    """
    connection = None
    
    try:
        logger.info("Starting RabbitMQ consumer for security key emails")
        
        # Establish connection
        connection_params = pika.ConnectionParameters(
            host=settings.RABBITMQ_HOST,
            port=settings.RABBITMQ_PORT,
            credentials=pika.PlainCredentials(
                settings.RABBITMQ_USER,
                settings.RABBITMQ_PASSWORD
            ),
            heartbeat=600,
            blocked_connection_timeout=300,
        )
        
        connection = pika.BlockingConnection(connection_params)
        channel = connection.channel()
        
        # Declare queue with durability
        channel.queue_declare(
            queue=settings.RABBITMQ_QUEUE,
            durable=True
        )
        
        # Configure QoS to process one message at a time
        channel.basic_qos(prefetch_count=1)
        
        # Set up consumer
        channel.basic_consume(
            queue=settings.RABBITMQ_QUEUE,
            on_message_callback=process_message,
            auto_ack=False  # Manual acknowledgment for reliability
        )
        
        logger.info(f"Consumer ready. Waiting for messages on queue: {settings.RABBITMQ_QUEUE}")
        channel.start_consuming()
        
    except AMQPConnectionError as e:
        logger.error(f"RabbitMQ connection error: {e}")
    except AMQPChannelError as e:
        logger.error(f"RabbitMQ channel error: {e}")
    except KeyboardInterrupt:
        logger.info("Consumer interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error in consumer: {e}")
    finally:
        # Clean shutdown
        if connection and not connection.is_closed:
            try:
                connection.close()
                logger.info("RabbitMQ connection closed")
            except Exception as e:
                logger.error(f"Error closing RabbitMQ connection: {e}")


if __name__ == "__main__":
    # Allow running consumer as standalone script
    start_consumer()
