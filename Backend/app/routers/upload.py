from typing import Optional, List
import fastapi
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from datetime import date, datetime
import pandas as pd
from io import BytesIO, StringIO
from sqlalchemy.orm import Session
from sqlalchemy import inspect, func, and_
import logging
import traceback
import re
from dateutil.parser import parse
import pdfplumber  # Enhanced PDF support

from pydantic_schemas.schemas import FileUploadResponse
from db.db_setup import get_db, SessionLocal

from db.models.file_upload import (
    ExtrasReport, ApartmentsRevenueSummary, LeasideRevenueSummary,
    MonasterySuitesRevenueSummary, VillaNovaPhysiotherapySales,
    RiversideTherapeuticsSales, MonasteryHealthSales,
    ProductSales, ServiceSales
)
from db.models.additional_table import LeasideRevenue

import plotly.express as px
import plotly.io as pio
pio.templates.default = "plotly_white"

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = fastapi.APIRouter()

# Table mapping
TABLE_MODELS = {
    "ExtrasReport": ExtrasReport,
    "ApartmentsRevenueSummary": ApartmentsRevenueSummary,
    "LeasideRevenueSummary": LeasideRevenueSummary,
    "MonasterySuitesRevenueSummary": MonasterySuitesRevenueSummary,
    "VillaNovaPhysiotherapySales": VillaNovaPhysiotherapySales,
    "RiversideTherapeuticsSales": RiversideTherapeuticsSales,
    "MonasteryHealthSales": MonasteryHealthSales,
    "ProductSales": ProductSales,
    "ServiceSales": ServiceSales
}

# Constants
SUPPORTED_FILE_EXTENSIONS = ('.csv', '.xlsx', '.xls', '.pdf')
CSV_ENCODINGS = ['utf-8', 'utf-8-sig', 'latin-1', 'iso-8859-1', 'cp1252']
NA_VALUES = ['', 'N/A', 'NULL', 'null', 'NA', 'N/A', 'n/a']

def apply_date_trunc_to_query(query, model, date_column='CorrespondingDate'):
    """
    Modify query to group by truncated date.
    """
    truncated_date = func.date_trunc('day', getattr(model, date_column)).label(date_column)
    return query.add_columns(truncated_date).group_by(truncated_date)

def generate_interactive_trend_plot(df: pd.DataFrame, x: str, y: str, title: str = "Trends Over Time") -> str:
    """
    Generate an interactive Plotly chart with a ggplot-style palette and return HTML
    """
    fig = px.line(
        df,
        x=x,
        y=y,
        title=title,
        markers=True,
        template="ggplot2",
        color_discrete_sequence=px.colors.qualitative.Set2,
        hover_name=x,
        labels={x: "Date", y: "Total"}
    )
    fig.update_traces(mode="lines+markers")
    fig.update_layout(
        hovermode="x unified",
        margin=dict(t=50, b=40, l=40, r=40),
        xaxis_title=x,
        yaxis_title=y,
        font=dict(size=14)
    )
    return fig.to_html(full_html=False, include_plotlyjs='cdn')

