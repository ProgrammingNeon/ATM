from typing import Annotated
from sqlalchemy import (
    Numeric,
    String,
    MetaData,
    Table,
    Column,
    Integer
    
)

from sqlalchemy.orm import relationship

from sqlalchemy.orm import Mapped, mapped_column
from database import Base


from sqlalchemy import ForeignKey, DateTime
from datetime import datetime


# intpk = Annotated[int, mapped_column(primary_key=True)]



class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    login = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    currency = Column(String(10), nullable=False)
    balance = Column(Numeric(12, 2), default=0)

    transactions = relationship(
        "Transaction",
        passive_deletes=True
    )

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)


    account_id = Column(
        Integer,
        ForeignKey("accounts.id", ondelete="SET NULL"),
        nullable=True
    )

    login = Column(String(50), nullable=False)
    type = Column(String(20), nullable=False)

    amount = Column(Numeric(12, 2), nullable=False)
    balance = Column(Numeric(12, 2), nullable=False)

    currency = Column(String(10), nullable=False)
    related_account = Column(String(50), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)



metadata_obj = MetaData()



