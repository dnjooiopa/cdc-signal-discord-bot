import discord
from discord.ext import commands
from datetime import datetime
import os
import time

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.cdc_factory import add_pairs, check_pairs, generate_graph, get_availabel_exchange, get_availabel_pairs, get_historical_signal, init, refetch, get_signals_with_tf, get_all_signals
from config import CRYPTO_CHANNEL, BOT_TOKEN, UNKNOWN_MESSAGE, WELCOME_MESSAGE, HOUR, MINUTE, SECOND

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

    cmds = [None] * 4

    for i, cmd in enumerate(commands):
      if i >= 4:
        break
      cmds[i] = cmd

    if len(commands) == 1:
      msg = f'🚷 {WELCOME_MESSAGE} 🚀🚀'
      msg += '\n\nℹ️ Use command below for more information.```!cdc info```'
      msg += get_all_signals(0)
    else:
      if cmds[1] == 'update': # 2
        refetch()
        msg = get_all_signals(0)
      elif cmds[1] == 'future':
        msg = get_all_signals(1)
      elif cmds[1] == 'pairs' or cmds[1] == 'list':
        msg = get_availabel_pairs()
      elif cmds[1] == 'info':
        msg = 'รอก่อน กำลังทำ...'
      elif cmds[1] == 'checktime':
        timestamp = time.time()
        currentLocalTime = get_local_time(timestamp)
        msg = '⏱  ' + currentLocalTime
      elif cmds[1] == 'exchange' or cmds[1] == 'exchanges' or cmds[1] == 'ex':
        msg = get_availabel_exchange()
      elif cmds[1] == 'history' and cmds[2] is not None: # 3
        msg = get_historical_signal(cmds[2].lower())
      elif cmds[1] == 'add' and cmds[2] is not None:
        msg = add_pairs(cmds[2].lower())
      elif cmds[1] == 'check' and cmds[2] is not None:
        msg = check_pairs(cmds[2].lower())
      elif cmds[1] == 'graph':
        tf  = cmds[3] if cmds[3] is not None else '1d'
        await send_graph(message.channel, cmds[2], tf)
        sent = True

    if sent is False:
      await message.channel.send(msg)

def start():
  init()
  bot.run(BOT_TOKEN)