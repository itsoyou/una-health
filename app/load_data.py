import csv
from pathlib import Path
from datetime import datetime
import uuid
import logging

from app.database import SessionLocal
from app.models import GlucoseRecord

logger = logging.getLogger(__name__)


async def load_csv():
    base_dir = Path(__file__).parent.parent
    csv_dir = base_dir / "sample-data"
    csv_files = list(csv_dir.glob("*.csv"))

    async with SessionLocal() as session:
        for csv_file in csv_files:
            user_id = uuid.UUID(csv_file.stem)

            with open(csv_file, newline="", encoding="utf-8-sig") as file:
                lines = file.readlines()

            lines = [line for line in lines if line.strip()]
            reader = csv.DictReader(lines[1:])
            records = []

            for row in reader:
                row = {k.strip(): v.strip() for k, v in row.items() if k is not None}

                timestamp_str = row.get("Gerätezeitstempel", "")
                try:
                    device_timestamp = datetime.strptime(
                        timestamp_str, "%d-%m-%Y %H:%M"
                    )
                except Exception:
                    continue

                try:
                    glucose_record = GlucoseRecord(
                        user_id=user_id,
                        device=row.get("Gerät"),
                        serial_number=row.get("Seriennummer"),
                        device_timestamp=device_timestamp,
                        record_type=(
                            int(row.get("Aufzeichnungstyp", 0))
                            if row.get("Aufzeichnungstyp")
                            else None
                        ),
                        glucose_value=(
                            int(row.get("Glukosewert-Verlauf mg/dL", 0))
                            if row.get("Glukosewert-Verlauf mg/dL")
                            else None
                        ),
                        glucose_scan=(
                            int(row.get("Glukose-Scan mg/dL", 0))
                            if row.get("Glukose-Scan mg/dL")
                            else None
                        ),
                    )
                    session.add(glucose_record)
                    records.append(glucose_record)
                except Exception as e:
                    msg = (
                        f"❌ Failed to create GlucoseRecord for row in {csv_file.name}"
                    )
                    logger.error(f"{msg}: {row}\n{e}")
                    continue

            await session.commit()
            logger.info(f"✅ Committed {len(records)} records from {csv_file}")
