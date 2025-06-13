"""
Development database module that mocks MongoDB functionality.
This is used for development when MongoDB is not available.
"""
import logging
import sqlite3
import json
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class DevDB:
    """A simple SQLite-based mock for MongoDB during development."""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.db_path = "dev_db.sqlite"
        self.admin = self.AdminCommand()
    
    class AdminCommand:
        async def command(self, cmd):
            if cmd == 'ping':
                return True
            return False
    
    async def connect_to_database(self):
        """Create database connection."""
        try:
            # Create the SQLite database file if it doesn't exist
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create a generic table for storing collections and documents
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                collection TEXT,
                document_id TEXT,
                data TEXT,
                PRIMARY KEY (collection, document_id)
            )
            ''')
            
            conn.commit()
            conn.close()
            
            self.client = self
            self.db = self
            logger.info("Connected to development database (SQLite)!")
        except Exception as e:
            logger.error(f"Could not connect to development database: {e}")
            raise
    
    async def close_database_connection(self):
        """Close database connection."""
        self.client = None
        self.db = None
        logger.info("Closed development database connection!")
    
    def __getitem__(self, collection_name):
        """Access a collection by name."""
        return Collection(collection_name, self.db_path)

class Collection:
    """Mock MongoDB collection using SQLite."""
    
    def __init__(self, name, db_path):
        self.name = name
        self.db_path = db_path
    
    async def find_one(self, query):
        """Find a single document."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Convert the query to a simple key-value lookup
        if "_id" in query:
            document_id = str(query["_id"])
        else:
            # Use the first key-value pair in the query
            key = next(iter(query))
            document_id = str(query[key])
        
        cursor.execute(
            "SELECT data FROM documents WHERE collection = ? AND document_id = ?",
            (self.name, document_id)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return json.loads(result[0])
        return None
    
    async def find(self, query=None):
        """Find documents matching a query."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT data FROM documents WHERE collection = ?",
            (self.name,)
        )
        results = cursor.fetchall()
        conn.close()
        
        documents = [json.loads(row[0]) for row in results]
        return MockCursor(documents)
    
    async def insert_one(self, document):
        """Insert a document."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Use the _id field as document_id, or generate one
        document_id = str(document.get("_id", f"auto_{len(document)}"))
        
        cursor.execute(
            "INSERT OR REPLACE INTO documents (collection, document_id, data) VALUES (?, ?, ?)",
            (self.name, document_id, json.dumps(document))
        )
        conn.commit()
        conn.close()
        
        return InsertResult(document_id)
    
    async def update_one(self, query, update):
        """Update a document."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Convert the query to a simple key-value lookup
        if "_id" in query:
            document_id = str(query["_id"])
        else:
            # Use the first key-value pair in the query
            key = next(iter(query))
            document_id = str(query[key])
        
        # Get the existing document
        cursor.execute(
            "SELECT data FROM documents WHERE collection = ? AND document_id = ?",
            (self.name, document_id)
        )
        result = cursor.fetchone()
        
        if result:
            document = json.loads(result[0])
            
            # Apply the update
            if "$set" in update:
                for key, value in update["$set"].items():
                    document[key] = value
            
            # Save the updated document
            cursor.execute(
                "UPDATE documents SET data = ? WHERE collection = ? AND document_id = ?",
                (json.dumps(document), self.name, document_id)
            )
            conn.commit()
        
        conn.close()
        return UpdateResult(matched_count=1 if result else 0, modified_count=1 if result else 0)

class MockCursor:
    """Mock MongoDB cursor."""
    
    def __init__(self, documents):
        self.documents = documents
    
    async def to_list(self, length=None):
        """Convert cursor to list."""
        if length is None:
            return self.documents
        return self.documents[:length]

class InsertResult:
    """Mock MongoDB insert result."""
    
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id

class UpdateResult:
    """Mock MongoDB update result."""
    
    def __init__(self, matched_count, modified_count):
        self.matched_count = matched_count
        self.modified_count = modified_count

# Create global instance
mongodb = DevDB() 