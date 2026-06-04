"""
CRUD endpoints for CropInput (inventory) management.
Tracks farming supplies like seeds, fertilizers, pesticides.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.connection import get_db
from database.models import CropInput
from schemas.crop_input import CropInputCreate, CropInputUpdate, CropInputResponse
from utils.dependencies import get_current_user
from database.models import User
from typing import List

cropinputrouter = APIRouter(prefix="/api/crop-inputs", tags=["Crop Inputs (Inventory)"])

@cropinputrouter.post("/", response_model=CropInputResponse, status_code=status.HTTP_201_CREATED)
async def create_crop_input(
    input_data: CropInputCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add a new item to inventory (seeds, fertilizer, pesticide, etc.)
    """
    new_input = CropInput(
        user_id=current_user.userid,
        name=input_data.name,
        input_type=input_data.input_type.value,
        unit=input_data.unit,
        current_stock=input_data.current_stock,
        reorder_point=input_data.reorder_point,
        unit_cost=input_data.unit_cost,
        notes=input_data.notes
    )
    
    db.add(new_input)
    await db.commit()
    await db.refresh(new_input)
    
    return new_input

@cropinputrouter.get("/", response_model=List[CropInputResponse])
async def get_all_crop_inputs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    input_type: str = None,  # Optional filter by type
    low_stock_only: bool = False,  # Only show items below reorder point
    skip: int = 0,
    limit: int = 100
):
    """
    Get all inventory items for the user.
    - input_type: filter by type (seed, fertilizer, pesticide, etc.)
    - low_stock_only: only show items where current_stock <= reorder_point
    """
    query = select(CropInput).where(CropInput.user_id == current_user.userid)
    
    if input_type:
        query = query.where(CropInput.input_type == input_type)
    
    if low_stock_only:
        query = query.where(
            CropInput.current_stock <= CropInput.reorder_point
        ).where(CropInput.reorder_point.isnot(None))
    
    query = query.offset(skip).limit(limit).order_by(CropInput.name)
    
    result = await db.execute(query)
    inputs = result.scalars().all()
    return inputs

@cropinputrouter.get("/{input_id}", response_model=CropInputResponse)
async def get_crop_input_by_id(
    input_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific inventory item by ID.
    """
    result = await db.execute(
        select(CropInput).where(CropInput.id == input_id, CropInput.user_id == current_user.userid)
    )
    crop_input = result.scalar_one_or_none()
    
    if not crop_input:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crop input with id {input_id} not found"
        )
    
    return crop_input

@cropinputrouter.put("/{input_id}", response_model=CropInputResponse)
async def update_crop_input(
    input_id: int,
    input_data: CropInputUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an inventory item (e.g., adjust stock levels).
    """
    result = await db.execute(
        select(CropInput).where(CropInput.cropinputid == input_id, CropInput.user_id == current_user.userid)
    )
    crop_input = result.scalar_one_or_none()
    
    if not crop_input:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crop input with id {input_id} not found"
        )
    
    if input_data.name is not None:
        crop_input.name = input_data.name
    if input_data.input_type is not None:
        crop_input.input_type = input_data.input_type.value
    if input_data.unit is not None:
        crop_input.unit = input_data.unit
    if input_data.current_stock is not None:
        crop_input.current_stock = input_data.current_stock
    if input_data.reorder_point is not None:
        crop_input.reorder_point = input_data.reorder_point
    if input_data.unit_cost is not None:
        crop_input.unit_cost = input_data.unit_cost
    if input_data.notes is not None:
        crop_input.notes = input_data.notes
    
    await db.commit()
    await db.refresh(crop_input)
    
    return crop_input

@cropinputrouter.delete("/{input_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_crop_input(
    input_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete an inventory item.
    """
    result = await db.execute(
        select(CropInput).where(CropInput.cropinputid == input_id, CropInput.user_id == current_user.userid)
    )
    crop_input = result.scalar_one_or_none()
    
    if not crop_input:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crop input with id {input_id} not found"
        )
    
    await db.delete(crop_input)
    await db.commit()