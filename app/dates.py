from datetime import datetime
from zoneinfo import ZoneInfo
def invoice_date(timestamp_utc: str, account_timezone: str) -> str:
    timestamp = timestamp_utc.replace("Z", "+00:00")
    instant = datetime.fromisoformat(timestamp)
    return instant.astimezone(ZoneInfo(account_timezone)).date().isoformat()