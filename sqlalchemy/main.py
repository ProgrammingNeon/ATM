#py -m venv venv
#venv\Scripts\activate

from queries.orm import SyncORM

def try_convert():
    try:
        rate = SyncORM.get_exchange_rate("USD", "UAH")
        print(f"Поточний курс USD/UAH: {rate}")
    except Exception as e:
        print(f"❌ Не вдалося отримати курс: {e}")



if __name__ == "__main__":
    SyncORM.main()