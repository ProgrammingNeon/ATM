from decimal import Decimal
import asyncio
import requests
import os
import random

from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext



from database import Base, session_factory, sync_engine
import keyboards as kb
from models import Account, Transaction
from states import RegStates, AuthStates, ActionStates, UserState, TransferStates


EXCHANGE_API_URL = "https://open.er-api.com/v6/latest/"
user = Router()





#########################
#   ВАЖЛИВІ ФУНКЦІЇ     #
#########################
    

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





# --- ВХІД ---

@user.message(Command("start"))
async def start(msg: types.Message, state: FSMContext):
    await state.clear() 
    await msg.answer("🏦 ATM Bot v2.0.0 вітає вас!", reply_markup=kb.main_kb)











#########################
#       ДО ВХОДУ        #
#########################

# --- БЛОК РЕЄСТРАЦІЇ ---

@user.message(F.text == "➕ Реєстрація")
async def reg_start(msg: types.Message, state: FSMContext):
    await state.set_state(RegStates.login)
    await msg.answer("📝 Введіть бажаний логін:")

@user.message(RegStates.login)
async def reg_login(msg: types.Message, state: FSMContext):
    await state.update_data(login=msg.text)
    await state.set_state(RegStates.password)
    await msg.answer("🔑 Введіть пароль:")

@user.message(RegStates.password)
async def reg_password(msg: types.Message, state: FSMContext):
    await state.update_data(password=msg.text)
    await state.set_state(RegStates.currency)
    await msg.answer("💱 Оберіть валюту (USD, EUR, UAH):")

@user.message(RegStates.currency)
async def reg_finish(msg: types.Message, state: FSMContext):
    user_data = await state.get_data()
    
    with session_factory() as session:
        new_acc = Account(
            login=user_data['login'],
            password=user_data['password'],
            currency=msg.text.upper(),
            balance=0
        )
        session.add(new_acc)
        session.commit()
    
    await msg.answer(f"✅ Рахунок для {user_data['login']} створено!", reply_markup=kb.main_kb)
    await state.clear()












# --- БЛОК ВХОДУ ---

@user.message(F.text == "🔑 Вхід")
async def login_start(msg: types.Message, state: FSMContext):
    await state.set_state(AuthStates.login)
    await msg.answer("👤 Введіть логін:")

@user.message(AuthStates.login)
async def login_nm(msg: types.Message, state: FSMContext):
    await state.update_data(login=msg.text)
    await state.set_state(AuthStates.password)
    await msg.answer("🔒 Введіть пароль:")

