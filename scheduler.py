import time
import logging
import schedule
from pipeline import run_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("pipeline.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    logger.info("Scheduler started")

    # Run once immediately on startup, so you don't wait for the first interval
    run_pipeline()

    # Then repeat on a schedule
    schedule.every(1).hours.do(run_pipeline)

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()