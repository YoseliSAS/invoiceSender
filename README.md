## Overview

Invoice Sender is a command-line utility that automates the process of extracting information from invoice PDFs and sending them via email to the appropriate recipients. It's designed to be flexible, supporting different invoice formats through a pluggable parser system.

## Features

- Extract key information from PDF invoices (invoice number, order number, total amount)
- Match order numbers to recipient email addresses using a mapping file
- Customizable email templates for subject and body
- Test mode to preview emails without sending
- Support for different invoice formats via pluggable parsers
- SMTP email integration

## Installation

### Prerequisites

- Python 3.6 or higher
- pip (Python package manager)

### Step 1: Clone the repository

```bash
git clone https://github.com/YoseliSAS/invoiceSender
cd invoiceSender
```

### Step 2: Install dependencies

```bash
pip install pypdf
```

## Configuration

### Mail Configuration File (mail_template.ini)

Create a configuration file for email settings:

```ini
[mail]
from = invoices@example.com
subject_template = Invoice {invoice_number}
body_template = Dear customer,

Please find attached invoice {invoice_number} for your order {order_number}.
The total amount is {total_ttc} EUR.

Best regards,
Your Company

[sendemail]
smtpserver = smtp.example.com
smtpserverport = 587
smtpuser = your_username
smtppass = your_password
```

### Order Mapping File (orders_mapping.txt)

Create a mapping file that links order numbers to recipient email addresses:

```
# Format: ORDER_NUMBER:email1@example.com,email2@example.com
ABC-123:john.doe@example.com
DEF-456:jane.smith@example.com,accounts@company.com
```

## Usage

Basic usage:

```bash
./invoiceSender.py --pdf invoice.pdf --mail-config mail_template.ini --map orders_mapping.txt
```

### Command-line Options

- `--pdf`: Path to the PDF invoice file (required)
- `--mail-config`: Path to the mail configuration INI file (required)
- `--map`: Path to the order mapping file (required)
- `--test`: Generate email without sending it (test mode)
- `--verbose`: Enable verbose output for debugging
- `--parser`: Invoice parser to use (default: "dougs")

### Examples

**Test mode (preview email without sending):**

```bash
./invoiceSender.py --pdf invoice.pdf --mail-config mail_template.ini --map orders_mapping.txt --test
```

**Using a specific parser:**

```bash
./invoiceSender.py --pdf invoice.pdf --mail-config mail_template.ini --map orders_mapping.txt --parser alternate
```

**Verbose mode for debugging:**

```bash
./invoiceSender.py --pdf invoice.pdf --mail-config mail_template.ini --map orders_mapping.txt --verbose
```

## Adding Custom Invoice Parsers

The system supports different invoice formats through parser plugins. To add a new parser:

1. Edit `invoiceParsers.py`
2. Create a new class that inherits from `InvoiceParser`
3. Implement the `extract_info` method
4. Add your parser to the `AVAILABLE_PARSERS` dictionary

## Troubleshooting

If you encounter issues:

1. Try running with the `--verbose` flag for more detailed logs
2. Ensure your PDF is readable and contains the expected information
3. Verify your configuration files have the correct format and permissions
4. Check that the SMTP server settings are correct

## License

This project is licensed under the MIT License - see the LICENSE file for details.
