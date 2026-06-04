"""
Pydantic schemas for CropInput model.
Tracks inventory of farming supplies.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum

class CropInputTypeEnum(str, Enum):
    SEED = "seed"
    FERTILIZER = "fertilizer"
    PESTICIDE = "pesticide"
    HERBICIDE = "herbicide"
    OTHER = "other"

class CropInputBase(BaseModel):
    """Shared fields for crop input operations"""
    name: str = Field(..., min_length=1, max_length=150, description="Product name")
    input_type: CropInputTypeEnum = Field(..., description="Type of input")
    unit: str = Field(..., min_length=1, max_length=20, description="Unit: kg, liter, bag, etc.")
    current_stock: float = Field(0, ge=0, description="Current quantity in stock")
    reorder_point: Optional[float] = Field(None, ge=0, description="Alert when stock falls below this")
    unit_cost: Optional[float] = Field(None, ge=0, description="Cost per unit in Liberian Dollars")
    notes: Optional[str] = None

class CropInputCreate(CropInputBase):
    """Client sends this when adding new inventory item"""
    pass

class CropInputUpdate(BaseModel):
    """Client sends this when updating inventory"""
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    input_type: Optional[CropInputTypeEnum] = None
    unit: Optional[str] = Field(None, min_length=1, max_length=20)
    current_stock: Optional[float] = Field(None, ge=0)
    reorder_point: Optional[float] = Field(None, ge=0)
    unit_cost: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None

class CropInputResponse(CropInputBase):
    """Server sends this when returning inventory data"""
    cropinputid: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True