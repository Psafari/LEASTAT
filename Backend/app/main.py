# FastAPI app entry point and route registration
# main.py
import fastapi
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import users, export, upload, analyze  

from db.db_setup import engine
from db.models.mixins import Timestamp
from db.models import additional_table, file_upload, user

user.Base.metadata.create_all(bind=engine)
additional_table.Base.metadata.create_all(bind=engine)
file_upload.Base.metadata.create_all(bind=engine)

# FastAPI application instance
app = FastAPI(
    title="Leaside Data API",
    description="Data management and analysis for LeasideGroup",
    version="LG Version 1"
)

# CORS configuration for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # would replace with specific origins in production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router, prefix="/api/v1", tags=["users"])
app.include_router(export.router, prefix="/api/v1", tags=["export"])
app.include_router(upload.router, tags=["upload"])  # don't have to do a prefix here just so for upload to match frontend 
app.include_router(analyze.router, prefix="/api/v1", tags=["analyze"])

@app.get("/")
def read_root():
    return {
        "message": "Welcome to Leaside Analytics API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "leaside-analytics-api"}

#SDFOJOOJS
