from sqlalchemy import Column, Boolean,Text, Enum, Integer, String, Float, Date, DateTime, ForeignKey
from ..db_setup import Base
from sqlalchemy.orm import relationship
from sqlalchemy_utils import EmailType
from datetime import datetime

from .mixins import Timestamp

# Profile: permanent identity info
class Profile(Base,Timestamp):
    __tablename__ = 'Profiles'
    
    id = Column(Integer, primary_key=True, index=True)
    firstname = Column(String(100))
    lastname = Column(String(100))
    email = Column(EmailType(100), unique=True, nullable=False)
    department = Column(String(100))
    password = Column(String(128))  # Store hashed passwords in production

    user = relationship("ActiveUser", back_populates="profile", uselist=False)

# User: session/activity info
class ActiveUser(Base,Timestamp):
    __tablename__ = "Users"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("Profiles.id"), nullable=False)
    department = Column(String(50))
    is_active = Column(Boolean, default=False)

    profile = relationship("Profile", back_populates="user")

