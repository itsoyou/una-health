from app.models import GlucoseRecord
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


from app.main import app
import uuid
from datetime import datetime


@pytest.mark.asyncio
async def test_create_glucose_record_success(
    client: AsyncClient, db_session: AsyncSession
):
    # Create a new record
    test_user_id = str(uuid.uuid4())
    new_record = {
        "user_id": test_user_id,
        "device": "test_device",
        "serial_number": "test_serial",
        "device_timestamp": datetime.now().isoformat(),
        "record_type": 0,
        "glucose_value": 100,
        "glucose_scan": 100,
    }

    response = await client.post("/api/v1/levels/", json=new_record)
    assert response.status_code == 200
    created_record = response.json()

    # Verify the created record
    assert created_record["user_id"] == new_record["user_id"]
    assert created_record["device"] == new_record["device"]
    assert created_record["serial_number"] == new_record["serial_number"]
    assert created_record["glucose_value"] == new_record["glucose_value"]


@pytest.mark.asyncio
async def test_create_glucose_record_failure(
    client: AsyncClient, db_session: AsyncSession
):
    # Test with invalid data
    invalid_record = {
        "user_id": "test_user",
        "device": "test_device",
        # Missing required fields
    }
    response = await client.post("/api/v1/levels/", json=invalid_record)
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_get_glucose_record_by_id_success(
    client: AsyncClient, db_session: AsyncSession
):
    # Create a new record
    test_user_id = str(uuid.uuid4())
    test_record = GlucoseRecord(
        user_id=test_user_id,
        device="test_device",
        serial_number="test_serial",
        device_timestamp=datetime.now(),
        record_type=1,
        glucose_value=80,
        glucose_scan=80,
    )

    db_session.add(test_record)
    await db_session.commit()

    result = await db_session.execute(
        select(GlucoseRecord).where(GlucoseRecord.user_id == test_user_id)
    )
    saved_records = result.scalars().all()
    assert len(saved_records) == 1

    # First get a list of records to get a valid ID
    response = await client.get(f"/api/v1/levels/?user_id={test_user_id}")
    assert response.status_code == 200
    records = response.json()
    if records:
        record_id = records[0]["id"]

        # Test getting specific record
        response = await client.get(f"/api/v1/levels/{record_id}")
        assert response.status_code == 200
        record = response.json()
        assert record["id"] == record_id


@pytest.mark.asyncio
async def test_get_glucose_record_by_id_failure(client: AsyncClient):
    invalid_id = str(uuid.uuid4())
    response = await client.get(f"/api/v1/levels/{invalid_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_glucose_records_by_user_id(
    client: AsyncClient, db_session: AsyncSession
):
    test_user_id = str(uuid.uuid4())
    test_record = GlucoseRecord(
        user_id=test_user_id,
        device="test_device",
        serial_number="test_serial",
        device_timestamp=datetime.now(),
        record_type=1,
        glucose_value=80,
        glucose_scan=80,
    )
    db_session.add(test_record)
    test_record = GlucoseRecord(
        user_id=test_user_id,
        device="test_device",
        serial_number="test_serial",
        device_timestamp=datetime.now(),
        record_type=1,
        glucose_value=100,
        glucose_scan=100,
    )
    db_session.add(test_record)
    await db_session.commit()

    result = await db_session.execute(
        select(GlucoseRecord).where(GlucoseRecord.user_id == test_user_id)
    )
    saved_records = result.scalars().all()
    assert len(saved_records) == 2

    # Test getting records for a specific user
    response = await client.get(f"/api/v1/levels/?user_id={test_user_id}")
    assert response.status_code == 200
    records = response.json()
    assert isinstance(records, list)
    assert len(records) == 2

    # Test with pagination
    response = await client.get(
        f"/api/v1/levels/?user_id={test_user_id}&limit=1&offset=1"
    )
    assert response.status_code == 200
    assert len(response.json()) == 1

    # Test with date filters
    response = await client.get(
        f"/api/v1/levels/?user_id={test_user_id}&start=2024-01-01T00:00:00"
    )
    assert response.status_code == 200
    assert len(response.json()) == 2
    response = await client.get(
        f"/api/v1/levels/?user_id={test_user_id}&start=2024-01-01"
    )
    assert response.status_code == 200
    assert len(response.json()) == 2
