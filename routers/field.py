"""
CRUD endpoints for Field management.
All endpoints require authentication.
Users can only access their own fields.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.connection import get_db
from database.models import Field
from schemas.field import FieldCreate, FieldUpdate, FieldResponse
from utils.dependencies import get_current_user
from database.models import User
from typing import List

fieldrouter = APIRouter(prefix="/api/fields", tags=["Fields"])

@fieldrouter.post("/", response_model=FieldResponse, status_code=status.HTTP_201_CREATED)
async def create_field(
    field_data: FieldCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new field for the authenticated user.
    User ID is automatically set from the JWT token.
    """
    # Create new field instance
    new_field = Field(
        userid=current_user.userid,  # Automatically assign to logged-in user
        name=field_data.name,
        areahectares=field_data.areahectares,
        soiltype=field_data.soiltype,
        soilph=field_data.soilph,
        notes=field_data.notes
    )
    
    db.add(new_field)
    await db.commit()
    await db.refresh(new_field)
    
    return new_field

@fieldrouter.get("/", response_model=List[FieldResponse])
async def get_all_fields(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,  # For pagination: number of records to skip
    limit: int = 100  # For pagination: max records to return
):
    """
    Get all fields belonging to the authenticated user.
    Supports pagination with skip and limit parameters.
    """
    result = await db.execute(
        select(Field)
        .where(Field.userid == current_user.userid)
        .offset(skip)
        .limit(limit)
        .order_by(Field.createdat.desc())
    )
    fields = result.scalars().all()
    return fields

@fieldrouter.get("/{field_id}", response_model=FieldResponse)
async def get_field_by_id(
    field_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific field by ID.
    Returns 404 if field doesn't exist or doesn't belong to user.
    """
    result = await db.execute(
        select(Field).where(Field.fieldid == field_id, Field.userid == current_user.userid)
    )
    field = result.scalar_one_or_none()
    
    if not field:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Field with id {field_id} not found"
        )
    
    return field

@fieldrouter.put("/{field_id}", response_model=FieldResponse)
async def update_field(
    field_id: int,
    field_data: FieldUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing field.
    Only fields belonging to the user can be updated.
    """
    # First, verify field exists and belongs to user
    result = await db.execute(
        select(Field).where(Field.fieldid == field_id, Field.userid == current_user.userid)
    )
    field = result.scalar_one_or_none()
    
    if not field:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Field with id {field_id} not found"
        )
    
    # Update only fields that were provided (not None)
    if field_data.name is not None:
        field.name = field_data.name
    if field_data.areahectares is not None:
        field.areahectares = field_data.areahectares
    if field_data.soiltype is not None:
        field.soiltype = field_data.soiltype
    if field_data.soilph is not None:
        field.soilph = field_data.soilph
    if field_data.notes is not None:
        field.notes = field_data.notes
    
    await db.commit()
    await db.refresh(field)
    
    return field

@fieldrouter.delete("/{field_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_field(
    field_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a field.
    Cascade delete will automatically delete all related plantings, harvests, etc.
    """
    result = await db.execute(
        select(Field).where(Field.fieldid == field_id, Field.userid == current_user.userid)
    )
    field = result.scalar_one_or_none()
    
    if not field:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Field with id {field_id} not found"
        )
    
    await db.delete(field)
    await db.commit()
    
    return None  # 204 No Content response