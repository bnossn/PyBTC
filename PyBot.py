# -*- coding: utf-8 -*-

import asyncio
import os
import sys
import time
from collections import defaultdict

import BotLogging
import trade_mod
from trade_mod import TradeData, PairData
import file_management as file_manag
# import ccxt
from ccxt import decimal_to_precision
from ccxt import TRUNCATE
from ccxt import DECIMAL_PLACES
import ccxt.async_support as ccxta  # noqa: E402

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root + "/python")

# async def async_client(exchange):
#     tickers = {}
#     try:
#         await exchange.load_markets(True) #True forces the reload of the maket, not fetching the cached one.
#         for i in range(len(symbols)):

#             if symbols[i] not in exchange.symbols:
#                 tickers[symbolsT[i]] = await exchange.fetch_l2_order_book(symbolsT[i], 100)
#             else:
#                 tickers[symbols[i]] = await exchange.fetch_l2_order_book(symbols[i], 100)

#         return tickers
#     finally:
#         await exchange.close()


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


async def instantiate_exchange(exchange):
    exch_obj = getattr(ccxta, exchange)(
        {"enableRateLimit": True}  # required accoding to the Manual
    )
    await exch_obj.load_markets(True)
    return exch_obj


def calc_avg_price(price_table):
    # False is returned whenever trading amount takes the entire order book
    # avg_price is returned either way.

    max_trading_cost = TRADING_AMOUNT * SAFE_ORDERBOOK_MULTIPLIER
    curr_trading_cost = 0
    curr_trading_volume = 0

    for price, volume in price_table:
        if curr_trading_cost < max_trading_cost:
            curr_trading_cost += price * volume
            curr_trading_volume += volume
        else:
            avg_price = curr_trading_cost / curr_trading_volume
            return True, avg_price

    avg_price = curr_trading_cost / curr_trading_volume
    return False, avg_price


def list_unique_pairs(source1, source2):
    result = []
    for p1 in range(len(source1)):
        for p2 in range(len(source2)):
            if ([source2[p2], source1[p1]] not in result) and (source1[p1] != source2[p2]): #remove duplicates
                result.append([source1[p1], source2[p2]])
    return result


def print_ask_bid_table(asks, bids):
    logger.info("               ")
    for exchange in all_exchanges:
        logger.info("{}         ".format(exchange[:3]))
    loggerln.info("")
    for sym in symbols:
        logger.info(sym + " ")
        for i in range(2):
            logger.info("asks ")  if i == 0 else logger.info("        bids ")
            for exchange in all_exchanges:
                if i == 0:
                    if asks[exchange][sym] >= 100:
                        logger.info("{:.4f} <> ".format(asks[exchange][sym]))
                    else:
                        logger.info("  {:.4f} <> ".format(asks[exchange][sym]))
                else:
                    if bids[exchange][sym] >= 100:
                        logger.info("{:.4f} <> ".format(bids[exchange][sym]))
                    else:
                        logger.info("  {:.4f} <> ".format(bids[exchange][sym]))

            loggerln.info("")
        loggerln.info("")


