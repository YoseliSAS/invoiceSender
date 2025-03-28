import re
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class InvoiceParser(ABC):
    @abstractmethod
    def extract_info(self, text):
        """Extract invoice information from text content."""
        pass

class DougsInvoiceParser(InvoiceParser):
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
    def extract_info(self, text):
        # Different parsing logic for other invoice formats
        pass
