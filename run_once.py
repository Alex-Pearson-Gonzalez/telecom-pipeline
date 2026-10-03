"""Run the pipeline once, then show the latest snapshot for each operator."""
import logging

from sqlalchemy import func, select

from load import Session, engine
from models import Base, NetworkSnapshot
from pipeline import run_pipeline

# Entry point = the place where logging gets configured (same rule as scheduler.py)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def show_latest() -> None:
    session = Session()
    try:
        # Inner query: the newest id for each operator.
        # Outer query: fetch exactly those rows.
        latest_ids = select(func.max(NetworkSnapshot.id)).group_by(NetworkSnapshot.asn)
        rows = session.scalars(
            select(NetworkSnapshot)
            .where(NetworkSnapshot.id.in_(latest_ids))
            .order_by(NetworkSnapshot.asn)
        ).all()
        print("\nLatest snapshot per operator:")
        for r in rows:
            print(
                f"  {r.operator_name:<22} {r.asn:<8} "
                f"{r.prefix_count:>6} prefixes   {r.fetched_at:%Y-%m-%d %H:%M}"
            )
    finally:
        session.close()


if __name__ == "__main__":
    Base.metadata.create_all(engine)  # make sure the table exists
    run_pipeline()                    # extract -> transform -> load, once
    show_latest()                     # put the result in front of you
