"""
Stock tracking for harvests - tracks how much remains unsold
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database.connection import get_db
from database.models import Sale, Harvest, Planting, Field
from utils.dependencies import get_current_user
from database.models import User
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

stockrouter = APIRouter(prefix="/api/harvests", tags=["Harvest Stock"])

@stockrouter.get("/stock")
async def get_all_harvest_stock(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    only_remaining: bool = False
):
    """
    Get stock status for all harvests - shows how much remains unsold.
    """
    # Get all harvests for this user
    harvests_result = await db.execute(
        select(Harvest)
        .join(Planting)
        .join(Field)
        .where(Field.userid == current_user.userid)
        .order_by(Harvest.harvest_date.desc())
    )
    harvests = harvests_result.scalars().all()
    
    results = []
    
    for harvest in harvests:
        # Get total sold quantity
        sales_result = await db.execute(
            select(func.sum(Sale.quantity_kg).label('total_sold'))
            .where(Sale.harvest_id == harvest.harvestid)
        )
        total_sold = sales_result.scalar() or 0
        
        remaining = float(harvest.yield_kg) - float(total_sold)
        
        # Get crop and field names
        planting = await db.get(Planting, harvest.planting_id)
        field = await db.get(Field, planting.field_id)
        
        stock_item = {
            "harvest_id": harvest.harvestid,
            "crop_name": planting.cropname,
            "field_name": field.name,
            "harvest_date": harvest.harvest_date.isoformat(),
            "total_yield_kg": float(harvest.yield_kg),
            "sold_kg": float(total_sold),
            "remaining_kg": round(remaining, 2),
            "sold_percentage": round((float(total_sold) / float(harvest.yield_kg) * 100), 2) if harvest.yield_kg > 0 else 0
        }
        
        # Filter if only showing harvests with remaining stock
        if only_remaining and remaining <= 0:
            continue
            
        results.append(stock_item)
    
    return results

@stockrouter.get("/{harvest_id}/stock")
async def get_harvest_stock(
    harvest_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed stock status for a specific harvest with all sales.
    """
    # Verify harvest belongs to user
    harvest_result = await db.execute(
        select(Harvest)
        .join(Planting)
        .join(Field)
        .where(Harvest.harvestid == harvest_id, Field.userid == current_user.userid)
    )
    harvest = harvest_result.scalar_one_or_none()
    
    if not harvest:
        raise HTTPException(status_code=404, detail="Harvest not found")
    
    # Get all sales for this harvest
    sales_result = await db.execute(
        select(Sale)
        .where(Sale.harvest_id == harvest_id)
        .order_by(Sale.sale_date.desc())
    )
    sales = sales_result.scalars().all()
    
    total_sold = sum(s.quantity_kg for s in sales)
    remaining = harvest.yield_kg - total_sold
    
    planting = await db.get(Planting, harvest.planting_id)
    
    return {
        "harvest_id": harvest.harvest_id,
        "crop_name": planting.cropname,
        "field_name": field.name if field else "Unknown",
        "harvest_date": harvest.harvest_date,
        "total_yield_kg": float(harvest.yield_kg),
        "sold_kg": float(total_sold),
        "remaining_kg": float(remaining),
        "sales": [
            {
                "sale_id": sale.saleid,
                "date": sale.sale_date,
                "quantity_kg": float(sale.quantity_kg),
                "unit_price": float(sale.unit_price),
                "total": float(sale.quantity_kg * sale.unit_price),
                "buyer": sale.buyer_name
            }
            for sale in sales
        ]
    }