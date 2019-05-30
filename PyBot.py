# -*- coding: utf-8 -*-

import asyncio
import os
import sys
import time

import trade_mod
import file_management as file_manag
import ccxt
import ccxt.async_support as ccxta  # noqa: E402

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root + "/python")


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
        print("Caught Error within async_client")
        raise e
    finally:
        await client.close()


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


def execute_trading(pair, buying_exchange, selling_exchange, symbol):
    global opened_trades

    # garantees that the exchange has at least the MIN_TRADE_AMOUNT avaiable for trading
    if (real_balance[all_exchanges.index(buying_exchange)] < MIN_TRADE_AMOUNT) or (
        real_balance[all_exchanges.index(selling_exchange)] < MIN_TRADE_AMOUNT
    ):
        print(
            f"Insuficient amount available in either exchange! {buying_exchange} or {selling_exchange}"
        )
        return

    # FIX ME: FEES CANNOT BE STATIC. THERE WOULD NOT BE CONTROL TO DEDUCE THE FEE BALANCE WHEN CLOSING A TRADE?
    amount_bought = real_balance[all_exchanges.index(buying_exchange)] * TRADING_FACTOR
    if amount_bought < MIN_TRADE_AMOUNT:
        amount_bought = MIN_TRADE_AMOUNT

    amount_sold = real_balance[all_exchanges.index(selling_exchange)] * TRADING_FACTOR
    if amount_sold < MIN_TRADE_AMOUNT:
        amount_sold = MIN_TRADE_AMOUNT

    # Garantees that the amount sold/bought are the same
    if amount_bought > amount_sold:
        amount_bought = amount_sold
    else:
        amount_sold = amount_bought

    trading_fees = amount_bought * FEES_FACTOR
    amount_bought -= trading_fees
    amount_sold -= trading_fees

    trade_mod.buy_token(buying_exchange, amount_bought, symbol)
    trade_mod.sell_token(selling_exchange, amount_sold, symbol)

    # Update Balances
    real_balance[all_exchanges.index(buying_exchange)] -= (amount_bought + trading_fees)
    fees_balance[all_exchanges.index(buying_exchange)] += trading_fees

    real_balance[all_exchanges.index(selling_exchange)] -= (amount_sold + trading_fees)
    fees_balance[all_exchanges.index(selling_exchange)] += trading_fees
    margin_balance[all_exchanges.index(selling_exchange)] += amount_sold

    # if trade sucessful:
    file_manag.register_trade(
        pair, symbol, buying_exchange, amount_bought, selling_exchange, amount_sold
    )

    opened_trades[symbols.index(symbol)][exchange_pairs.index(pair)] = True
    pass


def init():
    file_manag.init_files()


# Pairs to trade
symbols = ["BTC/USD", "ETH/USD"]
# Exchanges to trade
all_exchanges = ["bitfinex", "kraken", "okcoinusd", "cex"]
# All possible trading Pairs:
exchange_pairs = list_unique_pairs(all_exchanges)
# Usado para garantir que o bot não entrará na mesma operação duas vezes.
opened_trades = [
    [False for x in range(len(list_unique_pairs(all_exchanges)))]
    for y in range(len(symbols))
]


max_pair_spread = [[], []]
min_pair_spread = [[], []]
current_pair_trailing = [[], []]
# Trailing is the percentage from the max to trade
# TRAILING_STOP = 0.8
# MIN_MARGIN = 1
TRAILING_STOP = 0.99
MIN_MARGIN = 0.2 / 100

# FIX ME: balances NOT USED
# Trading Accounts - Considers all accounts starts with USD only.
real_balance = [5000 for x in range(len(all_exchanges))]
margin_balance = [0 for x in range(len(all_exchanges))]
# Amount reserved to pay for fees
fees_balance = [0 for x in range(len(all_exchanges))]
# Percentage of the trade reserved for fees.
FEES_FACTOR = 0.1
# Min amount per trade
MIN_TRADE_AMOUNT = 50
# Max % of the available balance to be used in a single trade.
TRADING_FACTOR = 0.2


