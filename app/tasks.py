import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    filename='product_activity.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def log_product_creation(product_name: str):
    """
    Logs the creation of a new product to a file.
    This is intended to be run as a background task.
    """
    logging.info(f"New product created: {product_name}")
