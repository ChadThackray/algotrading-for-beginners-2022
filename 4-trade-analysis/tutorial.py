import pandas as pd

df = pd.read_csv("trades.csv")


trades = []

for x in range(0, len(df), 2):

    buy_trade = df.iloc[x]
    sell_trade = df.iloc[x+1]

    trade = {
            "sym":buy_trade.sym,
            "buy_price":buy_trade.price,
            "sell_price":sell_trade.price,
            "profit": sell_trade.price - buy_trade.price
            }

    trades.append(trade)

trades = pd.DataFrame(trades)
trades["percent_profit"] = 100*(trades["profit"]/trades["buy_price"])

print(trades[ trades["profit"] > 0])
