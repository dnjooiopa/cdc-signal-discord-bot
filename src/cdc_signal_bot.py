import discord
from discord.ext import commands
from datetime import datetime
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.cdc_factory import add_pairs, check_if_pairs_exists, generate_graph, get_availabel_pairs, get_historical_signal, init, refetch, get_signals_with_tf, get_all_signals
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

@bot.command()
async def send_graph(channel, pairs, tfName):

  tf = None
  tempTF = tfName.replace(' ', '')
  if tempTF == '12h' or tempTF == '12hours':
    tf = '43200'
  elif tempTF == '1d' or tempTF == '1day':
    tf = '86400'
  
  if tf is not None:
    msg = generate_graph(pairs, tf)
    if msg is None:
      image = discord.File(os.path.join(os.getcwd(), "data", 'graph.png'))
      await channel.send(file=image)
    else:
      await channel.send(msg)
  else:
    await channel.send(f'🔴 Wrong time frame : {tfName}\n✅ Availabel : 1d | 1days | 12h | 12hours')
  
@bot.event
async def on_ready():
  print("Bot Started!")

  scheduler = AsyncIOScheduler()
  scheduler.add_job(send_update_signal, CronTrigger(hour="0,12", minute="0", second="30"))

  scheduler.start()

@bot.event
async def on_message(message):
  print('Incoming message')
  print(message)

  msgContent = message.content
  msg = f'{UNKNOWN_MESSAGE}'
  sent = False
  if msgContent.startswith('!cdc') :
    contents = msgContent.split(' ')
    print('contents')
    print(contents)

    dayOffset = 0
    if len(contents) == 1:
      msg = f'🚷 {WELCOME_MESSAGE} 🚀🚀'
      msg += '\n\nℹ️ Use command below for more information.```!cdc info```'
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
      elif contents[1] == 'graph':
        await send_graph(message.channel, contents[2].lower(), '1d')
        sent = True
    elif len(contents) == 4:
      if contents[1] == 'graph':
        await send_graph(message.channel, contents[2].lower(), contents[3])
        sent = True

    if sent is False:
      await message.channel.send(msg)

def start():
  init()
  bot.run(BOT_TOKEN)