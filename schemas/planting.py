"""
Pydantic schemas for Planting model.
Tracks each crop cycle from planting to harvest.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class PlantingBase(BaseModel):
    """Shared fields for planting operations"""
    cropname: str = Field(..., min_length=1, max_length=100, description="Crop type: Corn, Rice, etc.")
    cropvariety: Optional[str] = Field(None, max_length=100, description="Specific variety name")
    plantingdate: datetime = Field(..., description="When seeds were planted")
    seedquantitykg: Optional[float] = Field(None, ge=0, description="Amount of seed used in kg")
    seedcost: Optional[float] = Field(None, ge=0, description="Cost of seeds in Liberian Dollars")
    plantsperhectare: Optional[int] = Field(None, gt=0, description="Target plant population density")
    rowspacingcm: Optional[int] = Field(None, gt=0, description="Distance between rows in cm")
    status: Optional[str] = Field("planted", description="Status: planted, growing, harvested, failed")
    notes: Optional[str] = None

class PlantingCreate(PlantingBase):
    """Client sends this when creating a new planting"""
    field_id: int = Field(..., gt=0, description="ID of field where planting occurs")

class PlantingUpdate(BaseModel):
    """Client sends this when updating existing planting - all fields optional"""
    cropname: Optional[str] = Field(None, min_length=1, max_length=100)
    cropvariety: Optional[str] = Field(None, max_length=100)
    plantingdate: Optional[datetime] = None
    seedquantitykg: Optional[float] = Field(None, ge=0)
    seedcost: Optional[float] = Field(None, ge=0)
    plantsperhectare: Optional[int] = Field(None, gt=0)
    rowspacingcm: Optional[int] = Field(None, gt=0)
    status: Optional[str] = None
    notes: Optional[str] = None

class PlantingResponse(PlantingBase):
    """Server sends this when returning planting data"""
    plantingid: int
    field_id: int
    createdat: datetime
    updatedat: Optional[datetime] = None
    
    class Config:
        from_attributes = True