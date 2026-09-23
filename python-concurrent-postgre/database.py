from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from models import Base

# The standard format: postgresql+driver://user:password@host:port/dbname
DATABASE_URL = "postgresql+asyncpg://postgres:yourpassword@localhost:5432/powder_db"

# 1. Create the Async Engine
engine = create_async_engine(DATABASE_URL, echo=False)

# 2. Create the Async Session Maker
AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# 3. FastAPI Dependency
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session