def extract_tables_from_pdf(pdf_bytes: bytes, filename: str = "") -> List[pd.DataFrame]:
    """
    Enhanced table extraction from PDF content using pdfplumber
    Handles various PDF layouts and table structures
    """
    try:
        tables = []
        filename_lower = filename.lower()
        
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            logger.info(f"Processing PDF with {len(pdf.pages)} pages")
            
            for page_num, page in enumerate(pdf.pages):
                logger.info(f"Processing page {page_num + 1}")
                
                # Method 1: Try to extract tables directly
                page_tables = page.extract_tables()
                if page_tables:
                    for table_idx, table in enumerate(page_tables):
                        if table and len(table) > 0:
                            # Filter out empty rows
                            filtered_table = [row for row in table if any(cell and str(cell).strip() for cell in row)]
                            
                            if len(filtered_table) > 1:  # Need at least header + 1 data row
                                # Clean and create DataFrame
                                df = pd.DataFrame(filtered_table[1:], columns=filtered_table[0])
                                # Remove completely empty columns
                                df = df.dropna(axis=1, how='all')
                                # Remove completely empty rows
                                df = df.dropna(axis=0, how='all')
                                
                                if not df.empty:
                                    logger.info(f"Extracted table {table_idx + 1} from page {page_num + 1}: {df.shape}")
                                    tables.append(df)
                
                # Method 2: If no tables found, try text-based extraction for structured data
                if not page_tables:
                    text = page.extract_text()
                    if text:
                        # Try to identify structured data patterns
                        lines = [line.strip() for line in text.split('\n') if line.strip()]
                        
                        # Look for tabular patterns (lines with multiple columns separated by spaces/tabs)
                        potential_table_lines = []
                        for line in lines:
                            # Check if line has multiple segments (potential columns)
                            segments = re.split(r'\s{2,}|\t+', line)  # Split on multiple spaces or tabs
                            if len(segments) > 2:  # At least 3 columns
                                potential_table_lines.append(segments)
                        
                        if len(potential_table_lines) > 1:
                            # Try to create a DataFrame from text extraction
                            try:
                                max_cols = max(len(line) for line in potential_table_lines)
                                # Pad lines to have same number of columns
                                padded_lines = []
                                for line in potential_table_lines:
                                    padded_line = line + [''] * (max_cols - len(line))
                                    padded_lines.append(padded_line)
                                
                                if len(padded_lines) > 1:
                                    df = pd.DataFrame(padded_lines[1:], columns=padded_lines[0])
                                    df = df.dropna(axis=1, how='all').dropna(axis=0, how='all')
                                    
                                    if not df.empty:
                                        logger.info(f"Extracted text-based table from page {page_num + 1}: {df.shape}")
                                        tables.append(df)
                            except Exception as e:
                                logger.warning(f"Failed to create DataFrame from text extraction: {e}")
        
        if not tables:
            logger.warning("No tables found in PDF")
            
            # Last resort: extract all text and try to find key-value pairs or structured data
            all_text = ""
            with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        all_text += page_text + "\n"
            
            if all_text.strip():
                # Try to identify if this is a report that can be parsed differently
                lines = [line.strip() for line in all_text.split('\n') if line.strip()]
                
                # Look for specific patterns based on file type
                if any(keyword in filename_lower for keyword in ['extras', 'revenue', 'sales']):
                    # Create a simple DataFrame with the text content for further processing
                    # This allows the existing logic to attempt to parse it
                    df = pd.DataFrame({'content': lines})
                    tables.append(df)
                    logger.info("Created text-based DataFrame for further processing")
        
        logger.info(f"Total tables extracted from PDF: {len(tables)}")
        return tables
        
    except Exception as e:
        logger.error(f"Error extracting tables from PDF: {e}")
        raise HTTPException(status_code=400, detail=f"Error reading PDF: {str(e)}")

def select_best_table_from_pdf(tables: List[pd.DataFrame], filename: str) -> pd.DataFrame:
    """
    Select the most appropriate table from extracted PDF tables
    based on filename and content analysis
    """
    if not tables:
        raise HTTPException(status_code=400, detail="No tables found in PDF")
    
    if len(tables) == 1:
        return tables[0]
    
    filename_lower = filename.lower()
    
    # Score tables based on relevance to file type
    scored_tables = []
    
    for idx, df in enumerate(tables):
        score = 0
        df_content = df.to_string().lower()
        
        # Scoring based on file type keywords
        if "extras" in filename_lower:
            keywords = ['check in', 'check out', 'reservation', 'guest', 'extra', 'category', 'total']
        elif "revenue" in filename_lower:
            keywords = ['room', 'extras', 'taxes', 'reservations', 'nights', 'occupancy', 'adr', 'revpar']
        elif "sales" in filename_lower:
            keywords = ['location', 'date', 'patient', 'item', 'staff', 'invoice', 'total', 'collected']
        elif "product" in filename_lower:
            keywords = ['brand', 'quantity', 'amount', 'sales', 'tax', 'refund']
        elif "service" in filename_lower:
            keywords = ['category', 'quantity', 'amount', 'sales', 'tax', 'refund']
        else:
            keywords = ['date', 'total', 'amount']  # Generic keywords
        
        # Count matching keywords
        for keyword in keywords:
            if keyword in df_content:
                score += 1
        
        # Prefer tables with more columns (likely to be data tables)
        score += len(df.columns) * 0.1
        
        # Prefer tables with more rows (more data)
        score += len(df) * 0.01
        
        # Penalize tables that are mostly empty
        non_empty_cells = df.count().sum()
        total_cells = len(df) * len(df.columns)
        if total_cells > 0:
            fill_ratio = non_empty_cells / total_cells
            score += fill_ratio * 5
        
        scored_tables.append((score, idx, df))
    
    # Sort by score descending
    scored_tables.sort(key=lambda x: x[0], reverse=True)
    
    best_score, best_idx, best_table = scored_tables[0]
    logger.info(f"Selected table {best_idx} with score {best_score:.2f} from {len(tables)} tables")
    
    return best_table

