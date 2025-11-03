# Pydantic models for API requests/responses validation even before reaching db. if invalid data bypasses, db constraints come into play to ensure data integrity
# schemas.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import date, datetime

#signup endpoint schema
class ProfileCreate(BaseModel): 
    firstname: str = Field(...,alias="First Name")
    lastname: str = Field(...,alias="Last Name")
    email: EmailStr = Field(...,alias="Email Address")
    department: str = Field(...,alias="Department")
    password: str = Field(...,alias="Password")
    Confirm_password : str = Field(...,alias="Confirm Password")


#signin request schema
class UserRequest(BaseModel):
    email:EmailStr = Field(...,alias="Email Address")
    department: str = Field(...,alias="Department")
    Password:str = Field(...,alias="Password")
    

#signin response endpoint schema
class UserResponse(BaseModel): #define this return responses in the sign in endpoint as well.
    id: int
    firstname: str


#file upload request endpoint schema
class FileUploadRequest(BaseModel):
    Data_Date: str = Field(...,alias="Data Date",description="Date for the data records")
    Revenue_Type: Optional[str] = Field(None,alias="Revenue Type",description="Required for revenue files: 'Leaside', 'Apartments', 'Monastery Suites'")


#file upload response endpoint - Updated to match the actual upload.py response
class FileUploadResponse(BaseModel):
    message: str
    filename: str
    fileDate: date
    rows_processed: Optional[int] = Field(None, description="Number of rows processed")
    target_table: Optional[str] = Field(None, description="Database table used")

    class Config:
        # Allow serialization of date objects
        json_encoders = {
            date: lambda v: v.isoformat() if v else None
        }

#accomodations request schema
class AccomodationsTargetRequest(BaseModel):
    Select_month: str = Field(...,alias="Select Month")
    Select_year:str = Field(...,alias="Select Year")

#accomodations response schema
class AccomodationsTargetResponse(BaseModel):
    Current: float #would be gotten from the table of either revenues or the other tables
    Target: float #would be gotten from the target table for that data


#Health request schema
class HealthTargetRequest(BaseModel):
    Select_month: str = Field(...,alias="Select Month")
    Select_year:str = Field(...,alias="Select Year")

#Health response schema
class HealthTargetResponse(BaseModel):
    Current: float #would be gotten from the table of either revenues or the other tables
    Target: float #would be gotten from the target table for that data


#Restuarants request schema
class RestuarantsTargetRequest(BaseModel):
    Select_month: str = Field(...,alias="Select Month")
    Select_year:str = Field(...,alias="Select Year")

#Restuarants response schema
class RestuarantsTargetResponse(BaseModel):
    Current: float #would be gotten from the table of either revenues or the other tables
    Target: float #would be gotten from the target table for that data


#Total request schema
class TotalTargetRequest(BaseModel):
    Select_month: str = Field(...,alias="Select Month")
    Select_year:str = Field(...,alias="Select Year")

#Total response schema
class TotalTargetResponse(BaseModel):
    Current: float #would be gotten from the table of either revenues or the other tables
    Target: float #would be gotten from the target table for that data


#Trends break down request schema
class TrendsBreakdownRequest(BaseModel):
    Date_Range : str = Field(..., alias="Date Range")
    Metric: str 
    Property: str
    Breakdown_by : str = Field(..., alias="Breakdown By")


class TrendsBreakdownResponse(BaseModel):
    visualisation:str #a base64-encoded image or image url graph visualisation after the analyses based on the filter values
    first_value:str #a value returned along with the visualisation
    second_value:str #another value returned with the visualisation after the analysis

    class Config:
        from_attributes = True

# Additional schemas for better error handling
class ErrorResponse(BaseModel):
    detail: str
    error_type: Optional[str] = None
    timestamp: Optional[datetime] = None

class ValidationErrorResponse(BaseModel):
    detail: str
    errors: List[dict] = []

# be adding more schemas for  other models as needed along the line..probably..