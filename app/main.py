import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator, List, Optional

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select, func

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import SessionLocal, engine
from app.load_data import load_csv
from app.models import Base, GlucoseRecord
from app.schemas import GlucoseRecordCreate, GlucoseRecordOut, ThresholdOut

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        # Drop all tables
        await conn.run_sync(Base.metadata.drop_all)
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

    await load_csv()
    yield


app = FastAPI(lifespan=lifespan)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


@app.get("/api/v1/levels/", response_model=List[GlucoseRecordOut])
async def get_glucose_records_by_user_id(
    user_id: str,
    start: Optional[str] = None,  # YYYY-MM-DDTHH:MM:SS or YYYY-MM-DD
    end: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    query = select(GlucoseRecord).filter(GlucoseRecord.user_id == user_id)
    if start:
        start_dt = (
            datetime.fromisoformat(start)
            if "T" in start
            else datetime.strptime(start, "%Y-%m-%d")
        )
        query = query.filter(GlucoseRecord.device_timestamp >= start_dt)
    if end:
        end_dt = (
            datetime.fromisoformat(end)
            if "T" in end
            else datetime.strptime(end, "%Y-%m-%d")
        )
        query = query.filter(GlucoseRecord.device_timestamp <= end_dt)
    result = await db.execute(query.offset(offset).limit(limit))
    return result.scalars().all()


@app.get("/api/v1/levels/{id}", response_model=GlucoseRecordOut)
async def get_glucose_records(id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    query = select(GlucoseRecord).filter(GlucoseRecord.id == id)
    result = await db.execute(query)
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@app.post("/api/v1/levels/", response_model=GlucoseRecordOut)
async def create_glucose_record(
    entry: GlucoseRecordCreate, db: AsyncSession = Depends(get_db)
):
    record = GlucoseRecord(
        user_id=entry.user_id,
        device=entry.device,
        serial_number=entry.serial_number,
        device_timestamp=entry.device_timestamp,
        record_type=entry.record_type,
        glucose_value=entry.glucose_value,
        glucose_scan=entry.glucose_scan,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@app.get("/api/v1/threshold/", response_model=ThresholdOut)
async def get_threshold_by_user(
    user_id: uuid.UUID, threshold: int, db: AsyncSession = Depends(get_db)
):
    query = (
        select(func.count())
        .select_from(GlucoseRecord)
        .filter(
            GlucoseRecord.user_id == user_id,
            (GlucoseRecord.glucose_value <= threshold)
            | (GlucoseRecord.glucose_scan <= threshold),
        )
    )
    result = await db.execute(query)
    selected_result = result.scalar_one()

    total_query = (
        select(func.count())
        .select_from(GlucoseRecord)
        .filter(GlucoseRecord.user_id == user_id)
    )
    total_result = await db.execute(total_query)
    total_count = total_result.scalar_one()

    if total_count == 0:
        return ThresholdOut(below_threshold=0.0)

    return ThresholdOut(below_threshold=float(selected_result) / float(total_count))
