"""Flask extensions initialization"""

from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Socket.IO
socket = SocketIO()

# JWT Manager
jwt = JWTManager()

# Database setup
POSTGRES_USER = os.getenv("POSTGRES_USERNAME")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DATABASE = os.getenv("PGDATABASE")
POSTGRES_HOSTNAME = os.getenv("POSTGRES_HOSTNAME")

conn_string = f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOSTNAME}:5432/{POSTGRES_DATABASE}"
engine = create_engine(conn_string)
SessionLocal = sessionmaker(engine)
