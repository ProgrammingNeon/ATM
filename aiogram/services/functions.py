#########################
#   ВАЖЛИВІ ФУНКЦІЇ     #
#########################
    

from decimal import Decimal
import asyncio
import requests


from models import Account, Transaction

EXCHANGE_API_URL = "https://open.er-api.com/v6/latest/"



async def log_transaction(
    session,
    account_id: int,
    login: str,
    type_: str,
    amount: Decimal,
    balance: Decimal,
    currency: str,
    related_account: str | None = None
    
):
    tx = Transaction(
        account_id=account_id,
        login=login,
        type=type_,
        amount=amount,
        balance=balance,
        currency=currency,
        related_account=related_account
    )
    session.add(tx)
    session.commit()




def get_rate(frm: str, to: str) -> Decimal:   
    r = requests.get(f"{EXCHANGE_API_URL}{frm}").json()
    if r.get("result") != "success":
        raise Exception("API error")
    return Decimal(r["rates"][to])
