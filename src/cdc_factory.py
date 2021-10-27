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

def fetch_crypto_pairs(pairs):
  global cryptoData
  url = f'https://api.cryptowat.ch/markets/binance/{pairs}/ohlc'
  sess = Session()
  response = sess.get(url, params=parameters)
  responseData = json.loads(response.text)
  if 'error' in responseData:
    print('error:', pairs.upper())
    return None

  for period in periods:
    data = responseData['result'][period]

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

def get_history_signal(period, pairs, backwardDays=365):
  availableDays = len(cryptoData[period][pairs]['timestamps'])
  if backwardDays > availableDays:
    backwardDays = availableDays

  signals = {'buys':{'timestamps':[], 'closing_prices':[]}, 'sells':{'timestamps':[], 'closing_prices':[]}}
  
  for i in range(availableDays - backwardDays + 1, availableDays):
    (isBuy, isSell, noSignal, timstamp, closingPrice) = get_signal(period, pairs, -backwardDays+3+i)
    if isBuy:
      signals['buys']['timestamps'].append(timstamp)
      signals['buys']['closing_prices'].append(closingPrice)
    elif isSell:
      signals['sells']['timestamps'].append(timstamp)
      signals['sells']['closing_prices'].append(closingPrice)

  return signals


allPairs = []

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
            print(f'Successfully fetched : {pairs.upper()} with tf {tf}')
    t2 = time.time()
    print(f'Fetched time usage: {round((t2 - t1),2)} seconds')

    with open(os.path.join(os.getcwd(), "src", "crypto-data.json"), "w") as outfile:
        json.dump(cryptoData, outfile, indent=4)
        outfile.close()


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
    tfName = '📈 Time frame 1 day'
    if tf == '43200':
        tfName = '📈 Time frame 12 hours'

    msg = f'\n{tfName}'

    for pairs in allPairs:
        signalMsg = get_signal_with_pairs(tf, pairs, dayOffset)
        msg += signalMsg
    if 'BUY' not in msg and 'SELL' not in msg:
        msg += '\nNo signal'
    return msg

def get_all_signals(dayOffset):
    msg = ''
    for tf in periods:
        signalMsg = get_signals_with_tf(tf, dayOffset)
        msg += signalMsg

    return msg

