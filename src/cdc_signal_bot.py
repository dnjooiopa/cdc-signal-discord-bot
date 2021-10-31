import discord
from discord.ext import commands
from datetime import datetime
import os
import time

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.cdc_factory import add_pairs, check_pairs, generate_graph, get_availabel_exchange, get_availabel_pairs, get_historical_signal, init, refetch, get_signals_with_tf, get_all_signals
from config import CRYPTO_CHANNEL, BOT_TOKEN, UNKNOWN_MESSAGE, WELCOME_MESSAGE, HOUR, MINUTE, SECOND, ADMIN_ID

bot = commands.Bot(command_prefix='!cdc')

def get_local_time(timestamp):
  localTimestamp = timestamp + (7*60*60)
  return datetime.utcfromtimestamp(localTimestamp).strftime("%Y:%m:%dT%H:%M:%S")

async def send_update_signal():
  timestamp = time.time()
  currentUTCTime = datetime.utcfromtimestamp(timestamp).strftime("%H:%M")
  
  currentLocalTime = get_local_time(timestamp)

  refetch()
  print('Sending... update')
  msg = f'\n✅ Authomatic update: {currentLocalTime}'
  
  if currentUTCTime == "00:00":
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
  scheduler.add_job(send_update_signal, CronTrigger(hour=HOUR, minute=MINUTE, second=SECOND))

  scheduler.start()

@bot.event
async def on_message(message):
  print('Incoming message')
  print(message)

  msgContent = message.content
  msg = f'{UNKNOWN_MESSAGE}'
  sent = False
  if msgContent.startswith('!cdc') :
    commands = msgContent.split(' ')
    print('contents')
    print(commands)

    if len(commands) == 1:
      msg = f'🚷 {WELCOME_MESSAGE} 🚀🚀'
      msg += '\n\nℹ️ Use command below for more information.```!cdc info```'
      msg += get_all_signals(0)
    elif len(commands) == 2:
      if commands[1] == 'update':
        refetch()
        msg = get_all_signals(0)
      elif commands[1] == 'future':
        msg = get_all_signals(1)
      elif commands[1] == 'pairs' or commands[1] == 'list':
        msg = get_availabel_pairs()
      elif commands[1] == 'info':
        msg = 'รอก่อน กำลังทำ...'
      elif commands[1] == 'checktime':
        timestamp = time.time()
        currentLocalTime = get_local_time(timestamp)
        msg = '⏱  ' + currentLocalTime
      elif commands[1] == 'exchange' or commands[1] == 'exchanges' or commands[1] == 'ex':
        msg = get_availabel_exchange()
    elif len(commands) == 3:
      if commands[1] == 'history':
        msg = get_historical_signal(commands[2].lower())
      elif commands[1] == 'add':
        msg = add_pairs(commands[2].lower())
      elif commands[1] == 'check':
        msg = check_pairs(commands[2].lower())
      elif commands[1] == 'graph':
        await send_graph(message.channel, commands[2], '1d')
        sent = True 
      elif commands[1] == 'remove' or commands[1] == 'rm':
        msg = 'removing ...'
    elif len(commands) == 4:
      if commands[1] == 'graph':
        await send_graph(message.channel, commands[2], commands[3])
        sent = True

    if sent is False:
      await message.channel.send(msg)

def start():
  init()
  bot.run(BOT_TOKEN)