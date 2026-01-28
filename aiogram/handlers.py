from decimal import Decimal
import asyncio
import random

from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext



from database import Base, session_factory, sync_engine
import keyboards as kb
from models import Account, Transaction
from states import RegStates, AuthStates, ActionStates, UserState, TransferStates
from services.security import hash_password, verify_password
from services.functions import get_rate, log_transaction, SUPPORTED_CURRENCIES, finish_registration




user = Router()




#########################
#        ПОЧАТОК        #
#########################

@user.message(Command("start"))
async def start(msg: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(UserState.before_loggin)
    await msg.answer("🏦 ATM Bot v2.0.0 вітає вас!", reply_markup=kb.before_loggin_kb)








#########################
#       ДО ВХОДУ        #
#########################




# --- БЛОК РЕЄСТРАЦІЇ ---

@user.message(F.text == "➕ Реєстрація", UserState.before_loggin)
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
    await msg.answer(
        f"💱 Оберіть валюту рахунку або введіть вручну з: {', '.join(SUPPORTED_CURRENCIES)}::",
        reply_markup=kb.currency_inline_kb
    )



@user.callback_query(RegStates.currency, F.data.startswith("currency_"))
async def reg_currency_inline(call: types.CallbackQuery, state: FSMContext):
    currency = call.data.split("_")[1]

    await finish_registration(
        msg=call.message,
        state=state,
        currency=currency
    )

    await call.answer()

@user.message(RegStates.currency)
async def reg_finish(msg: types.Message, state: FSMContext):
    await finish_registration(
        msg=msg,
        state=state,
        currency=msg.text.upper()
    )










# --- БЛОК ВХОДУ ---

@user.message(F.text == "🔑 Вхід", UserState.before_loggin)
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
        acc = session.query(Account).filter_by(login=data['login']).first()
        
        if acc and verify_password(msg.text, acc.password):
            await state.update_data(account_id=acc.id)
            
            await state.set_state(UserState.after_loggin) 
            
            await msg.answer(f"✅ Вітаємо, {acc.login}!", reply_markup=kb.after_loggin_kb)
        else:
            await msg.answer("❌ Помилка: логін або пароль невірні", reply_markup=kb.before_loggin_kb)
            await state.clear()
            await state.set_state(UserState.before_loggin)






#########################
#       ПІСЛЯ ВХОДУ     #
#########################



# --- ВИЙТИ З АКАУНТА---

@user.message(F.text == "🚪 Вийти", UserState.after_loggin)
async def logout(msg: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(UserState.before_loggin)
    await msg.answer("Ви вийшли з акаунта", reply_markup=kb.before_loggin_kb)




# --- Баланс ---

@user.message(F.text == "💰 Баланс", UserState.after_loggin)
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

@user.message(F.text == "➕ Поповнити", UserState.after_loggin)
async def deposit_start(msg: types.Message, state: FSMContext):
    await state.set_state(ActionStates.deposit_amount)
    await msg.answer("👉 Введіть суму поповнення:")


@user.message(ActionStates.deposit_amount)
async def deposit_finish(msg: types.Message, state: FSMContext):
    if not msg.text.replace(".", "", 1).isdigit():
        await msg.answer("❌ Невірне число", reply_markup=kb.after_loggin_kb)
        await state.set_state(UserState.after_loggin)
        return

    amount = Decimal(msg.text)
    
    if amount <= 0:
        await msg.answer("❌ Сума має бути більшою за 0", reply_markup=kb.after_loggin_kb)
        await state.set_state(UserState.after_loggin)
        return

    data = await state.get_data()
    with session_factory() as session:
        acc = session.get(Account, data["account_id"])
        acc.balance += amount
        session.commit()

    await msg.answer("✅ Рахунок поповнено", reply_markup=kb.after_loggin_kb)
    await state.set_state(UserState.after_loggin)
    
    
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






# --- РАНДОМНЕ ПОПОВНЕННЯ ---

@user.message(F.text == "➕ Поповнити (рандомне: 1-100)", UserState.after_loggin)
async def deposit_start(msg: types.Message, state: FSMContext):
    amount = Decimal(random.randint(1, 100))
    data = await state.get_data()
    with session_factory() as session:
        acc = session.get(Account, data["account_id"])
        acc.balance += amount
        session.commit()
    
        await msg.answer(f"✅ Рахунок поповнено на {amount} {acc.currency}", reply_markup=kb.after_loggin_kb)

    await state.set_state(UserState.after_loggin)

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

@user.message(F.text == "➖ Зняти", UserState.after_loggin)
async def withdraw_start(msg: types.Message, state: FSMContext):
    await state.set_state(ActionStates.withdraw_amount)
    await msg.answer("👉 Введіть суму зняття:")


@user.message(ActionStates.withdraw_amount)
async def withdraw_finish(msg: types.Message, state: FSMContext):
    if not msg.text.replace(".", "", 1).isdigit():
        await msg.answer("❌ Невірне число", reply_markup=kb.after_loggin_kb)
        await state.set_state(UserState.after_loggin)
        return

    amount = Decimal(msg.text)
    data = await state.get_data()

    with session_factory() as session:
        acc = session.get(Account, data["account_id"])
        if amount <= 0 or amount > acc.balance:
            await msg.answer("❌ Недостатньо коштів", reply_markup=kb.after_loggin_kb)
            await state.set_state(UserState.after_loggin)
            return

        acc.balance -= amount
        session.commit()

    await msg.answer("✅ Кошти знято", reply_markup=kb.after_loggin_kb)
    await state.set_state(UserState.after_loggin)

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

@user.message(F.text == "❌ Видалити рахунок", UserState.after_loggin)
async def delete_start(msg: types.Message, state: FSMContext):
    await state.set_state(ActionStates.delete_confirm_1)
    await msg.answer("⚠️ Введіть DELETE для підтвердження")


@user.message(ActionStates.delete_confirm_1)
async def delete_confirm_1(msg: types.Message, state: FSMContext):
    if msg.text != "DELETE":
        await msg.answer("❌ Скасовано", reply_markup=kb.after_loggin_kb)
        await state.set_state(UserState.after_loggin)
        return

    await state.set_state(ActionStates.delete_confirm_2)
    await msg.answer("⚠️ Напишіть пароль для підтвердження:")


@user.message(ActionStates.delete_confirm_2)
async def delete_confirm_2(msg: types.Message, state: FSMContext):
    data = await state.get_data()

    with session_factory() as session:
        acc = session.get(Account, data["account_id"])

        if not acc:
            await msg.answer("❌ Акаунт не знайдено")
            await state.clear()
            return

        # 🔐 перевірка пароля
        if not verify_password(msg.text, acc.password):
            await msg.answer("❌ Невірний пароль", reply_markup=kb.after_loggin_kb)
            await state.set_state(UserState.after_loggin)
            return

        # 1 ВИДАЛЯЄМО БЕЗЗМІСТОВНІ ТРАНЗАКЦІЇ
        session.query(Transaction).filter(
            Transaction.account_id == acc.id,
            Transaction.type.in_(["deposit", "withdraw"])
        ).delete(synchronize_session=False)

        # 2 ОНОВЛЮЄМО ПЕРЕКАЗИ, ДЕ ЦЕЙ АКАУНТ — ІНШИЙ БІК
        session.query(Transaction).filter(
            Transaction.related_account == acc.login
        ).update(
            {Transaction.related_account: "DELETED"},
            synchronize_session=False
        )

        # 3 ОНОВЛЮЄМО ВЛАСНІ ПЕРЕКАЗИ АКАУНТА
        session.query(Transaction).filter(
            Transaction.account_id == acc.id,
            Transaction.type.in_(["transfer_in", "transfer_out"])
        ).update(
            {
                Transaction.account_id: None,
                Transaction.login: "DELETED"
            },
            synchronize_session=False
        )

        # 4 ВИДАЛЯЄМО ПЕРЕКАЗИ, ДЕ ОБИДВА АКАУНТИ ВЖЕ ВИДАЛЕНІ
        session.query(Transaction).filter(
            Transaction.account_id == None,
            Transaction.related_account == "DELETED",
            Transaction.type.in_(["transfer_in", "transfer_out"])
        ).delete(synchronize_session=False)



        # 5 ВИДАЛЯЄМО САМ АКАУНТ
        session.delete(acc)
        session.commit()

    await state.clear()
    await state.set_state(UserState.before_loggin)
    await msg.answer("🗑️ Рахунок та історія оновлені", reply_markup=kb.before_loggin_kb)













# --- ПЕРЕКАЗ ---

@user.message(F.text == "🔁 Переказ", UserState.after_loggin)
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
        await msg.answer("❌ Невірне число", reply_markup=kb.after_loggin_kb)
        await state.set_state(UserState.after_loggin)
        return

    amount = Decimal(msg.text)
    if amount <= 0:
        await msg.answer("❌ Сума має бути більшою за 0", reply_markup=kb.after_loggin_kb)
        await state.set_state(UserState.after_loggin)
        return

    data = await state.get_data()

    with session_factory() as session:
        sender = session.get(Account, data["account_id"])
        receiver = session.query(Account).filter_by(login=data["target_login"]).first()

        if not receiver:
            await msg.answer("❌ Отримувача не знайдено", reply_markup=kb.after_loggin_kb)
            await state.set_state(UserState.after_loggin)
            return

        if sender.balance < amount:
            await msg.answer("❌ Недостатньо коштів", reply_markup=kb.after_loggin_kb)
            await state.set_state(UserState.after_loggin)
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
            reply_markup=kb.after_loggin_kb
        )

    await state.set_state(UserState.after_loggin)

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







# --- Історія транзакцій --- 

@user.message(F.text == "📜 Історія", UserState.after_loggin)
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















#--- Невідома команда ---

@user.message(F.text, UserState.after_loggin)
async def logout(msg: types.Message, state: FSMContext):
    await msg.answer("❌ Невідома команда", reply_markup=kb.after_loggin_kb)

@user.message(F.text)
async def logout(msg: types.Message, state: FSMContext):
    await msg.answer("❌ Невідома команда", reply_markup=kb.before_loggin_kb)