def clean_product_sales_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean ProductSales data according to specified requirements"""
    logger.info("Cleaning ProductSales data")
    
    # If we're dealing with the multi-header format (like in the sample file)
    if len(df.columns) > 20:  # The sample has 54 columns
        try:
            # Convert to CSV string and split lines
            content_str = df.to_csv(index=False)
            lines = content_str.split('\n')
            
            # Find the header line
            header_line = None
            for line in lines:
                if 'ProductBrandName' in line:
                    header_line = line
                    break
            
            if header_line:
                # Get the column names
                headers = header_line.strip().split(',')
                
                # Find where the actual data starts
                data_lines = []
                for line in lines[lines.index(header_line)+1:]:
                    if line.strip():  # Skip empty lines
                        data_lines.append(line)
                
                # Create a new DataFrame with proper headers
                df_clean = pd.read_csv(StringIO('\n'.join(data_lines)), names=headers)
                
                # Select only the columns we need
                required_columns = {
                    'ProductBrandName': 'Brand',
                    'ProductBrandQuantity': 'Quantity',
                    'ProductBrandAmount': 'Amount',
                    'ProductBrandAdjustment': 'Adjustment',
                    'ProductBrandTotalSales': 'Total Sales',
                    'ProductBrandTax': 'Tax',
                    'ProductBrandRefund': 'Refund'
                }
                
                df_clean = df_clean.rename(columns=required_columns)
                df_clean = df_clean[list(required_columns.values())]
                
                # Clean numeric columns
                numeric_cols = ['Quantity', 'Amount', 'Adjustment', 'Total Sales', 'Tax', 'Refund']
                for col in numeric_cols:
                    if col in df_clean.columns:
                        # Remove dollar signs and convert to numeric
                        df_clean[col] = df_clean[col].astype(str).str.replace(r'[\$,]', '', regex=True)
                        df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0)
                
                return df_clean
        except Exception as e:
            logger.error(f"Error processing multi-header ProductSales file: {e}")
            raise HTTPException(status_code=400, detail="Error processing ProductSales file format")
    
    # Original cleaning logic for simpler files
    expected_headers = ["Brand", "Quantity", "Amount", "Adjustment", "Total Sales", "Tax", "Refund"]
    
    # Find header row
    header_row_idx = None
    for idx, row in df.iterrows():
        row_str = ' '.join(str(cell) for cell in row.values if pd.notna(cell))
        if sum(header.lower() in row_str.lower() for header in expected_headers) >= 3:
            header_row_idx = idx
            break
    
    if header_row_idx is None:
        logger.warning("Could not find header row in ProductSales file")
        raise HTTPException(status_code=400, detail="Could not find header row in ProductSales file")
    
    # Map actual columns to expected headers
    actual_headers = []
    for col_idx, cell_value in enumerate(df.iloc[header_row_idx].values):
        if pd.isna(cell_value):
            continue
        for expected in expected_headers:
            if expected.lower() in str(cell_value).lower():
                actual_headers.append((col_idx, expected))
                break
    
    if not actual_headers:
        logger.warning("No expected columns found after header row")
        raise HTTPException(status_code=400, detail="No expected columns found after header row")
    
    # Create cleaned DataFrame
    clean_data = []
    for row_idx in range(header_row_idx + 1, len(df)):
        row_data = {}
        for col_idx, header in actual_headers:
            value = df.iloc[row_idx, col_idx]
            if pd.isna(value) and header == "Brand":
                break
            row_data[header] = value
        else:
            clean_data.append(row_data)
    
    df_clean = pd.DataFrame(clean_data)
    
    # Stop at 'Total' row if exists
    if 'Brand' in df_clean.columns:
        total_idx = df_clean[df_clean['Brand'].astype(str).str.contains('Total', case=False, na=False)].index
        if len(total_idx) > 0:
            df_clean = df_clean.iloc[:total_idx[0]]
    
    # Convert numeric columns
    numeric_cols = ['Quantity', 'Amount', 'Adjustment', 'Total Sales', 'Tax', 'Refund']
    for col in numeric_cols:
        if col in df_clean.columns:
            # Remove dollar signs if present
            if df_clean[col].dtype == 'object':
                df_clean[col] = df_clean[col].astype(str).str.replace(r'[\$,]', '', regex=True)
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0)
    
    logger.info(f"ProductSales data cleaned. Shape: {df_clean.shape}")
    return df_clean

def clean_service_sales_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean ServiceSales data according to specified requirements"""
    logger.info("Cleaning ServiceSales data")
    
    expected_headers = ["Category", "Quantity", "Amount", "Adjustment", "Total Sales", "Tax", "Refund"]
    
    # Find header row
    header_row_idx = None
    for idx, row in df.iterrows():
        row_str = str(row.values).lower()
        if any(header.lower() in row_str for header in expected_headers):
            header_row_idx = idx
            break
    
    if header_row_idx is None:
        logger.warning("Could not find expected headers in ServiceSales file")
        raise HTTPException(status_code=400, detail="Could not find expected headers in ServiceSales file")
    
    # Set columns from header row and skip to data
    df.columns = df.iloc[header_row_idx].values
    df_clean = df.iloc[header_row_idx + 1:].reset_index(drop=True)
    
    # Keep only expected columns
    columns_to_keep = [col for col in df_clean.columns if col in expected_headers]
    df_clean = df_clean[columns_to_keep]
    
    # Remove rows after "Total"
    if 'Category' in df_clean.columns:
        total_idx = df_clean[df_clean['Category'].astype(str).str.contains('Total', case=False, na=False)].index
        if len(total_idx) > 0:
            df_clean = df_clean.iloc[:total_idx[0]]
    
    # Remove columns after "Refund"
    if 'Refund' in df_clean.columns:
        refund_col_idx = df_clean.columns.get_loc('Refund')
        df_clean = df_clean.iloc[:, :refund_col_idx + 1]
    
    # Clean numeric columns
    numeric_cols = ['Quantity', 'Amount', 'Adjustment', 'Total Sales', 'Tax', 'Refund']
    for col in numeric_cols:
        if col in df_clean.columns:
            # Remove dollar signs if present
            if df_clean[col].dtype == 'object':
                df_clean[col] = df_clean[col].astype(str).str.replace(r'[\$,]', '', regex=True)
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0)
    
    logger.info(f"ServiceSales data cleaned. Shape: {df_clean.shape}")
    return df_clean

