"""Configuration from environment variables"""
import os

# MongoDB
MONGODB_HOST = os.getenv("MONGODB_HOST", "localhost")
MONGODB_PORT = os.getenv("MONGODB_PORT", "27017")
MONGODB_USER = os.getenv("MONGODB_USER", "admin")
MONGODB_PASSWORD = os.getenv("MONGODB_PASSWORD", "password")
MONGODB_DB = os.getenv("MONGODB_DB")
MONGODB_URL = os.getenv("MONGODB_URL")

# RabbitMQ
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")

# Rate Limiting
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "1000"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

# CSV Seeding
CSV_PATH = os.getenv("CSV_PATH", "/app/data/events_sample.csv")