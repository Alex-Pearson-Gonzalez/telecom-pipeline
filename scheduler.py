import time
import logging
import schedule
from pipeline import run_pipeline
from models import Base
from load import engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("pipeline.log"), logging.StreamHandler()]
)

logger = logging.getLogger(__name__)


def main():
    logger.info("Scheduler started")

    Base.metadata.create_all(engine)
    logger.info("Database schema verified")

    run_pipeline()
    schedule.every(1).hours.do(run_pipeline)

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()