def parse_date(date_str: str) -> datetime:
    """Parse date string with multiple format support"""
    try:
        # Try parsing with dayfirst=True (for dd-mm-yyyy formats)
        return parse(date_str, dayfirst=True)
    except ValueError:
        try:
            # Try parsing with default settings (for mm/dd/yyyy formats)
            return parse(date_str)
        except ValueError as e:
            logger.error(f"Could not parse date: {date_str}")
            raise HTTPException(status_code=400, detail=f"Invalid date format: {date_str}")

def read_file_to_dataframe(contents: bytes, filename: str) -> pd.DataFrame:
    """Read uploaded file contents into pandas DataFrame"""
    try:
        logger.info(f"Reading file: {filename}, size: {len(contents)} bytes")
        
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        
        if filename.endswith('.pdf'):
            # Enhanced PDF handling
            tables = extract_tables_from_pdf(contents, filename)
            if not tables:
                raise HTTPException(status_code=400, detail="No tables found in PDF")
            
            # Select the best table based on filename and content
            df = select_best_table_from_pdf(tables, filename)
            
            # Apply special cleaning based on file type
            if "product" in filename.lower():
                return clean_product_sales_data(df)
            elif "service" in filename.lower():
                return clean_service_sales_data(df)
            
            logger.info(f"Successfully processed PDF file. Final DataFrame shape: {df.shape}")
            return df
            
        elif filename.endswith('.csv'):
            # First try reading with standard approach
            try:
                # Try to detect if this is the multi-header format
                content_str = contents.decode('utf-8-sig')
                first_line = content_str.split('\n')[0]
                
                if 'ProductBrandName' in first_line:
                    # This is the special Product Sales format
                    df = pd.read_csv(StringIO(content_str))
                    return clean_product_sales_data(df)
                
                # Standard CSV reading with date parsing for ExtrasReport
                if 'extras' in filename.lower():
                    df = pd.read_csv(
                        StringIO(content_str),
                        skipinitialspace=True,
                        na_values=NA_VALUES,
                        parse_dates=['Check In', 'Check Out'],
                        date_parser=parse_date
                    )
                else:
                    df = pd.read_csv(
                        StringIO(content_str),
                        skipinitialspace=True,
                        na_values=NA_VALUES
                    )
                
                logger.info("Successfully read CSV with standard approach")
                return df
            except Exception as e:
                logger.warning(f"Standard CSV read failed, trying alternative approaches: {e}")
                
                # Try different encodings
                for encoding in CSV_ENCODINGS:
                    try:
                        content_str = contents.decode(encoding)
                        if 'extras' in filename.lower():
                            df = pd.read_csv(
                                StringIO(content_str),
                                skipinitialspace=True,
                                na_values=NA_VALUES,
                                parse_dates=['Check In', 'Check Out'],
                                date_parser=parse_date
                            )
                        else:
                            df = pd.read_csv(
                                StringIO(content_str),
                                skipinitialspace=True,
                                na_values=NA_VALUES
                            )
                        logger.info(f"Successfully read CSV with {encoding} encoding")
                        return df
                    except Exception as e:
                        logger.warning(f"Failed to read CSV with {encoding}: {e}")
                        continue
                
                raise ValueError("Could not decode CSV file with any supported encoding")
                
        elif filename.endswith(('.xlsx', '.xls')):
            # For Excel files, we need to handle the Service Sales format
            df = pd.read_excel(BytesIO(contents), na_values=NA_VALUES)
            
            # Special handling for Service Sales
            if "service" in filename.lower():
                # Find the row with headers
                header_row = None
                for idx, row in df.iterrows():
                    if 'Category' in str(row.values):
                        header_row = idx
                        break
                
                if header_row is not None:
                    # Set headers and skip to data
                    df.columns = df.iloc[header_row]
                    df = df.iloc[header_row+1:]
                    
                    # Remove rows after "Total"
                    if 'Category' in df.columns:
                        total_idx = df[df['Category'].astype(str).str.contains('Total', case=False, na=False)].index
                        if len(total_idx) > 0:
                            df = df.iloc[:total_idx[0]]
            
            logger.info("Successfully read Excel file")
            return df
            
        else:
            raise ValueError("Unsupported file format")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading file {filename}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")

