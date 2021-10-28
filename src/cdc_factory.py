from datetime import datetime
import time
from requests import Session
import os
import json

from config import API_KEY

# Initialize Global Variable
timeIdx = 0
closeIdx = 4

current_unix_time = int(time.time())
days = 120

periods = ['86400', '43200']
parameters = {
  'apikey': API_KEY,
  'after': current_unix_time - (86400*days),
  'periods': '43200,86400'
}

cryptoData = {
    '43200': {},
    '86400': {}
}

allPairs = []

TF_NAME = {
  '86400': '1 day',
  '43200': '12 hours'
}

def get_format_time(unix):
    return datetime.utcfromtimestamp(unix).strftime('%Y %m %d')

def get_current_timstamp():
    current_unix_time = int(time.time())
    parameters['after'] = current_unix_time - (86400*days)
    return current_unix_time

def calculate_ema(prices, days, smoothing=2):
    ema = [sum(prices[:days]) / days]
    for price in prices[days:]:
        ema.append((price * (smoothing / (1 + days))) + ema[-1] * (1 - (smoothing / (1 + days))))
    return ema

def make_request(url):
  sess = Session()
  response = sess.get(url, params=parameters)
  responseData = json.loads(response.text)
  if 'error' in responseData:
    return None
  return responseData['result']

def fetch_crypto_pairs(pairs):
  global cryptoData
  
  url = f'https://api.cryptowat.ch/markets/binance/{pairs}/ohlc'

  for period in periods:
    result = make_request(url)

    if result is None:
      print(f'Error cannot fetch : {pairs.upper()}')
      continue

    data = result[period]

    if len(data) < 27:
      continue
    
    closingPrices = [x[closeIdx] for x in data]
    timestamps = [x[timeIdx] for x in data]

    ema12 = calculate_ema(closingPrices, 12)
    ema26 = calculate_ema(closingPrices, 26)

    ema12 = ema12[26-12:]
    timestamps = timestamps[25:]
    closingPrices = closingPrices[25:]

    cryptoData[period][pairs] = {
        'closing_prices': closingPrices,
        'ema12': ema12,
        'ema26': ema26,
        'timestamps': timestamps
    }
    print(f'Successfully fetched : {pairs.upper()} with tf {period}')

def save_pairs():
  with open(os.path.join(os.getcwd(), "src", "crypto-info.json"), "w") as outfile:
    json.dump({'pairs':allPairs}, outfile, indent=4)
    outfile.close()

def save_crypto_data():
  with open(os.path.join(os.getcwd(), "src", "crypto-data.json"), "w") as outfile:
      json.dump(cryptoData, outfile, indent=4)
      outfile.close()

def refetch():
    print("Refetching...")
    t1 = time.time()
    for tf in periods:
        for pairs in allPairs:
            if pairs in cryptoData[tf]:
                if int(time.time()) > cryptoData[tf][pairs]['timestamps'][-1]:
                    fetch_crypto_pairs(pairs)
            else:
                fetch_crypto_pairs(pairs)
    t2 = time.time()
    print(f'Fetched time usage: {round((t2 - t1),2)} seconds')

    save_crypto_data()

def init():
    global allPairs, cryptoData
    print("Application starting...")

    with open(os.path.join(os.getcwd(), "src", "crypto-info.json")) as cryptoInfoFile:
        data = json.load(cryptoInfoFile)
        allPairs = data['pairs']
        cryptoInfoFile.close()

    with open(os.path.join(os.getcwd(), "src", "crypto-data.json")) as cryptoDataFile:
        data = json.load(cryptoDataFile)
        cryptoData = data
        cryptoDataFile.close()

    refetch()

def get_signal(period, pairs, dayOffSet=0):
    currentIdx = dayOffSet-2
    previousIdx = dayOffSet-3

    isBuySignal = cryptoData[period][pairs]['ema12'][currentIdx] > cryptoData[period][pairs]['ema26'][currentIdx] and cryptoData[period][pairs]['ema12'][previousIdx] < cryptoData[period][pairs]['ema26'][previousIdx]
    isSellSignal = cryptoData[period][pairs]['ema12'][currentIdx] < cryptoData[period][pairs]['ema26'][currentIdx] and cryptoData[period][pairs]['ema12'][previousIdx] > cryptoData[period][pairs]['ema26'][previousIdx]
    
    timestamp = cryptoData[period][pairs]['timestamps'][currentIdx]
    closingPrice = cryptoData[period][pairs]['closing_prices'][currentIdx]

    if isBuySignal:
        return (True, False, False, timestamp, closingPrice)
    elif isSellSignal:
        return (False, True, False, timestamp, closingPrice)
    else:
        return (False, False, True, timestamp, closingPrice)

def get_signal_with_pairs(tf, pairs, dayOffset):
    (buy, sell, noSignal, timestamp, closingPrice) = get_signal(tf, pairs, dayOffset)
    formatTime = get_format_time(timestamp)
    msg = ''
    if buy:
        msg = f'\n{formatTime} : {pairs.upper()} : BUY 🟢 at {closingPrice}$'
    elif sell:
        msg = f'\n{formatTime} : {pairs.upper()} : SELL 🔴 at {closingPrice}$'

    return msg

def get_signals_with_tf(tf, dayOffset):
    msg = f'\n📈 Time frame {TF_NAME[tf]}'

    for pairs in allPairs:
        signalMsg = get_signal_with_pairs(tf, pairs, dayOffset)
        msg += signalMsg
    if 'BUY' not in msg and 'SELL' not in msg:
        msg += '\nNo signal'
    return msg

def get_historical_signal(pairs):
  if pairs not in allPairs:
    return f'❌ Pairs not exists : {pairs.upper()}\nType "!cdc add pair {pairs}" to add this pairs.'

  msg = ''
  for tf in periods:
    backwardDays=1000
    availableDays = len(cryptoData[tf][pairs]['timestamps'])
    if backwardDays > availableDays:
      backwardDays = availableDays

    msg += f'\n📈 Historical signal for time frame {TF_NAME[tf]} (last {days} days)'
    for i in range(availableDays - backwardDays + 1, availableDays):
      msg += get_signal_with_pairs(tf, pairs, -backwardDays+2+i)
  return msg

def get_all_signals(dayOffset):
    msg = ''
    for tf in periods:
        signalMsg = get_signals_with_tf(tf, dayOffset)
        msg += signalMsg

    return msg

def get_availabel_pairs():
    return ','.join([x.upper() for x in allPairs])

def check_pairs(pairs):
  url = f'https://api.cryptowat.ch/markets/binance/{pairs}/ohlc'
  result = make_request(url)
  return result

def check_if_pairs_exists(pairs):
  if pairs in allPairs:
    return f'✅ Pairs already exists : {pairs.upper()}'
  else:
    return f'❌ Pairs does not exists : {pairs.upper()}'

def add_pairs(pairs): 
  if pairs in allPairs:
    return  f'✅ Pairs already exists : {pairs.upper()}'

  msg = f'❌ Pairs not found in Binance : {pairs.upper()}'
  if check_pairs(pairs) is not None:
    allPairs.append(pairs)
    refetch()
    save_pairs()
    msg = f'✅ Pairs added : {pairs.upper()}'
  return msg
