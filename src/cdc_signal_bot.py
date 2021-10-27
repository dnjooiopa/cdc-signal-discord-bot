from discord.ext import commands, tasks
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.cdc_factory import init, refetch, get_signals_with_tf, get_all_signals
from config import CRYPTO_CHANNEL, BOT_TOKEN

bot = commands.Bot(command_prefix='!cdc')

async def send_update_signal():
  now = datetime.now()
  current_time = now.strftime("%H:%M")
  current_date = now.strftime("%Y:%m:%d %H:%M:%S")

  refetch()
  print('Sending... update')
  msg = f'\n✅ Authomatic update: {current_date}'
  
  if current_time == "00:00":
    channel = bot.get_channel(int(CRYPTO_CHANNEL))
    msg += get_all_signals(0)
    await channel.send(msg)
  else:
    channel = bot.get_channel(int(CRYPTO_CHANNEL))
    msg += get_signals_with_tf('43200', 0)
    await channel.send(msg)
  
@bot.event
async def on_ready():
  print("Bot Started!")

  scheduler = AsyncIOScheduler()
  scheduler.add_job(send_update_signal, CronTrigger(hour="0, 12", minute="0", second="30"))

  scheduler.start()

@bot.event
async def on_message(message):
  print('Incoming message')
  print(message)

  msgContent = message.content
  msg = 'พิมพ์ให้ถูกดิ๊ ควย!!!'
  if msgContent.startswith('!cdc') :
    contents = msgContent.split(' ')
    print('contents')
    print(contents)

    dayOffset = 0
  
    if len(contents) == 2:
      if contents[1] == 'update':
        refetch()
      if contents[1] == 'future':
        dayOffset = 1

      msg = get_all_signals(dayOffset)
    else:
      msg = get_all_signals(0)
    await message.channel.send(msg)

def start():
  init()
  bot.run(BOT_TOKEN)