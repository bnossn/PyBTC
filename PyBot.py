# -*- coding: utf-8 -*-

import asyncio
import os
import sys
import time

import BotLogging
import trade_mod
from trade_mod import TradeData, PairData
import file_management as file_manag
import ccxt
import ccxt.async_support as ccxta  # noqa: E402

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root + "/python")

async def async_client(exchange):
    tickers = {}
    try:
        # client = getattr(ccxta, exchange)()
        client = getattr(ccxta, exchange)(
            {"enableRateLimit": True}  # required accoding to the Manual
        )
        await client.load_markets(True) #True forces the reload of the maket, not fetching the cached one.
        for i in range(len(symbols)):

            if symbols[i] not in client.symbols:
                tickers[symbolsT[i]] = await client.fetch_order_book(symbolsT[i])
                # raise Exception(exchange + " does not support symbol " + symbols[i])
            else:
                tickers[symbols[i]] = await client.fetch_order_book(symbols[i])

        return tickers
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
        loggerln.info(
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


    trading_buying_reserve = amount_bought_sym1 * FEES_FACTOR # garantees you`re going to have money for fees (updated later)
    amount_bought_sym1 -= trading_buying_reserve

    trading_selling_reserve = amount_sold_sym1 * FEES_FACTOR # garantees you`re going to have money for fees updated later)
    amount_sold_sym1 -= trading_selling_reserve


    ask_price = asks_list[symbols.index(symbol)][all_exchanges.index(buying_exchange)]
    bid_price = bids_list[symbols.index(symbol)][all_exchanges.index(selling_exchange)]

    amount_bought_sym2 = amount_bought_sym1 / ask_price
    amount_sold_sym2 = amount_sold_sym1 / bid_price

    # Garantees that the amount sold/bought are the same on sym2 - That keeps trade market neutral
    # FIX ME: The best condition is to operate with the amount of sym2 bought (would garantee max profit). Take care with the margin condition
    # amount_bought_sym2 always > amount_sold_sym2
    if amount_bought_sym2 > amount_sold_sym2:
        amount_traded_sym2 = amount_sold_sym2
    else:
        amount_traded_sym2 = amount_bought_sym2
    

    # Update the amount spent in dollars on the trade according to the amount of sym2 traded (same amount of sym2 on both exchanges)
    amount_bought_sym1 = ask_price * amount_traded_sym2
    amount_sold_sym1 = bid_price * amount_traded_sym2


    # Calculates the absolute fee paid on each exchange
    perc_buying_fee = exchanges_fees[all_exchanges.index(buying_exchange)] # % of fees buying exchange
    perc_selling_fee = exchanges_fees[all_exchanges.index(selling_exchange)] # % of fees selling exchange

    abs_buy_entry_fee = amount_bought_sym1 * perc_buying_fee
    abs_sell_entry_fee = amount_sold_sym1 * perc_selling_fee

    # update the reserve amount to avoid to much fee reserved on either exchange.
    trading_buying_reserve = amount_bought_sym1 * FEES_FACTOR
    trading_selling_reserve = amount_sold_sym1 * FEES_FACTOR

    # decrease the fee paid from the reserve
    trading_buying_reserve -= abs_buy_entry_fee
    trading_selling_reserve -= abs_sell_entry_fee

    # Round all amounts here before trading (Try to avoid float point hardware approximation)
    amount_bought_sym1 = round(amount_bought_sym1, 2)
    amount_sold_sym1 = round(amount_sold_sym1, 2)
    trading_buying_reserve = round(trading_buying_reserve, 2)
    trading_selling_reserve = round(trading_selling_reserve, 2)
    abs_buy_entry_fee = round(abs_buy_entry_fee, 2)
    abs_sell_entry_fee = round(abs_sell_entry_fee, 2)


    trade_mod.buy_token(buying_exchange, amount_bought_sym1, symbol)
    trade_mod.sell_token(selling_exchange, amount_sold_sym1, symbol) # Short sell

    # Update Balances
    real_balance[all_exchanges.index(buying_exchange)] -= (amount_bought_sym1 + abs_buy_entry_fee + trading_buying_reserve)
    reserve_balance[all_exchanges.index(buying_exchange)] += trading_buying_reserve

    # YOU DO NOT DECREASE THE REAL BALANCE WHEN YOU SELL CRYPTO (Margin trade). Margin balance really needed?
    real_balance[all_exchanges.index(selling_exchange)] += amount_sold_sym1
    real_balance[all_exchanges.index(selling_exchange)] -= (abs_sell_entry_fee + trading_selling_reserve)
    reserve_balance[all_exchanges.index(selling_exchange)] += trading_selling_reserve
    #margin_balance[all_exchanges.index(selling_exchange)] += amount_sold_sym1

    # if trade sucessful:
        # Register the trade
    file_manag.register_trade(
        symbol,
        "Opening",
        spread,
        amount_traded_sym2,
        buying_exchange,
        ask_price,
        amount_bought_sym1,
        abs_buy_entry_fee,
        trading_buying_reserve,
        selling_exchange,
        bid_price,
        amount_sold_sym1,
        abs_sell_entry_fee,
        trading_selling_reserve,
        0
    )

    file_manag.updt_balance_files(
        all_exchanges, real_balance, margin_balance, reserve_balance
    )


        # Update the opened trade matrix
    opened_trades[symbols.index(symbol)][exchange_pairs.index(pair)].set_is_trade_open(True)

    opened_trades[symbols.index(symbol)][exchange_pairs.index(pair)].set_traded_symbol(symbol)

    opened_trades[symbols.index(symbol)][exchange_pairs.index(pair)].set_buying_exchange(buying_exchange)

    opened_trades[symbols.index(symbol)][exchange_pairs.index(pair)].set_amount_bought_symbol1(amount_bought_sym1)

    opened_trades[symbols.index(symbol)][exchange_pairs.index(pair)].set_fee_reserved_buying_exchange(trading_buying_reserve)

    opened_trades[symbols.index(symbol)][exchange_pairs.index(pair)].set_selling_exchange(selling_exchange)

    opened_trades[symbols.index(symbol)][exchange_pairs.index(pair)].set_amount_sold_symbol1(amount_sold_sym1)

    opened_trades[symbols.index(symbol)][exchange_pairs.index(pair)].set_fee_reserved_selling_exchange(trading_selling_reserve)

    opened_trades[symbols.index(symbol)][exchange_pairs.index(pair)].set_amount_traded_symbol2(amount_traded_sym2)

    opened_trades[symbols.index(symbol)][exchange_pairs.index(pair)].set_entry_spread(spread)

    opened_trades[symbols.index(symbol)][exchange_pairs.index(pair)].set_abs_buy_entry_fee(abs_buy_entry_fee)

    opened_trades[symbols.index(symbol)][exchange_pairs.index(pair)].set_abs_sell_entry_fee(abs_sell_entry_fee)

    opened_trades[symbols.index(symbol)][exchange_pairs.index(pair)].set_exit_spread(
        spread - SPREAD_TARGET - 2 * (perc_selling_fee + perc_buying_fee)
    )
   

        # Update the opened_trades object file
    file_manag.save_trades_data(opened_trades)

    pass


def close_trade(pair, asks_list, bids_list, symbol, spread):
    global opened_trades, pairs_data

    loggerln.info(f"Closing trade on pairs: {pair[0]}/{pair[1]} - Symbol = {symbol}")

    nsymbol = symbols.index(symbol)
    npair = exchange_pairs.index(pair)

    # find where to buy, where to sell and how much of symbol2 is going to be sold/bought
    buy_on_exchange = opened_trades[nsymbol][npair].get_selling_exchange()
    sell_on_exchange = opened_trades[nsymbol][npair].get_buying_exchange()

    amount_traded_symbol2 = opened_trades[nsymbol][npair].get_amount_traded_symbol2()

    trading_buying_reserve = opened_trades[nsymbol][npair].get_fee_reserved_selling_exchange()
    trading_selling_reserve = opened_trades[nsymbol][npair].get_fee_reserved_buying_exchange()

    # sell the buying one and buy the selling one according to the ask/bid list
    ask_price = asks_list[nsymbol][all_exchanges.index(buy_on_exchange)]
    bid_price = bids_list[nsymbol][all_exchanges.index(sell_on_exchange)]

        # Update the amount spent in dollars on the trade according to the amount of sym2 traded (same amount of sym2 on both exchanges)
    amount_bought_sym1 = ask_price * amount_traded_symbol2
    amount_sold_sym1 = bid_price * amount_traded_symbol2

    # Calculates the absolute fee paid on each exchange
    perc_buying_fee = exchanges_fees[all_exchanges.index(buy_on_exchange)] # % of fees buying exchange
    perc_selling_fee = exchanges_fees[all_exchanges.index(sell_on_exchange)] # % of fees selling exchange

    abs_buying_fee_sym1 = amount_bought_sym1 * perc_buying_fee
    abs_selling_fee_sym1 = amount_sold_sym1 * perc_selling_fee

    # Round to 2 decimals
    amount_bought_sym1 = round(amount_bought_sym1, 2)
    amount_sold_sym1 = round(amount_sold_sym1, 2)
    abs_buying_fee_sym1 = round(abs_buying_fee_sym1, 2)
    abs_selling_fee_sym1 = round(abs_selling_fee_sym1, 2)

    trade_mod.buy_token(buy_on_exchange, amount_bought_sym1, symbol) # Close short selling operation
    trade_mod.sell_token(sell_on_exchange, amount_sold_sym1, symbol)

    # Update the balances

    real_balance[all_exchanges.index(buy_on_exchange)] -= amount_bought_sym1 # Close short selling operation (Margin trade)
    reserve_balance[all_exchanges.index(buy_on_exchange)] -= trading_buying_reserve
    trading_buying_reserve -= abs_buying_fee_sym1
    real_balance[all_exchanges.index(buy_on_exchange)] += trading_buying_reserve

    real_balance[all_exchanges.index(sell_on_exchange)] += amount_sold_sym1
    reserve_balance[all_exchanges.index(sell_on_exchange)] -= trading_selling_reserve
    trading_selling_reserve -= abs_selling_fee_sym1
    real_balance[all_exchanges.index(sell_on_exchange)] += trading_selling_reserve

    total_fees = opened_trades[nsymbol][npair].get_abs_buy_entry_fee() + opened_trades[nsymbol][npair].get_abs_sell_entry_fee() + abs_buying_fee_sym1 + abs_selling_fee_sym1
    total_profit = (opened_trades[nsymbol][npair].get_amount_sold_symbol1() - opened_trades[nsymbol][npair].get_amount_bought_symbol1()) + (amount_sold_sym1 - amount_bought_sym1) - total_fees

    # register the trade
        # if trade sucessful:
    file_manag.register_trade(
        symbol,
        "Closing",
        spread,
        amount_traded_symbol2,
        buy_on_exchange,
        ask_price,
        amount_bought_sym1,
        abs_buying_fee_sym1,
        0,  # reserved_buying_fees
        sell_on_exchange,
        bid_price,
        amount_sold_sym1,
        abs_selling_fee_sym1,
        0,  # reserved_selling_fees
        total_profit
    )

    file_manag.updt_balance_files(
        all_exchanges, real_balance, margin_balance, reserve_balance
    )

    #update the opened trades
    opened_trades[nsymbol][npair].set_is_trade_open(False)
    opened_trades[nsymbol][npair] = TradeData(pair)
    # Update the opened_trades object file
    file_manag.save_trades_data(opened_trades)

    # Zero max/min spread and trailing data
    pairs_data[nsymbol][npair] = PairData(pair)

    pass


def close_all_opened_trades(asks_list, bids_list, pairs_data_list):

    for symbol in symbols:
        for pair in exchange_pairs:
            if opened_trades[symbols.index(symbol)][exchange_pairs.index(pair)].get_is_trade_open():
                close_trade(pair, asks_list, bids_list, symbol, pairs_data_list[symbols.index(symbol)][exchange_pairs.index(pair)].get_curr_spread())


def init():
    global real_balance, margin_balance, reserve_balance, opened_trades, loggerln, logger, is_online, pairs_data
    

    if not file_manag.file_exists(LOG_FILE_NAME):
        file_manag.create_file(LOG_FILE_NAME)
    #logging.basicConfig(filename=log_file_name, level=logging.INFO, format='%(message)s')
    loggerln = BotLogging.getLogger(r'\n', LOG_FILE_NAME,  terminator='\n')
    logger = BotLogging.getLogger(r' ', LOG_FILE_NAME, terminator='')
    logger.setLevel(BotLogging.logging.INFO)
    loggerln.setLevel(BotLogging.logging.INFO)


    file_manag.init_all_files(all_exchanges)


    temp_dict = file_manag.fetch_stored_balances()
    for i in range(len(all_exchanges)):
        real_balance[i] = float(temp_dict["real_balance"][all_exchanges[i]])
        margin_balance[i] = float(temp_dict["margin_balance"][all_exchanges[i]])
        reserve_balance[i] = float(temp_dict["reserve_balance"][all_exchanges[i]])


    file_name = 'tradesData.bin'
    if os.path.isfile(file_name):
        opened_trades = file_manag.load_trades_data()
    else:
        # Holds all possible combinations trading pairs/symbols and stores a TradeData for each
        opened_trades = [
            [TradeData(pair) for pair in exchange_pairs]
            for y in range(len(symbols))
        ]
        # Update the opened_trades object file
        file_manag.save_trades_data(opened_trades)


    # Holds all possible combinations trading pairs/symbols and stores a PairData for each
    pairs_data = [
            [PairData(pair) for pair in exchange_pairs]
            for y in range(len(symbols))
        ]


    is_online = [False for i in range(len(all_exchanges))]

    pass


# Pairs to trade
# symbols = ["BTC/USD", "ETH/USD", "BCH/USD", "LTC/USD", "XLM/USD", "XRP/USD", "ZEC/USD"] # With margin Trade
symbols = ["ETH/USD", "EOS/USD", "XRP/USD", ] #Without Margin trade (Transfering currencies) 
symbolsT = ["ETH/USDT", "EOS/USDT", "XRP/USDT", ] #Without Margin trade (Transfering currencies) 
#symbols = ["BTC/USD", "ETH/USD"]
# Exchanges to trade
#all_exchanges = ["bitfinex", "kraken", "okcoinusd", "cex"]
# all_exchanges = ["binance", "huobipro", "hitbtc2", "zb", "gateio", "kucoin"] # USDT
# all_exchanges = ["coinbasepro", "bitfinex", "kraken", "exmo", "yobit"] #USD
usdt_exchanges = ["binance", "huobipro", "hitbtc2", "zb", "gateio", "kucoin"]
usd_exchanges = ["coinbasepro", "bitfinex", "kraken", "exmo", "yobit"]
all_exchanges = ["binance", "huobipro", "hitbtc2", "zb", "coinbasepro"]
exchanges_fees = [0.25/100 for i in range(len(all_exchanges))]
# Holds whether an exchange fetch was not successful
is_online = []
# All possible trading Pairs:
exchange_pairs = list_unique_pairs(all_exchanges)
# Usado  para gravar os TradeData e para garantir que o bot não entrará na mesma operação duas vezes.
opened_trades = []
#Used mainly to record the spread data of each pair / symbol 
pairs_data = []

# max_pair_spread = [[], []]
# min_pair_spread = [[], []]
# current_pair_trailing = [[], []]
# current_pairs_spread = [[], []]

# Trailing is the percentage from the max to trade
TRIGGER_SPREAD = 1/100
SPREAD_TARGET = 0.5/100
TRAILING_STOP = 0.9

# TRIGGER_SPREAD = 0.2/100
# SPREAD_TARGET = -2/100
# TRAILING_STOP = 0.99


# FIX ME: balances NOT USED
# Trading Accounts - Considers all accounts starts with USD only.
real_balance = [0 for x in range(len(all_exchanges))]
margin_balance = [0 for x in range(len(all_exchanges))]
# Amount reserved to pay for fees
reserve_balance = [0 for x in range(len(all_exchanges))]
# Percentage of the trade reserved for fees.
FEES_FACTOR = 5/100
# Min amount per trade
MIN_TRADE_AMOUNT = 50
# Max ammount traded in each oppotunity found (If balance < TRADING_AMOUNT, oppotunity is going to take all balance available):
TRADING_AMOUNT = 2500

FILE_STOP_TRADING = "stoptrading.txt"
FILE_CLOSE_ALL_TRADES = "closetrades.txt"

# Log file and variables
LOG_FILE_NAME = "./logFiles/tradings.log"
loggerln = None
logger = None

if __name__ == "__main__":

    init()

    print("%d pairings" % len(exchange_pairs))

    loggerln.info("%d pairings" % len(exchange_pairs))

    print(f"real_balance = {real_balance}")
    print(f"margin_balance = {margin_balance}")
    print(f"reserve_balance = {reserve_balance}")
    print(" ")

    # Counter used to know that the code is still running from the python terminal
    ncounter = 0

    loggerln.info(f"real_balance = {real_balance}")
    loggerln.info(f"margin_balance = {margin_balance}")
    loggerln.info(f"reserve_balance = {reserve_balance}")
    loggerln.info(" ")


    while True:

        print(f"Code running, cycle: {ncounter}")
        ncounter += 1

        # Holds on two dimensiona array [Exchange][Symbol]
        bids = [[0 for x in range(len(all_exchanges))] for y in range(len(symbols))]
        asks = [[0 for x in range(len(all_exchanges))] for y in range(len(symbols))]

        # !!! Fetch data
        tic = time.time()
        loop = asyncio.get_event_loop()
        a1 = loop.run_until_complete(multi_orderbooks(all_exchanges))

        loggerln.info("async call spend: {:.2f}  -  TimeStamp: {}".format((time.time() - tic), str(file_manag.get_timestamp())))
        # !!! \Fetch data
        loggerln.info(" ")

        # Update the isOnline list according to the returned values/exceptions
        for i in range(len(all_exchanges)):
            is_online[i] = not isinstance(a1[i], Exception)

        # !!! Take Bids/Asks
        for nSym in range(len(symbols)):
            for index, exchange in enumerate(a1):
                if is_online[index]:
                    if all_exchanges[index] in usd_exchanges:
                        bids[nSym][index] = exchange[symbols[nSym]]["bids"][0][0]
                        asks[nSym][index] = exchange[symbols[nSym]]["asks"][0][0]
                    else:
                        bids[nSym][index] = exchange[symbolsT[nSym]]["bids"][0][0]
                        asks[nSym][index] = exchange[symbolsT[nSym]]["asks"][0][0]
        # !!! \Take Bids/Asks

        loggerln.info(f"bids: {bids}")
        loggerln.info(f"asks: {asks}")
        loggerln.info(" ")

        if file_manag.file_exists(FILE_CLOSE_ALL_TRADES):
            close_all_opened_trades(asks, bids, pairs_data)
            sys.exit()

        # !!! finding/logging opportunities
        for nSym in range(len(symbols)):
            loggerln.info(f"Symbol: {symbols[nSym]} :")

            for nPair, pair in enumerate(exchange_pairs):
                
                # Check if any of the two exchanges are offline and do nothing if so
                if (not is_online[all_exchanges.index(pair[0])]) or (not is_online[all_exchanges.index(pair[1])]):
                    logger.info("Either Exchange is Offline: Pair = {}/{}".format(pair[0][:3], pair[1][:3]))
                    logger.info(" - {} = ".format(pair[0], ))
                    logger.info("Online") if is_online[all_exchanges.index(pair[0])] else logger.info("Offline")
                    logger.info(" / {} = ".format(pair[1], ))
                    loggerln.info("Online") if is_online[all_exchanges.index(pair[1])] else loggerln.info("Offline")
                    continue


                # Spread for opened trades are calculated in a different manner                
                if opened_trades[nSym][nPair].get_is_trade_open():
                    # Buy on the one you initially sold and sell on the one you initially bought
                    temp_exc_buy = opened_trades[nSym][nPair].get_selling_exchange()
                    temp_exc_sell = opened_trades[nSym][nPair].get_buying_exchange()

                    # Consider the prices to exit the trade, not the ones used to enter the trade
                    temp_ask = asks[nSym][all_exchanges.index(opened_trades[nSym][nPair].get_selling_exchange())]
                    temp_bid = bids[nSym][all_exchanges.index(opened_trades[nSym][nPair].get_buying_exchange())]                    

                    # To exit the trade, the calculated spread has to be the inverse.
                    pairs_data[nSym][nPair].set_curr_spread((temp_ask / temp_bid) - 1)
                else: 
                    
                    temp_spread_1 = (bids[nSym][all_exchanges.index(pair[0])] / asks[nSym][all_exchanges.index(pair[1])]) - 1
                    temp_spread_2 = (bids[nSym][all_exchanges.index(pair[1])] / asks[nSym][all_exchanges.index(pair[0])]) - 1

                    if (temp_spread_1 > temp_spread_2):
                        temp_ask = asks[nSym][all_exchanges.index(pair[1])]
                        temp_exc_buy = pair[1]
                        temp_bid = bids[nSym][all_exchanges.index(pair[0])]
                        temp_exc_sell = pair[0]
                    else:
                        temp_ask = asks[nSym][all_exchanges.index(pair[0])]
                        temp_exc_buy = pair[0]
                        temp_bid = bids[nSym][all_exchanges.index(pair[1])]
                        temp_exc_sell = pair[1]
                    pairs_data[nSym][nPair].set_curr_spread((temp_bid / temp_ask) - 1)


                # Calculates the all times spread max, min e traling
                if (
                    pairs_data[nSym][nPair].get_curr_spread() > pairs_data[nSym][nPair].get_max_spread()
                ) or (pairs_data[nSym][nPair].get_max_spread() == 0):
                    pairs_data[nSym][nPair].set_max_spread(pairs_data[nSym][nPair].get_curr_spread())

                    pairs_data[nSym][nPair].set_curr_trailing(pairs_data[nSym][nPair].get_max_spread() * TRAILING_STOP)


                if (
                    pairs_data[nSym][nPair].get_curr_spread() < pairs_data[nSym][nPair].get_min_spread()
                ) or (pairs_data[nSym][nPair].get_min_spread() == 0):
                    pairs_data[nSym][nPair].set_min_spread(pairs_data[nSym][nPair].get_curr_spread())
                
                # \Calculates the all times spread max, min e traling


                # Verificar condicao para entrar no trade
                if (
                    (pairs_data[nSym][nPair].get_curr_spread() >= TRIGGER_SPREAD)
                    and (
                        pairs_data[nSym][nPair].get_curr_spread() <= pairs_data[nSym][nPair].get_curr_trailing()
                    )
                    and (
                        not opened_trades[nSym][nPair].get_is_trade_open()
                    )
                ):

                    logger.info(
                        "Pair (buy/sell): {}/{} (% Max Spread: {:.2%}, Min Spread: {:.2%}, Spread: {:.2%}, Trailing: {:.2%})".format(
                            temp_exc_buy[:3],
                            temp_exc_sell[:3],
                            pairs_data[nSym][nPair].get_max_spread(),
                            pairs_data[nSym][nPair].get_min_spread() ,
                            pairs_data[nSym][nPair].get_curr_spread(),
                            pairs_data[nSym][nPair].get_curr_trailing(),
                        ),
                    )
                    logger.info(" - Opportunity Found!")
                    
                    # Added a way to stop entering new trades
                    if not file_manag.file_exists(FILE_STOP_TRADING):
                        open_trade(pair, asks, bids, pairs_data[nSym][nPair].get_curr_spread(), temp_exc_buy, temp_exc_sell, symbols[nSym])
                    else:
                        logger.info(" New Trades are Paused")

                    loggerln.info("")

                elif opened_trades[nSym][nPair].get_is_trade_open():

                    logger.info(
                        "Pair (buy/sell): {}/{} (% Max Spread: {:.2%}, Min Spread: {:.2%}, Spread: {:.2%}, Trailing: {:.2%})".format(
                            temp_exc_buy[:3],
                            temp_exc_sell[:3],
                            pairs_data[nSym][nPair].get_max_spread(),
                            pairs_data[nSym][nPair].get_min_spread(),
                            pairs_data[nSym][nPair].get_curr_spread(),
                            pairs_data[nSym][nPair].get_curr_trailing(),
                        ),
                    )

                    if (pairs_data[nSym][nPair].get_curr_spread() <= opened_trades[nSym][nPair].get_exit_spread()):
                        close_trade(pair, asks, bids, symbols[nSym], pairs_data[nSym][nPair].get_curr_spread())
                        #rlogger.info("- TRADE CLOSED!!!")
                    else:
                        logger.info(" - OPENED TRADE! - ")
                        loggerln.info("Entry Spread = {:.2%} - Exit Spread = {:.2%}".format(
                            opened_trades[nSym][nPair].get_entry_spread(),
                            opened_trades[nSym][nPair].get_exit_spread(),
                            )
                        )


                else:

                    loggerln.info(
                        "Pair (buy/sell): {}/{} (% Max Spread: {:.2%}, Min Spread: {:.2%}, Spread: {:.2%}, Trailing: {:.2%})".format(
                            temp_exc_buy[:3],
                            temp_exc_sell[:3],
                            pairs_data[nSym][nPair].get_max_spread(),
                            pairs_data[nSym][nPair].get_min_spread(),
                            pairs_data[nSym][nPair].get_curr_spread(),
                            pairs_data[nSym][nPair].get_curr_trailing(),
                        )
                    )
                # \Verificar condicao para entrar no trade

            # Show the best available pair to operate on each symbol
        
            operate_pair_spread = -100 # Starts with a pretty low number
            is_pair_available = False
            for nPair, pair in enumerate(exchange_pairs):
                if not opened_trades[nSym][exchange_pairs.index(pair)].get_is_trade_open():
                    if operate_pair_spread < pairs_data[nSym][nPair].get_curr_spread():
                        operate_pair_spread = pairs_data[nSym][nPair].get_curr_spread()
                        temp_min_ask = min(asks[nSym][all_exchanges.index(pair[0])], asks[nSym][all_exchanges.index(pair[1])])
                        temp_max_bid = max(bids[nSym][all_exchanges.index(pair[0])], bids[nSym][all_exchanges.index(pair[1])])
                        is_pair_available = True
            
            if is_pair_available:
                min_ask_index = asks[nSym][::].index(temp_min_ask)
                max_bid_index = bids[nSym][::].index(temp_max_bid)
                loggerln.info("!!!! Operate on \\/ !!!!")
                loggerln.info(
                    f"Buy/Sell = {all_exchanges[min_ask_index]} / {all_exchanges[max_bid_index]}"
                )
                loggerln.info(
                    "Highest Absolute Spread: {:.2f}".format(
                        temp_max_bid - temp_min_ask
                    )
                )

                # temp_max_spread handles ZeroDivisionError
                loggerln.info("% Spread: {:.2%}".format(operate_pair_spread))
                # loggerln.info("% Spread: {:.2%}".format(((max(bids[nSym][::]) / min(asks[nSym][::])) - 1)))
            else:
                loggerln.info("There are no Pairs Available for Trading")

            loggerln.info(" ")
            # \Show the best available pair to operate on each symbol

        # !!! \finding/logging opportunities



        loggerln.info("----------------------------------------------------------------")
