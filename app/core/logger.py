import logging
import sys


# =====================================================
# 🔥 LOGGER CONFIGURATION
# =====================================================

logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(message)s"
    ),
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("medroute")