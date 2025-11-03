from fastapi import APIRouter, Query, HTTPException, Depends
from datetime import datetime, timedelta, date
from typing import Optional
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
import base64
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_  
from db.db_setup import get_db
from db.models.file_upload import (
     LeasideRevenueSummary,
    ApartmentsRevenueSummary, MonasterySuitesRevenueSummary,
    VillaNovaPhysiotherapySales, RiversideTherapeuticsSales,
    MonasteryHealthSales, ProductSales, ServiceSales
)
from db.models.additional_table import LeasideRevenue,LeasideRevenueTargets
from pydantic_schemas.schemas import AccomodationsTargetResponse,HealthTargetResponse,RestuarantsTargetResponse,TotalTargetResponse,TrendsBreakdownResponse,TrendsBreakdownRequest

router = APIRouter()

# Helper functions
def get_date_range(date_range: str):
    today = date.today()
    if date_range == "7":
        start_date = today - timedelta(days=7)
    elif date_range == "30":
        start_date = today - timedelta(days=30)
    elif date_range == "90":
        start_date = today - timedelta(days=90)
    elif date_range == "365":
        start_date = today - timedelta(days=365)
    else:
        start_date = today - timedelta(days=30)  # default
    
    return start_date, today

def generate_chart_image(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

# Revenue Analysis
@router.post('/analysis/trends', response_model=TrendsBreakdownResponse)
async def analyze_trends(
    filters: TrendsBreakdownRequest,
    db: Session = Depends(get_db)
):
    try:
        start_date, end_date = get_date_range(filters.Date_Range)
        
        if filters.Metric == "Revenue":
            return await analyze_revenue(filters, start_date, end_date, db)
        elif filters.Metric == "ADR":
            return await analyze_adr(filters, start_date, end_date, db)
        elif filters.Metric == "Occupancy":
            return await analyze_occupancy(filters, start_date, end_date, db)
        else:
            raise HTTPException(status_code=400, detail="Invalid metric selected")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def analyze_revenue(filters: TrendsBreakdownRequest, start_date: date, end_date: date, db: Session):
    # Determine grouping
    if filters.Breakdown_by == "Day":
        group_by = LeasideRevenue.CorrespondingDate
    elif filters.Breakdown_by == "Week":
        group_by = func.date_trunc('week', LeasideRevenue.CorrespondingDate)
    else:  # Month
        group_by = func.date_trunc('month', LeasideRevenue.CorrespondingDate)

    # Base query
    query = db.query(
        group_by.label("date"),
        func.sum(LeasideRevenue.Total).label("total")
    ).filter(
        LeasideRevenue.CorrespondingDate.between(start_date, end_date)
    )

    # Filter by property if not "all"
    if filters.Property != "all":
        property_map = {
            "Leaside Manor": LeasideRevenue.Leaside,
            "Apartments": LeasideRevenue.Apartments,
            "Monastery Suites": LeasideRevenue.Monastery_Health,
            "Spa Services": LeasideRevenue.Spa_Service,
            "Medispa Services": LeasideRevenue.MediSpa,
            "Bistro": LeasideRevenue.Bistro_and_Extras,
            "Riverside Therapeutics": LeasideRevenue.Riverside_Therapeutics,
            "Villanova Physio": LeasideRevenue.VillaNova_Physiotherapy
        }
        query = query.filter(property_map[filters.Property] > 0)

    # Apply grouping and order
    results = query.group_by(group_by).order_by(group_by).all()

    if not results:
        raise HTTPException(status_code=404, detail="No data found for selected filters")

    # Process results
    dates = [r.date() if hasattr(r[0], 'date') else r[0] for r in results]
    values = [float(r[1]) for r in results]

    # Generate chart
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(dates, values, marker='o', color='#22313f')
    ax.set_title(f"Revenue Trend ({filters.Breakdown_by})")
    ax.set_ylabel("Revenue ($)")
    ax.grid(True)

    return TrendsBreakdownResponse(
        visualisation=generate_chart_image(fig),
        first_value=f"Max Revenue: ${max(values):,.2f}",
        second_value=f"Min Revenue: ${min(values):,.2f}"
    )


async def analyze_adr(filters: TrendsBreakdownRequest, start_date: date, end_date: date, db: Session):
    # Determine which table to query based on property
    table_map = {
        "Leaside Manor": LeasideRevenueSummary,
        "Apartments": ApartmentsRevenueSummary,
        "Monastery Suites": MonasterySuitesRevenueSummary
    }
    
    if filters.Property not in table_map:
        raise HTTPException(status_code=400, detail="ADR analysis only available for specific properties")
    
    model = table_map[filters.Property]
    
    # Query ADR data
    query = db.query(
        model.CorrespondingDate,
        model.adr
    ).filter(
        model.CorrespondingDate.between(start_date, end_date)
    )
    
    # Group by breakdown
    if filters.Breakdown_by == "Day":
        group_by = model.CorrespondingDate
    elif filters.Breakdown_by == "Week":
        group_by = func.date_trunc('week', model.CorrespondingDate)
    else:  # Month
        group_by = func.date_trunc('month', model.CorrespondingDate)
    
    results = query.group_by(group_by).order_by(group_by).all()
    
    if not results:
        raise HTTPException(status_code=404, detail="No data found for selected filters")
    
    # Process results
    dates = [r[0] for r in results]
    values = [float(r[1]) for r in results]
    
    # Generate chart
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(dates, values, marker='o', color='#22313f')
    ax.set_title(f"ADR Trend ({filters.Breakdown_by})")
    ax.set_ylabel("ADR ($)")
    ax.grid(True)
    
    # Calculate metrics
    max_adr = max(values)
    min_adr = min(values)
    
    return TrendsBreakdownResponse(
        visualisation=generate_chart_image(fig),
        first_value=f"Max ADR: ${max_adr:,.2f}",
        second_value=f"Min ADR: ${min_adr:,.2f}"
    )

async def analyze_occupancy(filters: TrendsBreakdownRequest, start_date: date, end_date: date, db: Session):
    # Determine which table to query based on property
    table_map = {
        "Leaside Manor": LeasideRevenueSummary,
        "Apartments": ApartmentsRevenueSummary,
        "Monastery Suites": MonasterySuitesRevenueSummary
    }
    
    if filters.Property not in table_map:
        raise HTTPException(status_code=400, detail="Occupancy analysis only available for specific properties")
    
    model = table_map[filters.Property]
    
    # Query occupancy data (remove % sign and convert to float)
    query = db.query(
        model.CorrespondingDate,
        func.replace(model.occupancy, '%', '').cast(db.Float)
    ).filter(
        model.CorrespondingDate.between(start_date, end_date)
    )
    
    # Group by breakdown
    if filters.Breakdown_by == "Day":
        group_by = model.CorrespondingDate
    elif filters.Breakdown_by == "Week":
        group_by = func.date_trunc('week', model.CorrespondingDate)
    else:  # Month
        group_by = func.date_trunc('month', model.CorrespondingDate)
    
    results = query.group_by(group_by).order_by(group_by).all()
    
    if not results:
        raise HTTPException(status_code=404, detail="No data found for selected filters")
    
    # Process results
    dates = [r[0] for r in results]
    values = [float(r[1]) for r in results]
    
    # Generate chart
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(dates, values, marker='o', color='#22313f')
    ax.set_title(f"Occupancy Trend ({filters.Breakdown_by})")
    ax.set_ylabel("Occupancy (%)")
    ax.grid(True)
    
    # Calculate metrics
    max_occ = max(values)
    min_occ = min(values)
    
    return TrendsBreakdownResponse(
        visualisation=generate_chart_image(fig),
        first_value=f"Max Occupancy: {max_occ:.1f}%",
        second_value=f"Min Occupancy: {min_occ:.1f}%"
    )

# Sales Analysis
@router.get('/analysis/sales', response_model=TrendsBreakdownResponse)
async def analyze_sales(
    date_range: str = Query(..., description="eg. 'last 30 days'"),
    sales_by: str = Query(..., description="eg. products"),
    db: Session = Depends(get_db)
):
    try:
        start_date, end_date = get_date_range(date_range)
        
        if sales_by == "products":
            return await analyze_product_sales(start_date, end_date, db)
        elif sales_by == "spa":
            return await analyze_service_sales(start_date, end_date, db)
        elif sales_by == "mh":
            return await analyze_monastery_health_sales(start_date, end_date, db)
        elif sales_by == "vp":
            return await analyze_villanova_sales(start_date, end_date, db)
        elif sales_by == "rt":
            return await analyze_riverside_sales(start_date, end_date, db)
        else:
            raise HTTPException(status_code=400, detail="Invalid sales category")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def analyze_product_sales(start_date: date, end_date: date, db: Session):
    # Query product sales data
    results = db.query(
        ProductSales.brand,
        func.sum(ProductSales.total_sales).label('total')
    ).filter(
        ProductSales.CorrespondingDate.between(start_date, end_date)
    ).group_by(
        ProductSales.brand
    ).order_by(
        func.sum(ProductSales.total_sales).desc()
    ).all()
    
    if not results:
        raise HTTPException(status_code=404, detail="No product sales data found")
    
    brands = [r[0] for r in results]
    sales = [float(r[1]) for r in results]
    total_sales = sum(sales)
    top_brand = brands[0]
    
    # Generate chart
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(brands, sales, color='#22313f')
    ax.set_title("Product Sales by Brand")
    ax.set_ylabel("Sales ($)")
    plt.xticks(rotation=45)
    ax.grid(True)
    
    return TrendsBreakdownResponse(
        visualisation=generate_chart_image(fig),
        first_value=f"Total Sales: ${total_sales:,.2f}",
        second_value=f"Top Brand: {top_brand}"
    )

async def analyze_service_sales(start_date: date, end_date: date, db: Session):
    # Query service sales data
    results = db.query(
        ServiceSales.category,
        func.sum(ServiceSales.total_sales).label('total')
    ).filter(
        ServiceSales.CorrespondingDate.between(start_date, end_date)
    ).group_by(
        ServiceSales.category
    ).order_by(
        func.sum(ServiceSales.total_sales).desc()
    ).all()
    
    if not results:
        raise HTTPException(status_code=404, detail="No service sales data found")
    
    categories = [r[0] for r in results]
    sales = [float(r[1]) for r in results]
    total_sales = sum(sales)
    top_category = categories[0]
    
    # Generate chart
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(categories, sales, color='#22313f')
    ax.set_title("Service Sales by Category")
    ax.set_ylabel("Sales ($)")
    plt.xticks(rotation=45)
    ax.grid(True)
    
    return TrendsBreakdownResponse(
        visualisation=generate_chart_image(fig),
        first_value=f"Total Sales: ${total_sales:,.2f}",
        second_value=f"Top Category: {top_category}"
    )

async def analyze_villanova_sales(start_date: date, end_date: date, db: Session):
    # Query Villa Nova sales data
    results = db.query(
        VillaNovaPhysiotherapySales.item,
        func.sum(VillaNovaPhysiotherapySales.subtotal).label('total')
    ).filter(
        VillaNovaPhysiotherapySales.CorrespondingDate.between(start_date, end_date)
    ).group_by(
        VillaNovaPhysiotherapySales.item
    ).order_by(
        func.sum(VillaNovaPhysiotherapySales.subtotal).desc()
    ).all()
    
    if not results:
        raise HTTPException(status_code=404, detail="No Villa Nova sales data found")
    
    items = [r[0] for r in results]
    sales = [float(r[1]) for r in results]
    total_sales = sum(sales)
    top_item = items[0]
    
    # Generate chart
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(items, sales, color='#22313f')
    ax.set_title("Villa Nova Sales by Item")
    ax.set_ylabel("Sales ($)")
    plt.xticks(rotation=45)
    ax.grid(True)
    
    return TrendsBreakdownResponse(
        visualisation=generate_chart_image(fig),
        first_value=f"Total Sales: ${total_sales:,.2f}",
        second_value=f"Top Item: {top_item}"
    )

async def analyze_riverside_sales(start_date: date, end_date: date, db: Session):
    # Query Riverside sales data
    results = db.query(
        RiversideTherapeuticsSales.item,
        func.sum(RiversideTherapeuticsSales.subtotal).label('total')
    ).filter(
        RiversideTherapeuticsSales.CorrespondingDate.between(start_date, end_date)
    ).group_by(
        RiversideTherapeuticsSales.item
    ).order_by(
        func.sum(RiversideTherapeuticsSales.subtotal).desc()
    ).all()
    
    if not results:
        raise HTTPException(status_code=404, detail="No Riverside sales data found")
    
    items = [r[0] for r in results]
    sales = [float(r[1]) for r in results]
    total_sales = sum(sales)
    top_item = items[0]
    
    # Generate chart
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(items, sales, color='#22313f')
    ax.set_title("Riverside Sales by Item")
    ax.set_ylabel("Sales ($)")
    plt.xticks(rotation=45)
    ax.grid(True)
    
    return TrendsBreakdownResponse(
        visualisation=generate_chart_image(fig),
        first_value=f"Total Sales: ${total_sales:,.2f}",
        second_value=f"Top Item: {top_item}"
    )

async def analyze_monastery_health_sales(start_date: date, end_date: date, db: Session):
    # Query Monastery Health sales data
    results = db.query(
        MonasteryHealthSales.item,
        func.sum(MonasteryHealthSales.subtotal).label('total')
    ).filter(
        MonasteryHealthSales.CorrespondingDate.between(start_date, end_date)
    ).group_by(
        MonasteryHealthSales.item
    ).order_by(
        func.sum(MonasteryHealthSales.subtotal).desc()
    ).all()
    
    if not results:
        raise HTTPException(status_code=404, detail="No Monastery Health sales data found")
    
    items = [r[0] for r in results]
    sales = [float(r[1]) for r in results]
    total_sales = sum(sales)
    top_item = items[0]
    
    # Generate chart
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(items, sales, color='#22313f')
    ax.set_title("Monastery Health Sales by Item")
    ax.set_ylabel("Sales ($)")
    plt.xticks(rotation=45)
    ax.grid(True)
    
    return TrendsBreakdownResponse(
        visualisation=generate_chart_image(fig),
        first_value=f"Total Sales: ${total_sales:,.2f}",
        second_value=f"Top Item: {top_item}"
    )

# Revenue Target Cards
@router.get('/analysis/accomodations', response_model=AccomodationsTargetResponse)
async def display_accommodations(
    select_month: str = Query(..., description="e.g 'December'"),
    select_year: int = Query(..., description="e.g '2021'"),
    db: Session = Depends(get_db)
):
    return await get_revenue_target("accommodations", select_month, select_year, db)

@router.get('/analysis/health', response_model=HealthTargetResponse)
async def display_health(
    select_month: str = Query(..., description="eg 'December'"),
    select_year: int = Query(..., description="eg '2010'"),
    db: Session = Depends(get_db)
):
    return await get_revenue_target("health", select_month, select_year, db)

@router.get('/analysis/restaurants', response_model=RestuarantsTargetResponse)
async def display_restaurants(
    select_month: str = Query(..., description="e.g 'December'"),
    select_year: int = Query(..., description="e.g '2021'"),
    db: Session = Depends(get_db)
):
    return await get_revenue_target("restaurants", select_month, select_year, db)

@router.get('/analysis/total_revenue', response_model=TotalTargetResponse)
async def display_total_revenue(
    select_month: str = Query(..., description="e.g 'December'"),
    select_year: int = Query(..., description="e.g '2021'"),
    db: Session = Depends(get_db)
):
    return await get_revenue_target("total", select_month, select_year, db)

async def get_revenue_target(card_type: str, month: str, year: int, db: Session):
    try:
        # Get target data
        target_query = db.query(LeasideRevenueTargets).filter(
            LeasideRevenueTargets.CorrespondingMonth == month,
            LeasideRevenueTargets.CorrespondingYear == year
        ).first()
        
        if not target_query:
            raise HTTPException(status_code=404, detail="Target data not found for selected period")
        
        # Get current revenue data
        start_date = datetime.strptime(f"{month} {year}", "%B %Y").date()
        end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        revenue_query = db.query(
            func.sum(LeasideRevenue.Total).label('total')
        ).filter(
            LeasideRevenue.CorrespondingDate.between(start_date, end_date)
        ).first()
        
        current_revenue = float(revenue_query[0]) if revenue_query[0] else 0.0
        
        # Map card types to target fields
        target_map = {
            "accommodations": (target_query.Hotel + target_query.Apartments, "Hotel + Apartments"),
            "health": (target_query.VillaNova_Physiotherapy + target_query.Riverside_Therapeutics + target_query.Monastery_Health, "Health Services"),
            "restaurants": (target_query.Bistro_and_Extras, "Bistro & Extras"),
            "total": (target_query.Total, "Total Revenue")
        }
        
        target_value, target_name = target_map.get(card_type, (0.0, "Unknown"))
        
        if card_type == "total":
            # For total, we already have the complete sum
            pass
        elif card_type == "accommodations":
            # For accommodations, sum Leaside and Apartments revenue
            revenue_query = db.query(
                func.sum(LeasideRevenue.Leaside + LeasideRevenue.Apartments).label('total')
            ).filter(
                LeasideRevenue.CorrespondingDate.between(start_date, end_date)
            ).first()
            current_revenue = float(revenue_query[0]) if revenue_query[0] else 0.0
        elif card_type == "health":
            # For health, sum the three health services
            revenue_query = db.query(
                func.sum(LeasideRevenue.VillaNova_Physiotherapy + 
                        LeasideRevenue.Riverside_Therapeutics + 
                        LeasideRevenue.Monastery_Health).label('total')
            ).filter(
                LeasideRevenue.CorrespondingDate.between(start_date, end_date)
            ).first()
            current_revenue = float(revenue_query[0]) if revenue_query[0] else 0.0
        elif card_type == "restaurants":
            # For restaurants, use Bistro_and_Extras
            revenue_query = db.query(
                func.sum(LeasideRevenue.Bistro_and_Extras).label('total')
            ).filter(
                LeasideRevenue.CorrespondingDate.between(start_date, end_date)
            ).first()
            current_revenue = float(revenue_query[0]) if revenue_query[0] else 0.0
        
        # Create response based on card type
        if card_type == "accommodations":
            return AccomodationsTargetResponse(Current=current_revenue, Target=float(target_value))
        elif card_type == "health":
            return HealthTargetResponse(Current=current_revenue, Target=float(target_value))
        elif card_type == "restaurants":
            return RestuarantsTargetResponse(Current=current_revenue, Target=float(target_value))
        else:  # total
            return TotalTargetResponse(Current=current_revenue, Target=float(target_value))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))