from sqlalchemy import Column, Boolean,Text, Enum, Integer, String, Float, Date, DateTime, ForeignKey
from ..db_setup import Base
from sqlalchemy.orm import relationship
from datetime import datetime
#from file_upload import CurrencyToFloat

from .mixins import Timestamp

# All leaside Revenue Summary Model
class LeasideRevenue(Base,Timestamp):
    __tablename__ = 'LeasideRevenue'
    
    
    id = Column(Integer, primary_key=True, index=True)
    CorrespondingDate = Column(Date,nullable=False)
    Leaside = Column(Float)
    Hotel = Column(Float)
    Apartments = Column(Float)
    Spa_Service = Column(Float)
    MediSpa = Column(Float)
    Products = Column(Float)
    Bistro_and_Extras = Column(Float)
    Riverside_Therapeutics = Column(Float)
    Monastery_Health = Column(Float)
    VillaNova_Physiotherapy = Column(Float)
    Total = Column(Float)
    target_id = Column(Integer, ForeignKey("LeasideRevenueTargets.id"))
    target = relationship("LeasideRevenueTargets", back_populates="revenues")

#Revenue targets for Leaside brands

class LeasideRevenueTargets(Base,Timestamp):
    __tablename__ = 'LeasideRevenueTargets'
    
    
    id = Column(Integer, primary_key=True, index=True)
    CorrespondingMonth = Column(String(25))
    CorrespondingYear = Column(Integer)
    Leaside = Column(Float)
    Hotel = Column(Float)
    Apartments = Column(Float)
    Spa_Service = Column(Float)
    MediSpa = Column(Float)
    Products = Column(Float)
    Bistro_and_Extras = Column(Float)
    Riverside_Therapeutics = Column(Float)
    Monastery_Health = Column(Float)
    VillaNova_Physiotherapy = Column(Float)
    Total = Column(Float)
    revenues = relationship("LeasideRevenue", back_populates="target")


