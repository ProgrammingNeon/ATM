#########################
#   ВАЖЛИВІ ФУНКЦІЇ     #
#########################
    

from decimal import Decimal
import asyncio
import requests


from aiogram import types
from aiogram.fsm.context import FSMContext



from database import session_factory, sync_engine
import keyboards as kb
from models import Account, Transaction
from states import UserState
from services.security import hash_password




EXCHANGE_API_URL = "https://open.er-api.com/v6/latest/"

SUPPORTED_CURRENCIES = ["USD", "EUR", "UAH", "GBP", "JPY"] 


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



async def finish_registration(msg: types.Message, state: FSMContext, currency: str):
    user_data = await state.get_data()

    if currency not in SUPPORTED_CURRENCIES:
        await msg.answer(
            f"❌ Непідтримувана валюта. Доступні: {', '.join(SUPPORTED_CURRENCIES)}",
            reply_markup=kb.before_loggin_kb
        )
        await state.set_state(UserState.before_loggin)
        return

    with session_factory() as session:
        acc = session.query(Account).filter_by(login=user_data["login"]).first()

        if acc:
            await msg.answer(
                "❌ Такий логін вже існує, спробуйте інший",
                reply_markup=kb.before_loggin_kb
            )
            await state.set_state(UserState.before_loggin)
            return

        new_acc = Account(
            login=user_data["login"],
            password=hash_password(user_data["password"]),
            currency=currency,
            balance=0
        )

        session.add(new_acc)
        session.commit()

    await msg.answer(
        f"✅ Рахунок для {user_data['login']} створено!",
        reply_markup=kb.before_loggin_kb
    )
    await state.clear()
    await state.set_state(UserState.before_loggin)