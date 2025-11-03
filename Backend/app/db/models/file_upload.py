from sqlalchemy import Column, Boolean,Text, Enum, Integer, String, Float, Date, DateTime, ForeignKey,TypeDecorator
from ..db_setup import Base
from sqlalchemy.orm import relationship
from datetime import datetime

from .mixins import Timestamp


#for typecoercion - handling the currency floats
from sqlalchemy import TypeDecorator, Float

class CurrencyToFloat(TypeDecorator):
    impl = Float

    def process_bind_param(self, value, dialect):
        if value and isinstance(value, str):
            return float(value.replace("$", "").replace(",", ""))
        return value


#extras

# Extras Report Model
class ExtrasReport(Base,Timestamp):
    __tablename__ = 'ConcatenatedExtras'
    
    id = Column(Integer, primary_key=True, index=True)
    CorrespondingDate = Column(Date,nullable=False)
    check_in = Column(Date)
    check_out = Column(Date)
    reservation_number = Column(String(50))
    guest_name = Column(String(100))
    extra = Column(String)
    category = Column(String(50))
    total = Column(CurrencyToFloat)


# Apartments Revenue Summary Model
class ApartmentsRevenueSummary(Base,Timestamp):
    __tablename__ = 'apartments_revenue_summary'
    
    id = Column(Integer, primary_key=True, index=True)
    CorrespondingDate = Column(Date,nullable=False)
    room = Column(CurrencyToFloat)
    extras = Column(CurrencyToFloat)
    taxes = Column(CurrencyToFloat)
    reservations = Column(Integer)
    nights = Column(Integer)
    occupancy = Column(String(10))
    adr = Column(CurrencyToFloat)
    lead_time = Column(Integer)
    los = Column(Integer)
    revpar = Column(CurrencyToFloat)


# Leaside Revenue Summary Model
class LeasideRevenueSummary(Base,Timestamp):
    __tablename__ = 'leaside_revenue_summary'
    
    id = Column(Integer, primary_key=True, index=True)
    CorrespondingDate = Column(Date,nullable=False)
    room = Column(CurrencyToFloat)
    extras = Column(CurrencyToFloat)
    taxes = Column(CurrencyToFloat)
    reservations = Column(Integer)
    nights = Column(Integer)
    occupancy = Column(String(10))
    adr = Column(CurrencyToFloat)
    lead_time = Column(Integer)
    los = Column(Integer)
    revpar = Column(CurrencyToFloat)


# Monastery Suites Revenue Summary Model
class MonasterySuitesRevenueSummary(Base,Timestamp):
    __tablename__ = 'monastery_suites_revenue_summary'
    
    id = Column(Integer, primary_key=True, index=True)
    CorrespondingDate = Column(Date,nullable=False)
    room = Column(CurrencyToFloat)
    extras = Column(CurrencyToFloat)
    taxes = Column(CurrencyToFloat)
    reservations = Column(Integer)
    nights = Column(Integer)
    occupancy = Column(String(10))
    adr = Column(CurrencyToFloat)
    lead_time = Column(Integer)
    los = Column(Integer)
    revpar = Column(CurrencyToFloat)


# Villa Nova Physiotherapy Sales Model
class VillaNovaPhysiotherapySales(Base,Timestamp):
    __tablename__ = 'villa_nova_physiotherapy_sales'
    
    id = Column(Integer, primary_key=True, index=True)
    CorrespondingDate = Column(Date,nullable=False)
    location = Column(String(100))
    purchase_date = Column(DateTime)
    invoice_date = Column(DateTime)
    patient_guid = Column(String(50))
    patient = Column(String(100))
    item = Column(String(100))
    staff_member = Column(String(100))
    payer = Column(String(100))
    invoice_number = Column(String(50))
    income_category = Column(String(100))
    details = Column(String)
    status = Column(String(50))
    subtotal = Column(CurrencyToFloat)
    hst = Column(CurrencyToFloat)
    total = Column(CurrencyToFloat)
    collected = Column(CurrencyToFloat)
    balance = Column(CurrencyToFloat)


# Riverside Therapeutics Sales Model
class RiversideTherapeuticsSales(Base,Timestamp):
    __tablename__ = 'riverside_therapeutics_sales'
    
    id = Column(Integer, primary_key=True, index=True)
    CorrespondingDate = Column(Date,nullable=False)
    location = Column(String(100))
    purchase_date = Column(DateTime)
    invoice_date = Column(DateTime)
    patient_guid = Column(String(50))
    patient = Column(String(100))
    item = Column(String(100))
    staff_member = Column(String(100))
    payer = Column(String(100))
    invoice_number = Column(String(50))
    income_category = Column(String(100))
    details = Column(String)
    status = Column(String(50))
    subtotal = Column(CurrencyToFloat)
    total = Column(CurrencyToFloat)
    collected = Column(CurrencyToFloat)
    balance = Column(CurrencyToFloat)


# Monastery Health Sales Model
class MonasteryHealthSales(Base,Timestamp):
    __tablename__ = 'monastery_health_sales'
    
    id = Column(Integer, primary_key=True, index=True)
    CorrespondingDate = Column(Date,nullable=False)
    location = Column(String(100))
    purchase_date = Column(DateTime)
    invoice_date = Column(DateTime)
    patient_guid = Column(String(50))
    patient = Column(String(100))
    item = Column(String(100))
    staff_member = Column(String(100))
    payer = Column(String(100))
    invoice_number = Column(String(50))
    income_category = Column(String(100))
    details = Column(String)
    status = Column(String(50))
    subtotal = Column(CurrencyToFloat)
    hst = Column(CurrencyToFloat)
    total = Column(CurrencyToFloat)
    collected = Column(CurrencyToFloat)
    balance = Column(CurrencyToFloat)


# Product Sales Model
class ProductSales(Base,Timestamp):
    __tablename__ = 'product_sales'
    
    id = Column(Integer, primary_key=True, index=True)
    CorrespondingDate = Column(Date,nullable=False)
    brand = Column(String(100))
    quantity = Column(Integer)
    amount = Column(CurrencyToFloat)
    adjustment = Column(CurrencyToFloat)
    total_sales = Column(CurrencyToFloat)
    tax = Column(CurrencyToFloat)
    refund = Column(CurrencyToFloat)

# Service Sales Model
class ServiceSales(Base,Timestamp):
    __tablename__ = 'service_sales'
    
    id = Column(Integer, primary_key=True, index=True)
    CorrespondingDate = Column(Date,nullable=False)
    category = Column(String(100))
    quantity = Column(Integer)
    amount = Column(CurrencyToFloat)
    adjustment = Column(CurrencyToFloat)
    total_sales = Column(CurrencyToFloat)
    tax = Column(CurrencyToFloat)
    refund = Column(CurrencyToFloat)

