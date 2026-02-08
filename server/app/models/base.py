# This is the "Parent" class all models inherit from
from app.core.database import Base

# This registers them with SQLAlchemy so Alembic can find them.
from app.models.user import User
from app.models.doctor import Doctor