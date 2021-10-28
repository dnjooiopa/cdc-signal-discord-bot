from discord.ext import commands
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.cdc_factory import add_pairs, check_if_pairs_exists, get_availabel_pairs, get_historical_signal, init, refetch, get_signals_with_tf, get_all_signals
from config import CRYPTO_CHANNEL, BOT_TOKEN, UNKNOWN_MESSAGE, WELCOME_MESSAGE

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
  msg = f'{UNKNOWN_MESSAGE}'
  if msgContent.startswith('!cdc') :
    contents = msgContent.split(' ')
    print('contents')
    print(contents)

    dayOffset = 0

    if len(contents) == 1:
      msg = f'🚀🚀 {WELCOME_MESSAGE}'
      msg += '\nFor more infomation ```!cdc info```'
      msg += get_all_signals(0)
    if len(contents) == 2:
      if contents[1] == 'update':
        refetch()
        msg = get_all_signals(dayOffset)
      elif contents[1] == 'future':
        dayOffset = 1
        msg = get_all_signals(dayOffset)
      elif contents[1] == 'pairs' or contents[1] == 'list':
        msg = get_availabel_pairs()
      elif contents[1] == 'info':
        msg = 'รอก่อน กำลังทำ...'
    elif len(contents) == 3:
      if contents[1] == 'history':
        msg = get_historical_signal(contents[2].lower())
      elif contents[1] == 'add':
        msg = add_pairs(contents[2].lower())
      elif contents[1] == 'check':
        msg = check_if_pairs_exists(contents[2].lower())

    await message.channel.send(msg)

def start():
  init()
  bot.run(BOT_TOKEN)