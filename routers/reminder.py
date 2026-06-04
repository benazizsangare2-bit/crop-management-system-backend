"""
CRUD endpoints for Reminder management.
Manages task reminders for farmers, including relative reminders based on planting dates.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, timedelta
from database.connection import get_db
from database.models import Reminder, Planting, Field
from schemas.reminder import ReminderCreate, ReminderUpdate, ReminderResponse
from utils.dependencies import get_current_user
from database.models import User
from typing import List

reminderrouter = APIRouter(prefix="/api/reminders", tags=["Reminders"])

@reminderrouter.post("/", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
async def create_reminder(
    reminder_data: ReminderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new reminder.
    If days_after_planting is provided, automatically calculate due_date.
    If planting_id is provided, verify it belongs to user.
    """
    calculated_due_date = reminder_data.due_date
    
    # If this is a relative reminder, calculate the actual due date
    if reminder_data.days_after_planting is not None and reminder_data.planting_id:
        # Verify planting exists and belongs to user
        planting_result = await db.execute(
            select(Planting)
            .join(Field)
            .where(Planting.plantingid == reminder_data.planting_id, Field.userid == current_user.userid)
        )
        planting = planting_result.scalar_one_or_none()
        
        if not planting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Planting with id {reminder_data.planting_id} not found"
            )
        
        # Calculate due date = planting_date + days_after_planting
        calculated_due_date = planting.plantingdate + timedelta(days=reminder_data.days_after_planting)
    
    # Create reminder
    new_reminder = Reminder(
        user_id=current_user.userid,
        planting_id=reminder_data.planting_id,
        title=reminder_data.title,
        reminder_type=reminder_data.reminder_type.value,  # Convert enum to string
        due_date=calculated_due_date,
       # days_after_planting=reminder_data.days_after_planting,  # Store for reference
        notes=reminder_data.notes,
        is_completed=False
    )
    
    db.add(new_reminder)
    await db.commit()
    await db.refresh(new_reminder)
    
    return new_reminder

@reminderrouter.get("/", response_model=List[ReminderResponse])
async def get_all_reminders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    include_completed: bool = False,
    upcoming_days: int = None,  # Get reminders due in next X days
    skip: int = 0,
    limit: int = 100
):
    """
    Get all reminders for the user.
    - include_completed: if False, only shows pending reminders
    - upcoming_days: if provided, only shows reminders due in next N days
    """
    query = select(Reminder).where(Reminder.user_id == current_user.userid)
    
    # Filter out completed reminders if requested
    if not include_completed:
        query = query.where(Reminder.is_completed == False)
    
    # Filter by upcoming days
    if upcoming_days:
        cutoff_date = datetime.utcnow()
        future_date = cutoff_date + timedelta(days=upcoming_days)
        query = query.where(
            and_(
                Reminder.due_date >= cutoff_date,
                Reminder.due_date <= future_date
            )
        )
    
    query = query.offset(skip).limit(limit).order_by(Reminder.due_date.asc())
    
    result = await db.execute(query)
    reminders = result.scalars().all()
    return reminders

@reminderrouter.get("/{reminder_id}", response_model=ReminderResponse)
async def get_reminder_by_id(
    reminder_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific reminder by ID.
    """
    result = await db.execute(
        select(Reminder).where(Reminder.reminderid == reminder_id, Reminder.user_id == current_user.userid)
    )
    reminder = result.scalar_one_or_none()
    
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reminder with id {reminder_id} not found"
        )
    
    return reminder

@reminderrouter.put("/{reminder_id}/complete", response_model=ReminderResponse)
async def mark_reminder_complete(
    reminder_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark a reminder as completed.
    This is a specialized endpoint for the most common action.
    """
    result = await db.execute(
        select(Reminder).where(Reminder.reminderid == reminder_id, Reminder.user_id == current_user.userid)
    )
    reminder = result.scalar_one_or_none()
    
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reminder with id {reminder_id} not found"
        )
    
    reminder.is_completed = True
    reminder.completed_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(reminder)
    
    return reminder

@reminderrouter.put("/{reminder_id}", response_model=ReminderResponse)
async def update_reminder(
    reminder_id: int,
    reminder_data: ReminderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a reminder.
    """
    result = await db.execute(
        select(Reminder).where(Reminder.reminderid == reminder_id, Reminder.user_id == current_user.userid)
    )
    reminder = result.scalar_one_or_none()
    
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reminder with id {reminder_id} not found"
        )
    
    if reminder_data.title is not None:
        reminder.title = reminder_data.title
    if reminder_data.reminder_type is not None:
        reminder.reminder_type = reminder_data.reminder_type.value
    if reminder_data.due_date is not None:
        reminder.due_date = reminder_data.due_date
    if reminder_data.days_after_planting is not None:
        reminder.days_after_planting = reminder_data.days_after_planting
    if reminder_data.notes is not None:
        reminder.notes = reminder_data.notes
    if reminder_data.is_completed is not None:
        reminder.is_completed = reminder_data.is_completed
        if reminder_data.is_completed and not reminder.completed_at:
            reminder.completed_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(reminder)
    
    return reminder

@reminderrouter.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reminder(
    reminder_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a reminder.
    """
    result = await db.execute(
        select(Reminder).where(Reminder.reminderid == reminder_id, Reminder.user_id == current_user.userid)
    )
    reminder = result.scalar_one_or_none()
    
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reminder with id {reminder_id} not found"
        )
    
    await db.delete(reminder)
    await db.commit()