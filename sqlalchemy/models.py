from typing import Annotated
from sqlalchemy import (
    Numeric,
    String,
    MetaData,
    Table,
    Column,
    Integer

)


from sqlalchemy.orm import Mapped, mapped_column
from database import Base

# intpk = Annotated[int, mapped_column(primary_key=True)]



class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    login = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    currency = Column(String(10), nullable=False)
    balance = Column(Numeric(12, 2), default=0)




metadata_obj = MetaData()



