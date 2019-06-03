# -*- coding: utf-8 -*-

import asyncio
import os
import sys
import time

import trade_mod
from trade_mod import TradeData
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


def open_trade(pair, asks_list, bids_list, spread, buying_exchange, selling_exchange, symbol):
    global opened_trades

    # garantees that the exchange has at least the MIN_TRADE_AMOUNT avaiable for trading
    if (real_balance[all_exchanges.index(buying_exchange)] < MIN_TRADE_AMOUNT) or (
        real_balance[all_exchanges.index(selling_exchange)] < MIN_TRADE_AMOUNT
    ):
        print(
            f"Insuficient amount available in either exchange! {buying_exchange} or {selling_exchange}"
        )
        return


    # Find out how much usd you are going to spend on the trade
    # Amount bought sym1 means that it was bought x dollars worth of sym2
    if real_balance[all_exchanges.index(buying_exchange)] > TRADING_AMOUNT:
        amount_bought_sym1 = TRADING_AMOUNT
    else:
        amount_bought_sym1 = real_balance[all_exchanges.index(buying_exchange)]
    if real_balance[all_exchanges.index(selling_exchange)] > TRADING_AMOUNT:
        amount_sold_sym1 = TRADING_AMOUNT
    else:
        amount_sold_sym1 = real_balance[all_exchanges.index(selling_exchange)]


    trading_buying_fees = amount_bought_sym1 * FEES_FACTOR # garantees you`re going to have money for fees (updated later)
    amount_bought_sym1 -= trading_buying_fees

    trading_selling_fees = amount_sold_sym1 * FEES_FACTOR # garantees you`re going to have money for fees updated later)
    amount_sold_sym1 -= trading_selling_fees


    ask_price = asks_list[symbols.index(symbol)][all_exchanges.index(buying_exchange)]
    bid_price = bids_list[symbols.index(symbol)][all_exchanges.index(selling_exchange)]

    amount_bought_sym2 = amount_bought_sym1 / ask_price
    amount_sold_sym2 = amount_sold_sym1 / bid_price

    # Garantees that the amount sold/bought are the same on sym2 - That keeps trade market neutral
    # FIX ME: The best condition is to operate with the amount of sym2 bought (would garantee max profit). Take care with the margin condition
    # amount_bought_sym2 always > amount_sold_sym2
    if amount_bought_sym2 > amount_sold_sym2:
        amount_bought_sym2 = amount_sold_sym2
    else:
        amount_sold_sym2 = amount_bought_sym2

    # Update the amount spent in dollars on the trade according to the amount of sym2 traded (same amount of sym2 on both exchanges)
    amount_bought_sym1 = ask_price * amount_bought_sym2
    amount_sold_sym1 = bid_price * amount_sold_sym2


    # update the fee amount to avoid to much fee reserved on either exchange.
    trading_buying_fees = amount_bought_sym1 * FEES_FACTOR
    trading_selling_fees = amount_sold_sym1 * FEES_FACTOR



    # Round all amounts here before trading (Try to avoid float point hardware approximation)
    amount_bought_sym1 = round(amount_bought_sym1, 2)
    amount_sold_sym1 = round(amount_sold_sym1, 2)
    trading_buying_fees = round(trading_buying_fees, 2)
    trading_selling_fees = round(trading_selling_fees, 2)


    trade_mod.buy_token(buying_exchange, amount_bought_sym1, symbol)
    trade_mod.sell_token(selling_exchange, amount_sold_sym1, symbol) # Short sell

    # Update Balances
    real_balance[all_exchanges.index(buying_exchange)] -= (amount_bought_sym1 + trading_buying_fees)
    fees_balance[all_exchanges.index(buying_exchange)] += trading_buying_fees

    # YOU DO NOT DECREASE THE REAL BALANCE WHEN YOU SELL CRYPTO (Margin trade). Margin balance really needed?
    real_balance[all_exchanges.index(selling_exchange)] += amount_sold_sym1
    real_balance[all_exchanges.index(selling_exchange)] -= trading_selling_fees
    fees_balance[all_exchanges.index(selling_exchange)] += trading_selling_fees
    #margin_balance[all_exchanges.index(selling_exchange)] += amount_sold_sym1

    # if trade sucessful:
    file_manag.register_trade(
        pair, symbol, buying_exchange, amount_bought_sym1, selling_exchange, amount_sold_sym1
    )

    file_manag.updt_balance_files(
        all_exchanges, real_balance, margin_balance, fees_balance
    )


    # Update the opened trade matrix
    opened_trades[symbols.index(symbol)][exchange_pairs.index(pair)].set_is_trade_open(True)

    opened_trades[symbols.index(symbol)][exchange_pairs.index(pair)].set_traded_symbol(symbol)

    opened_trades[symbols.index(symbol)][exchange_pairs.index(pair)].set_buying_exchange(buying_exchange)

    opened_trades[symbols.index(symbol)][exchange_pairs.index(pair)].set_amount_bought_symbol1(amount_bought_sym1)

    opened_trades[symbols.index(symbol)][exchange_pairs.index(pair)].set_fee_reserved_buying_exchange(trading_buying_fees)

    opened_trades[symbols.index(symbol)][exchange_pairs.index(pair)].set_selling_exchange(selling_exchange)

    opened_trades[symbols.index(symbol)][exchange_pairs.index(pair)].set_amount_sold_symbol1(amount_sold_sym1)

    opened_trades[symbols.index(symbol)][exchange_pairs.index(pair)].set_fee_reserved_selling_exchange(trading_selling_fees)

    opened_trades[symbols.index(symbol)][exchange_pairs.index(pair)].set_amount_traded_symbol2(amount_bought_sym2)

    opened_trades[symbols.index(symbol)][exchange_pairs.index(pair)].set_opportunity_spread(spread)
   
    # Update the opened_trades object file
    file_manag.save_trades_data(opened_trades)
    pass


