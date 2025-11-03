import fastapi
from pydantic import BaseModel
from typing import Optional


router = fastapi.APIRouter()

@router.get('/user/live')
async def display_user():
    return {"user first and last name"}


@router.post('/user')
async def create_user():
    return {"user created"}