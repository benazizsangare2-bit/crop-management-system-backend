"""
Sales Analytics - What sold most, quantities, remaining stock
"""



from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from database.connection import get_db
from database.models import Sale, Harvest, Planting, Field
from utils.dependencies import get_current_user
from database.models import User


analyticsrouter = APIRouter(prefix="/api/analytics", tags=["Analytics"])
@analyticsrouter.get("/sales/top-products")
async def get_top_products(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 5
):
    """
    What product sold the most? Returns top selling crops by quantity and revenue.
    """
    # Get all sales for this user
    query = select(Sale).join(Harvest).join(Planting).join(Field).where(Field.userid == current_user.userid)
    sales_result = await db.execute(query)
    sales = sales_result.scalars().all()
    
    # Aggregate by crop
    crop_stats = {}
    
    for sale in sales:
        harvest = await db.get(Harvest, sale.harvest_id)
        planting = await db.get(Planting, harvest.planting_id)
        crop_name = planting.cropname
        
        if crop_name not in crop_stats:
            crop_stats[crop_name] = {
                "total_quantity_kg": 0,
                "total_revenue": 0,
                "transaction_count": 0
            }
        
        crop_stats[crop_name]["total_quantity_kg"] += sale.quantity_kg
        crop_stats[crop_name]["total_revenue"] += sale.quantity_kg * sale.unit_price
        crop_stats[crop_name]["transaction_count"] += 1
    
    # Convert to list and sort
    result = []
    for crop_name, stats in crop_stats.items():
        result.append({
            "crop_name": crop_name,
            "total_quantity_kg": round(stats["total_quantity_kg"], 2),
            "total_revenue_lrd": round(stats["total_revenue"], 2),
            "transaction_count": stats["transaction_count"]
        })
    
    # Sort by quantity sold (highest first)
    result.sort(key=lambda x: x["total_quantity_kg"], reverse=True)
    
    return {
        "top_products": result[:limit],
        "total_products_sold": len(result)
    }

@analyticsrouter.get("/sales/summary")
async def get_sales_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Complete sales summary: total sold, by crop, remaining stock, losses.
    """
    # Get all harvests for this user
    harvests_result = await db.execute(
        select(Harvest)
        .join(Planting)
        .join(Field)
        .where(Field.userid == current_user.userid)
        .options(selectinload(Harvest.planting).selectinload(Planting.field))
    )
    harvests = harvests_result.scalars().all()
    
    total_harvested_kg = 0
    total_sold_kg = 0
    total_revenue = 0
    crop_details = []
    
    for harvest in harvests:
        planting = harvest.planting
        crop_name = planting.cropname if planting else "Unknown"
        
        # Get sales for this harvest
        sales_result = await db.execute(
            select(Sale).where(Sale.harvest_id == harvest.harvestid)
        )
        sales = sales_result.scalars().all()
        
        sold_kg = sum(s.quantity_kg for s in sales)
        revenue = sum(s.quantity_kg * s.unit_price for s in sales)
        remaining_kg = harvest.yield_kg - sold_kg
        
        total_harvested_kg += harvest.yield_kg
        total_sold_kg += sold_kg
        total_revenue += revenue
        
        crop_details.append({
            "crop_name": crop_name,
            "field_name": planting.field.name if planting and planting.field else "Unknown",
            "harvest_id": harvest.harvestid,
            "harvest_date": harvest.harvest_date,
            "harvested_kg": float(harvest.yield_kg),
            "sold_kg": float(sold_kg),
            "remaining_kg": float(remaining_kg),
            "revenue_lrd": float(revenue)
        })
    
    # Calculate loss (harvested but not sold)
    loss_kg = total_harvested_kg - total_sold_kg
    loss_percentage = (loss_kg / total_harvested_kg * 100) if total_harvested_kg > 0 else 0
    
    return {
        "summary": {
            "total_harvested_kg": round(total_harvested_kg, 2),
            "total_sold_kg": round(total_sold_kg, 2),
            "total_loss_kg": round(loss_kg, 2),
            "loss_percentage": round(loss_percentage, 2),
            "total_revenue_lrd": round(total_revenue, 2)
        },
        "by_crop": crop_details
    }

@analyticsrouter.get("/sales/remaining-stock")
async def get_remaining_stock_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Show only crops that still have unsold stock remaining.
    """
    # Get all harvests for this user
    harvests_result = await db.execute(
        select(Harvest)
        .join(Planting)
        .join(Field)
        .where(Field.userid == current_user.userid)
        .options(selectinload(Harvest.planting).selectinload(Planting.field))
    )
    harvests = harvests_result.scalars().all()
    
    remaining_stock = []
    
    for harvest in harvests:
        planting = harvest.planting
        
        # Get total sold
        sales_result = await db.execute(
            select(func.sum(Sale.quantity_kg))
            .where(Sale.harvest_id == harvest.harvestid)
        )
        sold_kg = sales_result.scalar() or 0
        
        remaining_kg = harvest.yield_kg - sold_kg
        
        # Only include if there's remaining stock
        if remaining_kg > 0:
            remaining_stock.append({
                "crop_name": planting.cropname if planting else "Unknown",
                "field_name": planting.field.name if planting and planting.field else "Unknown",
                "harvest_id": harvest.harvestid,
                "harvest_date": harvest.harvest_date,
                "remaining_kg": float(remaining_kg),
                "total_harvested_kg": float(harvest.yield_kg),
                "sold_kg": float(sold_kg)
            })
    
    return {
        "has_remaining_stock": len(remaining_stock) > 0,
        "items": remaining_stock,
        "total_remaining_kg": sum(item["remaining_kg"] for item in remaining_stock)
    }