from cdc_factory import init, refetch, get_signals_with_tf, get_all_signals
from config import BOT_TOKEN

import threading
from datetime import datetime

init()

from discord.ext import commands
bot = commands.Bot(command_prefix='!cdc')

@bot.event
async def on_ready():
  print("Bot Started!")

@bot.event
async def on_message(message) :
  msgContent = message.content
  msg = 'พิมพ์ให้ถูกดิ๊ ควย!!!'
  if msgContent.startswith('!cdc') :
    contents = msgContent.split(' ')
    print(message)
    print('Incoming message:', contents)
    if len(contents) == 2:
      if contents[1] == 'signal':
        msg = get_all_signals(0)
      if contents[1] == 'update':
        refetch()
        msg = get_all_signals(0)
    else:
      msg = get_all_signals(0)
    await message.channel.send(msg)

def runThread():
    # This function runs periodically every 1 second
    threading.Timer(1, runThread).start()

    now = datetime.now()

    current_time = now.strftime("%H:%M:%S")
    print("\rCurrent Time =", current_time)

    if(current_time == '00:00:30'):  # check if matches with the desired time
        channel = bot.get_channel(902555809580449822)
        refetch()
        msg = get_all_signals(0)
        channel.send(msg)
#runThread()

bot.run(BOT_TOKEN)