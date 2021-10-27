from src.cdc_factory import add_pairs, check_pairs, init, get_availabel_pairs


def start_test():

  init()
  print("=== Availabel Pairs ===")
  print(get_availabel_pairs())

  print("=== Check Pairs ===")
  print(check_pairs('btcusdt'))
  print(check_pairs('btcthb'))

  print("=== Add Pairs ===")
  print(add_pairs('btcusdt'))
  print(add_pairs('btcthb'))
  print(add_pairs('dydxusdt'))


