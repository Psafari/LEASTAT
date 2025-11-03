import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Import all your models (adjust the import path as needed)
try:
    from models.file_upload import (
        ExtrasReport, ApartmentsRevenueSummary, LeasideRevenueSummary,
        MonasterySuitesRevenueSummary, VillaNovaPhysiotherapySales,
        RiversideTherapeuticsSales, MonasteryHealthSales, ProductSales, ServiceSales
    )
    from models.additional_table import LeasideRevenue, LeasideRevenueTargets
except ImportError as e:
    print(f" Error importing models: {e}")
    sys.exit(1)

def clear_database():
    # Database connection
    DATABASE_URL = "postgresql://postgres:Hello7898.pgsql@localhost:5432/leaside"
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        print(" Clearing existing data...")
        
        # List of models in proper deletion order (child tables first)
        models_to_clear = [
            LeasideRevenue,
            ExtrasReport,
            ApartmentsRevenueSummary,
            LeasideRevenueSummary,
            MonasterySuitesRevenueSummary,
            VillaNovaPhysiotherapySales,
            RiversideTherapeuticsSales,
            MonasteryHealthSales,
            ProductSales,
            ServiceSales,
            LeasideRevenueTargets
        ]

        # Verify connection
        db.execute("SELECT 1")
        print(" Database connection verified")

        # Clear all tables
        for model in models_to_clear:
            try:
                deleted_count = db.query(model).delete()
                print(f"   ▸ Cleared {deleted_count} records from {model.__tablename__}")
                db.commit()
            except SQLAlchemyError as e:
                db.rollback()
                print(f" Error clearing {model.__tablename__}: {e}")
                continue

        print(" Existing data cleared successfully!")
        
    except SQLAlchemyError as e:
        db.rollback()
        print(f" Database error occurred: {e}")
        sys.exit(1)
    except Exception as e:
        print(f" Unexpected error: {e}")
        sys.exit(1)
    finally:
        db.close()
        print(" Database connection closed")

if __name__ == "__main__":
    # Safety confirmation
    confirm = input(" WARNING: This will DELETE ALL DATA. Type 'YES' to confirm: ")
    if confirm.strip().upper() == "YES":
        clear_database()
    else:
        print(" Operation cancelled")