def open_trade(pair, asks, bids, symbol, spread, buying_exchange, selling_exchange):
    global opened_trades

    # garantees that the exchange has at least the MIN_TRADE_AMOUNT avaiable for trading
    if (real_balance[buying_exchange] < MIN_TRADE_AMOUNT):
        return False, f"Insuficient USD amount available on {buying_exchange}"


  #### Handles the USD/USDT difference in the exchange methods. ####
    if buying_exchange in usdt_exchanges:
        buying_symbol = symbol + "T"
    else:
        buying_symbol = symbol

    if selling_exchange in usdt_exchanges:
        selling_symbol = symbol + "T"
    else:
        selling_symbol = symbol
  #### \Handles the USD/USDT difference in the exchange methods. ####

  #### Get the Fees ####
    if exchanges_obj[all_exchanges.index(buying_exchange)].markets[buying_symbol]['percentage']:
        buying_maker_fee = exchanges_obj[all_exchanges.index(buying_exchange)].markets[buying_symbol]['maker']
    else:
        return False, f"Exchange {buying_exchange} don`t use percentage fee on market {symbol}"

    if exchanges_obj[all_exchanges.index(selling_exchange)].markets[selling_symbol]['percentage']:
        selling_maker_fee = exchanges_obj[all_exchanges.index(selling_exchange)].markets[selling_symbol]['maker']
    else:
        return False, f"Exchange {selling_exchange} don`t use percentage fee on market {symbol}"
  #### \Get the Fees ####

  #### Get and check the precision ####
    amount_sym2_precision = exchanges_obj[all_exchanges.index(buying_exchange)].markets[buying_symbol]['precision']['amount']

    # A negative amount precision means that the amount should be an integer multiple of 10
    if (amount_sym2_precision < 0):
        return False, f"Coin `{symbol}` amount must be multiple of 10 and is not implemented on {buying_exchange} yet."
  #### \Get and check the precision ####


    # Find out how much usd you are going to spend on the trade.
    # Amount bought sym1 means that it was bought x dollars worth of sym2
    if real_balance[buying_exchange] > TRADING_AMOUNT:
        amount_bought_sym1 = TRADING_AMOUNT
    else:
        amount_bought_sym1 = real_balance[buying_exchange]


    ask_price = asks[buying_exchange][symbol]
    bid_price = bids[selling_exchange][symbol]

    amount_bought_sym2 = amount_bought_sym1 / ask_price

    #Amount that will be bought!!!!!!! \/ (fees will be taken from this amount)
    str_amount_bought_sym2 = decimal_to_precision(amount_bought_sym2, TRUNCATE, amount_sym2_precision, DECIMAL_PLACES)
    amount_bought_sym2 = float(str_amount_bought_sym2)


  #### Handles Limits ####
    max_amount_limit = exchanges_obj[all_exchanges.index(buying_exchange)].markets[buying_symbol]['limits']['amount']['max']
    if max_amount_limit != None:
        if amount_bought_sym2 > max_amount_limit:
            amount_bought_sym2 = exchanges_obj[all_exchanges.index(buying_exchange)].markets[buying_symbol]['limits']['amount']['max']
            amount_bought_sym1 = amount_bought_sym2 * ask_price

    min_amount_limit = exchanges_obj[all_exchanges.index(buying_exchange)].markets[buying_symbol]['limits']['amount']['min']
    if min_amount_limit != None:
        if amount_bought_sym2 < min_amount_limit:
            return False, f"Amount of Crypto you tried to buy is below the minimum allowed by {buying_exchange}"
  #### \Handles Limits ####

    if SIM_MODE:

        #Update amount in usd according to the new amount in Crypto
        amount_bought_sym1 = amount_bought_sym2 * ask_price

        calculated_fees_sym2 = (buying_maker_fee * amount_bought_sym2) + withdraw_fees[symbol]

        amount_bought_sym1 = round(amount_bought_sym1, 2)
        calculated_fees_sym2 = round(calculated_fees_sym2, amount_sym2_precision)

        # Update Balances
        real_balance[buying_exchange] -= (amount_bought_sym1)

      #### Expected results on the selling exchange if trade was instantaneous ####
        expected_amount_selling_exchange_sym2 = amount_bought_sym2 - calculated_fees_sym2
        expected_selling_fees = (expected_amount_selling_exchange_sym2 * bid_price) * selling_maker_fee
        expected_total_sold_sym1 = (expected_amount_selling_exchange_sym2 * bid_price) - expected_selling_fees
      #### \Expected results on the selling exchange if trade was instantaneous ####

    else:
        pass
        # CODE FOR ACTUAL TRADING GOES HERE

        # trade_mod.buy_token(buying_exchange, amount_bought_sym1, symbol)
        # trade_mod.sell_token(selling_exchange, amount_sold_sym1, symbol) # Short sell


    # if trade sucessful:
        # Register the trade
    file_manag.register_trade(
        symbol,
        "Opening",
        spread,
        amount_bought_sym2,
        buying_exchange,
        ask_price,
        amount_bought_sym1,
        calculated_fees_sym2,
        selling_exchange,
        expected_amount_selling_exchange_sym2,
        bid_price,
        expected_total_sold_sym1,
        expected_selling_fees,
        0
    )

    file_manag.updt_balance_files(all_exchanges, real_balance)

    nsymbol = symbols.index(symbol)
    npair = exchange_pairs.index(pair)

        # Update the opened trade matrix
    opened_trades[npair][nsymbol].set_is_trade_open(True)

    opened_trades[npair][nsymbol].set_traded_symbol(symbol)

    opened_trades[npair][nsymbol].set_buying_exchange(buying_exchange)

    opened_trades[npair][nsymbol].set_amount_bought_symbol1(amount_bought_sym1)

    opened_trades[npair][nsymbol].set_total_fees_buying_exchange(calculated_fees_sym2)

    opened_trades[npair][nsymbol].set_total_bought_sym2(amount_bought_sym2)

    opened_trades[npair][nsymbol].set_selling_exchange(selling_exchange)

    opened_trades[npair][nsymbol].set_expected_amount_selling_sym2(expected_amount_selling_exchange_sym2)

    opened_trades[npair][nsymbol].set_expected_total_sold_sym1(expected_total_sold_sym1)

    opened_trades[npair][nsymbol].set_expected_selling_fees(expected_selling_fees)

    opened_trades[npair][nsymbol].set_entry_spread(spread)

    opened_trades[npair][nsymbol].set_opp_initial_time(time.time())

    # Update the opened_trades object file
    file_manag.save_trades_data(opened_trades)

    return True, "Trade was Successful!"
    pass


