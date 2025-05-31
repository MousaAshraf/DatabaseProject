from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager
from db.database import SessionLocal
from db.models import User
from core.security import get_password_hash
from routers import auth, tickets, subscriptions, user, payment, stations

from admin import setup_admin


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Metro System API",
        version="1.0.0",
        description="Metro system backend with JWT Auth",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "jwtAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    for path in openapi_schema["paths"].values():
        for method in path.values():
            method["security"] = [{"jwtAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create initial admin user
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.is_admin).first():
            admin = User(
                username="Admin",
                FirstName="Admin",
                LastName="Admin",
                Email="admin@cairometro.com",
                password=get_password_hash("admin123"),
                phone="+201234567890",
                Role="admin",
                is_admin=True,
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()
    yield


app = FastAPI(lifespan=lifespan)
app.openapi = custom_openapi

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(tickets.router)
app.include_router(subscriptions.router)
app.include_router(payment.router)
app.include_router(stations.router)


@app.get("/")
def read_root():
    return {"message": "Cairo Metro API"}


setup_admin(app)
