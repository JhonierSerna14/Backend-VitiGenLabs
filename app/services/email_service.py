"""
Enhanced Brevo Email Service

This module provides comprehensive email sending functionality using Brevo's REST API.
It supports transactional emails with advanced features like templates, attachments,
scheduling, tracking, and more.
"""

import requests
import logging
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from pathlib import Path
import base64
from app.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Brevo API endpoints
BREVO_API_BASE = "https://api.brevo.com/v3"
SMTP_EMAIL_ENDPOINT = f"{BREVO_API_BASE}/smtp/email"


class BrevoEmailService:
    """Enhanced Brevo Email Service with advanced features."""
    
    def __init__(self):
        self.api_key = settings.BREVO_API_KEY
        self.sender_name = settings.BREVO_SENDER_NAME
        self.sender_email = settings.BREVO_SENDER_EMAIL
        self.headers = {
            'accept': 'application/json',
            'api-key': self.api_key,
            'content-type': 'application/json'
        }

    def send_email(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        html_content: Optional[str] = None,
        text_content: Optional[str] = None,
        template_id: Optional[int] = None,
        template_params: Optional[Dict[str, Any]] = None,
        sender_name: Optional[str] = None,
        sender_email: Optional[str] = None,
        reply_to_email: Optional[str] = None,
        reply_to_name: Optional[str] = None,
        cc: Optional[List[Dict[str, str]]] = None,
        bcc: Optional[List[Dict[str, str]]] = None,
        attachments: Optional[List[Dict[str, str]]] = None,
        tags: Optional[List[str]] = None,
        scheduled_at: Optional[datetime] = None,
        preheader: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Send an advanced transactional email using Brevo's API.

        Args:
            to_email: Recipient email address
            to_name: Recipient name
            subject: Email subject (ignored if template_id is provided)
            html_content: HTML content (ignored if template_id is provided)
            text_content: Plain text content
            template_id: Brevo template ID to use
            template_params: Parameters for template customization
            sender_name: Sender name (defaults to config)
            sender_email: Sender email (defaults to config)
            reply_to_email: Reply-to email address
            reply_to_name: Reply-to name
            cc: List of CC recipients [{"email": "...", "name": "..."}]
            bcc: List of BCC recipients [{"email": "...", "name": "..."}]
            attachments: List of attachments [{"url": "..."/"content": "base64", "name": "..."}]
            tags: List of tags for email tracking
            scheduled_at: UTC datetime to schedule email
            preheader: Preview text shown in inbox
            headers: Custom headers dictionary

        Returns:
            Dict containing the API response

        Raises:
            requests.RequestException: If the API request fails
        """
        # Use defaults from settings if not provided
        sender_name = sender_name or self.sender_name
        sender_email = sender_email or self.sender_email

        # Build payload
        payload = {
            "sender": {
                "name": sender_name,
                "email": sender_email
            },
            "to": [
                {
                    "email": to_email,
                    "name": to_name
                }
            ]
        }

        # Add template or content
        if template_id:
            payload["templateId"] = template_id
            if template_params:
                payload["params"] = template_params
        else:
            if not subject or not html_content:
                raise ValueError("Subject and html_content are required when not using template_id")
            payload["subject"] = subject
            payload["htmlContent"] = html_content
            if text_content:
                payload["textContent"] = text_content

        # Add optional fields
        if reply_to_email:
            payload["replyTo"] = {"email": reply_to_email}
            if reply_to_name:
                payload["replyTo"]["name"] = reply_to_name

        if cc:
            payload["cc"] = cc
        if bcc:
            payload["bcc"] = bcc
        if attachments:
            payload["attachment"] = attachments
        if tags:
            payload["tags"] = tags
        if scheduled_at:
            payload["scheduledAt"] = scheduled_at.isoformat() + "Z"
        if preheader:
            payload["preheader"] = preheader
        if headers:
            payload["headers"] = headers

        try:
            logger.info(f"Sending email to {to_email} with subject: {subject or f'Template {template_id}'}")
            response = requests.post(SMTP_EMAIL_ENDPOINT, headers=self.headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            message_id = result.get('messageId', 'N/A')
            logger.info(f"Email sent successfully to {to_email}. Message ID: {message_id}")
            return result

        except requests.RequestException as e:
            logger.error(f"Error sending email to {to_email}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            raise

    def send_security_key_email(
        self,
        email: str,
        security_key: str,
        user_name: str = "User"
    ) -> bool:
        """
        Send a professionally designed security key email.

        Args:
            email: Recipient email address
            security_key: The security key to send
            user_name: Name of the user

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        subject = "🔐 Your VitiGenLabs Security Code"
        preheader = f"Your verification code is {security_key}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Código de Seguridad - VitiGenLabs</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8f9fa;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 30px; text-align: center;">
                    <h1 style="color: #ffffff; font-size: 28px; margin: 0; font-weight: 600;">🧬 VitiGenLabs</h1>
                    <p style="color: #e8ebff; font-size: 16px; margin: 10px 0 0 0;">Plataforma de Análisis Genético</p>
                </div>
                
                <!-- Content -->
                <div style="padding: 40px 30px;">
                    <h2 style="color: #333333; font-size: 24px; margin: 0 0 20px 0; font-weight: 600;">
                        ¡Hola {user_name}! 👋
                    </h2>
                    
                    <p style="color: #666666; font-size: 16px; line-height: 1.6; margin: 0 0 30px 0;">
                        Hemos recibido una solicitud para acceder a tu cuenta en VitiGenLabs. 
                        Utiliza el siguiente código de 6 dígitos para completar tu autenticación:
                    </p>
                    
                    <!-- Security Code Box -->
                    <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 12px; padding: 30px; text-align: center; margin: 30px 0;">
                        <p style="color: #ffffff; font-size: 14px; margin: 0 0 10px 0; text-transform: uppercase; letter-spacing: 1px; font-weight: 500;">
                            Tu Código de Seguridad
                        </p>
                        <div style="background-color: rgba(255, 255, 255, 0.2); border-radius: 8px; padding: 20px; margin: 10px 0;">
                            <span style="color: #ffffff; font-size: 36px; font-weight: 700; letter-spacing: 12px; font-family: 'Courier New', monospace;">
                                {security_key}
                            </span>
                        </div>
                        
                        <p style="color: rgba(255, 255, 255, 0.9); font-size: 14px; margin: 15px 0 0 0;">
                            ⏰ Este código expira en 24 horas
                        </p>
                    </div>
                    
                    <!-- Instructions -->
                    <div style="background-color: #f8f9ff; border-left: 4px solid #667eea; padding: 20px; margin: 30px 0; border-radius: 0 8px 8px 0;">
                        <h3 style="color: #333333; font-size: 18px; margin: 0 0 15px 0; font-weight: 600;">
                            📋 Instrucciones:
                        </h3>
                        <ol style="color: #666666; font-size: 14px; line-height: 1.6; margin: 0; padding-left: 20px;">
                            <li>Regresa a la página de login de VitiGenLabs</li>
                            <li>Copia este código: <strong>{security_key}</strong></li>
                            <li>Pégalo en el campo de verificación</li>
                            <li>Completa tu proceso de autenticación</li>
                        </ol>
                    </div>
                    
                    <!-- Quick Access Section -->
                    <div style="background-color: #e8f5e8; border: 1px solid #4ade80; border-radius: 8px; padding: 20px; margin: 30px 0; text-align: center;">
                        <p style="color: #166534; font-size: 14px; margin: 0 0 10px 0; font-weight: 600;">
                            🚀 Código de Verificación
                        </p>
                        <p style="color: #166534; font-size: 18px; margin: 0; line-height: 1.5; font-weight: 700; font-family: 'Courier New', monospace;">
                            {security_key}
                        </p>
                    </div>
                    
                    <!-- Security Notice -->
                    <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 20px; margin: 30px 0;">
                        <p style="color: #856404; font-size: 14px; margin: 0; line-height: 1.5;">
                            🔒 <strong>Nota de Seguridad:</strong> Si no solicitaste este código, puedes ignorar este mensaje de forma segura. 
                            Tu cuenta permanece protegida. Este código de 6 dígitos es único y expira automáticamente.
                        </p>
                    </div>
                    
                    <p style="color: #666666; font-size: 16px; line-height: 1.6; margin: 30px 0 0 0;">
                        ¿Necesitas ayuda? Contáctanos respondiendo a este email.
                    </p>
                </div>
                
                <!-- Footer -->
                <div style="background-color: #f8f9fa; padding: 30px; text-align: center; border-top: 1px solid #e9ecef;">
                    <p style="color: #6c757d; font-size: 14px; margin: 0 0 10px 0;">
                        <strong>VitiGenLabs</strong> - Investigación en Genética de la Vid
                    </p>
                    <p style="color: #6c757d; font-size: 12px; margin: 0;">
                        Este es un mensaje automático, por favor no respondas directamente a este email.
                    </p>
                    <p style="color: #6c757d; font-size: 12px; margin: 10px 0 0 0;">
                        © 2025 VitiGenLabs. Todos los derechos reservados.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        🧬 VitiGenLabs - Código de Seguridad
        
        ¡Hola {user_name}!
        
        Hemos recibido una solicitud para acceder a tu cuenta en VitiGenLabs.
        
        Tu código de seguridad de 6 dígitos es: {security_key}
        
        Instrucciones:
        1. Regresa a la página de login de VitiGenLabs
        2. Copia este código: {security_key}
        3. Pégalo en el campo de verificación
        4. Completa tu proceso de autenticación
        
        Este código expira en 24 horas.
        
        Nota de Seguridad: Si no solicitaste este código, puedes ignorar este mensaje.
        
        VitiGenLabs - Investigación en Genética de la Vid
        © 2025 VitiGenLabs. Todos los derechos reservados.
        """

        try:
            self.send_email(
                to_email=email,
                to_name=user_name,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                preheader=preheader,
                tags=["security-key", "authentication", "transactional"],
                reply_to_email=self.sender_email,
                reply_to_name="Soporte VitiGenLabs"
            )
            return True
        except Exception as e:
            logger.error(f"Error sending security key email to {email}: {e}")
            return False
    def send_welcome_email(
        self,
        email: str,
        user_name: str,
        login_url: str = "https://vitigenlabs.com/login"
    ) -> bool:
        """
        Send a welcome email to new users.

        Args:
            email: Recipient email address
            user_name: Name of the user
            login_url: URL to login page

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        subject = "🎉 ¡Bienvenido a VitiGenLabs!"
        preheader = "Tu cuenta ha sido creada exitosamente. Comienza tu investigación genética."
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Bienvenido a VitiGenLabs</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8f9fa;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 40px 30px; text-align: center;">
                    <h1 style="color: #ffffff; font-size: 32px; margin: 0; font-weight: 700;">🧬 VitiGenLabs</h1>
                    <p style="color: #e8f8ff; font-size: 18px; margin: 15px 0 0 0;">¡Bienvenido a la revolución genética!</p>
                </div>
                
                <!-- Content -->
                <div style="padding: 40px 30px;">
                    <h2 style="color: #333333; font-size: 28px; margin: 0 0 20px 0; font-weight: 600;">
                        ¡Hola {user_name}! 🎉
                    </h2>
                    
                    <p style="color: #666666; font-size: 16px; line-height: 1.6; margin: 0 0 30px 0;">
                        ¡Felicitaciones! Tu cuenta en VitiGenLabs ha sido creada exitosamente. 
                        Ahora tienes acceso a nuestra plataforma de análisis genético de última generación.
                    </p>
                    
                    <!-- CTA Button -->
                    <div style="text-align: center; margin: 40px 0;">
                        <a href="{login_url}" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; text-decoration: none; padding: 18px 40px; border-radius: 50px; font-weight: 600; font-size: 16px; display: inline-block; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4); transition: all 0.3s ease;">
                            🚀 Acceder a Mi Cuenta
                        </a>
                    </div>
                    
                    <!-- Features -->
                    <div style="background-color: #f8f9ff; border-radius: 12px; padding: 30px; margin: 30px 0;">
                        <h3 style="color: #333333; font-size: 20px; margin: 0 0 20px 0; font-weight: 600; text-align: center;">
                            🔬 ¿Qué puedes hacer en VitiGenLabs?
                        </h3>
                        
                        <div style="display: grid; gap: 20px;">
                            <div style="display: flex; align-items: flex-start; gap: 15px;">
                                <span style="font-size: 24px;">📊</span>
                                <div>
                                    <h4 style="color: #333333; font-size: 16px; margin: 0 0 5px 0; font-weight: 600;">Análisis de Archivos VCF</h4>
                                    <p style="color: #666666; font-size: 14px; margin: 0; line-height: 1.5;">Sube y procesa archivos VCF para análisis genético avanzado de variedades de vid.</p>
                                </div>
                            </div>
                            
                            <div style="display: flex; align-items: flex-start; gap: 15px;">
                                <span style="font-size: 24px;">🔍</span>
                                <div>
                                    <h4 style="color: #333333; font-size: 16px; margin: 0 0 5px 0; font-weight: 600;">Búsqueda de Genes</h4>
                                    <p style="color: #666666; font-size: 14px; margin: 0; line-height: 1.5;">Explora bases de datos genéticas con filtros avanzados y búsqueda en tiempo real.</p>
                                </div>
                            </div>
                            
                            <div style="display: flex; align-items: flex-start; gap: 15px;">
                                <span style="font-size: 24px;">📈</span>
                                <div>
                                    <h4 style="color: #333333; font-size: 16px; margin: 0 0 5px 0; font-weight: 600;">Reportes Detallados</h4>
                                    <p style="color: #666666; font-size: 14px; margin: 0; line-height: 1.5;">Genera reportes profesionales con visualizaciones y estadísticas avanzadas.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <p style="color: #666666; font-size: 16px; line-height: 1.6; margin: 30px 0 0 0;">
                        Si tienes alguna pregunta o necesitas ayuda para comenzar, 
                        no dudes en contactarnos respondiendo a este email.
                    </p>
                </div>
                
                <!-- Footer -->
                <div style="background-color: #f8f9fa; padding: 30px; text-align: center; border-top: 1px solid #e9ecef;">
                    <p style="color: #6c757d; font-size: 14px; margin: 0 0 10px 0;">
                        <strong>VitiGenLabs</strong> - Investigación en Genética de la Vid
                    </p>
                    <p style="color: #6c757d; font-size: 12px; margin: 0;">
                        Universidad de Caldas | Facultad de Ciencias Exactas y Naturales
                    </p>
                    <p style="color: #6c757d; font-size: 12px; margin: 10px 0 0 0;">
                        © 2025 VitiGenLabs. Todos los derechos reservados.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        try:
            self.send_email(
                to_email=email,
                to_name=user_name,
                subject=subject,
                html_content=html_content,
                preheader=preheader,
                tags=["welcome", "onboarding", "new-user"],
                reply_to_email=self.sender_email,
                reply_to_name="Equipo VitiGenLabs"
            )
            return True
        except Exception as e:
            logger.error(f"Error sending welcome email to {email}: {e}")
            return False

    def add_attachment_from_file(self, file_path: str, name: Optional[str] = None) -> Dict[str, str]:
        """
        Convert a local file to base64 attachment format.

        Args:
            file_path: Path to the file
            name: Custom name for the attachment

        Returns:
            Dict with attachment data for Brevo API
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(path, "rb") as file:
            content = base64.b64encode(file.read()).decode('utf-8')
        
        return {
            "content": content,
            "name": name or path.name
        }

    def add_attachment_from_url(self, url: str, name: str) -> Dict[str, str]:
        """
        Create attachment from URL.

        Args:
            url: URL to the file
            name: Name for the attachment

        Returns:
            Dict with attachment data for Brevo API
        """
        return {
            "url": url,
            "name": name
        }


# Global service instance
email_service = BrevoEmailService()

# Backward compatibility functions
def send_email(
    to_email: str,
    to_name: str,
    subject: str,
    html_content: str,
    sender_name: Optional[str] = None,
    sender_email: Optional[str] = None
) -> Dict[str, Any]:
    """Backward compatible send_email function."""
    return email_service.send_email(
        to_email=to_email,
        to_name=to_name,
        subject=subject,
        html_content=html_content,
        sender_name=sender_name,
        sender_email=sender_email
    )


def send_security_key_email(email: str, security_key: str, user_name: str = "User") -> bool:
    """Backward compatible security key email function."""
    return email_service.send_security_key_email(email, security_key, user_name)