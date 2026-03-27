from datetime import date
from numbers import Number

import pandas as pd
from sqlalchemy.orm import Session

from app.models.models import DutySchedule


REQUIRED_COLUMNS = ["日期", "星期", "值班人"]


def import_schedule_from_excel(file_path: str, db: Session) -> dict:
    xls = pd.ExcelFile(file_path)
    imported = 0
    updated = 0
    skipped = 0
    skipped_details: list[dict] = []

    # Handle duplicate dates within the same import file/batch.
    pending_by_date: dict[date, DutySchedule] = {}

    for sheet_name in xls.sheet_names:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        if any(col not in df.columns for col in REQUIRED_COLUMNS):
            skipped += len(df)
            skipped_details.append({"sheet": sheet_name, "reason": "缺少必需列(日期/星期/值班人)", "count": int(len(df))})
            continue

        for idx, row in df.iterrows():
            duty_date = _safe_to_date(row.get("日期"))
            if not duty_date:
                skipped += 1
                skipped_details.append({"sheet": sheet_name, "row": int(idx) + 2, "reason": "日期为空或格式错误"})
                continue

            weekday = str(row.get("星期", "")).strip()
            person_name = str(row.get("值班人", "")).strip()
            if not person_name:
                skipped += 1
                skipped_details.append({"sheet": sheet_name, "row": int(idx) + 2, "reason": "值班人为空"})
                continue

            existed = pending_by_date.get(duty_date)
            if existed:
                # Duplicate date in current import file: keep latest row and count as update.
                existed.weekday_text = weekday
                existed.duty_person_name = person_name
                existed.source_sheet = sheet_name
                updated += 1
                continue

            existed = db.query(DutySchedule).filter(DutySchedule.duty_date == duty_date).first()
            if existed:
                existed.weekday_text = weekday
                existed.duty_person_name = person_name
                existed.source_sheet = sheet_name
                pending_by_date[duty_date] = existed
                updated += 1
            else:
                new_item = DutySchedule(
                    duty_date=duty_date,
                    weekday_text=weekday,
                    duty_person_name=person_name,
                    source_sheet=sheet_name,
                )
                db.add(new_item)
                pending_by_date[duty_date] = new_item
                imported += 1

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {
        "imported": imported,
        "updated": updated,
        "skipped": skipped,
        "skipped_details": skipped_details[:200],
    }


def _safe_to_date(value) -> date | None:
    if pd.isna(value):
        return None

    try:
        if isinstance(value, pd.Timestamp):
            return value.date()

        # Excel serial date number: 1 -> 1899-12-31 (with pandas/origin adjustment)
        # Avoid parsing plain integers like 1 as unix timestamp (1970-01-01).
        if isinstance(value, Number) and not isinstance(value, bool):
            # Basic sanity guard to avoid absurd serial numbers.
            if value < 1 or value > 200000:
                return None
            return pd.to_datetime(value, unit="D", origin="1899-12-30").date()

        parsed = pd.to_datetime(value, errors="coerce")
        if pd.isna(parsed):
            return None
        return parsed.date()
    except Exception:
        return None
