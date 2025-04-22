from pydantic import BaseModel
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

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda dt: dt.strftime("%Y-%m-%d %H:%M:%S")
        }


class GlucoseRecordCreate(BaseModel):
    user_id: str
    device: Optional[str]
    serial_number: Optional[str]
    device_timestamp: Optional[datetime]
    record_type: Optional[int]
    glucose_value: Optional[int]
    glucose_scan: Optional[int]
