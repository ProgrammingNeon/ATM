from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy import create_engine
from config import settings

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

class Base(DeclarativeBase):
    pass

sync_engine = create_engine(
    url=settings.DATABASE_URL_psycopg,
    echo=False,
    
    # pool_size=5,
    # max_overflow=10,
)
session_factory = sessionmaker(sync_engine,expire_on_commit=False,)


"""create async engine and session factory."""
# async_engine = create_async_engine(
#     url=settings.DATABASE_URL_asyncpg,
#     echo=False,
# )

# async_session_factory = async_sessionmaker(async_engine)

""""create all tables in the database. (for 1 time use)"""
# def create_tables_for_1_time():
#     # Цей рядок видалить старі таблиці (обережно!) і створить нові за моделями
#     Base.metadata.drop_all(sync_engine)
#     Base.metadata.create_all(sync_engine)
#     print("Таблиці успішно створені!")
# create_tables_for_1_time()





"""create all tables in the database."""
# if __name__ == "__main__":
#     Base.metadata.create_all(sync_engine)