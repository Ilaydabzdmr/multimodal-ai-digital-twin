"""
Infrastructure and Database Connection Module
=============================================

This module provides connections to infrastructure services like PostgreSQL, Redis, and MinIO.
It manages database operations, cache management, and file storage functions.

PURPOSE:
- Manage database connections
- Coordinate cache services
- Provide file storage operations
- Perform event logging and monitoring

REASON FOR CREATION:
- Provide centralized infrastructure management
- Optimize connection pooling
- Provide error handling and fallback
- Optimize performance

TECHNOLOGIES USED:
- PostgreSQL: Main database
- Redis: In-memory cache
- MinIO: Object storage
- psycopg: PostgreSQL adapter

FEATURES:
- Lazy initialization
- Connection pooling
- Error handling
- Event logging
"""

# === Infrastructure and Database ===
# Forward reference support for Python 3.7+
from __future__ import annotations

# Operating system operations and environment variables
import os

# Type hints: Optional = optional, Dict = dictionary, Any = any type
from typing import Optional, Dict, Any

# === Database Connections ===
# PostgreSQL database connection (psycopg v3)
try:
    import psycopg
except ImportError:
    psycopg = None

# Redis cache client library
import redis

# MinIO object storage client
from minio import Minio


# --- Global client variables ---
# Global PostgreSQL connection (lazy initialization)
_pg_conn: Optional[Any] = None
# Global Redis client object
_redis_client: Optional[redis.Redis] = None
# Global MinIO client object
_minio_client: Optional[Minio] = None

# --- PostgreSQL connection ---
def get_pg_conn():
	global _pg_conn
	# Return existing connection if already initialized
	if _pg_conn is not None:
		return _pg_conn
	# DSN (Data Source Name) is read from environment variable
	pg_dsn = os.getenv("POSTGRES_DSN", "")
	if not pg_dsn or psycopg is None:
		return None
	try:
		_pg_conn = psycopg.connect(pg_dsn, autocommit=True)
		# Creating schema and tables
		_with_schema(_pg_conn)
		return _pg_conn
	except Exception:
		return None


def _with_schema(conn) -> None:
	# Ensures event_log table exists in PostgreSQL
	try:
		with conn.cursor() as cur:
			cur.execute(
				"""
				CREATE TABLE IF NOT EXISTS event_log (
					id SERIAL PRIMARY KEY,
					event_type TEXT,
					details JSONB,
					created_at TIMESTAMP DEFAULT NOW()
				);
				"""
			)
	except Exception:
		pass

# Function to log events to PostgreSQL
def log_event(event_type: str, details: Dict[str, Any]) -> None:
	conn = get_pg_conn()
	if not conn:
		return
	try:
		with conn.cursor() as cur:
			# details dict → written as JSON string
			cur.execute("INSERT INTO event_log (event_type, details) VALUES (%s, %s)", (event_type, json.dumps(details)))
	except Exception:
		pass


# --- Redis client ---
def get_redis_client():
	global _redis_client
	if _redis_client is not None:
		return _redis_client
	redis_url = os.getenv("REDIS_URL", "")
	if not redis_url:
		return None
	try:
		_redis_client = redis.from_url(redis_url)
		return _redis_client
	except Exception:
		return None

# --- MinIO client ---
def get_minio_client() -> Minio:
	global _minio_client
	if _minio_client is not None:
		return _minio_client
	
	# MinIO endpoint and credentials are retrieved from environment variables
	endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
	access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
	secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
	secure = os.getenv("MINIO_SECURE", "false").lower() == "true"
	_minio_client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)
	return _minio_client

# Checks if object storage bucket exists, creates if missing
def ensure_buckets(client: Minio) -> None:
	bucket = os.getenv("OBJECT_BUCKET", "health-coach")
	try:
		if not client.bucket_exists(bucket):
			client.make_bucket(bucket)
	except Exception:
		pass

# import placed last to avoid circular at module import
# Import json last to avoid circular import issues
import json  # noqa: E402
