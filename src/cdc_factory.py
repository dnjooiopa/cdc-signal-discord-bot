from datetime import datetime
import time
from requests import Session
import os
import json
import matplotlib.pyplot as plt

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

exchanges = ['binance', 'okex', 'ftx']

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

  for tf in periods:
    result = None
    exName = None
    for ex in exchanges:
      url = f'https://api.cryptowat.ch/markets/{ex}/{pairs}/ohlc'
      result = make_request(url)
      if result is not None:
        exName = ex
        break

    if result is None:
      print(f'Error cannot fetch : {pairs.upper()}')
      continue

    data = result[tf]

    if len(data) < 27:
      continue
    
    closingPrices = [x[closeIdx] for x in data]
    timestamps = [x[timeIdx] for x in data]

    ema12 = calculate_ema(closingPrices, 12)
    ema26 = calculate_ema(closingPrices, 26)

    ema12 = ema12[26-12:]
    timestamps = timestamps[25:]
    closingPrices = closingPrices[25:]

   
    cryptoData[tf][pairs] = {
        'closing_prices': closingPrices,
        'ema12': ema12,
        'ema26': ema26,
        'timestamps': timestamps,
    }
    cryptoData[tf][pairs]['signals'] = get_historical_signal_data(tf, pairs)
    cryptoData['exchange_indexes'][pairs] = exName

    print(f'Successfully fetched : {pairs.upper()} with tf {tf}')

def save_file(fileName, data):
  with open(os.path.join(os.getcwd(), "data", fileName), "w") as outfile:
    json.dump(data, outfile, indent=4)
    outfile.close()
    print(f'{fileName} has been saved.')

def open_file(fileName, directory='data'):
  with open(os.path.join(os.getcwd(), directory, fileName)) as openfile:
    data = json.load(openfile)
    openfile.close()
    return data

def file_exists(fileName, directory='data'):
  return os.path.exists(os.path.join(os.getcwd(), directory, fileName))

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
  save_file('crypto-data.json', cryptoData)
  print(f'Fetched time usage: {round((t2 - t1),2)} seconds')

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
  exName = cryptoData['exchange_indexes'][pairs].upper()
  if buy:
      msg = f'\n{formatTime} : {exName} : {pairs.upper()} : BUY 🟢 at {closingPrice}$'
  elif sell:
      msg = f'\n{formatTime} : {exName} : {pairs.upper()} : SELL 🔴 at {closingPrice}$'

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
  print(pairs not in allPairs)
  if pairs not in allPairs:
    return f'❌ Pairs not exists : {pairs.upper()}\nℹ️ Use command below to add new pairs.\n```!cdc add NEW_PAIRS```'

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

def get_historical_signal_data(tf, pairs):
  availableDays = len(cryptoData[tf][pairs]['timestamps'])

  signals = {'buys': {'closing_prices': [], 'timestamps': []}, 'sells': {'closing_prices': [], 'timestamps': []}}
  for i in range(1, availableDays):
    (buy, sell, noSignal, timestamp, closingPrice) = get_signal(tf, pairs, -availableDays+2+i)
    if buy:
      signals['buys']['closing_prices'].append(closingPrice)
      signals['buys']['timestamps'].append(timestamp)
    elif sell:
      signals['sells']['closing_prices'].append(closingPrice)
      signals['sells']['timestamps'].append(timestamp)

  return signals

def get_all_signals(dayOffset):
    msg = ''
    for tf in periods:
      signalMsg = get_signals_with_tf(tf, dayOffset)
      msg += signalMsg

    return msg

def get_availabel_pairs():

  msg = ''
  for ex in exchanges:
    msg += f'\n✅ {ex.upper()}:\n'
    for pairs in cryptoData['exchange_indexes'].keys():
      if cryptoData['exchange_indexes'][pairs] == ex:
        msg += pairs.upper() + ','

  msg += f'\n\n🪙 Pairs Availabel : {len(allPairs)}'
  return msg

def find_pairs(pairs):
  result = None
  exName = None
  for ex in exchanges:
    url = f'https://api.cryptowat.ch/markets/{ex}/{pairs}/ohlc'
    result = make_request(url)
    if result is not None:
      exName = ex
      break
  return result, exName

