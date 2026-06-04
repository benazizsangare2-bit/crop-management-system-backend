"""
CRUD endpoints for Harvest management.
Records yield from plantings.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.connection import get_db
from database.models import Harvest, Planting, Field
from schemas.harvest import HarvestCreate, HarvestUpdate, HarvestResponse
from utils.dependencies import get_current_user
from database.models import User
from typing import List

harvestrouter = APIRouter(prefix="/api/harvests", tags=["Harvests"])

@harvestrouter.post("/", response_model=HarvestResponse, status_code=status.HTTP_201_CREATED)
async def create_harvest(
    harvest_data: HarvestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Record a harvest for a planting.
    Verifies the planting belongs to the current user.
    """
    # Verify planting exists and belongs to user
    planting_result = await db.execute(
        select(Planting)
        .join(Field)
        .where(Planting.plantingid == harvest_data.planting_id, Field.userid == current_user.userid)
    )
    planting = planting_result.scalar_one_or_none()
    
    if not planting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Planting with id {harvest_data.planting_id} not found"
        )
    
    # Check if harvest already exists for this planting
    existing_result = await db.execute(
        select(Harvest).where(Harvest.planting_id == harvest_data.planting_id)
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Harvest already recorded for planting {harvest_data.planting_id}"
        )
    
    # Create harvest
    new_harvest = Harvest(
        planting_id=harvest_data.planting_id,
        harvest_date=harvest_data.harvest_date,
        yield_kg=harvest_data.yield_kg,
        moisture_percent=harvest_data.moisture_percent,
        quality_grade=harvest_data.quality_grade,
        notes=harvest_data.notes
    )
    
    # Update planting status to 'harvested'
    planting.status = 'harvested'
    
    db.add(new_harvest)
    await db.commit()
    await db.refresh(new_harvest)
    
    return new_harvest

@harvestrouter.get("/", response_model=List[HarvestResponse])
async def get_all_harvests(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    planting_id: int = None,
    skip: int = 0,
    limit: int = 100
):
    """
    Get all harvests for the user.
    Optionally filter by planting_id.
    """
    query = select(Harvest).join(Planting).join(Field).where(Field.userid == current_user.userid)
    
    if planting_id:
        query = query.where(Harvest.planting_id == planting_id)
    
    query = query.offset(skip).limit(limit).order_by(Harvest.harvest_date.desc())
    
    result = await db.execute(query)
    harvests = result.scalars().all()
    return harvests

@harvestrouter.get("/{harvest_id}", response_model=HarvestResponse)
async def get_harvest_by_id(
    harvest_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific harvest by ID.
    """
    result = await db.execute(
        select(Harvest)
        .join(Planting)
        .join(Field)
        .where(Harvest.harvestid == harvest_id, Field.userid == current_user.userid)
    )
    harvest = result.scalar_one_or_none()
    
    if not harvest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Harvest with id {harvest_id} not found"
        )
    
    return harvest

@harvestrouter.put("/{harvest_id}", response_model=HarvestResponse)
async def update_harvest(
    harvest_id: int,
    harvest_data: HarvestUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing harvest.
    """
    result = await db.execute(
        select(Harvest)
        .join(Planting)
        .join(Field)
        .where(Harvest.harvestid == harvest_id, Field.userid == current_user.userid)
    )
    harvest = result.scalar_one_or_none()
    
    if not harvest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Harvest with id {harvest_id} not found"
        )
    
    if harvest_data.harvest_date is not None:
        harvest.harvest_date = harvest_data.harvest_date
    if harvest_data.yield_kg is not None:
        harvest.yield_kg = harvest_data.yield_kg
    if harvest_data.moisture_percent is not None:
        harvest.moisture_percent = harvest_data.moisture_percent
    if harvest_data.quality_grade is not None:
        harvest.quality_grade = harvest_data.quality_grade
    if harvest_data.notes is not None:
        harvest.notes = harvest_data.notes
    
    await db.commit()
    await db.refresh(harvest)
    
    return harvest

@harvestrouter.delete("/{harvest_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_harvest(
    harvest_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a harvest.
    """
    result = await db.execute(
        select(Harvest)
        .join(Planting)
        .join(Field)
        .where(Harvest.harvestid == harvest_id, Field.userid == current_user.userid)
    )
    harvest = result.scalar_one_or_none()
    
    if not harvest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Harvest with id {harvest_id} not found"
        )
    
    # Get the planting to update its status
    planting_result = await db.execute(
        select(Planting).where(Planting.plantingid == harvest.planting_id)
    )
    planting = planting_result.scalar_one_or_none()
    if planting:
        planting.status = 'growing'  # Reset status
    
    await db.delete(harvest)
    await db.commit()