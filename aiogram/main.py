from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.storage.memory import MemoryStorage

import os
from dotenv import load_dotenv

from handlers import user


load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

    

async def main():
        print("Bot started")
        await dp.start_polling(bot)
        


if __name__ == "__main__":    
    try:    
        import asyncio
        
        bot = Bot(token=TOKEN)
        dp = Dispatcher(storage=MemoryStorage())    
        dp.include_router(user)
        
        asyncio.run(main())
    except (KeyboardInterrupt):
        print("Bot stopped")