def close_trade(pair, asks_list, bids_list, symbol):
    global opened_trades, max_pair_spread, min_pair_spread, current_pair_trailing

    print(f"Closing trade on pairs: {pair[0]}/{pair[1]} - Symbol = {symbol}")

    # find where to buy, where to sell and how much of symbol2 is going to be sold/bought
    buy_on_exchange = opened_trades[symbols.index(symbol)][exchange_pairs.index(pair)].get_selling_exchange()
    sell_on_exchange = opened_trades[symbols.index(symbol)][exchange_pairs.index(pair)].get_buying_exchange()

    amount_traded_symbol2 = opened_trades[symbols.index(symbol)][exchange_pairs.index(pair)].get_amount_traded_symbol2()

    trading_buying_fees = opened_trades[symbols.index(symbol)][exchange_pairs.index(pair)].get_fee_reserved_selling_exchange()
    trading_selling_fees = opened_trades[symbols.index(symbol)][exchange_pairs.index(pair)].get_fee_reserved_buying_exchange()

    # sell the buying one and buy the selling one according to the ask/bid list
    ask_price = asks_list[symbols.index(symbol)][all_exchanges.index(buy_on_exchange)]
    bid_price = bids_list[symbols.index(symbol)][all_exchanges.index(sell_on_exchange)]

        # Update the amount spent in dollars on the trade according to the amount of sym2 traded (same amount of sym2 on both exchanges)
    amount_bought_sym1 = ask_price * amount_traded_symbol2
    amount_sold_sym1 = bid_price * amount_traded_symbol2

    amount_bought_sym1 = round(amount_bought_sym1, 2)
    amount_sold_sym1 = round(amount_sold_sym1, 2)

    trade_mod.buy_token(buy_on_exchange, amount_bought_sym1, symbol) # Close short selling operation
    trade_mod.sell_token(sell_on_exchange, amount_sold_sym1, symbol)

    # Update the balances

    real_balance[all_exchanges.index(buy_on_exchange)] -= amount_bought_sym1 # Close short selling operation (Margin trade)
    fees_balance[all_exchanges.index(buy_on_exchange)] -= trading_buying_fees
    real_balance[all_exchanges.index(buy_on_exchange)] += trading_buying_fees

    real_balance[all_exchanges.index(sell_on_exchange)] += amount_sold_sym1
    fees_balance[all_exchanges.index(sell_on_exchange)] -= trading_selling_fees
    real_balance[all_exchanges.index(sell_on_exchange)] += trading_selling_fees

    # register the trade
        # if trade sucessful:
    file_manag.register_trade(
        pair, symbol, buy_on_exchange, amount_bought_sym1, sell_on_exchange, amount_sold_sym1
    )

    file_manag.updt_balance_files(
        all_exchanges, real_balance, margin_balance, fees_balance
    )

    #update the opened trades
    opened_trades[symbols.index(symbol)][exchange_pairs.index(pair)].set_is_trade_open(False)
    opened_trades[symbols.index(symbol)][exchange_pairs.index(pair)] = TradeData(pair)
    # Update the opened_trades object file
    file_manag.save_trades_data(opened_trades)

    # Zeroa max/min spread and trailing data
    max_pair_spread[symbols.index(symbol)][exchange_pairs.index(pair)] = 0
    min_pair_spread[symbols.index(symbol)][exchange_pairs.index(pair)] = 0
    current_pair_trailing[symbols.index(symbol)][exchange_pairs.index(pair)] = 0

    pass


def close_all_opened_trades(asks_list, bids_list):

    for symbol in symbols:
        for pair in exchange_pairs:
            if opened_trades[symbols.index(symbol)][exchange_pairs.index(pair)].get_is_trade_open():
                close_trade(pair, asks_list, bids_list, symbol)
    

