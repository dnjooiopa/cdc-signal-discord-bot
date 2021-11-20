from src.cdc_factory import add_pairs, check_pairs, generate_graph, get_availabel_exchange, get_historical_signal, init, get_availabel_pairs, remove_pairs, get_signals_with_tf

def start_test():

  init()
  print("=== Availabel Pairs ===")
  print(get_availabel_pairs())

  print("=== Add Pairs ===")
  print(add_pairs('btcusdt'))
  print(add_pairs('btcthb'))
  print(add_pairs('dydxusdt'))
  print(add_pairs('copeusd'))
  print(add_pairs('waxpusdt'))

  print("=== Check if Pairs exists ===")
  print(check_pairs('btcusdt'))
  print(check_pairs('btcthb'))

  print("=== Get Historical signals ===")
  print(get_historical_signal('btcusdt'))
  print(get_historical_signal('btcthb'))

  print("=== Get Availabel Exchanges ===")
  print(get_availabel_exchange())

  print("=== Generate Graph")
  generate_graph('btcusdt')
  generate_graph('btcthb')

  print("=== Remove Pairs ====")
  print(remove_pairs('waxpusdt'))
  print(remove_pairs('waxpusdt'))

  print("=== Get signal with tf ===")
  print(get_signals_with_tf('86400', 0))
