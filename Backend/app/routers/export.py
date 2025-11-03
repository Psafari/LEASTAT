# Create CSV/XLSX response from processed data
import fastapi
from fastapi import Query, FastAPI
router = fastapi.APIRouter()

# for displaying the revenue data in tabular format for particular time durations
@router.get('/insights/viewtable')
async def view_table(
        select_month : str = Query(..., description="eg.'september r all months'"),
        select_year: int = Query(..., description="eg. '2021'")
):
    return {"table printed"}


#for displaying the recently viewd graphs so you don't go through the process of reselecting the form fields again
@router.get('/insights/viewRecent')
async def export_quickly():
    return {"content displayed "}