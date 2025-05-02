from sqlalchemy import Column, Integer, String, DateTime, UUID
from sqlalchemy.orm import declarative_base
import uuid

Base = declarative_base()


class GlucoseRecord(Base):
    __tablename__ = "glucose_records"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    device = Column(String, nullable=True)
    serial_number = Column(String, nullable=True)
    device_timestamp = Column(DateTime, nullable=True)
    record_type = Column(Integer, nullable=True)
    glucose_value = Column(Integer, nullable=True)
    glucose_scan = Column(Integer, nullable=True)
