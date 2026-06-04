"""
Pydantic schemas for Harvest model.
Records yield from a planting.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class HarvestBase(BaseModel):
        """Shared fields for harvest operations"""
        harvest_date: datetime = Field(..., description="When the crop was harvested")
        yield_kg: float = Field(..., gt=0, description="Total yield in kilograms")
        moisture_percent: Optional[float] = Field(None, ge=0, le=100, description="Moisture content percentage")
        quality_grade: Optional[str] = Field(None, max_length=10, description="Grade: A, B, C, Premium, etc.")
        notes: Optional[str] = None

class HarvestCreate(HarvestBase):
        """Client sends this when recording a harvest"""
        planting_id: int = Field(..., gt=0, description="ID of planting being harvested")

class HarvestUpdate(BaseModel):
        """Client sends this when updating harvest - all fields optional"""
        harvest_date: Optional[datetime] = None
        yield_kg: Optional[float] = Field(None, gt=0)
        moisture_percent: Optional[float] = Field(None, ge=0, le=100)
        quality_grade: Optional[str] = Field(None, max_length=10)
        notes: Optional[str] = None

class HarvestResponse(HarvestBase):
        """Server sends this when returning harvest data"""
        harvestid: int
        planting_id: int
        created_at: datetime
        
class Config:
            from_attributes = True