from datetime import datetime
import time
from requests import Session
import os
import json
import matplotlib.pyplot as plt

from config import API_KEY, DAYS

# Initialize Global Variable
timeIdx = 0
closeIdx = 4

current_unix_time = int(time.time())
days = DAYS

parameters = {}

crypto = {}

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

  result = None
  exName = None
  for ex in crypto['exchanges']:
    url = f'https://api.cryptowat.ch/markets/{ex}/{pairs}/ohlc'
    result = make_request(url)
    if result is not None:
      exName = ex
      break

  if result is None:
    print(f'Error cannot fetch : {pairs.upper()}')
    return

  if len(result['86400']) < 30:
    print(pairs)
    return

  for tf in crypto['time_frames']:
    data = result[tf]
    
    closingPrices = [x[closeIdx] for x in data]
    timestamps = [x[timeIdx] for x in data]

    ema12 = calculate_ema(closingPrices, 12)
    ema26 = calculate_ema(closingPrices, 26)

    ema12 = ema12[26-12:]
    timestamps = timestamps[25:]
    closingPrices = closingPrices[25:]

   
    crypto['data'][tf][pairs] = {
        'closing_prices': closingPrices,
        'ema12': ema12,
        'ema26': ema26,
        'timestamps': timestamps
    }
    crypto['data'][tf][pairs]['signals'] = get_historical_signal_data(tf, pairs)
    
    crypto['exchange_indexes'][pairs] = exName

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
  for pairs in crypto['pairs']:
    outdate = False
    if pairs in crypto['data']['86400'] or pairs in crypto['data']['86400']:
      for tf in crypto['time_frames']:
        if int(time.time()) > crypto['data'][tf][pairs]['timestamps'][-1]:
          outdate = True
          break
      if outdate:
        fetch_crypto_pairs(pairs) 
    else:
      fetch_crypto_pairs(pairs)
  t2 = time.time()
  save_file('crypto-data.json', crypto)
  print(f'Fetched time usage: {round((t2 - t1),2)} seconds')

def get_signal(tf, pairs, dayOffSet=0):
  currentIdx = dayOffSet-2
  previousIdx = dayOffSet-3

  isBuySignal = crypto['data'][tf][pairs]['ema12'][currentIdx] > crypto['data'][tf][pairs]['ema26'][currentIdx] and crypto['data'][tf][pairs]['ema12'][previousIdx] < crypto['data'][tf][pairs]['ema26'][previousIdx]
  isSellSignal = crypto['data'][tf][pairs]['ema12'][currentIdx] < crypto['data'][tf][pairs]['ema26'][currentIdx] and crypto['data'][tf][pairs]['ema12'][previousIdx] > crypto['data'][tf][pairs]['ema26'][previousIdx]
  
  timestamp = crypto['data'][tf][pairs]['timestamps'][currentIdx]
  closingPrice = crypto['data'][tf][pairs]['closing_prices'][currentIdx]

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
  exName = crypto['exchange_indexes'][pairs].upper()
  msgObj = {}
  if buy:
      msg = f'\n{formatTime} : {exName} : {pairs.upper()} : BUY 🟢 at {closingPrice}$'
      msgObj = {'pairs': pairs, 'ex_name': exName, 'order': 'buy'}
  elif sell:
      msg = f'\n{formatTime} : {exName} : {pairs.upper()} : SELL 🔴 at {closingPrice}$'
      msgObj = {'pairs': pairs, 'ex_name': exName, 'order': 'sell'}

  return msg, msgObj

def get_signals_with_tf(tf, dayOffset):
    msg = f'\n📈 Time frame {TF_NAME[tf]}'
    signalPayload = []
    for pairs in crypto['exchange_indexes'].keys():
        signalMsg, msgObj = get_signal_with_pairs(tf, pairs, dayOffset)
        msg += signalMsg

        if msgObj['ex_name'] == 'binance':
          signalPayload.append({
            'asset_name': msgObj['pairs'].replace('usdt', ''),
            'pair_name': 'busd',
            'order': msgObj['order']
          })

    if 'BUY' not in msg and 'SELL' not in msg:
        msg += '\nNo signal'
    return msg, signalPayload

def get_historical_signal(pairs):
  if pairs not in crypto['pairs']:
    return f'❌ Pairs not exists : {pairs.upper()}\nℹ️ Use command below to add new pairs.\n```!cdc add NEW_PAIRS```'

  msg = ''
  for tf in crypto['time_frames']:
    backwardDays=1000
    availableDays = len(crypto['data'][tf][pairs]['timestamps'])
    if backwardDays > availableDays:
      backwardDays = availableDays

    msg += f'\n📈 Historical signal for time frame {TF_NAME[tf]} (last {days} days)'
    historicalMsg = ''
    for i in range(availableDays - backwardDays + 1, availableDays):
      hMsg, _ = get_signal_with_pairs(tf, pairs, -backwardDays+2+i)
      historicalMsg += hMsg
    if historicalMsg == '':
      historicalMsg = '\nNo historical signal'
  return msg + historicalMsg

def get_historical_signal_data(tf, pairs):
  availableDays = len(crypto['data'][tf][pairs]['timestamps'])

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
    for tf in crypto['time_frames']:
      signalMsg, _ = get_signals_with_tf(tf, dayOffset)
      msg += signalMsg

    return msg

