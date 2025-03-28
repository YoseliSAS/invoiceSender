#!/usr/bin/env python3
import re
import sys
import os
import logging
import configparser
import argparse
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from pypdf import PdfReader
from invoiceParsers import get_parser, AVAILABLE_PARSERS

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("InvoiceSender")

def extract_text_from_pdf(pdf_file):
    """Extract text content from a PDF file."""
    try:
        with open(pdf_file, "rb") as f:
            reader = PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        return text
    except FileNotFoundError:
        raise ValueError(f"PDF file not found: {pdf_file}")
    except Exception as e:
        raise ValueError(f"Error reading PDF file: {e}")

def extract_invoice_info(text, parser_name=None):
    """Extract invoice information using the configured parser."""
    parser = get_parser(parser_name)
    return parser.extract_info(text)

def load_mail_config(config_file):
    """Load email configuration from an INI file."""
    if not os.path.exists(config_file):
        raise ValueError(f"Config file not found: {config_file}")

    config = configparser.ConfigParser()
    config.read(config_file)
    try:
        sender = config.get('mail', 'from')
        subject_template = config.get('mail', 'subject_template')
        body_template = config.get('mail', 'body_template')

        smtp_server = config.get('sendemail', 'smtpserver')
        smtp_port = config.getint('sendemail', 'smtpserverport')
        smtp_user = config.get('sendemail', 'smtpuser')
        smtp_password = config.get('sendemail', 'smtppass')
    except configparser.Error as e:
        raise ValueError(f"Error reading mail configuration: {e}")

    return sender, subject_template, body_template, smtp_server, smtp_port, smtp_user, smtp_password


def validate_email(email):
    """Simple email validation."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def get_recipients(order_number, mapping_file):
    """Get recipient email addresses for a given order number."""
    if not os.path.exists(mapping_file):
        raise ValueError(f"Mapping file not found: {mapping_file}")

    recipients = []
    with open(mapping_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith(order_number + ":"):
                emails = line.split(":", 1)[1]
                for email in emails.split(","):
                    email = email.strip()
                    if email and validate_email(email):
                        recipients.append(email)
                break

    if not recipients:
        raise ValueError(f"No valid recipients found for order {order_number}.")

    logger.info(f"Found {len(recipients)} recipients for order {order_number}")
    return recipients


def create_email_message(info, sender, subject_template, body_template, recipients, pdf_file):
    """Create an email message with the invoice information and PDF attachment."""
    subject = subject_template.format(invoice_number=info['invoice_number'])
    body = body_template.format(
        invoice_number=info['invoice_number'],
        order_number=info['order_number'],
        total_ttc=info['total_ttc']
    )

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = ", ".join(recipients)
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # Attach the PDF file
    try:
        with open(pdf_file, 'rb') as f:
            attach = MIMEApplication(f.read(), _subtype='pdf')
        filename = os.path.basename(pdf_file)
        attach.add_header('Content-Disposition', 'attachment', filename=filename)
        msg.attach(attach)
    except FileNotFoundError:
        logger.error(f"Could not attach PDF file {pdf_file} - file not found")
        raise

    return msg


def send_email_smtp(sender, recipients, msg, smtp_server, smtp_port, smtp_user, smtp_password):
    """Send an email message via SMTP."""
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        logger.info(f"Email sent successfully to {len(recipients)} recipients")
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error: {e}")
        raise ValueError(f"Failed to send email: {e}")

def display_email(msg, recipients):
    """Display email content in a human-readable format for test mode."""
    separator = "-" * 70

    print(separator)
    print("📧 EMAIL PREVIEW 📧")
    print(separator)
    print(f"From: {msg['From']}")
    print(f"To: {', '.join(recipients)}")
    print(f"Subject: {msg['Subject']}")
    print(separator)

    # Extract and print the email body
    for part in msg.walk():
        if part.get_content_type() == "text/plain":
            print("BODY:")
            print(part.get_payload(decode=True).decode('utf-8'))
            print(separator)

    # List attachments
    attachments = []
    for part in msg.walk():
        if part.get_content_disposition() == 'attachment':
            filename = part.get_filename()
            attachments.append(filename)

    if attachments:
        print("ATTACHMENTS:")
        for attachment in attachments:
            print(f"- {attachment}")
        print(separator)
    print(separator)

def main():
    parser = argparse.ArgumentParser(
        description="invoiceSender: Generate and send invoice emails."
    )
    parser.add_argument("--pdf", required=True, help="Path to the PDF invoice file.")
    parser.add_argument("--mail-config", required=True, help="Path to the mail configuration INI file.")
    parser.add_argument("--map", required=True, help="Path to the order mapping file.")
    parser.add_argument("--dry-run", action="store_true", help="Generate email without sending it (test mode).")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output.")
    parser.add_argument("--parser", choices=list(AVAILABLE_PARSERS.keys()),
                        default="dougs",
                        help="Invoice parser to use.")

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(2)

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    try:
        logger.info(f"Processing invoice from PDF: {args.pdf}")
        text = extract_text_from_pdf(args.pdf)
        logger.debug(f"Extracted text: {text[:200]}...")  # Show only first 200 chars

        info = extract_invoice_info(text, args.parser)
        sender, subject_template, body_template, smtp_server, smtp_port, smtp_user, smtp_password = \
            load_mail_config(args.mail_config)
        recipients = get_recipients(info['order_number'], args.map)

        msg = create_email_message(info, sender, subject_template, body_template, recipients, args.pdf)

        display_email(msg, recipients)

        if args.dry_run:
            logger.info("Dry run mode - email was not sent")
        else:
            # Ask for confirmation unless --no-confirm is specified
            confirm = input(f"\nSend this email to {len(recipients)} recipient(s)? (y/N): ").strip().lower()
            if confirm != 'y':
                logger.info("Email sending cancelled by user")
                return

            logger.info(f"Sending email to {len(recipients)} recipients")
            send_email_smtp(sender, recipients, msg, smtp_server, smtp_port, smtp_user, smtp_password)
            logger.info("Email sent successfully")

    except ValueError as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