@user.message(AuthStates.password)
async def login_finish(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    
    with session_factory() as session:
        acc = session.query(Account).filter_by(login=data['login'], password=msg.text).first()
        
        if acc:
            # Зберігаємо ID акаунта
            await state.update_data(account_id=acc.id)
            
            # ВАЖЛИВО: Переводимо користувача у нейтральний стан
            await state.set_state(UserState.main_menu) 
            
            await msg.answer(f"✅ Вітаємо, {acc.login}!", reply_markup=kb.account_kb)
        else:
            await msg.answer("❌ Помилка: логін або пароль невірні", reply_markup=kb.main_kb)
            await state.clear()






#########################
#       ПІСЛЯ ВХОДУ     #
#########################



# --- ВИЙТИ З АКАУНТА---

@user.message(F.text == "🚪 Вийти", UserState.main_menu)
async def logout(msg: types.Message, state: FSMContext):
    await state.clear()
    await msg.answer("Ви вийшли з акаунта", reply_markup=kb.main_kb)




# --- Баланс ---

@user.message(F.text == "💰 Баланс", UserState.main_menu)
async def check_balance(msg: types.Message, state: FSMContext):
    #await check_balancef(msg=msg, state=state)
    
    
    data = await state.get_data()
    #print(data)
    with session_factory() as session:
        acc = session.get(Account, data['account_id'])
        if acc:
            await msg.answer(f"💳 Ваш баланс: {acc.balance} {acc.currency}")
        else:
            await msg.answer("❌ Помилка доступу до даних.")








# --- ПОПОВНЕННЯ ---

@user.message(F.text == "➕ Поповнити", UserState.main_menu)
async def deposit_start(msg: types.Message, state: FSMContext):
    await state.set_state(ActionStates.deposit_amount)
    await msg.answer("👉 Введіть суму поповнення:")


@user.message(ActionStates.deposit_amount)
async def deposit_finish(msg: types.Message, state: FSMContext):
    if not msg.text.replace(".", "", 1).isdigit():
        await msg.answer("❌ Невірне число", reply_markup=kb.account_kb)
        await state.set_state(UserState.main_menu)
        return

    amount = Decimal(msg.text)
    
    if amount <= 0:
        await msg.answer("❌ Сума має бути більшою за 0", reply_markup=kb.account_kb)
        await state.set_state(UserState.main_menu)
        return

    data = await state.get_data()
    with session_factory() as session:
        acc = session.get(Account, data["account_id"])
        acc.balance += amount
        session.commit()

    await msg.answer("✅ Рахунок поповнено", reply_markup=kb.account_kb)
    await state.set_state(UserState.main_menu)
    
    
    await check_balance(msg=msg, state=state)

    await log_transaction(
        session,
        acc.account_id,
        acc.login,
        "deposit",
        amount,
        acc.balance,
        acc.currency
    )   



# --- РАНДОМНЕ ПОПОВНЕННЯ ---

@user.message(F.text == "➕ Поповнити (рандомне: 1-100)", UserState.main_menu)
async def deposit_start(msg: types.Message, state: FSMContext):
    amount = Decimal(random.randint(1, 100))
    data = await state.get_data()
    with session_factory() as session:
        acc = session.get(Account, data["account_id"])
        acc.balance += amount
        session.commit()
    
        await msg.answer(f"✅ Рахунок поповнено на {amount} {acc.currency}", reply_markup=kb.account_kb)

    await state.set_state(UserState.main_menu)

    await check_balance(msg=msg, state=state)

    await log_transaction(
        session,
        acc.id,
        acc.login,
        "deposit",
        amount,
        acc.balance,
        acc.currency
    ) 


# --- ЗНЯТТЯ ---

@user.message(F.text == "➖ Зняти", UserState.main_menu)
async def withdraw_start(msg: types.Message, state: FSMContext):
    await state.set_state(ActionStates.withdraw_amount)
    await msg.answer("👉 Введіть суму зняття:")


@user.message(ActionStates.withdraw_amount)
async def withdraw_finish(msg: types.Message, state: FSMContext):
    if not msg.text.replace(".", "", 1).isdigit():
        await msg.answer("❌ Невірне число", reply_markup=kb.account_kb)
        await state.set_state(UserState.main_menu)
        return

    amount = Decimal(msg.text)
    data = await state.get_data()

    with session_factory() as session:
        acc = session.get(Account, data["account_id"])
        if amount <= 0 or amount > acc.balance:
            await msg.answer("❌ Недостатньо коштів", reply_markup=kb.account_kb)
            await state.set_state(UserState.main_menu)
            return

        acc.balance -= amount
        session.commit()

    await msg.answer("✅ Кошти знято", reply_markup=kb.account_kb)
    await state.set_state(UserState.main_menu)

    await check_balance(msg=msg, state=state)


    await log_transaction(
        session,
        acc.id,
        acc.login,
        "withdraw",
        amount,
        acc.balance,
        acc.currency
    ) 






# --- ВИДАЛЕННЯ РАХУНКУ ---

@user.message(F.text == "❌ Видалити рахунок", UserState.main_menu)
async def delete_start(msg: types.Message, state: FSMContext):
    await state.set_state(ActionStates.delete_confirm_1)
    await msg.answer("⚠️ Введіть DELETE для підтвердження")


@user.message(ActionStates.delete_confirm_1)
async def delete_confirm_1(msg: types.Message, state: FSMContext):
    if msg.text != "DELETE":
        await msg.answer("❌ Скасовано", reply_markup=kb.account_kb)
        await state.set_state(UserState.main_menu)
        return

    await state.set_state(ActionStates.delete_confirm_2)
    await msg.answer("⚠️ Підтвердіть ще раз: DELETE")


@user.message(ActionStates.delete_confirm_2)
async def delete_confirm_2(msg: types.Message, state: FSMContext):
    if msg.text != "DELETE":
        await msg.answer("❌ Скасовано", reply_markup=kb.account_kb)
        await state.set_state(UserState.main_menu)
        return

    data = await state.get_data()
    
    with session_factory() as session:
        acc = session.get(Account, data["account_id"])
        session.delete(acc)
        session.commit()

    await state.clear()
    await msg.answer("🗑️ Рахунок видалено", reply_markup=kb.main_kb)













# --- ПЕРЕКАЗ ---

@user.message(F.text == "🔁 Переказ", UserState.main_menu)
async def transfer_start(msg: types.Message, state: FSMContext):
    await state.set_state(TransferStates.target_login)
    await msg.answer("Введіть логін отримувача:")


@user.message(TransferStates.target_login)
async def transfer_target(msg: types.Message, state: FSMContext):
    await state.update_data(target_login=msg.text)
    await state.set_state(TransferStates.amount)
    await msg.answer("Введіть суму переказу:")


@user.message(TransferStates.amount)
async def transfer_finish(msg: types.Message, state: FSMContext):
    if not msg.text.replace(".", "", 1).isdigit():
        await msg.answer("❌ Невірне число", reply_markup=kb.account_kb)
        await state.set_state(UserState.main_menu)
        return

    amount = Decimal(msg.text)
    if amount <= 0:
        await msg.answer("❌ Сума має бути більшою за 0", reply_markup=kb.account_kb)
        await state.set_state(UserState.main_menu)
        return

    data = await state.get_data()

    with session_factory() as session:
        sender = session.get(Account, data["account_id"])
        receiver = session.query(Account).filter_by(login=data["target_login"]).first()

        if not receiver:
            await msg.answer("❌ Отримувача не знайдено")
            return

        if sender.balance < amount:
            await msg.answer("❌ Недостатньо коштів")
            return

        final_amount = Decimal(amount)

        if sender.currency != receiver.currency:
            await msg.answer("Рахунок отримувача має іншу валюту, тому переказ буде конвертований за актуальним курсом")
            rate = get_rate(sender.currency, receiver.currency)
            final_amount = round(amount * rate, 2)

        sender.balance -= amount
        receiver.balance += final_amount
        session.commit()

        await msg.answer(
            f"✅ Переказ виконано\n"
            f"{amount} {sender.currency} → {final_amount} {receiver.currency}",
            reply_markup=kb.account_kb
        )

    await state.set_state(UserState.main_menu)

    await log_transaction(
        session,
        sender.id,
        sender.login,
        "transfer_out",
        amount,
        sender.balance,
        sender.currency,
        receiver.login
    )

    await log_transaction(
        session,
        receiver.id,
        receiver.login,
        "transfer_in",
        final_amount,
        receiver.balance,
        receiver.currency,
        sender.login
    )









@user.message(F.text == "📜 Історія", UserState.main_menu)
async def history(msg: types.Message, state: FSMContext):
    data = await state.get_data()

    with session_factory() as session:
        txs = (
            session.query(Transaction)
            .filter_by(account_id=data["account_id"])
            .order_by(Transaction.created_at.desc())
            .limit(13)
            .all()
        )

    if not txs:
        await msg.answer("Історія порожня")
        return

    text = "📜 Останні транзакції:\n\n"

    for tx in txs:
        text += (
            f"{tx.created_at:%d.%m %H:%M} | "
            f"{tx.type} | "
            f"{tx.amount} {tx.currency}"
        )
        if tx.related_account:
            text += f" → {tx.related_account}"
        text += "\n"

    await msg.answer(text)

















@user.message(F.text, UserState.main_menu)
async def logout(msg: types.Message, state: FSMContext):
    await msg.answer("❌ Невідома команда", reply_markup=kb.account_kb)

@user.message(F.text)
async def logout(msg: types.Message, state: FSMContext):
    await msg.answer("❌ Невідома команда", reply_markup=kb.main_kb)