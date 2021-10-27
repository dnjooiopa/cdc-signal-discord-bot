from src.cdc_factory import add_pairs, check_if_pairs_exists, check_pairs, init, get_availabel_pairs


def start_test():

  init()
  print("=== Availabel Pairs ===")
  print(get_availabel_pairs())

  print("=== Check Pairs ===")
  print(check_pairs('btcusdt') is not None)
  print(check_pairs('btcthb') is None)

  print("=== Add Pairs ===")
  print(add_pairs('btcusdt'))
  print(add_pairs('btcthb'))
  print(add_pairs('dydxusdt'))

  print("=== Check if Pairs exists ===")
  print(check_if_pairs_exists('btcusdt'))
  print(check_if_pairs_exists('btcthb'))

