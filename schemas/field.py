"""
Pydantic schemas for Field model.
These validate and serialize data for field-related API endpoints.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

# Base schema with common attributes (used as foundation for others)
class FieldBase(BaseModel):
    """Shared fields between create, update, and response schemas"""
    name: str = Field(..., min_length=1, max_length=100, description="Field name like 'North Field'")
    areahectares: float = Field(..., gt=0, description="Size in hectares, must be positive")
    soiltype: Optional[str] = Field(None, max_length=50, description="Soil type: clay, sandy, loamy, etc.")
    soilph: Optional[float] = Field(None, ge=3.5, le=9.5, description="Soil pH between 3.5 and 9.5")
    notes: Optional[str] = None

# Schema for creating a new field (same as base, no ID needed yet)
class FieldCreate(FieldBase):
    """What the client sends when creating a field"""
    pass

# Schema for updating an existing field (all fields optional)
class FieldUpdate(BaseModel):
    """What the client sends when updating a field - all fields optional"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    areahectares: Optional[float] = Field(None, gt=0)
    soiltype: Optional[str] = Field(None, max_length=50)
    soilph: Optional[float] = Field(None, ge=3.5, le=9.5)
    notes: Optional[str] = None

# Schema for returning field data to client
class FieldResponse(FieldBase):
    """What the server sends back when client requests field data"""
    fieldid: int
    userid: int
    createdat: datetime
    updatedat: Optional[datetime] = None
    
    class Config:
        from_attributes = True  # Allows creating from SQLAlchemy model