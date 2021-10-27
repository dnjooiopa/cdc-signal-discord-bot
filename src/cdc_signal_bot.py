from src.cdc_factory import init, refetch, get_signals_with_tf, get_all_signals
from config import CRYPTO_CHANNEL

import threading
from datetime import datetime

init()

from discord.ext import commands
bot = commands.Bot(command_prefix='!cdc')


def runThread():
    threading.Timer(1, runThread).start()

    now = datetime.now()

    current_time = now.strftime("%H:%M:%S")
    current_date = now.strftime("%Y:%m%:%d")

    print("\rCurrent Time =", current_time)
    if(current_time == '00:00:24'): 
        refetch()
        print(f'Sending... update for {current_date}')
        channel = bot.get_channel(int(CRYPTO_CHANNEL))
        msg = get_all_signals(0)
        channel.send(msg)

@bot.event
async def on_ready():
  print("Bot Started!")
  runThread()

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

    if len(contents) >= 3:
      if contents[2] == 'future':
        dayOffset = 1
    if len(contents) >= 2:
      if contents[1] == 'signal':
        msg = get_all_signals(dayOffset)
      if contents[1] == 'update':
        refetch()
        msg = get_all_signals(dayOffset)
    else:
      msg = get_all_signals(0)
    await message.channel.send(msg)

