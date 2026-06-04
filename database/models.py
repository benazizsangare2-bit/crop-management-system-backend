from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from database.connection import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Boolean, Text, Enum, Float
from sqlalchemy.orm import relationship
import enum


"""
This file contains all database models for the Crop Management System.
Each model represents a table in PostgreSQL.
Relationships between models:
User -> Field (one-to-many)
Field -> Planting (one-to-many)
Planting -> Harvest (one-to-one) 
Planting -> Reminder (one-to-many)
Harvest -> Sale (one-to-many)
User -> CropInput (one-to-many) - for tracking inventory
"""


class User(Base):
    __tablename__ = "users"
    
    userid = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    farm_name = Column(String(200), nullable=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# Define enum for activity types (used in reminders)
class ReminderTypeEnum(str, enum.Enum):
    FERTILIZER = "fertilizer"
    IRRIGATION = "irrigation"
    PESTICIDE = "pesticide"
    HARVEST = "harvest"
    SOIL_TEST = "soil_test"
    OTHER = "other"

class CropInputTypeEnum(str, enum.Enum):
    SEED = "seed"
    FERTILIZER = "fertilizer"
    PESTICIDE = "pesticide"
    HERBICIDE = "herbicide"
    OTHER = "other"


# ==================== FIELD MODEL ====================
class Field(Base):
    """
    Represents a physical piece of land where crops are grown.
    Each field belongs to one user (farm owner).
    One field can have multiple planting cycles over time.
    """
    __tablename__ = "fields"
    
    fieldid = Column(Integer, primary_key=True, index=True)  # Auto-incrementing ID
    userid = Column(Integer, ForeignKey("users.userid", ondelete="CASCADE"), nullable=False)  # Owner of this field
    name = Column(String(100), nullable=False)  # User-given name like "North Field" or "Rice Paddy #3"
    areahectares = Column(Numeric(10, 2), nullable=False)  # Size in hectares (supports decimals like 2.5)
    soiltype = Column(String(50), nullable=True)  # e.g., "clay", "sandy", "loamy" - optional but helpful
    soilph = Column(Numeric(3, 1), nullable=True)  # Soil acidity (3.5 to 9.5 range) - optional
    notes = Column(Text, nullable=True)  # Any extra info like "rocky area on east side"
    createdat = Column(DateTime(timezone=True), server_default=func.now())
    updatedat = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships (for SQLAlchemy ORM to easily access related data)
    # This allows: field.plantings to get all planting records for this field
    plantings = relationship("Planting", back_populates="field", cascade="all, delete-orphan")

# ==================== PLANTING MODEL ====================
class Planting(Base):
    """
    Represents a single crop cycle in a specific field.
    When you plant seeds in a field, you create a Planting record.
    This tracks everything from planting to harvest for that specific batch.
    """
    __tablename__ = "plantings"
    
    plantingid = Column(Integer, primary_key=True, index=True)
    field_id = Column(Integer, ForeignKey("fields.fieldid", ondelete="CASCADE"), nullable=False)  # Which field
    cropname = Column(String(100), nullable=False)  # What was planted (e.g., "Corn", "Rice", "Soybeans")
    cropvariety = Column(String(100), nullable=True)  # Specific variety (e.g., "Golden Harvest Bt", "Jasmine")
    plantingdate = Column(DateTime(timezone=True), nullable=False)  # When seeds went into the ground
    seedquantitykg = Column(Numeric(10, 2), nullable=True)  # How many kg of seeds were used
    seedcost = Column(Numeric(10, 2), nullable=True)  # How much was spent on seeds (in Liberian Dollars - LRD)
    plantsperhectare = Column(Integer, nullable=True)  # Target plant density (e.g., 45000 plants per hectare)
    rowspacingcm = Column(Integer, nullable=True)  # Distance between rows in centimeters
    status = Column(String(20), default="planted")  # 'planted', 'growing', 'harvested', 'failed'
    notes = Column(Text, nullable=True)  # Observations: "good germination", "drought stress", etc.
    createdat = Column(DateTime(timezone=True), server_default=func.now())
    updatedat = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    field = relationship("Field", back_populates="plantings")
     # IMPORTANT: 'harvest' is SINGULAR because it's one-to-one
    harvest = relationship("Harvest", back_populates="planting", uselist=False, cascade="all, delete-orphan")
    reminders = relationship("Reminder", back_populates="planting", cascade="all, delete-orphan")
# ==================== HARVEST MODEL ====================
class Harvest(Base):
    """
    Records the yield from a Planting.
    One planting has exactly one harvest record (when the crop is fully harvested).
    """
    __tablename__ = "harvests"
    
    harvestid = Column(Integer, primary_key=True, index=True)
    planting_id = Column(Integer, ForeignKey("plantings.plantingid", ondelete="CASCADE"), nullable=False, unique=True)  # Links to planting
    harvest_date = Column(DateTime(timezone=True), nullable=False)  # When harvesting occurred
    yield_kg = Column(Float(10, 2), nullable=False)  # Total weight harvested in kilograms
    moisture_percent = Column(Numeric(5, 2), nullable=True)  #% of water in crop (affects storage and price)
    quality_grade = Column(String(10), nullable=True)  # e.g., "A", "B", "C", "Premium", "Standard"
    notes = Column(Text, nullable=True)  # "Harvested during dry weather", "Some rot at edges"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    planting = relationship("Planting", back_populates="harvest")
    sales = relationship("Sale", back_populates="harvest", cascade="all, delete-orphan")  # One-to-many

# ==================== SALE MODEL ====================
class Sale(Base):
    """
    Tracks when harvested crops are sold.
    One harvest can be sold in multiple transactions (e.g., sell 1000kg to Buyer A, 500kg to Buyer B).
    Calculates total price automatically based on quantity × unit_price.
    """
    __tablename__ = "sales"
    
    saleid = Column(Integer, primary_key=True, index=True)
    harvest_id = Column(Integer, ForeignKey("harvests.harvestid", ondelete="CASCADE"), nullable=False)
    sale_date = Column(DateTime(timezone=True), nullable=False)  # When the sale happened
    quantity_kg = Column(Numeric(10, 2), nullable=False)  # How many kg were sold in this transaction
    unit_price = Column(Numeric(10, 2), nullable=False)  # Price per kg (in Liberian Dollars - LRD)
    # total_price is NOT stored - we calculate it when needed (quantity_kg × unit_price)
    buyer_name = Column(String(200), nullable=True)  # Who purchased the crop
    notes = Column(Text, nullable=True)  # "Cash payment", "Delivered to warehouse", etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    harvest = relationship("Harvest", back_populates="sales")

# ==================== REMINDER MODEL ====================
class Reminder(Base):
    """
    Creates notifications for farmers about tasks they need to do.
    Supports two types of due dates:
    1. Fixed date: specific date and time (e.g., "Soil test on June 15")
    2. Relative to planting: days_after_planting (e.g., "Apply fertilizer 30 days after planting")
    When relative reminders are created, the system calculates the actual due_date based on planting_date.
    """
    __tablename__ = "reminders"
    
    reminderid = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.userid", ondelete="CASCADE"), nullable=False)  # Which farmer this reminder is for
    planting_id = Column(Integer, ForeignKey("plantings.plantingid", ondelete="CASCADE"), nullable=True)  # Optional: link to specific crop cycle
    title = Column(String(200), nullable=False)  # Short description: "Apply nitrogen fertilizer"
    reminder_type = Column(Enum(ReminderTypeEnum), nullable=False)  # fertilizer, irrigation, etc.
    due_date = Column(DateTime(timezone=True), nullable=True)  # Fixed date reminder
   # days_after_planting = Column(Integer, nullable=True)  # For relative reminders (e.g., 30 = 30 days after planting)
    is_completed = Column(Boolean, default=False)  # Has the task been done?
    completed_at = Column(DateTime(timezone=True), nullable=True)  # When they marked it done
    notes = Column(Text, nullable=True)  # "Apply 100kg per hectare to the north section only"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    planting = relationship("Planting", back_populates="reminders")

# ==================== CROP INPUT MODEL ====================
class CropInput(Base):
    """
    Tracks inventory of farming supplies: seeds, fertilizers, pesticides, etc.
    Helps farmers know when they're running low on supplies.
    """
    __tablename__ = "crop_inputs"
    
    cropinputid = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.userid", ondelete="CASCADE"), nullable=False)  # Owner of this inventory
    name = Column(String(150), nullable=False)  # e.g., "NPK 15-15-15 Fertilizer"
    input_type = Column(Enum(CropInputTypeEnum), nullable=False)  # seed, fertilizer, pesticide, etc.
    unit = Column(String(20), nullable=False)  # kg, liter, bag, etc.
    current_stock = Column(Numeric(10, 2), default=0)  # How much is available now
    reorder_point = Column(Numeric(10, 2), nullable=True)  # When stock falls below this, alert user
    unit_cost = Column(Numeric(10, 2), nullable=True)  # Cost per unit in LRD
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())