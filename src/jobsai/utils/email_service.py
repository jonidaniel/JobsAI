"""
Email Service for Sending Cover Letters via AWS SES.

This module provides functionality to send generated cover letters as email
attachments using AWS Simple Email Service (SES).

The service:
1. Downloads documents from S3
2. Creates email with attachments
3. Sends email via AWS SES
4. Handles errors and logging

Note:
    Requires AWS SES to be configured and the Lambda execution role to have
    permissions to send emails via SES.
"""

import os
from typing import List, Optional
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from jobsai.utils.logger import get_logger
from jobsai.utils.state_manager import get_document_from_s3

logger = get_logger(__name__)

# AWS SES Configuration
SES_REGION = os.environ.get("SES_REGION", "eu-north-1")
SES_FROM_EMAIL = os.environ.get("SES_FROM_EMAIL", "")
EMAIL_ENABLED = os.environ.get("EMAIL_ENABLED", "false").lower() == "true"


def send_cover_letters_email(
    recipient_email: str,
    job_id: str,
    s3_keys: List[str],
    filenames: List[str],
) -> bool:
    """Send cover letters as email attachments via AWS SES.

    Downloads documents from S3, creates an email with attachments,
    and sends it via AWS SES.

    Args:
        recipient_email: Email address to send to (validated format)
        job_id: Job identifier for logging and correlation
        s3_keys: List of S3 keys for documents to attach
        filenames: List of filenames for attachments (must match s3_keys length)

    Returns:
        True if email sent successfully, False otherwise

    Raises:
        ValueError: If s3_keys and filenames lengths don't match
        Exception: If SES is not available or email sending fails
    """
    if not EMAIL_ENABLED:
        logger.warning(
            "Email delivery is disabled",
            extra={
                "extra_fields": {
                    "job_id": job_id,
                    "recipient_email_hash": _hash_email(recipient_email),
                }
            },
        )
        return False

    if not SES_FROM_EMAIL:
        logger.error(
            "SES_FROM_EMAIL not configured",
            extra={
                "extra_fields": {
                    "job_id": job_id,
                    "recipient_email_hash": _hash_email(recipient_email),
                }
            },
        )
        return False

    if len(s3_keys) != len(filenames):
        raise ValueError(
            f"s3_keys ({len(s3_keys)}) and filenames ({len(filenames)}) must have the same length"
        )

    try:
        import boto3

        ses_client = boto3.client("ses", region_name=SES_REGION)
    except ImportError:
        logger.error(
            "boto3 not available for SES",
            extra={
                "extra_fields": {
                    "job_id": job_id,
                    "recipient_email_hash": _hash_email(recipient_email),
                }
            },
        )
        return False
    except Exception as e:
        logger.error(
            "Failed to initialize SES client",
            extra={
                "extra_fields": {
                    "job_id": job_id,
                    "recipient_email_hash": _hash_email(recipient_email),
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            },
            exc_info=True,
        )
        return False

    try:
        # Create email message
        msg = MIMEMultipart()
        msg["From"] = SES_FROM_EMAIL
        msg["To"] = recipient_email
        msg["Subject"] = "Your Cover Letters from JobsAI"

        # Email body
        body_text = f"""Hello,

Thank you for using JobsAI! Your personalized cover letters are attached to this email.

You requested {len(filenames)} cover letter{'s' if len(filenames) > 1 else ''}.

Best regards,
JobsAI Team
"""
        msg.attach(MIMEText(body_text, "plain"))

        # Attach documents
        for s3_key, filename in zip(s3_keys, filenames):
            try:
                # Download document from S3
                document_bytes = get_document_from_s3(s3_key)
                if not document_bytes:
                    logger.warning(
                        "Failed to retrieve document from S3 for email attachment",
                        extra={
                            "extra_fields": {
                                "job_id": job_id,
                                "s3_key": s3_key,
                                "filename": filename,
                            }
                        },
                    )
                    continue

                # Create attachment
                attachment = MIMEBase(
                    "application",
                    "vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
                attachment.set_payload(document_bytes)
                encoders.encode_base64(attachment)
                attachment.add_header(
                    "Content-Disposition",
                    f'attachment; filename= "{filename}"',
                )
                msg.attach(attachment)

                logger.info(
                    "Attached document to email",
                    extra={
                        "extra_fields": {
                            "job_id": job_id,
                            "s3_key": s3_key,
                            "filename": filename,
                            "size_bytes": len(document_bytes),
                        }
                    },
                )
            except Exception as e:
                logger.error(
                    "Failed to attach document to email",
                    extra={
                        "extra_fields": {
                            "job_id": job_id,
                            "s3_key": s3_key,
                            "filename": filename,
                            "error": str(e),
                            "error_type": type(e).__name__,
                        }
                    },
                    exc_info=True,
                )
                # Continue with other attachments even if one fails

        # Send email via SES
        response = ses_client.send_raw_email(
            Source=SES_FROM_EMAIL,
            Destinations=[recipient_email],
            RawMessage={"Data": msg.as_string()},
        )

        logger.info(
            "Email sent successfully",
            extra={
                "extra_fields": {
                    "job_id": job_id,
                    "recipient_email_hash": _hash_email(recipient_email),
                    "attachment_count": len(filenames),
                    "message_id": response.get("MessageId"),
                }
            },
        )
        return True

    except Exception as e:
        logger.error(
            "Failed to send email",
            extra={
                "extra_fields": {
                    "job_id": job_id,
                    "recipient_email_hash": _hash_email(recipient_email),
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            },
            exc_info=True,
        )
        return False


def _hash_email(email: str) -> str:
    """Hash email address for logging (privacy protection).

    Creates a simple hash of the email address to use in logs
    instead of the plain email address.

    Args:
        email: Email address to hash

    Returns:
        Hashed email string (first 3 chars + hash of rest)
    """
    import hashlib

    if not email or "@" not in email:
        return "invalid"

    local, domain = email.split("@", 1)
    # Show first 3 chars of local part, hash the rest
    visible = local[:3] if len(local) > 3 else local
    hash_part = hashlib.sha256(email.encode()).hexdigest()[:8]
    return f"{visible}***@{domain} ({hash_part})"
