import logging

import uvicorn

from app.core.config import current_settings


logging.basicConfig(
    level=getattr(logging, current_settings.LOG_LEVEL),
    format=current_settings.LOG_FORMAT,
)

logger = logging.getLogger(__name__)


def main():
    logger.info("Starting %s v%s", current_settings.APP_NAME, current_settings.APP_VERSION)
    logger.info("Environment: %s", "development" if current_settings.DEBUG else "production")
    logger.info("Listening on %s:%s", current_settings.API_HOST, current_settings.API_PORT)

    uvicorn.run(
        "app.main:app",
        host=current_settings.API_HOST,
        port=current_settings.API_PORT,
        reload=current_settings.DEBUG,
        log_level=current_settings.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    main()
