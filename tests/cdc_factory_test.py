from src.cdc_factory import add_pairs, check_if_pairs_exists, check_pairs, get_availabel_exchange, get_historical_signal, init, get_availabel_pairs


def start_test():

  init()
  print("=== Availabel Pairs ===")
  print(get_availabel_pairs())

  print("=== Check Pairs ===")
  print(check_pairs('btcusdt') is not None)
  print(check_pairs('btcthb') is not None)

  print("=== Add Pairs ===")
  print(add_pairs('btcusdt'))
  print(add_pairs('btcthb'))
  print(add_pairs('dydxusdt'))

  print("=== Check if Pairs exists ===")
  print(check_if_pairs_exists('btcusdt'))
  print(check_if_pairs_exists('btcthb'))

  print("=== Get Historical signals ===")
  print(get_historical_signal('btcusdt'))
  print(get_historical_signal('btcthb'))

  print("=== Get Availabel Exchanges ===")
  print(get_availabel_exchange())