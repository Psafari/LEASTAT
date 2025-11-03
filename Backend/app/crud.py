# DB operations: insert, fetch, query
# crud.py
from sqlalchemy.orm import Session

from . import models
from .pydantic_schemas import schemas

def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.UserCredentials(
        firstname=user.firstname,
        lastname=user.lastname,
        email=user.email,
        department=user.department,
        password=user.password  # You should hash this password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Add similar CRUD operations for your other models