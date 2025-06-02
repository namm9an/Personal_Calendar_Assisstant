"""
Monkeypatch for SQLAlchemy UUID columns to fix PostgreSQL compatibility in Docker tests.
This must be imported at the very beginning of conftest.py, before importing any models.
"""
import uuid
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID

# Original UUID initializer
_original_uuid_init = UUID.__init__

# Patched UUID initializer that uses String(36) instead
def _patched_uuid_init(self, *args, **kwargs):
    # Call original init with modified args
    _original_uuid_init(self, *args, **kwargs)
    # Override the type to be String(36)
    self.__class__ = String
    self.__init__(36)

# Apply the monkeypatch
UUID.__init__ = _patched_uuid_init

print("\n=== Applied UUID monkeypatch for PostgreSQL compatibility ===")
print("All UUID columns will be treated as String(36)")