def close_trade(pair, asks, bids, symbol, spread):
    global opened_trades, pairs_spread_data

  #### Check if transference has been accomplished ####
    if SIM_MODE:
        tic = opened_trades[exchange_pairs.index(pair)][symbols.index(symbol)].get_opp_initial_time()
        if (time.time() - tic) <= transfer_time[symbol]:
            return False, "Transference is still on the go"

    else:
        pass
        # CODE FOR ACTUAL TRADING GOES HERE

  #### \Check if transference has been accomplished ####

    nsymbol = symbols.index(symbol)
    npair = exchange_pairs.index(pair)

    selling_exchange = opened_trades[npair][nsymbol].get_selling_exchange()
    buying_exchange = opened_trades[npair][nsymbol].get_buying_exchange()

    loggerln.info(f"Closing trade on pairs: {pair[0]}/{pair[1]} - Symbol = {symbol} - by selling on {selling_exchange}")

  #### Handles the USD/USDT difference in the exchange methods. ####
    if buying_exchange in usdt_exchanges:
        buying_symbol = symbol + "T"
    else:
        buying_symbol = symbol

    if selling_exchange in usdt_exchanges:
        selling_symbol = symbol + "T"
    else:
        selling_symbol = symbol
  #### \Handles the USD/USDT difference in the exchange methods. ####

  #### Get the Fees ####
    if exchanges_obj[all_exchanges.index(buying_exchange)].markets[buying_symbol]['percentage']:
        buying_maker_fee = exchanges_obj[all_exchanges.index(buying_exchange)].markets[buying_symbol]['maker']
    else:
        return False, f"Exchange {buying_exchange} don`t use percentage fee on market {symbol}"

    if exchanges_obj[all_exchanges.index(selling_exchange)].markets[selling_symbol]['percentage']:
        selling_maker_fee = exchanges_obj[all_exchanges.index(selling_exchange)].markets[selling_symbol]['maker']
    else:
        return False, f"Exchange {selling_exchange} don`t use percentage fee on market {symbol}"
  #### \Get the Fees ####


    ask_price = asks[buying_exchange][symbol]
    bid_price = bids[selling_exchange][symbol]


    if SIM_MODE:
        amount_received_sym2 = opened_trades[npair][nsymbol].get_expected_amount_selling_sym2()
        selling_fees_sym1 = (amount_received_sym2 * bid_price) * selling_maker_fee
        amount_sold_sym1 = (amount_received_sym2 * bid_price) - selling_fees_sym1

        amount_sold_sym1 = round(amount_sold_sym1, 2)
        selling_fees_sym1 = round(selling_fees_sym1, 2)

        # Update Balances
        real_balance[selling_exchange] += (amount_sold_sym1)

        total_profit = amount_sold_sym1 - opened_trades[npair][nsymbol].get_amount_bought_symbol1()

    else:
        pass
        # CODE FOR ACTUAL TRADING GOES HERE

        # trade_mod.buy_token(buy_on_exchange, amount_bought_sym1, symbol) # Close short selling operation
        # trade_mod.sell_token(sell_on_exchange, amount_sold_sym1, symbol)

    # Update the balances


    # if trade sucessful:
        # Register the trade
    file_manag.register_trade(
        symbol,
        "Closing",
        spread,
        opened_trades[npair][nsymbol].get_total_bought_sym2(),
        buying_exchange,
        ask_price,
        opened_trades[npair][nsymbol].get_amount_bought_symbol1(),
        opened_trades[npair][nsymbol].get_total_fees_buying_exchange(),
        selling_exchange,
        amount_received_sym2,
        bid_price,
        amount_sold_sym1,
        selling_fees_sym1,
        total_profit
    )

    file_manag.updt_balance_files(all_exchanges, real_balance)

  #### Update the opened_trades object file ####
    opened_trades[npair][nsymbol].set_is_trade_open(False)
    opened_trades[npair][nsymbol] = TradeData(pair)
  #### \Update the opened_trades object file ####
    file_manag.save_trades_data(opened_trades)

    # Zero max/min spread and trailing data
    pairs_spread_data[npair][nsymbol] = PairData(pair)

    return True, "Close was Successful!"
    pass


