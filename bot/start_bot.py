import asyncio
import sys

from bot.main import MainBot



bot = MainBot()
print('START BOT')
asyncio.run(bot.main())
