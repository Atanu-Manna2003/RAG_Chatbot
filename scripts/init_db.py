#!/usr/bin/env python3
"""
Database initialization script - metadata only
"""
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.models.database import create_tables, engine

def init_database():
    """Initialize the database with required tables (metadata only)"""
    print("Initializing database for metadata storage...")
    create_tables()
    print("Database initialized successfully!")
    print("Storage: Document metadata in SQLite, chunks in ChromaDB vector store")

if __name__ == "__main__":
    init_database()