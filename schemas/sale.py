"""
Pydantic schemas for Sale model.
Tracks sales of harvested crops.
"""

from pydantic import BaseModel, Field, computed_field
from datetime import datetime
from typing import Optional
from decimal import Decimal

class SaleBase(BaseModel):
    """Shared fields for sale operations"""
    sale_date: datetime = Field(..., description="When the sale occurred")
    quantity_kg: Decimal = Field(..., gt=0, description="Quantity sold in kilograms")
    unit_price: Decimal = Field(..., gt=0, description="Price per kilogram in Liberian Dollars")
    buyer_name: Optional[str] = Field(None, max_length=200, description="Name of buyer/company")
    notes: Optional[str] = None

class SaleCreate(SaleBase):
    """Client sends this when recording a sale"""
    harvest_id: int = Field(..., gt=0, description="ID of harvest")

class SaleUpdate(BaseModel):
    """Client sends this when updating sale - all fields optional"""
    sale_date: Optional[datetime] = None
    quantity_kg: Optional[Decimal] = Field(None, gt=0)
    unit_price: Optional[Decimal] = Field(None, gt=0)
    buyer_name: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = None

class SaleResponse(SaleBase):
    """Server sends this when returning sale data"""
    saleid: int
    harvest_id: int
    created_at: datetime
    
    @computed_field  # This field is calculated, not stored in database
    @property
    def total_price(self) -> Decimal:
        """Calculate total revenue: quantity × unit price"""
        return self.quantity_kg * self.unit_price
    
    class Config:
        from_attributes = True