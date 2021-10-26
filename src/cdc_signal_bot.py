from cdc_factory import init, get_signals_with_tf, get_all_signals
from config import BOT_TOKEN

init()

from discord.ext import commands
bot = commands.Bot(command_prefix='!cdc') #กำหนด Prefix

@bot.event
async def on_ready() : #เมื่อระบบพร้อมใช้งาน
  print("Bot Started!") #แสดงผลใน CMD
@bot.event
async def on_message(message) : #ดักรอข้อความใน Chat
  msgContent = message.content
  msg = 'ควย !!!'
  if msgContent.startswith('!cdc') :
    #contents = msgContent.split(' ')
    msg = get_all_signals(0)
    await message.channel.send(msg)
bot.run(BOT_TOKEN)