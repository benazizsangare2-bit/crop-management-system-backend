"""
CRUD endpoints for Planting management.
Tracks each crop cycle in a field.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.connection import get_db
from database.models import Planting, Field
from schemas.planting import PlantingCreate, PlantingUpdate, PlantingResponse
from utils.dependencies import get_current_user
from database.models import User
from typing import List
from datetime import datetime

plantingrouter = APIRouter(prefix="/api/plantings", tags=["Plantings"])

@plantingrouter.post("/", response_model=PlantingResponse, status_code=status.HTTP_201_CREATED)
async def create_planting(
    planting_data: PlantingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new planting (start a crop cycle in a field).
    First verifies that the field belongs to the current user.
    """
    # Verify field exists and belongs to user
    field_result = await db.execute(
        select(Field).where(Field.fieldid == planting_data.field_id, Field.userid == current_user.userid)
    )
    field = field_result.scalar_one_or_none()
    
    if not field:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Field with id {planting_data.field_id} not found or doesn't belong to you"
        )
    
    # Create new planting
    new_planting = Planting(
        field_id=planting_data.field_id,
        cropname=planting_data.cropname,
        cropvariety=planting_data.cropvariety,
        plantingdate=planting_data.plantingdate,
        seedquantitykg=planting_data.seedquantitykg,
        seedcost=planting_data.seedcost,
        plantsperhectare=planting_data.plantsperhectare,
        rowspacingcm=planting_data.rowspacingcm,
        status=planting_data.status,
        notes=planting_data.notes,
        createdat=datetime.now(),
    )
    
    db.add(new_planting)
    await db.commit()
    await db.refresh(new_planting)
    
    return new_planting

@plantingrouter.get("/", response_model=List[PlantingResponse])
async def get_all_plantings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    field_id: int = None,  # Optional filter by field
    skip: int = 0,
    limit: int = 100
):
    """
    Get all plantings for the authenticated user.
    Optionally filter by field_id to see only plantings in a specific field.
    """
    # Build query
    query = select(Planting).join(Field).where(Field.userid == current_user.userid)
    
    # Apply filter if field_id provided
    if field_id:
        query = query.where(Planting.field_id == field_id)
    
    query = query.offset(skip).limit(limit).order_by(Planting.plantingdate.desc())
    
    result = await db.execute(query)
    plantings = result.scalars().all()
    return plantings

@plantingrouter.get("/{planting_id}", response_model=PlantingResponse)
async def get_planting_by_id(
    planting_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific planting by ID.
    Verifies the planting belongs to user via the field relationship.
    """
    result = await db.execute(
        select(Planting)
        .join(Field)
        .where(Planting.id == planting_id, Field.user_id == current_user.id)
    )
    planting = result.scalar_one_or_none()
    
    if not planting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Planting with id {planting_id} not found"
        )
    
    return planting

@plantingrouter.put("/{planting_id}", response_model=PlantingResponse)
async def update_planting(
    planting_id: int,
    planting_data: PlantingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing planting.
    """
    # Verify planting exists and belongs to user
    result = await db.execute(
        select(Planting)
        .join(Field)
        .where(Planting.plantingid == planting_id, Field.userid == current_user.userid)
    )
    planting = result.scalar_one_or_none()
    
    if not planting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Planting with id {planting_id} not found"
        )
    
    # Update provided fields
    if planting_data.cropname is not None:
        planting.cropname = planting_data.cropname
    if planting_data.cropvariety is not None:
        planting.cropvariety = planting_data.cropvariety
    if planting_data.plantingdate is not None:
        planting.plantingdate = planting_data.plantingdate
    if planting_data.seedquantitykg is not None:
        planting.seedquantitykg = planting_data.seedquantitykg
    if planting_data.seedcost is not None:
        planting.seedcost = planting_data.seedcost
    if planting_data.plantsperhectare is not None:
        planting.plantsperhectare = planting_data.plantsperhectare
    if planting_data.rowspacingcm is not None:
        planting.rowspacingcm = planting_data.rowspacingcm
    if planting_data.status is not None:
        planting.status = planting_data.status
    if planting_data.notes is not None:
        planting.notes = planting_data.notes
    
    await db.commit()
    await db.refresh(planting)
    
    return planting

@plantingrouter.delete("/{planting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_planting(
    planting_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a planting.
    Cascade will delete associated harvest, sales, and reminders.
    """
    result = await db.execute(
        select(Planting)
        .join(Field)
        .where(Planting.id == planting_id, Field.user_id == current_user.id)
    )
    planting = result.scalar_one_or_none()
    
    if not planting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Planting with id {planting_id} not found"
        )
    
    await db.delete(planting)
    await db.commit()