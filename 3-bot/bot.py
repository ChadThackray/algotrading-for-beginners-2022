from decouple import config
from binance.client import Client
import pandas as pd
import pandas_ta as ta
import json
import os
import time
import sys
import datetime



client = Client(config("API_KEY"), config("SECRET_KEY"), testnet= True)
asset = "BTCUSDT"
entry = 25
exit = 74


def fetch_klines(asset):

    klines = client.get_historical_klines(asset, Client.KLINE_INTERVAL_1MINUTE, "1 hour ago UTC")

    klines = [ [x[0],float(x[4]) ] for x in klines ]

    klines = pd.DataFrame(klines, columns = ["time","price"])
    klines["time"] = pd.to_datetime(klines["time"], unit = "ms") 

    return klines 

def get_rsi(asset):

    klines = fetch_klines(asset)
    klines["rsi"] = ta.rsi( close = klines["price"], length = 14)

    return klines["rsi"].iloc[-1]

def create_account():

    account = {
            "is_buying":True,
            "assets":{},
            }

    with open("bot_account.json","w") as f:
        f.write( json.dumps(account))

def log(msg):
    print(f"LOG: {msg}")
    if not os.path.isdir("logs"):
        os.mkdir("logs")

    now = datetime.datetime.now()
    today = now.strftime("%Y-%m-%d")
    time = now.strftime("%H-%M-%S")

    with open(f"logs/{today}.txt","a+") as log_file:
        log_file.write(f"{time} : {msg}\n")

def trade_log(sym, side, price, amount):
    log(f"{side} {amount} {sym} for {price} per")

    if not os.path.isdir("trades"):
        os.mkdir("trades")

    now = datetime.datetime.now()
    today = now.strftime("%Y-%m-%d")
    time = now.strftime("%H-%M-%S")

    if not os.path.isfile(f"trades/{today}.csv"):
        with open(f"trades/{today}.csv", "w") as trade_file:
            trade_file.write("sym,side,amount,price\n")

    with open(f"trades/{today}.csv", "a+") as trade_file:
        trade_file.write(f"{sym},{side},{amount},{price}\n")


def do_trade(account, client, asset, side, quantity):

    if side == "buy":

        order = client.order_market_buy(
                symbol = asset,
                quantity = quantity
                )
        account["is_buying"] = False

    else:

        order = client.order_market_sell(
                symbol = asset,
                quantity = quantity
                )
        account["is_buying"] = True

    order_id = order["orderId"]

    while order["status"] != "FILLED":

        order = client.get_order(
                symbol = asset,
                orderId = order_id)
        time.sleep(1)

    print(order)

    price_paid = sum([ float(fill["price"]) * float(fill["qty"]) \
            for fill in order["fills"] ])

    # log trade
    trade_log(asset, side, price_paid, quantity)

    with open("bot_account.json", "w") as f:
        f.write(json.dumps(account))


rsi = get_rsi(asset)
old_rsi = rsi


while True:

    try:

        if not os.path.exists("bot_account.json"):
            create_account()

        with open("bot_account.json") as f:
            account = json.load(f)
        
        print(account)

        old_rsi = rsi
        rsi = get_rsi(asset)

        if account["is_buying"]:

            if rsi < entry and old_rsi > entry:
                do_trade(account, client, asset, "buy", 0.01)


        else:

            if rsi > exit and old_rsi < exit:
                do_trade(account, client, asset, "sell", 0.01)

        print(rsi)
        time.sleep(10)

    except Exception as e:
        log("ERROR" + str(e))