def determine_target_table(filename: str, df: pd.DataFrame, revenue_type: Optional[str]) -> str:
    """Determine which database table to use based on filename and content"""
    logger.info(f"Determining target table for file: {filename}")
    
    filename_lower = filename.lower()
    df_content = df.to_string().lower()
    
    if "extras_report" in filename_lower or "extras" in filename_lower:
        return "ExtrasReport"
    elif "sales" in filename_lower:
        if "villanova" in df_content or "villa nova" in df_content:
            return "VillaNovaPhysiotherapySales"
        elif "monastery health" in df_content:
            return "MonasteryHealthSales"
        elif "riverside therapeutics" in df_content:
            return "RiversideTherapeuticsSales"
        else:
            raise HTTPException(status_code=400, detail="Could not determine sales table from file content")
    elif "service" in filename_lower:
        return "ServiceSales"
    elif "product" in filename_lower:
        return "ProductSales"
    elif "revenue" in filename_lower:
        if not revenue_type:
            raise HTTPException(status_code=400, detail="Revenue file detected but no revenue_type specified")
        
        table_map = {
            "leaside": "LeasideRevenueSummary",
            "apartments": "ApartmentsRevenueSummary", 
            "monastery suites": "MonasterySuitesRevenueSummary"
        }
        target_table = table_map.get(revenue_type.lower())
        if not target_table:
            raise HTTPException(status_code=400, detail=f"Invalid revenue_type: {revenue_type}")
        return target_table
    else:
        raise HTTPException(status_code=400, detail="Could not determine target table from filename")