def close_all_opened_trades(asks_list, bids_list, pairs_spread_data_list):

    for symbol in symbols:
        for pair in exchange_pairs:
            if opened_trades[exchange_pairs.index(pair)][symbols.index(symbol)].get_is_trade_open():
                close_trade(pair, asks_list, bids_list, symbol, pairs_spread_data_list[exchange_pairs.index(pair)][symbols.index(symbol)].get_curr_spread())


def init():
    global real_balance, margin_balance, exchanges_obj, opened_trades, loggerln, logger, is_online, pairs_spread_data, all_exchanges, exchange_pairs
    
    can_buy_exchanges.sort()
    can_sell_exchanges.sort()
    all_exchanges.extend(can_buy_exchanges)
    all_exchanges.extend(can_sell_exchanges)
    all_exchanges = list(set(all_exchanges)) #Transform it into a list of unique values
    all_exchanges.sort() # Sets are ordered randomly. This line garantees the order is always kept.


    exchange_pairs = list_unique_pairs(can_buy_exchanges, can_sell_exchanges)


    for exchange in all_exchanges:
        real_balance[exchange] = 0

        is_online[exchange] = False

        # exch_obj = getattr(ccxta, exchange)(
        #     {"enableRateLimit": True}  # required accoding to the Manual
        # )
        # exch_obj.load_markets()
        # exchanges_obj.append(exch_obj)

    tasks = [instantiate_exchange(exchange) for exchange in all_exchanges]
    loop = asyncio.get_event_loop()
    exchanges_obj = loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))


    if not file_manag.file_exists(LOG_FILE_NAME):
        file_manag.create_file(LOG_FILE_NAME)
    #logging.basicConfig(filename=log_file_name, level=logging.INFO, format='%(message)s')
    loggerln = BotLogging.getLogger(r'\n', LOG_FILE_NAME,  terminator='\n')
    logger = BotLogging.getLogger(r' ', LOG_FILE_NAME, terminator='')
    logger.setLevel(BotLogging.logging.INFO)
    loggerln.setLevel(BotLogging.logging.INFO)


    file_manag.init_all_files(all_exchanges)


    temp_dict = file_manag.fetch_stored_balances()
    for key in temp_dict["real_balance"]:
        if key in real_balance:
            real_balance[key] = float(temp_dict["real_balance"][key])


    file_name = 'tradesData.bin'
    if os.path.isfile(file_name):
        opened_trades = file_manag.load_trades_data()
    else:
        # Holds all possible combinations trading pairs/symbols and stores a TradeData for each
        opened_trades = [
            [TradeData(pair) for y in range(len(symbols))]
            for pair in exchange_pairs
        ]
        # Update the opened_trades object file
        file_manag.save_trades_data(opened_trades)


    # Holds all possible combinations trading pairs/symbols and stores a PairData for each
    pairs_spread_data = [
            [PairData(pair) for y in range(len(symbols))]
            for pair in exchange_pairs
        ]

    pass


