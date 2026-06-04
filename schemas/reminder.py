"""
Pydantic schemas for Reminder model.
Manages task reminders for farmers.
"""

from pydantic import BaseModel, Field, model_validator
from datetime import datetime
from typing import Optional
from enum import Enum

# Enum for reminder types (matches database enum)
class ReminderTypeEnum(str, Enum):
    FERTILIZER = "fertilizer"
    IRRIGATION = "irrigation"
    PESTICIDE = "pesticide"
    HARVEST = "harvest"
    SOIL_TEST = "soil_test"
    OTHER = "other"

class ReminderBase(BaseModel):
    """Shared fields for reminder operations"""
    title: str = Field(..., min_length=1, max_length=200, description="Task description")
    reminder_type: ReminderTypeEnum = Field(..., description="Type of task")
    due_date: Optional[datetime] = Field(None, description="Fixed date reminder")
    days_after_planting: Optional[int] = Field(None, description="Relative reminder: days after planting")
    notes: Optional[str] = None

    @model_validator(mode='after')
    def validate_reminder_dates(self) -> 'ReminderBase':
        """Ensure at least one type of date is provided"""
        if not self.due_date and self.days_after_planting is None:
            raise ValueError('Either due_date or days_after_planting must be provided')
        # if self.due_date and self.days_after_planting is not None:
        #     raise ValueError('Cannot provide both due_date and days_after_planting')
        return self

class ReminderCreate(ReminderBase):
    """Client sends this when creating a reminder"""
    planting_id: Optional[int] = Field(None, description="Optional: link to specific planting")

class ReminderUpdate(BaseModel):
    """Client sends this when updating reminder"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    reminder_type: Optional[ReminderTypeEnum] = None
    due_date: Optional[datetime] = None
    days_after_planting: Optional[int] = None
    notes: Optional[str] = None
    is_completed: Optional[bool] = None

class ReminderResponse(ReminderBase):
    """Server sends this when returning reminder data"""
    reminderid: int
    user_id: int
    planting_id: Optional[int] = None
    is_completed: bool
    completed_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True