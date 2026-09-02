"""
SAP HANA Database Connection.
"""

from hdbcli import dbapi
from core.config import settings
from core.logger import logger

class HanaConnection:
    client = None

    def connect(self):
        # Only attempt to connect if credentials are provided
        if not settings.hana_address or not settings.hana_user:
            logger.warning("SAP HANA credentials not fully configured. Skipping SAP HANA connection.")
            return

        logger.info(f"Connecting to SAP HANA Cloud at {settings.hana_address}:{settings.hana_port}")
        try:
            self.client = dbapi.connect(
                address=settings.hana_address,
                port=settings.hana_port,
                user=settings.hana_user,
                password=settings.hana_password
            )
            logger.info("Successfully connected to SAP HANA Cloud")
        except Exception as error:
            # We catch the error but do not raise it so we don't break the main app startup
            self.client = None
            logger.error("Failed to initialize SAP HANA Cloud connection", extra={"error": str(error)})

    def close(self):
        if self.client:
            self.client.close()
            logger.info("SAP HANA Cloud connection closed")

hana_connection = HanaConnection()
