import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import NetworkSnapshot

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

engine = create_engine(DATABASE_URL)
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


def load_snapshot(clean_data: dict) -> None:
    session = Session()
    try:
        snapshot = NetworkSnapshot(**clean_data)
        session.add(snapshot)
        session.commit()
        logger.info(f"Loaded snapshot for {clean_data['asn']}, id={snapshot.id}")
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to load data for {clean_data['asn']}: {e}")
        raise
    finally:
        session.close()