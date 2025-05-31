from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError

# Update with your actual MySQL credentials
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:ABCD%401234@localhost:3306/cairo_metro"

# Create the SQLAlchemy engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Session configuration
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


# Dependency for getting DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Optional: check database connection
if __name__ == "__main__":
    try:
        with engine.connect() as conn:
            print("✅ Database connection successful!")
    except OperationalError as e:
        print("❌ Failed to connect to database:", e)
