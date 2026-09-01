import logging
from extract import fetch_prefix_count
from transform import transform_prefix_data
from load import load_snapshot


logger = logging.getLogger(__name__)

ASNS = ["AS3352", "AS12430", "AS12479"]


def run_pipeline():
    logger.info("Pipeline started")
    success_count = 0
    failure_count = 0

    for asn in ASNS:
        try:
            logger.info(f"Processing {asn}...")

            raw = fetch_prefix_count(asn) # extract
            clean = transform_prefix_data(raw, asn) # transform
            load_snapshot(clean)  # load

            logger.info(f"{asn}: {clean['prefix_count']} prefixes loaded")
            success_count += 1

        except Exception as e:
            logger.error(f"Failed to process {asn}: {e}")
            failure_count += 1

    logger.info(f"Pipeline finished. Success: {success_count}, Failures: {failure_count}")


if __name__ == "__main__":
    run_pipeline()
