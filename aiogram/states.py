from aiogram.fsm.state import StatesGroup, State


#--- ДО ВХОДУ ---

class RegStates(StatesGroup):
    login = State()
    password = State()
    currency = State()


class AuthStates(StatesGroup):
    login = State()
    password = State()


#--- ПІСЛЯ ВХОДУ ---

class UserState(StatesGroup):
    after_loggin = State()
    before_loggin = State()



class ActionStates(StatesGroup):
    amount = State()
    deposit_amount = State()
    withdraw_amount = State()
    delete_confirm_1 = State()
    delete_confirm_2 = State()


class TransferStates(StatesGroup):
    target_login = State()
    amount = State()