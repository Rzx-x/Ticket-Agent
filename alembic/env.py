from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Import your models
from db.models import Base  

# Alembic Config
config = context.config
fileConfig(config.config_file_name)

# Target metadata
target_metadata = Base.metadata
