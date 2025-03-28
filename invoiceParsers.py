import re
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class InvoiceParser(ABC):
    @abstractmethod
    def extract_info(self, text):
        """Extract invoice information from text content."""
        pass

    @classmethod
    def name(cls):
        return cls.__name__.replace("InvoiceParser", "").lower()

class DougsInvoiceParser(InvoiceParser):
    @classmethod
    def name(cls):
        return "dougs"

    def extract_info(self, text):
        """Extract invoice information from text content."""
        invoice_match = re.search(r"Facture n°\s*([0-9]{4}-[0-9]{2}-FAC\s*\d+)", text)
        if invoice_match:
            invoice_number = invoice_match.group(1).replace("\n", " ").strip()
        else:
            raise ValueError("Invoice number not found.")

        order_match = re.search(r'Commande\s+([A-Z0-9\-]+)', text)
        if not order_match:
            raise ValueError("Order number not found.")
        order_number = order_match.group(1).strip()

        ttc_match = re.search(r'Total TTC\s*(?:à régler)?\s*([\d\s\.,]+)\s*€', text)
        if not ttc_match:
            raise ValueError("Total TTC not found.")
        total_ttc = ttc_match.group(1).strip()

        logger.info(f"Extracted invoice {invoice_number} for order {order_number}")
        return {
            'invoice_number': invoice_number,
            'order_number': order_number,
            'total_ttc': total_ttc
        }

# You could add more parser implementations for different invoice formats
class AlternateInvoiceParser(InvoiceParser):
    @classmethod
    def name(cls):
        return "alternate"

    def extract_info(self, text):
        # Different parsing logic for other invoice formats
        pass

# Registry of available parsers
AVAILABLE_PARSERS = {
    parser.name(): parser
    for parser in [DougsInvoiceParser, AlternateInvoiceParser]
}

def get_parser(name=None):
    """Factory function to get the appropriate parser"""
    if name is None:
        # Default to standard parser
        return DougsInvoiceParser()

    parser_class = AVAILABLE_PARSERS.get(name.lower())
    if parser_class is None:
        available = ", ".join(AVAILABLE_PARSERS.keys())
        raise ValueError(f"Unknown parser: {name}. Available parsers: {available}")

    return parser_class()