def init():
    global real_balance, margin_balance, fees_balance, opened_trades
    file_manag.init_all_files(all_exchanges)

    temp_dict = file_manag.fetch_stored_balances()
    for i in range(len(all_exchanges)):
        real_balance[i] = float(temp_dict["real_balance"][all_exchanges[i]])
        margin_balance[i] = float(temp_dict["margin_balance"][all_exchanges[i]])
        fees_balance[i] = float(temp_dict["fees_balance"][all_exchanges[i]])

    file_name = 'tradesData.bin'
    if os.path.isfile(file_name):
        opened_trades = file_manag.load_trades_data()
    else:
        # Holds all possible combinations trading pairs/symbols and stores a TradeData for each
        opened_trades = [
            [TradeData(exchange_pairs[x]) for x in range(len(exchange_pairs))]
            for y in range(len(symbols))
        ]
        # Update the opened_trades object file
        file_manag.save_trades_data(opened_trades)

    pass


# Pairs to trade
symbols = ["BTC/USD", "ETH/USD"]
# Exchanges to trade
all_exchanges = ["bitfinex", "kraken", "okcoinusd", "cex"]
# All possible trading Pairs:
exchange_pairs = list_unique_pairs(all_exchanges)
# Usado  para gravar as operacoes em aberto e para garantir que o bot não entrará na mesma operação duas vezes.
opened_trades = []

max_pair_spread = [[], []]
min_pair_spread = [[], []]
current_pair_trailing = [[], []]
# Trailing is the percentage from the max to trade
# TRAILING_STOP = 0.8
# MIN_MARGIN = 1/100
SPREAD_TO_CLOSE_TRADE = 0.05/100
TRAILING_STOP = 0.99
MIN_MARGIN = 0.5 / 100
# SPREAD_TO_CLOSE_TRADE = 0.7 / 100

# FIX ME: balances NOT USED
# Trading Accounts - Considers all accounts starts with USD only.
real_balance = [0 for x in range(len(all_exchanges))]
margin_balance = [0 for x in range(len(all_exchanges))]
# Amount reserved to pay for fees
fees_balance = [0 for x in range(len(all_exchanges))]
# Percentage of the trade reserved for fees.
FEES_FACTOR = 0.1
# Min amount per trade
MIN_TRADE_AMOUNT = 50
# Max ammount traded in each oppotunity found (If balance < TRADING_AMOUNT, oppotunity is going to take all balance available):
TRADING_AMOUNT = 5000

FILE_STOP_TRADING = "stoptrading.txt"
FILE_CLOSE_ALL_TRADES = "closetrades.txt"


if __name__ == "__main__":

    init()

    print("%d pairings" % len(exchange_pairs))

    print(f"real_balance = {real_balance}")
    print(f"margin_balance = {margin_balance}")
    print(f"fees_balance = {fees_balance}")
    print(" ")

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
        print("async call spend: {:.2f}".format(time.time() - tic), end=" - ")
        # !!! \Fetch data

        print("TimeStamp: " + str(file_manag.get_timestamp()))
        print(" ")

        # !!! Take Bids/Asks
        for nSym in range(len(symbols)):
            for index, exchange in enumerate(a1):
                bids[nSym][index] = exchange[symbols[nSym]]["bids"][0][0]
                asks[nSym][index] = exchange[symbols[nSym]]["asks"][0][0]
        # !!! \Take Bids/Asks

        print("bids: ", bids)
        print("asks: ", asks)
        print(" ")

        if file_manag.file_exists(FILE_CLOSE_ALL_TRADES):
            close_all_opened_trades(asks, bids)
            sys.exit()

        # !!! find/print opportunities
        for nSym in range(len(symbols)):
            print(f"Symbol: {symbols[nSym]} :")

            for pair in exchange_pairs:

                # FIX ME - as Vezes ele considera trade com a mesma exchange porque vale mais a pena do que seu par
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
                    (current_spread >= MIN_MARGIN)
                    and (
                        current_spread
                        <= current_pair_trailing[nSym][exchange_pairs.index(pair)]
                    )
                    and (
                        not opened_trades[nSym][
                            exchange_pairs.index(pair)
                        ].get_is_trade_open()
                    )
                ):

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
                    
                    # Added a way to stop entering new trades
                    if not file_manag.file_exists(FILE_STOP_TRADING):
                        open_trade(pair, asks, bids, current_spread, temp_exc_buy, temp_exc_sell, symbols[nSym])


                elif opened_trades[nSym][
                    exchange_pairs.index(pair)
                ].get_is_trade_open():

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

                    if (current_spread < SPREAD_TO_CLOSE_TRADE):
                        close_trade(pair, asks, bids, symbols[nSym])
                        #print("- TRADE CLOSED!!!")
                    else:
                        print("- OPENED TRADE! -", end=" ")
                        print("Opportunity Spread = {:.2%}".format(opened_trades[nSym][exchange_pairs.index(pair)].get_opportunity_spread()))

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
