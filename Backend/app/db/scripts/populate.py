import random
from datetime import datetime, date, timedelta
from faker import Faker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import all your models
from ..models.file_upload import (
    ExtrasReport, ApartmentsRevenueSummary, LeasideRevenueSummary,
    MonasterySuitesRevenueSummary, VillaNovaPhysiotherapySales,
    RiversideTherapeuticsSales, MonasteryHealthSales, ProductSales, ServiceSales
)
from ..models.additional_table import LeasideRevenue, LeasideRevenueTargets

# Initialize Faker
fake = Faker()

def generate_dummy_data():
    # Database connection
    DATABASE_URL = "postgresql://postgres:Hello7898.pgsql@localhost:5432/leaside"
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    # Helper functions
    def random_currency(min_val=0, max_val=1000):
        return round(random.uniform(min_val, max_val), 2)

    def random_date(start_date, end_date):
        time_between = end_date - start_date
        random_days = random.randrange(time_between.days)
        return start_date + timedelta(days=random_days)

    try:
        print(" Clearing existing data...")
        # Clear all tables in reverse order of dependencies
        db.query(LeasideRevenue).delete()
        db.query(LeasideRevenueTargets).delete()
        db.query(ExtrasReport).delete()
        db.query(ApartmentsRevenueSummary).delete()
        db.query(LeasideRevenueSummary).delete()
        db.query(MonasterySuitesRevenueSummary).delete()
        db.query(VillaNovaPhysiotherapySales).delete()
        db.query(RiversideTherapeuticsSales).delete()
        db.query(MonasteryHealthSales).delete()
        db.query(ProductSales).delete()
        db.query(ServiceSales).delete()
        db.commit()
        print(" Existing data cleared successfully!!!!")

        # Generate data for 2024-2025
        start_date = date(2024, 1, 1)
        end_date = date(2025, 12, 31)
        
        print("Starting dummy data generation...")
        
        # 1. Leaside Revenue Targets (monthly targets for 2024-2025)
        print(" Generating Leaside Revenue Targets...")
        targets = []
        for year in [2024, 2025]:
            for month in range(1, 13):
                if year == 2025 and month > 12:
                    break
                    
                target = LeasideRevenueTargets(
                    CorrespondingMonth=date(year, month, 1).strftime("%B"),
                    CorrespondingYear=year,
                    Leaside=random_currency(50000, 100000),
                    Hotel=random_currency(20000, 50000),
                    Apartments=random_currency(10000, 30000),
                    Spa_Service=random_currency(5000, 15000),
                    MediSpa=random_currency(3000, 10000),
                    Products=random_currency(2000, 8000),
                    Bistro_and_Extras=random_currency(1000, 5000),
                    Riverside_Therapeutics=random_currency(5000, 15000),
                    Monastery_Health=random_currency(3000, 10000),
                    VillaNova_Physiotherapy=random_currency(2000, 8000),
                    Total=random_currency(100000, 200000)
                )
                db.add(target)
                targets.append(target)
        db.commit()
        
        # 2. Leaside Revenue (daily data for 2024-2025)
        print(" Generating Leaside Revenue...")
        current_date = start_date
        batch = []
        while current_date <= end_date:
            target = next((t for t in targets 
                         if t.CorrespondingYear == current_date.year 
                         and t.CorrespondingMonth == current_date.strftime("%B")), None)
            
            if target:
                revenue = LeasideRevenue(
                    CorrespondingDate=current_date,
                    Leaside=random_currency(1000, 5000),
                    Hotel=random_currency(500, 2000),
                    Apartments=random_currency(300, 1500),
                    Spa_Service=random_currency(100, 800),
                    MediSpa=random_currency(50, 500),
                    Products=random_currency(20, 300),
                    Bistro_and_Extras=random_currency(10, 200),
                    Riverside_Therapeutics=random_currency(100, 600),
                    Monastery_Health=random_currency(50, 400),
                    VillaNova_Physiotherapy=random_currency(30, 300),
                    Total=random_currency(2000, 10000),
                    target_id=target.id
                )
                batch.append(revenue)
                
                if len(batch) >= 100:
                    db.bulk_save_objects(batch)
                    db.commit()
                    batch = []
            
            current_date += timedelta(days=1)
        
        if batch:
            db.bulk_save_objects(batch)
            db.commit()

        # 3. Extras Report
        print(" Generating Extras Report...")
        batch = []
        for _ in range(1000):
            check_in = random_date(start_date, end_date)
            check_out = check_in + timedelta(days=random.randint(1, 14))
            
            extra = ExtrasReport(
                CorrespondingDate=random_date(start_date, end_date),
                check_in=check_in,
                check_out=check_out,
                reservation_number=f"RES-{fake.random_number(digits=6)}",
                guest_name=fake.name(),
                extra=fake.word().capitalize() + " " + fake.word(),
                category=random.choice(["Food", "Beverage", "Spa", "Activity", "Transport"]),
                total=random_currency(10, 500)
            )
            batch.append(extra)
            
            if len(batch) >= 100:
                db.bulk_save_objects(batch)
                db.commit()
                batch = []
        
        if batch:
            db.bulk_save_objects(batch)
            db.commit()

        # 4. Revenue Summaries (daily data for 2024-2025)
        print(" Generating Revenue Summaries...")
        current_date = start_date
        while current_date <= end_date:
            # Apartments
            apartments = ApartmentsRevenueSummary(
                CorrespondingDate=current_date,
                room=random_currency(1000, 5000),
                extras=random_currency(100, 1000),
                taxes=random_currency(50, 500),
                reservations=random.randint(5, 50),
                nights=random.randint(10, 100),
                occupancy=f"{random.randint(30, 100)}%",
                adr=random_currency(100, 300),
                lead_time=random.randint(1, 30),
                los=random.randint(1, 14),
                revpar=random_currency(80, 250)
            )
            db.add(apartments)
            
            # Leaside
            leaside = LeasideRevenueSummary(
                CorrespondingDate=current_date,
                room=random_currency(2000, 8000),
                extras=random_currency(200, 1500),
                taxes=random_currency(100, 800),
                reservations=random.randint(10, 80),
                nights=random.randint(20, 150),
                occupancy=f"{random.randint(40, 100)}%",
                adr=random_currency(150, 400),
                lead_time=random.randint(1, 30),
                los=random.randint(1, 14),
                revpar=random_currency(120, 350)
            )
            db.add(leaside)
            
            # Monastery Suites
            monastery = MonasterySuitesRevenueSummary(
                CorrespondingDate=current_date,
                room=random_currency(1500, 6000),
                extras=random_currency(150, 1200),
                taxes=random_currency(75, 600),
                reservations=random.randint(8, 60),
                nights=random.randint(15, 120),
                occupancy=f"{random.randint(35, 100)}%",
                adr=random_currency(120, 350),
                lead_time=random.randint(1, 30),
                los=random.randint(1, 14),
                revpar=random_currency(100, 300)
            )
            db.add(monastery)
            
            if current_date.day % 10 == 0:  # Commit every 10 days
                db.commit()
            
            current_date += timedelta(days=1)
        db.commit()

        # 5. Therapy/Sales Data
        print(" Generating Therapy and Sales Data...")
        batch_size = 100
        for model_class, count in [
            (VillaNovaPhysiotherapySales, 500),
            (RiversideTherapeuticsSales, 500),
            (MonasteryHealthSales, 500)
        ]:
            print(f"   Generating {model_class.__name__}...")
            batch = []
            for _ in range(count):
                # Create proper datetime objects
                random_date_val = random_date(start_date, end_date)
                random_time = datetime.strptime(fake.time(), '%H:%M:%S').time()
                
                record = model_class(
                    CorrespondingDate=random_date_val,
                    location=random.choice(["Downtown", "Uptown", "Westside", "Eastside"]),
                    purchase_date=datetime.combine(random_date_val, random_time),
                    invoice_date=datetime.combine(random_date_val + timedelta(days=random.randint(0, 7)), random_time),
                    patient_guid=f"PAT-{fake.random_number(digits=8)}",
                    patient=fake.name(),
                    item=random.choice(["Massage", "Therapy", "Consultation", "Treatment"]),
                    staff_member=fake.name(),
                    payer=random.choice(["Patient", "Insurance", "Company"]),
                    invoice_number=f"INV-{fake.random_number(digits=6)}",
                    income_category=random.choice(["Standard", "Premium", "Corporate"]),
                    details=fake.sentence(),
                    status=random.choice(["Paid", "Pending", "Partial"]),
                    subtotal=random_currency(50, 500),
                    total=random_currency(50, 550),
                    collected=random_currency(0, 550),
                    balance=random_currency(-50, 550)
                )
                if hasattr(model_class, 'hst'):
                    record.hst = random_currency(5, 65)
                batch.append(record)
                
                if len(batch) >= batch_size:
                    db.bulk_save_objects(batch)
                    db.commit()
                    batch = []
            
            if batch:
                db.bulk_save_objects(batch)
                db.commit()
        # 6. Product and Service Sales
        print("🛍️ Generating Product and Service Sales...")
        for model_class, count, extra_fields in [
            (ProductSales, 300, {
                'brand': random.choice(["Brand A", "Brand B", "Brand C"])
            }),
            (ServiceSales, 300, {
                'category': random.choice(["Spa", "Massage", "Therapy"])
            })
        ]:
            print(f"   Generating {model_class.__name__}...")
            batch = []
            for _ in range(count):
                base_data = {
                    'CorrespondingDate': random_date(start_date, end_date),
                    'quantity': random.randint(1, 10),
                    'amount': random_currency(10, 200),
                    'adjustment': random_currency(-20, 20),
                    'total_sales': random_currency(10, 2000),
                    'tax': random_currency(1, 200),
                    'refund': random_currency(0, 100)
                }
                # Add model-specific fields
                base_data.update(extra_fields)
                
                record = model_class(**base_data)
                batch.append(record)
                
                if len(batch) >= batch_size:
                    db.bulk_save_objects(batch)
                    db.commit()
                    batch = []
            
            if batch:
                db.bulk_save_objects(batch)
                db.commit()

        print(" Dummy data generation completed successfully!")
        
    except Exception as e:
        db.rollback()
        print(f" Error generating dummy data: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    generate_dummy_data()