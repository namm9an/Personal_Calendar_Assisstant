#!/usr/bin/env python3
"""
Restore script for Calendar Assistant
Restores MongoDB data and Redis data from backups
"""

import os
import sys
import subprocess
import argparse
import logging
from pathlib import Path
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def restore_mongodb(backup_dir: str):
    """Restore MongoDB data"""
    logger.info("Restoring MongoDB data...")
    
    # Get MongoDB backup directory
    mongo_backup_dir = os.path.join(backup_dir, "mongodb")
    if not os.path.exists(mongo_backup_dir):
        logger.error(f"MongoDB backup directory not found: {mongo_backup_dir}")
        return False
    
    # Get MongoDB connection details from environment
    mongo_uri = os.getenv("MONGODB_URI")
    if not mongo_uri:
        logger.error("MONGODB_URI environment variable not set")
        return False
    
    # Run mongorestore
    try:
        subprocess.run([
            "mongorestore",
            "--uri", mongo_uri,
            "--dir", mongo_backup_dir
        ], check=True)
        logger.info("MongoDB restore completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"MongoDB restore failed: {str(e)}")
        return False

def restore_redis(backup_dir: str):
    """Restore Redis data"""
    logger.info("Restoring Redis data...")
    
    # Get Redis backup directory
    redis_backup_dir = os.path.join(backup_dir, "redis")
    if not os.path.exists(redis_backup_dir):
        logger.error(f"Redis backup directory not found: {redis_backup_dir}")
        return False
    
    # Get Redis connection details from environment
    redis_uri = os.getenv("REDIS_URI")
    if not redis_uri:
        logger.error("REDIS_URI environment variable not set")
        return False
    
    # Run redis-cli restore
    try:
        subprocess.run([
            "redis-cli",
            "-u", redis_uri,
            "FLUSHALL"
        ], check=True)
        
        # Restore Redis data
        subprocess.run([
            "redis-cli",
            "-u", redis_uri,
            "RESTORE", "dump.rdb"
        ], check=True)
        
        logger.info("Redis restore completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Redis restore failed: {str(e)}")
        return False

def main():
    """Main restore function"""
    parser = argparse.ArgumentParser(description="Restore Calendar Assistant data")
    parser.add_argument("--backup-dir", required=True, help="Backup directory to restore from")
    args = parser.parse_args()
    
    # Check if backup directory exists
    if not os.path.exists(args.backup_dir):
        logger.error(f"Backup directory not found: {args.backup_dir}")
        return 1
    
    # Check backup metadata
    metadata_file = os.path.join(args.backup_dir, "backup_metadata.json")
    if os.path.exists(metadata_file):
        with open(metadata_file, "r") as f:
            metadata = json.load(f)
            logger.info(f"Restoring from backup created at: {metadata['timestamp']}")
    
    # Restore MongoDB
    mongo_success = restore_mongodb(args.backup_dir)
    
    # Restore Redis
    redis_success = restore_redis(args.backup_dir)
    
    if mongo_success and redis_success:
        logger.info("Restore completed successfully")
        return 0
    else:
        logger.error("Restore completed with errors")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 