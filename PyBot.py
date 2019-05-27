# -*- coding: utf-8 -*-

import asyncio
import os
import sys
import time

import ccxt
import ccxt.async_support as ccxta  # noqa: E402

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root + "/python")

# symbol = "ETH/USD"
symbols = ["BTC/USD", "ETH/USD"]
exchanges = ["bitfinex", "kraken", "okcoinusd", "cex"]


async def async_client(exchange):
    # client = getattr(ccxta, exchange)()
    tickers = {}
    client = getattr(ccxta, exchange)(
        {"enableRateLimit": True}  # required accoding to the Manual
    )
    await client.load_markets()
    try:
        for i in range(len(symbols)):

            if symbols[i] not in client.symbols:
                raise Exception(exchange + " does not support symbol " + symbols[i])

            tickers[symbols[i]] = await client.fetch_order_book(symbols[i])

        await client.close()
        return tickers
    except ccxt.BaseError as e:
        print(type(e).__name__, str(e), str(e.args))
        raise e


async def multi_orderbooks(exchanges):
    input_coroutines = [async_client(exchange) for exchange in exchanges]
    tickers = await asyncio.gather(*input_coroutines, return_exceptions=True)
    return tickers


def list_unique_pairs(source):
    result = []
    for p1 in range(len(source)):
        for p2 in range(p1 + 1, len(source)):
            result.append([source[p1], source[p2]])
    return result


if __name__ == "__main__":

    exchange_pairs = list_unique_pairs(exchanges)
    print("%d pairings" % len(exchange_pairs))

    while True:

        # Holds on two dimensiona array [Exchange][Symbol]
        bids = [[0 for x in range(len(exchanges))] for y in range(len(symbols))]
        asks = [[0 for x in range(len(exchanges))] for y in range(len(symbols))]

        # !!! Fetch data
        tic = time.time()
        a1 = asyncio.get_event_loop().run_until_complete(multi_orderbooks(exchanges))
        print("async call spend: {:.2f}".format(time.time() - tic))
        # !!! \Fetch data

        # !!! Take Bids/Asks
        for Sym in range(len(symbols)):
            for index, exchange in enumerate(a1):
                bids[Sym][index] = exchange[symbols[Sym]]["bids"][0][0]
                asks[Sym][index] = exchange[symbols[Sym]]["asks"][0][0]
        # !!! \Take Bids/Asks

        print("bids: ", bids)
        print("asks: ", asks)
        print(" ")

        # !!! find/print opportunities
        for Sym in range(len(symbols)):
            print(f"Symbol: {symbols[Sym]} :")

            for pair in exchange_pairs:
                
                # FIX ME - as Vezes ele faz trade com a mesma exchange porque vale mais a pena do que seu par
                temp_ask = min(asks[Sym][exchanges.index(pair[0])], asks[Sym][exchanges.index(pair[1])])
                temp_bid = max(bids[Sym][exchanges.index(pair[0])], bids[Sym][exchanges.index(pair[1])])
                min_ask_index = asks[Sym][::].index(temp_ask)
                max_bid_index = bids[Sym][::].index(temp_bid)
                temp_ex_buy = exchanges[min_ask_index]
                temp_ex_sell = exchanges[max_bid_index]

                print(
                    "Pairs (buy/sell): {}/{} (% Spread {:.2%})".format(
                        temp_ex_buy,
                        temp_ex_sell,
                        ((temp_bid / temp_ask) - 1),
                    )
                )

            print("!!!! Operate on \/ !!!!")

            # Find exchanges for operations
            min_ask_index = asks[Sym][::].index(min(asks[Sym][::]))
            max_bid_index = bids[Sym][::].index(max(bids[Sym][::]))

            print(f"Buy/Sell = {exchanges[min_ask_index]} / {exchanges[max_bid_index]}")
            print(
                "Highest Spread: {:.2f}".format(max(bids[Sym][::]) - min(asks[Sym][::]))
            )
            print(
                "% Spread: {:.2%}".format(
                    ((max(bids[Sym][::]) / min(asks[Sym][::])) - 1)
                )
            )
            print(" ")
        # !!! \find/print opportunities

        print("----------------------------------------------------------------")