# exchanges_fees = [0.25/100 for i in range(len(all_exchanges))]

all_exchanges = [] # All registered exchanges (String)
exchange_pairs = [] # All possible trading Pairs (String)
exchanges_obj = []  # a placeholder for your instances (ccxta object)
is_online = {} # Holds whether an exchange fetch was not successful (Boolean)
opened_trades = [] # Usado  para gravar os TradeData e para garantir que o bot não entrará na mesma operação duas vezes. (TradeData object)
pairs_spread_data = [] #Used mainly to record the spread data of each pair / symbol (PairData Object)

#Balances:
real_balance = {}
# Amount reserved to pay for fees
# reserve_balance = [0 for x in range(len(all_exchanges))]


SIM_MODE = True # True indicates that simulation mode is on (Don't use private methods)
TRADING_MODE = False #False indicates that trades will not be perfomed but private methods will be used.
# Symbols to trade
symbols = ("ETH/USD", "EOS/USD", "XRP/USD") #Without Margin trade (Transfering currencies) 
symbolsT = ("ETH/USDT", "EOS/USDT", "XRP/USDT") #Without Margin trade (Transfering currencies)
withdraw_fees = {"ETH/USD" : 0.01 ,"EOS/USD": 0.1, "XRP/USD": 0.25}
transfer_time = {"ETH/USD" : 10*60, "EOS/USD": 10*60, "XRP/USD": 10*60}
# transfer_time = {"ETH/USD" : 10,"EOS/USD": 10, "XRP/USD": 10}


# Exchanges to trade
# all_exchanges = ["binance", "huobipro", "hitbtc2", "zb", "coinbasepro", "kucoin", "exmo", "poloniex" ]
usdt_exchanges = ["binance", "huobipro", "hitbtc2", "zb", "gateio", "kucoin", "poloniex"]
usd_exchanges = ["coinbasepro", "bitfinex", "kraken", "exmo", "yobit"]

can_buy_exchanges = ["binance", "huobipro", "hitbtc2", "zb", "coinbasepro", "kucoin", "exmo", "poloniex" ]
can_sell_exchanges = ["binance", "huobipro", "hitbtc2", "zb", "coinbasepro", "kucoin", "exmo", "poloniex" ]


# Trailing is the percentage from the max to trade
TRIGGER_SPREAD = 1/100
TRAILING_STOP = 0.9

# TRIGGER_SPREAD = 0.2/100
# TRAILING_STOP = 0.9


