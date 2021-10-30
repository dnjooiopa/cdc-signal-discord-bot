from src.cdc_factory import add_pairs, check_pairs, generate_graph, get_availabel_exchange, get_historical_signal, init, get_availabel_pairs


def start_test():

  init()
  print("=== Availabel Pairs ===")
  print(get_availabel_pairs())

  print("=== Add Pairs ===")
  print(add_pairs('btcusdt'))
  print(add_pairs('btcthb'))
  print(add_pairs('dydxusdt'))
  print(add_pairs('copeusd'))

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