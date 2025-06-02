"""
Fix for SQLAlchemy PostgreSQL UUID compilation errors in Docker tests.
This script patches UUID columns in SQLAlchemy models to use a compatible type.
"""
import uuid
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID

# Import the Base and all models to ensure they're loaded
from app.db.base import Base
from app.models.user import User
from app.models.calendar import UserCalendar, CalendarAction

def fix_uuid_columns():
    """
    Patch all UUID columns in models to be compatible with PostgreSQL in Docker.
    This function should be called before creating tables in tests.
    """
    print("Patching UUID columns for PostgreSQL compatibility...")
    
    # Count of columns patched
    patched_count = 0
    
    # Loop through all tables in metadata
    for table_name, table in Base.metadata.tables.items():
        print(f"Checking table: {table_name}")
        
        # Loop through all columns in the table
        for column in table.columns:
            # Check if it's a UUID column
            if isinstance(column.type, UUID):
                print(f"  Patching column: {column.name}")
                
                # Store the original properties
                orig_primary_key = column.primary_key
                orig_nullable = column.nullable
                orig_default = column.default
                
                # Create a new column with the same properties but String type
                # This is a workaround for the PostgreSQL UUID compilation error
                new_col = Column(
                    String(36),
                    primary_key=orig_primary_key,
                    nullable=orig_nullable,
                    default=orig_default
                )
                
                # Replace the column properties
                column.type = new_col.type
                
                patched_count += 1
    
    print(f"Patched {patched_count} UUID columns for PostgreSQL compatibility")
    return patched_count

if __name__ == "__main__":
    fix_uuid_columns()
