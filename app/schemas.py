from pydantic import BaseModel, ConfigDict, field_serializer
from typing import Optional
from datetime import datetime
import uuid


class GlucoseRecordOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    device: str
    serial_number: str
    device_timestamp: datetime
    record_type: Optional[int]
    glucose_value: Optional[int]
    glucose_scan: Optional[int]
    model_config = ConfigDict(
        from_attributes=True,
    )

    @field_serializer("device_timestamp")
    def serialize_device_timestamp(self, device_timestamp: datetime, _info):
        return device_timestamp.strftime("%Y-%m-%d %H:%M:%S")


class GlucoseRecordCreate(BaseModel):
    user_id: str
    device: Optional[str]
    serial_number: Optional[str]
    device_timestamp: Optional[datetime]
    record_type: Optional[int]
    glucose_value: Optional[int]
    glucose_scan: Optional[int]


class ThresholdOut(BaseModel):
    below_threshold: float
