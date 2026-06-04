from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import authrouter as auth
from routers import field, harvest, planting, sales, reminder, crop_input, analytics, harvest_stock
from database.connection import engine, Base

app = FastAPI(title="Crop Management System API", version="1.0.0")

# CORS middleware (allows Next.js to call this API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://crop-management-system-olive.vercel.app"],  # Next.js default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.authrouter)
app.include_router(field.fieldrouter)
app.include_router(planting.plantingrouter)
app.include_router(harvest_stock.stockrouter)
app.include_router(harvest.harvestrouter)
app.include_router(sales.salesrouter)
app.include_router(reminder.reminderrouter)
app.include_router(crop_input.cropinputrouter)
app.include_router(analytics.analyticsrouter)
@app.on_event("startup")
async def startup():
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created/verified")

@app.get("/")
async def root():
    return {"message": "Crop Management System API", "status": "running"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}