def get_model_columns(model_class) -> set:
    """Get all column names for a SQLAlchemy model"""
    try:
        inspector = inspect(model_class)
        return {column.name for column in inspector.columns}
    except Exception as e:
        logger.error(f"Error getting columns for model {model_class.__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"Error inspecting model: {str(e)}")

def prepare_dataframe_for_model(df: pd.DataFrame, model_class, corresponding_date: date) -> pd.DataFrame:
    """Prepare DataFrame to match database model schema"""
    logger.info(f"Preparing DataFrame for model {model_class.__name__}")
    
    model_columns = get_model_columns(model_class)
    df_processed = df.copy()
    
    # Handle empty DataFrame case
    if df_processed.empty:
        logger.warning("Empty DataFrame detected - creating default record with zeros")
        df_processed = pd.DataFrame([{}])  # Create single empty row
    
    # Add CorrespondingDate
    df_processed['CorrespondingDate'] = corresponding_date
    
    # Apply column mappings
    column_mappings = get_column_mappings(model_class.__name__)
    if column_mappings:
        df_processed = df_processed.rename(columns=column_mappings)
    
    # Handle date columns for ExtrasReport
    if model_class.__name__ == "ExtrasReport":
        for col in ['check_in', 'check_out']:
            if col in df_processed.columns:
                df_processed[col] = pd.to_datetime(
                    df_processed[col],
                    errors='coerce',
                    dayfirst=True
                )
                # Convert to date if datetime
                df_processed[col] = df_processed[col].dt.date
    
    # Define numeric and integer columns
    numeric_cols = ['total', 'amount', 'subtotal', 'hst', 'collected', 'balance', 
                   'room', 'extras', 'taxes', 'adr', 'revpar', 'total_sales', 
                   'tax', 'refund', 'adjustment']
    integer_cols = ['quantity', 'reservations', 'nights', 'lead_time', 'los']
    
    # Fill missing columns with appropriate zero values
    for col in model_columns:
        if col not in df_processed.columns and col not in ['id', 'created_at', 'updated_at']:
            if col in numeric_cols:
                df_processed[col] = 0.0
            elif col in integer_cols:
                df_processed[col] = 0
            else:
                df_processed[col] = None
    
    # Ensure numeric columns have zero instead of NaN/None
    for col in numeric_cols + integer_cols:
        if col in df_processed.columns:
            df_processed[col] = df_processed[col].fillna(0)
    
    # Keep only model columns
    df_processed = df_processed[[col for col in df_processed.columns if col in model_columns]]
    
    logger.info(f"Final processed DataFrame shape: {df_processed.shape}")
    return df_processed

def get_column_mappings(model_name: str) -> dict:
    """Define column mappings for different file formats to database columns"""
    mappings = {
        "ExtrasReport": {
            "Check In": "check_in",
            "Check Out": "check_out",
            "Reservation Number": "reservation_number",
            "Guest Name": "guest_name",
            "Extra": "extra",
            "Category": "category",
            "Total": "total"
        },
        "ApartmentsRevenueSummary": {
            "Room": "room",
            "Extras": "extras",
            "Taxes": "taxes",
            "Reservations": "reservations",
            "Nights": "nights",
            "Occupancy": "occupancy",
            "ADR": "adr",
            "Lead Time": "lead_time",
            "LOS": "los",
            "RevPAR": "revpar"
        },
        "LeasideRevenueSummary": {
            "Room": "room",
            "Extras": "extras",
            "Taxes": "taxes",
            "Reservations": "reservations",
            "Nights": "nights",
            "Occupancy": "occupancy",
            "ADR": "adr",
            "Lead Time": "lead_time",
            "LOS": "los",
            "RevPAR": "revpar"
        },
        "MonasterySuitesRevenueSummary": {
            "Room": "room",
            "Extras": "extras",
            "Taxes": "taxes",
            "Reservations": "reservations",
            "Nights": "nights",
            "Occupancy": "occupancy",
            "ADR": "adr",
            "Lead Time": "lead_time",
            "LOS": "los",
            "RevPAR": "revpar"
        },
        "VillaNovaPhysiotherapySales": {
            "Location": "location",
            "Purchase Date": "purchase_date",
            "Invoice Date": "invoice_date", 
            "Patient Guid": "patient_guid", 
            "Patient": "patient",
            "Item": "item", 
            "Staff Member": "staff_member", 
            "Payer": "payer", 
            "Invoice #": "invoice_number", 
            "Income Category": "income_category", 
            "Details": "details", 
            "Status": "status",
            "Subtotal": "subtotal",
            "HST": "hst", 
            "Total": "total",
            "Collected": "collected", 
            "Balance": "balance" 
        },
        "RiversideTherapeuticsSales": {
            "Location": "location",
            "Purchase Date": "purchase_date",
            "Invoice Date": "invoice_date", 
            "Patient Guid": "patient_guid", 
            "Patient": "patient",
            "Item": "item", 
            "Staff Member": "staff_member", 
            "Payer": "payer", 
            "Invoice #": "invoice_number", 
            "Income Category": "income_category", 
            "Details": "details", 
            "Status": "status",
            "Subtotal": "subtotal",
            "Total": "total",
            "Collected": "collected", 
            "Balance": "balance" 
        },
        "MonasteryHealthSales": {
            "Location": "location",
            "Purchase Date": "purchase_date",
            "Invoice Date": "invoice_date", 
            "Patient Guid": "patient_guid", 
            "Patient": "patient",
            "Item": "item", 
            "Staff Member": "staff_member", 
            "Payer": "payer", 
            "Invoice #": "invoice_number", 
            "Income Category": "income_category", 
            "Details": "details", 
            "Status": "status",
            "Subtotal": "subtotal",
            "Total": "total",
            "Collected": "collected", 
            "Balance": "balance" 
        },
        "ProductSales": {
            "Brand": "brand",
            "Quantity": "quantity",
            "Amount": "amount", 
            "Adjustment": "adjustment", 
            "Total Sales": "total_sales",
            "Tax": "tax", 
            "Refund": "refund" 
        },
        "ServiceSales": {
            "Category": "category",
            "Quantity": "quantity",
            "Amount": "amount", 
            "Adjustment": "adjustment", 
            "Total Sales": "total_sales",
            "Tax": "tax", 
            "Refund": "refund" 
        }
    }
    return mappings.get(model_name, {})

def insert_dataframe_to_db(df: pd.DataFrame, model_class, db: Session) -> int:
    """Insert DataFrame records into database"""
    logger.info(f"Inserting {len(df)} records into {model_class.__name__}")
    
    records = df.to_dict('records')
    db_objects = []
    
    for record in records:
        try:
            clean_record = {
                key: None if pd.isna(value) else value
                for key, value in record.items()
            }
            db_objects.append(model_class(**clean_record))
        except Exception as e:
            logger.error(f"Error creating record: {e}\nRecord data: {record}")
            raise HTTPException(status_code=400, detail=f"Error creating record: {str(e)}")
    
    try:
        db.add_all(db_objects)
        db.commit()
        logger.info(f"Successfully inserted {len(db_objects)} records")
        return len(db_objects)
    except Exception as e:
        logger.error(f"Database error during insertion: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

def update_leaside_revenue(table_name: str, corresponding_date: date, db: Session):
    """Update LeasideRevenue table based on uploaded data"""
    logger.info(f"Updating LeasideRevenue for {table_name} on {corresponding_date}")
    
    leaside_revenue = db.query(LeasideRevenue).filter(
        LeasideRevenue.CorrespondingDate == corresponding_date
    ).first()
    
    if not leaside_revenue:
        leaside_revenue = LeasideRevenue(CorrespondingDate=corresponding_date)
        db.add(leaside_revenue)
        db.flush()
    
    try:
        if table_name == "LeasideRevenueSummary":
            room_value = db.query(func.sum(LeasideRevenueSummary.room)).filter(
                LeasideRevenueSummary.CorrespondingDate == corresponding_date
            ).scalar() or 0
            leaside_revenue.Leaside = room_value
            
        elif table_name == "MonasterySuitesRevenueSummary":
            room_value = db.query(func.sum(MonasterySuitesRevenueSummary.room)).filter(
                MonasterySuitesRevenueSummary.CorrespondingDate == corresponding_date
            ).scalar() or 0
            leaside_revenue.Hotel = room_value
            
        elif table_name == "ApartmentsRevenueSummary":
            room_value = db.query(func.sum(ApartmentsRevenueSummary.room)).filter(
                ApartmentsRevenueSummary.CorrespondingDate == corresponding_date
            ).scalar() or 0
            leaside_revenue.Apartments = room_value
            
        elif table_name == "VillaNovaPhysiotherapySales":
            subtotal_sum = db.query(func.sum(VillaNovaPhysiotherapySales.subtotal)).filter(
                VillaNovaPhysiotherapySales.CorrespondingDate == corresponding_date
            ).scalar() or 0
            leaside_revenue.VillaNova_Physiotherapy = subtotal_sum
            
        elif table_name == "RiversideTherapeuticsSales":
            subtotal_sum = db.query(func.sum(RiversideTherapeuticsSales.subtotal)).filter(
                RiversideTherapeuticsSales.CorrespondingDate == corresponding_date
            ).scalar() or 0
            leaside_revenue.Riverside_Therapeutics = subtotal_sum
            
        elif table_name == "MonasteryHealthSales":
            subtotal_sum = db.query(func.sum(MonasteryHealthSales.subtotal)).filter(
                MonasteryHealthSales.CorrespondingDate == corresponding_date
            ).scalar() or 0
            leaside_revenue.Monastery_Health = subtotal_sum
            
        elif table_name == "ServiceSales":
            medispa_sum = db.query(func.sum(ServiceSales.total_sales)).filter(
                and_(
                    ServiceSales.CorrespondingDate == corresponding_date,
                    ServiceSales.category.in_(['Medical Spa Treatments', 'Laser Treatments'])
                )
            ).scalar() or 0
            leaside_revenue.MediSpa = medispa_sum
            
            spa_service_sum = db.query(func.sum(ServiceSales.total_sales)).filter(
                and_(
                    ServiceSales.CorrespondingDate == corresponding_date,
                    ~ServiceSales.category.in_(['Medical Spa Treatments', 'Laser Treatments'])
                )
            ).scalar() or 0
            leaside_revenue.Spa_Service = spa_service_sum
            
        elif table_name == "ProductSales":
            products_sum = db.query(func.sum(ProductSales.total_sales)).filter(
                and_(
                    ProductSales.CorrespondingDate == corresponding_date,
                    ProductSales.brand != '(No Brand)'
                )
            ).scalar() or 0
            leaside_revenue.Products = products_sum
            
            no_brand_sum = db.query(func.sum(ProductSales.total_sales)).filter(
                and_(
                    ProductSales.CorrespondingDate == corresponding_date,
                    ProductSales.brand == '(No Brand)'
                )
            ).scalar() or 0
            
            extras_sum = db.query(func.sum(ExtrasReport.total)).filter(
                ExtrasReport.CorrespondingDate == corresponding_date
            ).scalar() or 0
            
            leaside_revenue.Bistro_and_Extras = no_brand_sum + extras_sum
        
        db.commit()
        logger.info("Successfully updated LeasideRevenue")
        
    except Exception as e:
        logger.error(f"Error updating LeasideRevenue: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating LeasideRevenue: {str(e)}")

@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    select_date: date = Form(..., description="e.g. 2023-12-09", alias="Data Date"),
    revenue_type: Optional[str] = Form(None, alias="Revenue Type", description="Required for revenue files: 'Leaside', 'Apartments', 'Monastery Suites'"),
    db: Session = Depends(get_db)
):
    """
    Upload and process CSV/Excel/PDF files into appropriate database tables
    Enhanced PDF support with advanced table detection and extraction
    """
    logger.info(f"=== UPLOAD REQUEST RECEIVED ===")
    logger.info(f"File: {file.filename}")
    logger.info(f"Date: {select_date}")
    logger.info(f"Revenue Type: {revenue_type}")
    
    try:
        # Validate inputs
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        if not select_date:
            raise HTTPException(status_code=400, detail="Data date is required")
            
        if not any(file.filename.lower().endswith(ext) for ext in SUPPORTED_FILE_EXTENSIONS):
            raise HTTPException(status_code=400, detail="File must be CSV, XLSX, XLS, or PDF format")
        
        if 'revenue' in file.filename.lower() and not revenue_type:
            raise HTTPException(status_code=400, detail="Revenue type is required for revenue files")
        
        # Read file
        contents = await file.read()
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        
        # Process file with enhanced PDF support
        df = read_file_to_dataframe(contents, file.filename)
        if df.empty:
            raise HTTPException(status_code=400, detail="File contains no readable data")
        
        # Determine target table
        target_table_name = determine_target_table(file.filename, df, revenue_type)
        model_class = TABLE_MODELS.get(target_table_name)
        if not model_class:
            raise HTTPException(status_code=500, detail=f"Invalid target table: {target_table_name}")
        
        # Prepare and insert data
        df_processed = prepare_dataframe_for_model(df, model_class, select_date)
        rows_added = insert_dataframe_to_db(df_processed, model_class, db)
        
        # Update summary table
        update_leaside_revenue(target_table_name, select_date, db)
        
        result = FileUploadResponse(
            message=f"Successfully processed {rows_added} records into {target_table_name} and updated LeasideRevenue",
            filename=file.filename,
            fileDate=select_date,
            rows_processed=rows_added,
            target_table=target_table_name
        )
        
        logger.info(f"=== UPLOAD COMPLETED SUCCESSFULLY ===")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during upload: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")