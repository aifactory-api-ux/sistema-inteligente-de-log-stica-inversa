# backend/src/services/notification_service.py

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self):
        self.smtp_host = settings.smtp.SMTP_HOST
        self.smtp_port = settings.smtp.SMTP_PORT
        self.smtp_user = settings.smtp.SMTP_USER
        self.smtp_password = settings.smtp.SMTP_PASSWORD
        self.from_email = settings.smtp.SMTP_FROM
        self.enabled = os.getenv('SMTP_ENABLED', 'false').lower() == 'true'

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
    ) -> bool:
        if not self.enabled:
            logger.info(f"Email notifications disabled. Would send to {to_email}: {subject}")
            return True

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email

            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)

            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_user and self.smtp_password:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {to_email}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def send_return_confirmation(
        self,
        to_email: str,
        return_id: str,
        customer_name: str,
        destination: str,
        method: str,
    ) -> bool:
        subject = f"Confirmación de Devolución - {return_id}"
        body = f"""
Estimado/a {customer_name},

Su solicitud de devolución ha sido procesada exitosamente.

Detalles de la devolución:
- ID de devolución: {return_id}
- Destino: {destination}
- Método de retorno: {method}

 Recibirá más información sobre el seguimiento de su devolución pronto.

Saludos,
Equipo de Logística Inversa
        """.strip()

        html_body = f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
<h2 style="color: #1E40AF;">Confirmación de Devolución</h2>
<p>Estimado/a <strong>{customer_name}</strong>,</p>
<p>Su solicitud de devolución ha sido procesada exitosamente.</p>
<h3>Detalles:</h3>
<ul>
<li><strong>ID de devolución:</strong> {return_id}</li>
<li><strong>Destino:</strong> {destination}</li>
<li><strong>Método de retorno:</strong> {method}</li>
</ul>
<p>Recibirá más información sobre el seguimiento de su devolución pronto.</p>
<hr style="border: 1px solid #E5E7EB;">
<p style="color: #6B7280; font-size: 12px;">Equipo de Logística Inversa</p>
</body>
</html>
        """.strip()

        return self.send_email(to_email, subject, body, html_body)

    def send_kam_approval_request(
        self,
        to_email: str,
        kam_name: str,
        return_id: str,
        customer_id: str,
        total_items: int,
        total_value: float,
        channel: str,
    ) -> bool:
        subject = f"Solicitud de Aprobación KAM - Devolución {return_id}"
        body = f"""
Estimado/a {kam_name},

Se requiere su aprobación para una devolución B2B.

Detalles:
- ID de devolución: {return_id}
- ID de cliente: {customer_id}
- Canal: {channel}
- Total de artículos: {total_items}
- Valor total: {total_value:.2f} EUR

Por favor, acceda al Panel de Control para aprobar o rechazar esta solicitud.

Saludos,
Sistema de Logística Inversa
        """.strip()

        html_body = f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
<h2 style="color: #D97706;">Solicitud de Aprobación KAM</h2>
<p>Estimado/a <strong>{kam_name}</strong>,</p>
<p>Se requiere su aprobación para una devolución B2B.</p>
<h3>Detalles:</h3>
<ul>
<li><strong>ID de devolución:</strong> {return_id}</li>
<li><strong>ID de cliente:</strong> {customer_id}</li>
<li><strong>Canal:</strong> {channel}</li>
<li><strong>Total de artículos:</strong> {total_items}</li>
<li><strong>Valor total:</strong> {total_value:.2f} EUR</li>
</ul>
<p>Por favor, acceda al <strong>Panel de Control</strong> para aprobar o rechazar esta solicitud.</p>
<hr style="border: 1px solid #E5E7EB;">
<p style="color: #6B7280; font-size: 12px;">Sistema de Logística Inversa</p>
</body>
</html>
        """.strip()

        return self.send_email(to_email, subject, body, html_body)

    def send_kam_approval_notification(
        self,
        to_email: str,
        customer_name: str,
        return_id: str,
        approved: bool,
        approver_name: str,
        comments: Optional[str] = None,
    ) -> bool:
        status_text = "aprobada" if approved else "rechazada"
        subject = f"Devolución {return_id} - {'Aprobada' if approved else 'Rechazada'}"

        body = f"""
Estimado/a {customer_name},

Su solicitud de devolución {return_id} ha sido {status_text} por {approver_name}.
{"Se ha programado la recogida de su mercancía." if approved else f"Comentarios: {comments}" if comments else ""}

Saludos,
Equipo de Logística Inversa
        """.strip()

        html_body = f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
<h2 style="color: {'#059669' if approved else '#DC2626'};">Devolución {'Aprobada' if approved else 'Rechazada'}</h2>
<p>Estimado/a <strong>{customer_name}</strong>,</p>
<p>Su solicitud de devolución <strong>{return_id}</strong> ha sido <strong>{status_text}</strong> por {approver_name}.</p>
{"<p>Se ha programado la recogida de su mercancía.</p>" if approved else ""}
{('<p><strong>Comentarios:</strong> ' + comments + '</p>') if comments else ""}
<hr style="border: 1px solid #E5E7EB;">
<p style="color: #6B7280; font-size: 12px;">Equipo de Logística Inversa</p>
</body>
</html>
        """.strip()

        return self.send_email(to_email, subject, body, html_body)


notification_service = NotificationService()