def get_last_price(ex, pairs):
  url = f'https://api.cryptowat.ch/markets/{ex}/{pairs}/price'
  result = make_request(url)
  currentPrice = None if result is None else result['price']
  return currentPrice

def check_pairs(pairs):
  if pairs in allPairs:
    exName = cryptoData['exchange_indexes'][pairs].upper()
    currentPrice = get_last_price(exName, pairs)
    return f'✅ Pairs already exists : {exName} : {pairs.upper()}\n💰 Current Price : {currentPrice}$'
  else:
    return f'❌ Pairs does not exists : {pairs.upper()}\nℹ️ Use command below to add new pairs.\n```!cdc add NEW_PAIRS```'

def add_pairs(pairs): 
  if pairs in allPairs:
    exName = cryptoData['exchange_indexes'][pairs].upper()
    return f'✅ Pairs already exists : {exName} : {pairs.upper()}'
  exNames = ','.join(exchanges)
  msg = f'❌ Pairs not found in {exNames} : {pairs.upper()}'
  result, exName = find_pairs(pairs)
  if result is not None:
    allPairs.append(pairs)
    refetch()
    save_file('crypto-info.json', {"pairs": allPairs})
    exName = cryptoData['exchange_indexes'][pairs]
    msg = f'✅ Pairs added : {exName.upper()} : {pairs.upper()}'
  return msg

def save_graph(pairs, tf):
  plt.xlabel('Days')
  plt.ylabel('Prices')

  x_axis =  cryptoData[tf][pairs]['timestamps']
  exName = cryptoData['exchange_indexes'][pairs].upper()
  plt.title(f'{pairs.upper()} ({exName})', fontsize=20)

  plt.xticks(rotation=90)

  plt.plot(x_axis, cryptoData[tf][pairs]['closing_prices'], label='closing prices', color='cornflowerblue')
  plt.plot(x_axis, cryptoData[tf][pairs]['ema12'], label='EMA12', color='gold')
  plt.plot(x_axis, cryptoData[tf][pairs]['ema26'], label='EMA26', color='plum')

  buySignals = cryptoData[tf][pairs]['signals']['buys']
  sellSignals = cryptoData[tf][pairs]['signals']['sells']

  plt.scatter(buySignals['timestamps'], buySignals['closing_prices'], s=100, color='green')
  plt.scatter(sellSignals['timestamps'], sellSignals['closing_prices'], s=100, color='red')

  for i, txt in enumerate(buySignals['closing_prices']):
    formatTime = get_format_time(buySignals['timestamps'][i])
    label = f'   {formatTime}'
    label += f'\n   BUY at: {txt}$'
    plt.annotate(label, (buySignals['timestamps'][i], buySignals['closing_prices'][i]))

  for i, txt in enumerate(sellSignals['closing_prices']):
    formatTime = get_format_time(sellSignals['timestamps'][i])
    label = f'   {formatTime}'
    label += f'\n   SELL at: {txt}$'
    plt.annotate(label, (sellSignals['timestamps'][i], sellSignals['closing_prices'][i]), color='red')

  plt.savefig(os.path.join(os.getcwd(), "data", 'graph.png'))
  plt.close()

def generate_graph(pairs, tf='86400'):
  msg = None
  if pairs not in allPairs:
    msg = f'❌ Pairs does not exists : {pairs.upper()}' 
  else:
    save_graph(pairs, tf)
  return msg

def get_availabel_exchange():
  msg = ','.join([x.upper() for x in exchanges])
  return msg

def init():
  global allPairs, cryptoData
  print("Application starting...")

  if not file_exists("crypto-info.json"):
    allPairs = open_file('crypto-info.default.json', directory='default')['pairs']
  else:
    allPairs = open_file('crypto-info.json')['pairs']
  
  if not file_exists("crypto-data.json"):
    cryptoData = open_file('crypto-data.default.json', directory='default')
  else:
    cryptoData = open_file('crypto-data.json')

  refetch()

  plt.rcParams['figure.figsize'] = [20, 12]
  plt.rcParams["figure.autolayout"] = True
  plt.plot([1,2,3], [1,2,3])
  plt.savefig(os.path.join(os.getcwd(), "data", 'graph.png'))
  plt.close()