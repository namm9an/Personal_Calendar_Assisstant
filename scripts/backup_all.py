#!/usr/bin/env python3
"""
Backup script for Calendar Assistant
Backs up MongoDB data and Redis data
"""

import os
import sys
import subprocess
import argparse
from datetime import datetime
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def backup_mongodb(output_dir: str):
    """Backup MongoDB data"""
    logger.info("Backing up MongoDB data...")
    
    # Create MongoDB backup directory
    mongo_backup_dir = os.path.join(output_dir, "mongodb")
    os.makedirs(mongo_backup_dir, exist_ok=True)
    
    # Get MongoDB connection details from environment
    mongo_uri = os.getenv("MONGODB_URI")
    if not mongo_uri:
        logger.error("MONGODB_URI environment variable not set")
        return False
    
    # Run mongodump
    try:
        subprocess.run([
            "mongodump",
            "--uri", mongo_uri,
            "--out", mongo_backup_dir
        ], check=True)
        logger.info("MongoDB backup completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"MongoDB backup failed: {str(e)}")
        return False

def backup_redis(output_dir: str):
    """Backup Redis data"""
    logger.info("Backing up Redis data...")
    
    # Create Redis backup directory
    redis_backup_dir = os.path.join(output_dir, "redis")
    os.makedirs(redis_backup_dir, exist_ok=True)
    
    # Get Redis connection details from environment
    redis_uri = os.getenv("REDIS_URI")
    if not redis_uri:
        logger.error("REDIS_URI environment variable not set")
        return False
    
    # Run redis-cli save
    try:
        subprocess.run([
            "redis-cli",
            "-u", redis_uri,
            "SAVE"
        ], check=True)
        logger.info("Redis backup completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Redis backup failed: {str(e)}")
        return False

def main():
    """Main backup function"""
    parser = argparse.ArgumentParser(description="Backup Calendar Assistant data")
    parser.add_argument("--output", required=True, help="Output directory for backups")
    args = parser.parse_args()
    
    # Create backup directory
    backup_dir = os.path.join(args.output, datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(backup_dir, exist_ok=True)
    
    # Backup MongoDB
    mongo_success = backup_mongodb(backup_dir)
    
    # Backup Redis
    redis_success = backup_redis(backup_dir)
    
    # Create backup metadata
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "mongodb_backup": mongo_success,
        "redis_backup": redis_success
    }
    
    # Save metadata
    with open(os.path.join(backup_dir, "backup_metadata.json"), "w") as f:
        import json
        json.dump(metadata, f, indent=2)
    
    if mongo_success and redis_success:
        logger.info(f"Backup completed successfully: {backup_dir}")
        return 0
    else:
        logger.error("Backup completed with errors")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 