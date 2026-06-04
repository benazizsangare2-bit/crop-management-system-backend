"""
CRUD endpoints for Sale management.
Tracks sales of harvested crops.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database.connection import get_db
from database.models import Sale, Harvest, Planting, Field
from schemas.sale import SaleCreate, SaleUpdate, SaleResponse
from utils.dependencies import get_current_user
from database.models import User
from typing import List
from decimal import Decimal

salesrouter = APIRouter(prefix="/api/sales", tags=["Sales"])

@salesrouter.post("/", response_model=SaleResponse, status_code=status.HTTP_201_CREATED)
async def create_sale(
    sale_data: SaleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Record a sale from a harvest.
    Verifies the harvest belongs to the current user.
    """
    # Verify harvest exists and belongs to user
    harvest_result = await db.execute(
        select(Harvest)
        .join(Planting)
        .join(Field)
        .where(Harvest.harvestid == sale_data.harvest_id, Field.userid == current_user.userid)
    )
    harvest = harvest_result.scalar_one_or_none()
    
    if not harvest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Harvest with id {sale_data.harvest_id} not found"
        )
    
    # Optional: Check if total sales exceed harvest yield
    # Get total sold so far
    total_sold_result = await db.execute(
        select(func.sum(Sale.quantity_kg)).where(Sale.harvest_id == sale_data.harvest_id)
    )
    total_sold = total_sold_result.scalar() or Decimal(0)
    
    if total_sold + sale_data.quantity_kg > harvest.yield_kg:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot sell {sale_data.quantity_kg}kg. Only {harvest.yield_kg - total_sold}kg remaining"
        )
    
    # Create sale
    new_sale = Sale(
        harvest_id=sale_data.harvest_id,
        sale_date=sale_data.sale_date,
        quantity_kg=sale_data.quantity_kg,
        unit_price=sale_data.unit_price,
        buyer_name=sale_data.buyer_name,
        notes=sale_data.notes
    )
    
    db.add(new_sale)
    await db.commit()
    await db.refresh(new_sale)
    
    return new_sale

@salesrouter.get("/", response_model=List[SaleResponse])
async def get_all_sales(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    harvest_id: int = None,
    skip: int = 0,
    limit: int = 100
):
    """
    Get all sales for the user.
    Optionally filter by harvest_id.
    """
    query = select(Sale).join(Harvest).join(Planting).join(Field).where(Field.userid == current_user.userid)
    
    if harvest_id:
        query = query.where(Sale.harvest_id == harvest_id)
    
    query = query.offset(skip).limit(limit).order_by(Sale.sale_date.desc())
    
    result = await db.execute(query)
    sales = result.scalars().all()
    return sales

@salesrouter.get("/{sale_id}", response_model=SaleResponse)
async def get_sale_by_id(
    sale_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific sale by ID.
    """
    result = await db.execute(
        select(Sale)
        .join(Harvest)
        .join(Planting)
        .join(Field)
        .where(Sale.id == sale_id, Field.user_id == current_user.userid)
    )
    sale = result.scalar_one_or_none()
    
    if not sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sale with id {sale_id} not found"
        )
    
    return sale

@salesrouter.put("/{sale_id}", response_model=SaleResponse)
async def update_sale(
    sale_id: int,
    sale_data: SaleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing sale.
    """
    result = await db.execute(
        select(Sale)
        .join(Harvest)
        .join(Planting)
        .join(Field)
        .where(Sale.saleid == sale_id, Field.userid == current_user.userid)
    )
    sale = result.scalar_one_or_none()
    
    if not sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sale with id {sale_id} not found"
        )
    
    if sale_data.sale_date is not None:
        sale.sale_date = sale_data.sale_date
    if sale_data.quantity_kg is not None:
        sale.quantity_kg = sale_data.quantity_kg
    if sale_data.unit_price is not None:
        sale.unit_price = sale_data.unit_price
    if sale_data.buyer_name is not None:
        sale.buyer_name = sale_data.buyer_name
    if sale_data.notes is not None:
        sale.notes = sale_data.notes
    
    await db.commit()
    await db.refresh(sale)
    
    return sale

@salesrouter.delete("/{sale_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sale(
    sale_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a sale.
    """
    result = await db.execute(
        select(Sale)
        .join(Harvest)
        .join(Planting)
        .join(Field)
        .where(Sale.saleid == sale_id, Field.userid == current_user.userid)
    )
    sale = result.scalar_one_or_none()
    
    if not sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sale with id {sale_id} not found"
        )
    
    await db.delete(sale)
    await db.commit()