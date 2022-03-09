from datetime import datetime
import os
import time
import json

import discord
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from src.mqtt import initializeMQTT

import src.cdc_factory as cdcFactory
import config

bot = commands.Bot(command_prefix='!cdc')

mqttClient = initializeMQTT()

def publish(msg):
  print('Publishing... MQTT')
  result = mqttClient.publish('cdc/signal', msg, qos=1, retain=True)
  result.wait_for_publish(timeout=10)

async def sendMessage(channel, msg):
  if len(msg) > 1900:
    await channel.send(msg[:1900])
    await channel.send(msg[1900:])
  else:
    await channel.send(msg)

def get_local_time(timestamp):
  localTimestamp = timestamp + (7*60*60)
  return datetime.utcfromtimestamp(localTimestamp).strftime("%Y:%m:%dT%H:%M:%S")

async def send_update_signal():
  timestamp = time.time()
  currentUTCTime = datetime.utcfromtimestamp(timestamp).strftime("%H:%M")
  
  currentLocalTime = get_local_time(timestamp)

  cdcFactory.refetch()
  print('Sending... update')
  msg = f'\n✅ Authomatic update: {currentLocalTime}'
  
  if currentUTCTime == "00:00":
    channel = bot.get_channel(int(config.CRYPTO_CHANNEL))
    msgSignal, signalPayload = cdcFactory.get_signals_with_tf('86400', 0)
    msg += msgSignal
    publish(json.dumps(signalPayload))
    await sendMessage(channel, msg)
  else:
    channel = bot.get_channel(int(config.CRYPTO_CHANNEL))
    msgSignal, signalPayload = cdcFactory.get_signals_with_tf('43200', 0)
    msg += msgSignal
    await sendMessage(channel, msg)

@bot.command()
async def send_graph(channel, pairs, tfName):

  tf = None
  tempTF = tfName.replace(' ', '')
  if tempTF == '12h' or tempTF == '12hours':
    tf = '43200'
  elif tempTF == '1d' or tempTF == '1day':
    tf = '86400'
  
  if tf is not None:
    msg = cdcFactory.generate_graph(pairs, tf)
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
  scheduler.add_job(send_update_signal, CronTrigger(hour=config.HOUR, minute=config.MINUTE, second=config.SECOND))

  scheduler.start()

@bot.event
async def on_message(message):
  print('Incoming message')
  print(message)

  msgContent = message.content
  msg = f'{config.UNKNOWN_MESSAGE}'
  sent = False
  if msgContent.startswith('!cdc') :
    commands = msgContent.split(' ')
    print('commands:', commands)

    if len(commands) == 1:
      msg = f'🚷 {config.WELCOME_MESSAGE} 🚀'
      msg += '\n\nℹ️ Use command below for more information.```!cdc info```'
      msg += cdcFactory.get_all_signals(0)
    elif len(commands) == 2:
      if commands[1] == 'update':
        cdcFactory.refetch()
        msg, sinalPayload = cdcFactory.get_signals_with_tf('86400', 0)
      elif commands[1] == 'trader':
        msg, sinalPayload = cdcFactory.get_signals_with_tf('86400', 0)
        publish(json.dumps(sinalPayload))
      elif commands[1] == 'future':
        msg, _ = cdcFactory.get_signals_with_tf('86400', 1)
      elif commands[1] == 'pairs' or commands[1] == 'list':
        msg = cdcFactory.get_availabel_pairs()
      elif commands[1] == 'info':
        msg = 'รอก่อน กำลังทำ...'
      elif commands[1] == 'checktime':
        timestamp = time.time()
        currentLocalTime = get_local_time(timestamp)
        msg = '⏱  ' + currentLocalTime
      elif commands[1] == 'exchange' or commands[1] == 'exchanges' or commands[1] == 'ex':
        msg = cdcFactory.get_availabel_exchange()
    elif len(commands) == 3:
      if commands[1] == 'history':
        msg = cdcFactory.get_historical_signal(commands[2].lower())
      elif commands[1] == 'add':
        msg = cdcFactory.add_pairs(commands[2].lower())
      elif commands[1] == 'check':
        msg = cdcFactory.check_pairs(commands[2].lower())
      elif commands[1] == 'graph':
        print(commands[2].lower())
        await send_graph(message.channel, commands[2].lower(), '1d')
        sent = True 
      elif commands[1] == 'remove' or commands[1] == 'rm':
        if message.author.id == config.ADMIN_ID:
          msg = cdcFactory.remove_pairs(commands[2].lower())
        else:
          msg = '\n🚫 Only admin can remove pairs'
      if commands[1] == 'update' and commands[2] == 'all':
        cdcFactory.refetch()
        msg = cdcFactory.get_all_signals(0)
      elif commands[1] == 'future'  and commands[2] == 'all':
        msg = cdcFactory.get_all_signals(1)
    elif len(commands) == 4:
      if commands[1] == 'graph':
        await send_graph(message.channel, commands[2].lower(), commands[3])
        sent = True

    if sent is False:
      await sendMessage(message.channel, msg)

def start():
  cdcFactory.init()
  bot.run(config.BOT_TOKEN)