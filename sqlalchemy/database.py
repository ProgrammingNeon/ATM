from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy import create_engine
from config import settings



sync_engine = create_engine(
    url=settings.DATABASE_URL_psycopg,
    echo=False,
    # pool_size=5,
    # max_overflow=10,
)
session_factory = sessionmaker(sync_engine)


class Base(DeclarativeBase):
    pass



"""create async engine and session factory."""
# async_engine = create_async_engine(
#     url=settings.DATABASE_URL_asyncpg,
#     echo=False,
# )

# async_session_factory = async_sessionmaker(async_engine)



"""create all tables in the database."""
# if __name__ == "__main__":
#     Base.metadata.create_all(sync_engine)