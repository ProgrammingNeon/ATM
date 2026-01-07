from decimal import Decimal
from sqlalchemy.exc import IntegrityError
import getpass

from database import Base, sync_engine, session_factory
from models import Account

import requests

EXCHANGE_API_URL = "https://open.er-api.com/v6/latest"
SUPPORTED_CURRENCIES = ["USD", "EUR", "UAH", "GBP", "JPY"] 

class SyncORM:
    @staticmethod
    def main():
        while True:
            print("\n=== ATM ===")
            print("1 - Створити рахунок")
            print("2 - Увійти")
            print("3 - Видалити рахунок")
            print("0 - Вихід")

            choice = input("> ")

            if choice == "1":
                SyncORM.register()
            elif choice == "2":
                SyncORM.login()
            elif choice == "3":
                SyncORM.delete_account()
            elif choice == "0":
                break
            else:
                print("❌ Невірний вибір") 
    
    


    @staticmethod
    def register():
        with session_factory() as session:
            print("\n=== Реєстрація ===")
            login = input("Логін: ")
            password = getpass.getpass("Пароль: ")
            

            # Валідація валюти
            while True:
                currency = input(f"Валюта рахунку ({', '.join(SUPPORTED_CURRENCIES)}): ").upper()
                if currency in SUPPORTED_CURRENCIES:
                    break  
                else:
                    print(f"❌ Непідтримувана валюта. Будь ласка, введіть одну з: {', '.join(SUPPORTED_CURRENCIES)}")
            
            
            account = Account(
                login=login,
                password=password,
                currency=currency,
                balance=0
            )

            try:
                session.add(account)
                session.commit()
                print("✅ Рахунок успішно створено")
            except IntegrityError:
                session.rollback()
                print("❌ Логін вже існує")

    @staticmethod
    def login():
        with session_factory() as session:

            print("\n=== Вхід ===")
            login = input("Логін: ")
            password = getpass.getpass("Пароль: ")

            account = session.query(Account).filter_by(login=login, password=password).first()
            if not account:
                print("❌ Невірний логін або пароль")
                return

            print(f"\n✅ Вхід виконано. Баланс: {account.balance} {account.currency}")
            SyncORM.account_menu(session, account)

    



    @staticmethod
    def account_menu(session, account):
    
        while True:
            print("\n1 - Поповнити рахунок")
            print("2 - Зняти гроші")
            print("3 - Показати баланс")
            print("4 - Конвертувати валюту")
            print("5 - Переказ між рахунками")

            print("0 - Вийти")

            choice = input("> ")

            if choice == "1":
                # Конвертуємо введення в Decimal замість float
                amount = Decimal(input("Сума поповнення: ")) 
                account.balance += amount
                session.commit()
                print("✅ Рахунок поповнено")

            elif choice == "2":
                amount = Decimal(input("Сума зняття: "))
                if amount > account.balance:
                    print("❌ Недостатньо коштів")
                else:
                    account.balance -= amount
                    session.commit()
                    print("✅ Гроші знято")

            elif choice == "3":
                print(f"💰 Баланс: {account.balance} {account.currency}")
            elif choice == "4":
                SyncORM.convert_and_transfer(session, account)
            elif choice == "5":
                SyncORM.transfer_between_accounts(session, account)

            elif choice == "0":
                break






    @staticmethod
    def get_exchange_rate(from_currency: str, to_currency: str) -> float:
        """Отримати актуальний курс через open.er-api.com (актуально для 2026)"""
        try:
            # Формат цього API: open.er-api.com
            url = f"https://open.er-api.com/v6/latest/{from_currency}"
            response = requests.get(url, timeout=10)  # Додаємо таймаут для стабільності
            
            if response.status_code != 200:
                raise Exception(f"API статус код: {response.status_code}")

            data = response.json()

            if data.get("result") == "success":
                rates = data.get("rates", {})
                if to_currency in rates:
                    return Decimal(rates[to_currency])
                else:
                    raise Exception(f"Валюта {to_currency} не знайдена в списку")
            else:
                raise Exception(f"Помилка API: {data.get('error-type', 'unknown')}")

        except requests.exceptions.RequestException as e:
            raise Exception(f"Помилка мережі: {e}")
        except Exception as e:
            raise Exception(f"Помилка отримання курсу: {e}")

    @staticmethod
    def convert_and_transfer(session, from_account):
        print("\n    === Конвертація валюти ===")
        target_login = input("Логін рахунку для зарахування: ")

        target_account = session.query(Account).filter_by(login=target_login).first()
        if not target_account:
            print("❌ Рахунок не знайдено")
            return

        if target_account.currency == from_account.currency:
            print("❌ Валюти рахунків однакові")
            return

        amount = Decimal(input(f"Сума для конвертації ({from_account.currency}): "))

        if amount > from_account.balance:
            print("❌ Недостатньо коштів")
            return

        try:
            rate = SyncORM.get_exchange_rate(from_account.currency, target_account.currency)
        except Exception as e:
            print(f"❌ {e}")
            return

        converted_amount = round(amount * Decimal(str(rate)), 2)

        from_account.balance -= amount
        target_account.balance += converted_amount

        session.commit()

        print(
            f"✅ Конвертація успішна: {amount} {from_account.currency} → "
            f"{converted_amount} {target_account.currency} (курс: {rate})"
        )
                    








    @staticmethod
    def delete_account():
        with session_factory() as session:
            print("\n=== Видалення рахунку ===")

            login = input("Логін: ")
            password = getpass.getpass("Пароль: ")

            account = session.query(Account).filter_by(
                login=login,
                password=password
            ).first()

            if not account:
                print("❌ Невірний логін або пароль")
                return

            confirm1 = input("❗ Ви впевнені? (yes/no): ").lower()
            if confirm1 != "yes":
                print("❌ Видалення скасовано")
                return

            confirm2 = input("❗ Підтвердіть ще раз (yes/no): ").lower()
            if confirm2 != "yes":
                print("❌ Видалення скасовано")
                return

            session.delete(account)
            session.commit()

            print("✅ Рахунок успішно видалено")








    @staticmethod
    def transfer_between_accounts(session, from_account):
        print("\n=== Переказ між рахунками ===")

        target_login = input("Логін отримувача: ")
        target_account = session.query(Account).filter_by(login=target_login).first()

        if not target_account:
            print("❌ Рахунок отримувача не знайдено")
            return

        if target_account.id == from_account.id:
            print("❌ Неможливо переказати самому собі")
            return

        if target_account.currency != from_account.currency:
            print("❌ Валюти рахунків різні (конвертація не дозволена)")
            return

        amount = Decimal(input(f"Сума переказу ({from_account.currency}): "))

        if amount <= 0:
            print("❌ Некоректна сума")
            return

        if amount > from_account.balance:
            print("❌ Недостатньо коштів")
            return

        from_account.balance -= amount
        target_account.balance += amount
        session.commit()

        print(
            f"✅ Переказ успішний: {amount} {from_account.currency} → {target_account.login}"
        )
























    """"create all tables in the database. (for 1 time use)"""
    @staticmethod
    def create_tables_for_1_time():
        # Цей рядок видалить старі таблиці (обережно!) і створить нові за моделями
        # Base.metadata.drop_all(sync_engine)
        Base.metadata.create_all(sync_engine)
        print("Таблиці успішно створені!")