# FEES_FACTOR = 5/100 # Percentage of the trade reserved for fees.
MIN_TRADE_AMOUNT = 50 # Min amount per trade (in USD)
MIN_CRYPT_TRADE_AMOUNT = {"ETH/USD" : 50, "EOS/USD": 50, "XRP/USD":22}
TRADING_AMOUNT = 2500 # Max ammount traded in each opportunity found (If balance < TRADING_AMOUNT, oppotunity is going to take all balance available)
SAFE_ORDERBOOK_MULTIPLIER = 3  # Orders are calculated for n times the trading amount (to keep safe from low liquidity)

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
    print(" ")

    # Counter used to know that the code is still running from the python terminal
    ncounter = 0

    loggerln.info(f"real_balance = {real_balance}")
    loggerln.info(" ")


    while True:

        print(f"Code running, cycle: {ncounter}")
        ncounter += 1

        # Holds on two dimensiona array [Exchange][Symbol]
        bids = defaultdict(dict)
        asks = defaultdict(dict)
        has_bid_liquidity = defaultdict(dict)
        has_ask_liquidity = defaultdict(dict)
        for exchange in all_exchanges:
            for symbol in symbols:
                bids[exchange][symbol] = 0
                asks[exchange][symbol] = 0
                has_bid_liquidity[exchange][symbol] = False
                has_ask_liquidity[exchange][symbol] = False


        # !!! Fetch data
        tic = time.time()
        loop = asyncio.get_event_loop()
        a1 = loop.run_until_complete(multi_orderbooks(all_exchanges))

        loggerln.info("async call spend: {:.2f}  -  TimeStamp: {}".format((time.time() - tic), str(file_manag.get_timestamp())))
        # !!! \Fetch data
        loggerln.info(" ")

        # Update the isOnline list according to the returned values/exceptions
        for i in range(len(all_exchanges)):
            is_online[all_exchanges[i]] = not isinstance(a1[i], Exception)


        # !!! Take Bids/Asks
        for nSym, Sym in enumerate(symbols):
            for index, symbol_pairs in enumerate(a1):
                if is_online[all_exchanges[index]]:
                    if all_exchanges[index] in usd_exchanges:
                        has_bid_liquidity[all_exchanges[index]][Sym], bids[all_exchanges[index]][Sym] = calc_avg_price(symbol_pairs[symbols[nSym]]["bids"]) if len (symbol_pairs[symbols[nSym]]["bids"]) > 0 else None
                        has_ask_liquidity[all_exchanges[index]][Sym], asks[all_exchanges[index]][Sym] = calc_avg_price(symbol_pairs[symbols[nSym]]["asks"]) if len (symbol_pairs[symbols[nSym]]["asks"]) > 0 else None
                    else:
                        has_bid_liquidity[all_exchanges[index]][Sym], bids[all_exchanges[index]][Sym] = calc_avg_price(symbol_pairs[symbolsT[nSym]]["bids"]) if len (symbol_pairs[symbolsT[nSym]]["bids"]) > 0 else None
                        has_ask_liquidity[all_exchanges[index]][Sym], asks[all_exchanges[index]][Sym] = calc_avg_price(symbol_pairs[symbolsT[nSym]]["asks"]) if len (symbol_pairs[symbolsT[nSym]]["asks"]) > 0 else None
        # !!! \Take Bids/Asks


        print_ask_bid_table(asks, bids)
        

        # if file_manag.file_exists(FILE_CLOSE_ALL_TRADES):
        #     close_all_opened_trades(asks, bids, pairs_spread_data)
        #     sys.exit()

        # !!! finding/logging opportunities
        was_trade_opened = False #Used to avoid openning more than one trade in row. Once one trade is opened, wait for next fetch to open a new trade.
        for nSym, Sym in enumerate(symbols):
            loggerln.info(f"Symbol: {Sym} :")

            for nPair, pair in enumerate(exchange_pairs):
                
                # Check if any of the two exchanges are offline and do nothing if so
                if (not is_online[pair[0]]) or (not is_online[pair[1]]):
                    logger.info("Either Exchange is Offline: Pair = {}/{}".format(pair[0][:3], pair[1][:3]))
                    logger.info(" - {} = ".format(pair[0][:3]))
                    logger.info("Online") if is_online[pair[0]] else logger.info("Offline")
                    logger.info(" / {} = ".format(pair[1][:3]))
                    loggerln.info("Online") if is_online[pair[1]] else loggerln.info("Offline")
                    continue


                temp_spread_1 = -100 #Garantees that spread2 is used if it cannot sell/buy in either exchange
                temp_spread_2 = -100 #Garantees that spread1 is used if it cannot sell/buy in either exchange
                if (pair[0] in can_sell_exchanges and pair[1] in can_buy_exchanges):
                    temp_spread_1 = (bids[pair[0]][Sym] / asks[pair[1]][Sym]) - 1

                if (pair[1] in can_sell_exchanges and pair[0] in can_buy_exchanges):
                    temp_spread_2 = (bids[pair[1]][Sym] / asks[pair[0]][Sym]) - 1


                if (temp_spread_1 > temp_spread_2):
                    temp_ask = asks[pair[1]][Sym]
                    temp_exc_buy = pair[1]
                    temp_bid = bids[pair[0]][Sym]
                    temp_exc_sell = pair[0]
                else:
                    temp_ask = asks[pair[0]][Sym]
                    temp_exc_buy = pair[0]
                    temp_bid = bids[pair[1]][Sym]
                    temp_exc_sell = pair[1]
                pairs_spread_data[nPair][nSym].set_curr_spread((temp_bid / temp_ask) - 1)


                # Calculates the all times spread max, min e traling
                if (
                    pairs_spread_data[nPair][nSym].get_curr_spread() > pairs_spread_data[nPair][nSym].get_max_spread()
                ) or (pairs_spread_data[nPair][nSym].get_max_spread() == 0):
                    pairs_spread_data[nPair][nSym].set_max_spread(pairs_spread_data[nPair][nSym].get_curr_spread())

                    pairs_spread_data[nPair][nSym].set_curr_trailing(pairs_spread_data[nPair][nSym].get_max_spread() * TRAILING_STOP)


                if (
                    pairs_spread_data[nPair][nSym].get_curr_spread() < pairs_spread_data[nPair][nSym].get_min_spread()
                ) or (pairs_spread_data[nPair][nSym].get_min_spread() == 0):
                    pairs_spread_data[nPair][nSym].set_min_spread(pairs_spread_data[nPair][nSym].get_curr_spread())

                # \Calculates the all times spread max, min e traling

                # Verificar condicao para entrar no trade
                if (
                    (pairs_spread_data[nPair][nSym].get_curr_spread() >= TRIGGER_SPREAD)
                    and (
                        pairs_spread_data[nPair][nSym].get_curr_spread() <= pairs_spread_data[nPair][nSym].get_curr_trailing()
                    )
                    and (
                        not opened_trades[nPair][nSym].get_is_trade_open()
                    )
                ):

                    logger.info(
                        "Pair (buy/sell): {}/{} (% Max Spread: {:.2%}, Min Spread: {:.2%}, Spread: {:.2%}, Trailing: {:.2%})".format(
                            temp_exc_buy[:3],
                            temp_exc_sell[:3],
                            pairs_spread_data[nPair][nSym].get_max_spread(),
                            pairs_spread_data[nPair][nSym].get_min_spread() ,
                            pairs_spread_data[nPair][nSym].get_curr_spread(),
                            pairs_spread_data[nPair][nSym].get_curr_trailing(),
                        ),
                    )
                    logger.info(" - Opportunity Found! - ")
                    
                    # Added a way to stop entering new trades
                    if not file_manag.file_exists(FILE_STOP_TRADING):
                        if not was_trade_opened:
                            was_trade_successful, msg = open_trade(pair, asks, bids, symbols[nSym], pairs_spread_data[nPair][nSym].get_curr_spread(), temp_exc_buy, temp_exc_sell)
                            if (was_trade_successful):
                                logger.info("Trade Opened!")
                                was_trade_opened = True
                            else:
                                logger.info("Opening trade failed!: " + msg)
                        else:
                            logger.info("Trade has already been opened in this loop. Waiting for next loop")
                    else:
                        logger.info(" New Trades are Paused")

                    loggerln.info("")

                elif opened_trades[nPair][nSym].get_is_trade_open():

                    logger.info(
                        "Pair (buy/sell): {}/{} (% Max Spread: {:.2%}, Min Spread: {:.2%}, Spread: {:.2%}, Trailing: {:.2%})".format(
                            temp_exc_buy[:3],
                            temp_exc_sell[:3],
                            pairs_spread_data[nPair][nSym].get_max_spread(),
                            pairs_spread_data[nPair][nSym].get_min_spread(),
                            pairs_spread_data[nPair][nSym].get_curr_spread(),
                            pairs_spread_data[nPair][nSym].get_curr_trailing(),
                        ),
                    )
                    
                    was_close_successful, msg = close_trade(pair, asks, bids, symbols[nSym], pairs_spread_data[nPair][nSym].get_curr_spread())
                    if (was_close_successful):
                        logger.info("- TRADE CLOSED!!!")
                    else:
                        logger.info(" - OPENED TRADE! - ")
                        logger.info("Entry Spread = {:.2%} - ".format(
                            opened_trades[nPair][nSym].get_entry_spread(),
                            )
                        )
                        loggerln.info(msg)

                else:

                    loggerln.info(
                        "Pair (buy/sell): {}/{} (% Max Spread: {:.2%}, Min Spread: {:.2%}, Spread: {:.2%}, Trailing: {:.2%})".format(
                            temp_exc_buy[:3],
                            temp_exc_sell[:3],
                            pairs_spread_data[nPair][nSym].get_max_spread(),
                            pairs_spread_data[nPair][nSym].get_min_spread(),
                            pairs_spread_data[nPair][nSym].get_curr_spread(),
                            pairs_spread_data[nPair][nSym].get_curr_trailing(),
                        )
                    )
                # \Verificar condicao para entrar no trade

            # Show the best available pair to operate on each symbol
        
            # operate_pair_spread = -100 # Starts with a pretty low number
            # is_pair_available = False
            # for nPair, pair in enumerate(exchange_pairs):
            #     if not opened_trades[exchange_pairs.index(pair)][nSym].get_is_trade_open():
            #         if operate_pair_spread < pairs_spread_data[nPair][nSym].get_curr_spread():
            #             operate_pair_spread = pairs_spread_data[nPair][nSym].get_curr_spread()
            #             temp_min_ask = min(asks[pair[0]][Sym], asks[pair[1]][Sym])
            #             temp_max_bid = max(bids[pair[0]][Sym], bids[pair[1]][Sym])
            #             is_pair_available = True
            
            # if is_pair_available:
            #     min_ask_index = asks[nSym][::].index(temp_min_ask)
            #     max_bid_index = bids[nSym][::].index(temp_max_bid)
            #     loggerln.info("!!!! Operate on \\/ !!!!")
            #     loggerln.info(
            #         f"Buy/Sell = {all_exchanges[min_ask_index]} / {all_exchanges[max_bid_index]}"
            #     )
            #     loggerln.info(
            #         "Highest Absolute Spread: {:.2f}".format(
            #             temp_max_bid - temp_min_ask
            #         )
            #     )

            #     # temp_max_spread handles ZeroDivisionError
            #     loggerln.info("% Spread: {:.2%}".format(operate_pair_spread))
            #     # loggerln.info("% Spread: {:.2%}".format(((max(bids[nSym][::]) / min(asks[nSym][::])) - 1)))
            # else:
            #     loggerln.info("There are no Pairs Available for Trading")

            loggerln.info(" ")
            # \Show the best available pair to operate on each symbol

        # !!! \finding/logging opportunities



        loggerln.info("----------------------------------------------------------------")