if __name__ == "__main__":

    init()

    print("%d pairings" % len(exchange_pairs))

    # Lists of pair values need an initial zero value for the code to work
    max_pair_spread = [
        [0 for x in range(len(exchange_pairs))] for y in range(len(symbols))
    ]
    min_pair_spread = [
        [0 for x in range(len(exchange_pairs))] for y in range(len(symbols))
    ]
    current_pair_trailing = [
        [0 for x in range(len(exchange_pairs))] for y in range(len(symbols))
    ]

    while True:

        # Holds on two dimensiona array [Exchange][Symbol]
        bids = [[0 for x in range(len(all_exchanges))] for y in range(len(symbols))]
        asks = [[0 for x in range(len(all_exchanges))] for y in range(len(symbols))]

        # !!! Fetch data
        tic = time.time()
        a1 = asyncio.get_event_loop().run_until_complete(
            multi_orderbooks(all_exchanges)
        )
        print("async call spend: {:.2f}".format(time.time() - tic))
        # !!! \Fetch data

        # !!! Take Bids/Asks
        for nSym in range(len(symbols)):
            for index, exchange in enumerate(a1):
                bids[nSym][index] = exchange[symbols[nSym]]["bids"][0][0]
                asks[nSym][index] = exchange[symbols[nSym]]["asks"][0][0]
        # !!! \Take Bids/Asks

        print("bids: ", bids)
        print("asks: ", asks)
        print(" ")

        # !!! find/print opportunities
        for nSym in range(len(symbols)):
            print(f"Symbol: {symbols[nSym]} :")

            for pair in exchange_pairs:

                # FIX ME - as Vezes ele faz trade com a mesma exchange porque vale mais a pena do que seu par
                temp_ask = min(
                    asks[nSym][all_exchanges.index(pair[0])],
                    asks[nSym][all_exchanges.index(pair[1])],
                )
                temp_bid = max(
                    bids[nSym][all_exchanges.index(pair[0])],
                    bids[nSym][all_exchanges.index(pair[1])],
                )
                current_spread = (temp_bid / temp_ask) - 1
                min_ask_index = asks[nSym][::].index(temp_ask)
                max_bid_index = bids[nSym][::].index(temp_bid)
                temp_exc_buy = all_exchanges[min_ask_index]
                temp_exc_sell = all_exchanges[max_bid_index]

                # Calculates the all times spread max, min e traling
                if (
                    current_spread > max_pair_spread[nSym][exchange_pairs.index(pair)]
                ) or (max_pair_spread[nSym][exchange_pairs.index(pair)] == 0):
                    max_pair_spread[nSym][exchange_pairs.index(pair)] = current_spread

                if (
                    current_spread < min_pair_spread[nSym][exchange_pairs.index(pair)]
                ) or (min_pair_spread[nSym][exchange_pairs.index(pair)] == 0):
                    min_pair_spread[nSym][exchange_pairs.index(pair)] = current_spread

                current_pair_trailing[nSym][exchange_pairs.index(pair)] = (
                    max_pair_spread[nSym][exchange_pairs.index(pair)] * TRAILING_STOP
                )

                # Verificar condicao para entrar no trade
                if (
                    (
                        current_pair_trailing[nSym][exchange_pairs.index(pair)]
                        > MIN_MARGIN
                    )
                    and (
                        current_spread
                        <= current_pair_trailing[nSym][exchange_pairs.index(pair)]
                    )
                    and (not opened_trades[nSym][exchange_pairs.index(pair)])
                ):
                    # buy(temp_exc_buy)
                    # sell(temp_exc_sell)
                    print(
                        "Pairs (buy/sell): {}/{} (% Max Spread: {:.2%}, Min Spread: {:.2%}, Spread: {:.2%}, Trailing: {:.2%})".format(
                            temp_exc_buy[:3],
                            temp_exc_sell[:3],
                            max_pair_spread[nSym][exchange_pairs.index(pair)],
                            min_pair_spread[nSym][exchange_pairs.index(pair)],
                            current_spread,
                            current_pair_trailing[nSym][exchange_pairs.index(pair)],
                        ),
                        end=" ",
                    )
                    print("- Opportunity Found!")

                    execute_trading(pair, temp_exc_buy, temp_exc_sell, symbols[nSym])

                elif opened_trades[nSym][exchange_pairs.index(pair)]:

                    print(
                        "Pairs (buy/sell): {}/{} (% Max Spread: {:.2%}, Min Spread: {:.2%}, Spread: {:.2%}, Trailing: {:.2%})".format(
                            temp_exc_buy[:3],
                            temp_exc_sell[:3],
                            max_pair_spread[nSym][exchange_pairs.index(pair)],
                            min_pair_spread[nSym][exchange_pairs.index(pair)],
                            current_spread,
                            current_pair_trailing[nSym][exchange_pairs.index(pair)],
                        ),
                        end=" ",
                    )
                    print("- OPENED TRADE!")

                else:

                    print(
                        "Pairs (buy/sell): {}/{} (% Max Spread: {:.2%}, Min Spread: {:.2%}, Spread: {:.2%}, Trailing: {:.2%})".format(
                            temp_exc_buy[:3],
                            temp_exc_sell[:3],
                            max_pair_spread[nSym][exchange_pairs.index(pair)],
                            min_pair_spread[nSym][exchange_pairs.index(pair)],
                            current_spread,
                            current_pair_trailing[nSym][exchange_pairs.index(pair)],
                        )
                    )

            print("!!!! Operate on \\/ !!!!")

            # Find exchanges for operations
            min_ask_index = asks[nSym][::].index(min(asks[nSym][::]))
            max_bid_index = bids[nSym][::].index(max(bids[nSym][::]))

            print(
                f"Buy/Sell = {all_exchanges[min_ask_index]} / {all_exchanges[max_bid_index]}"
            )
            print(
                "Highest Spread: {:.2f}".format(
                    max(bids[nSym][::]) - min(asks[nSym][::])
                )
            )
            print(
                "% Spread: {:.2%}".format(
                    ((max(bids[nSym][::]) / min(asks[nSym][::])) - 1)
                )
            )
            print(" ")
        # !!! \find/print opportunities

        print("----------------------------------------------------------------")
