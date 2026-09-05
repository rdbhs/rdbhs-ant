# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "python-dotenv>=1.2.2",
# ]
# ///

import csv
import os
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

CALENDAR_START = datetime.strptime("2024-12-29", "%Y-%m-%d")
CALENDAR_END = datetime.strptime("2050-12-31", "%Y-%m-%d")

INCREMENT_DAYS = 14
PAYMENT_INCREMENT_DAYS = 6

LANDING_PATH = Path(os.environ.get("LANDING_PATH"))


def create_payroll_calendar(start_date, end_date: datetime) -> list[dict]:
    payroll_calendar = []
    current_start_date = start_date

    while current_start_date <= end_date:
        current_end_date = current_start_date + timedelta(days=INCREMENT_DAYS - 1)
        payment_date = current_end_date + timedelta(days=PAYMENT_INCREMENT_DAYS)
        payroll_calendar.append(
            {
                "start_date": current_start_date,
                "end_date": current_end_date,
                "payment_date": payment_date,
            }
        )
        current_start_date += timedelta(days=INCREMENT_DAYS)

    return payroll_calendar


def save_to_csv(calendar: list[dict], file_path: str) -> None:
    with open(file_path, mode="w", newline="") as csv_file:
        fieldnames = [
            "start_date",
            "end_date",
            "payment_date",
        ]

        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for period in calendar:
            writer.writerow(
                {
                    "start_date": period["start_date"].strftime("%Y-%m-%d"),
                    "end_date": period["end_date"].strftime("%Y-%m-%d"),
                    "payment_date": period["payment_date"].strftime("%Y-%m-%d"),
                }
            )


if __name__ == "__main__":
    calendar = create_payroll_calendar(CALENDAR_START, CALENDAR_END)

    base_path = LANDING_PATH / "payroll_calendar"
    base_path.mkdir(parents=True, exist_ok=True)
    csv_file_path = base_path / "payroll_calendar.csv"
    save_to_csv(calendar, csv_file_path)
