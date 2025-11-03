#setting thsi up to track timestamps for database operations (update, get,post,put)

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime
from sqlalchemy.orm import declarative_mixin

from datetime import datetime, timezone

@declarative_mixin
class Timestamp:
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)