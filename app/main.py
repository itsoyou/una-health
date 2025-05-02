import logging
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import AsyncGenerator, List, Optional
import uuid
from contextlib import asynccontextmanager
from sqlalchemy import select

from app.models import GlucoseRecord, Base
from app.schemas import GlucoseRecordOut, GlucoseRecordCreate
from app.database import engine, SessionLocal
from app.load_data import load_csv

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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
