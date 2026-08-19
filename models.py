from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class NetworkSnapshot(Base):
    __tablename__ = "network_snapshots"

    id = Column(Integer, primary_key=True)
    asn = Column(String(20), nullable=False)
    operator_name = Column(String(100))
    prefix_count = Column(Integer)
    fetched_at = Column(DateTime, nullable=False)

    def __repr__(self):
        return f"<NetworkSnapshot(asn={self.asn}, prefixes={self.prefix_count})>"