def get_availabel_pairs():

  msg = ''
  for ex in crypto['exchanges']:
    msg += f'\n✅ {ex.upper()}:\n'
    for pairs in crypto['exchange_indexes'].keys():
      if crypto['exchange_indexes'][pairs] == ex:
        msg += pairs.upper() + ','
  allPairs = crypto['pairs']
  msg += f'\n\n🪙 Pairs Availabel : {len(allPairs)}'
  return msg

def find_pairs(pairs):
  result = None
  exName = None
  for ex in crypto['exchanges']:
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
  if pairs in crypto['pairs']:
    exName = crypto['exchange_indexes'][pairs].upper()
    currentPrice = get_last_price(exName, pairs)
    return f'✅ Pairs already exists : {exName} : {pairs.upper()}\n💰 Current Price : {currentPrice}$'
  else:
    return f'❌ Pairs does not exists : {pairs.upper()}\nℹ️ Use command below to add new pairs.\n```!cdc add NEW_PAIRS```'

def add_pairs(pairs): 
  if pairs in crypto['pairs']:
    exName = crypto['exchange_indexes'][pairs].upper()
    return f'✅ Pairs already exists : {exName} : {pairs.upper()}'
  exNames = ','.join(crypto['exchanges'])
  msg = f'❌ Pairs not found in {exNames} : {pairs.upper()}'
  result, exName = find_pairs(pairs)
  if result is not None:
    crypto['pairs'].append(pairs)
    refetch()
    exName = crypto['exchange_indexes'][pairs]
    save_file('crypto-data.json', crypto)
    msg = f'✅ Pairs added : {exName.upper()} : {pairs.upper()}'
  return msg

def remove_pairs(pairs):
  if pairs in crypto['pairs']:
    crypto['pairs'].remove(pairs)
    del crypto['exchange_indexes'][pairs]

    for tf in crypto['time_frames']:
      del crypto['data'][tf][pairs]

    save_file('crypto-data.json', crypto)

    return f'✅ Pairs has been removed: {pairs.upper()}'
  else:
    return f'❌ Pairs does not exists : {pairs.upper()}\nℹ️ Use command below to add new pairs.\n```!cdc add NEW_PAIRS```'

def save_graph(pairs, tf):
  plt.xlabel('Days')
  plt.ylabel('Prices')

  x_axis =  crypto['data'][tf][pairs]['timestamps']
  exName = crypto['exchange_indexes'][pairs].upper()
  plt.title(f'{pairs.upper()} ({exName})', fontsize=20)

  plt.xticks(rotation=90)

  plt.plot(x_axis, crypto['data'][tf][pairs]['closing_prices'], label='closing prices', color='cornflowerblue')
  plt.plot(x_axis, crypto['data'][tf][pairs]['ema12'], label='EMA12', color='gold')
  plt.plot(x_axis, crypto['data'][tf][pairs]['ema26'], label='EMA26', color='plum')

  buySignals = crypto['data'][tf][pairs]['signals']['buys']
  sellSignals = crypto['data'][tf][pairs]['signals']['sells']

  plt.scatter(buySignals['timestamps'], buySignals['closing_prices'], s=100, color='green')
  plt.scatter(sellSignals['timestamps'], sellSignals['closing_prices'], s=100, color='red')

  for i, txt in enumerate(buySignals['closing_prices']):
    formatTime = get_format_time(buySignals['timestamps'][i])
    label = f'   {formatTime}'
    label += f'\n   BUY at {txt}$'
    plt.annotate(label, (buySignals['timestamps'][i], buySignals['closing_prices'][i]))

  for i, txt in enumerate(sellSignals['closing_prices']):
    formatTime = get_format_time(sellSignals['timestamps'][i])
    label = f'   {formatTime}'
    label += f'\n   SELL at {txt}$'
    plt.annotate(label, (sellSignals['timestamps'][i], sellSignals['closing_prices'][i]), color='red')

  plt.legend()
  plt.savefig(os.path.join(os.getcwd(), "data", 'graph.png'))
  print('graph.png has been saved')
  plt.close()

def generate_graph(pairs, tf='86400'):
  msg = None
  if pairs not in crypto['pairs']:
    msg = f'❌ Pairs does not exists : {pairs.upper()}\nℹ️ Use command below to add new pairs.\n```!cdc add NEW_PAIRS```'
  else:
    save_graph(pairs, tf)
  return msg

def get_availabel_exchange():
  msg = ','.join([x.upper() for x in crypto['exchanges']])
  return msg

def init():
  global crypto, parameters
  print("Application starting...")
  
  if not file_exists("crypto-data.json"):
    crypto = open_file('crypto-data.default.json', directory='default')
  else:
    crypto = open_file('crypto-data.json')

  parameters = {
    'apikey': API_KEY,
    'after': current_unix_time - (86400*days),
    'periods': ','.join(crypto['time_frames'])
    }

  refetch()

  plt.rcParams['figure.figsize'] = [20, 12]
  plt.rcParams["figure.autolayout"] = True
  plt.plot([1,2,3], [1,2,3])
  plt.savefig(os.path.join(os.getcwd(), "data", 'graph.png'))
  plt.close()