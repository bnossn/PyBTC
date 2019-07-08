def buy_token(buying_exchange, amount, symbol):
    pass


def sell_token(selling_exchange, amount, symbol):
    pass


class PairData:
    def __init__(self, exchange_pair):
        self.exchange_pair = exchange_pair

        self.max_spread = 0
        self.min_spread = 0
        self.curr_trailing = -1
        self.curr_spread = 0

    def set_max_spread(self, max_spread):
        self.max_spread = max_spread

    def set_min_spread(self, min_spread):
        self.min_spread = min_spread

    def set_curr_trailing(self, curr_trailing):
        self.curr_trailing = curr_trailing

    def set_curr_spread(self, curr_spread):
        self.curr_spread = curr_spread

    def get_exchange_pair(self):
        return self.exchange_pair

    def get_max_spread(self):
        return self.max_spread

    def get_min_spread(self):
        return self.min_spread

    def get_curr_trailing(self):
        return self.curr_trailing

    def get_curr_spread(self):
        return self.curr_spread


class TradeData:
    def __init__(self, exchange_pair):
        self.exchange_pair = exchange_pair
        self.traded_symbol = ""

        self.buying_exchange = ""
        self.amount_bought_symbol1 = 0  #Total spent Trade + Fees
        self.total_fees_buying_exchange = 0  # given in symbol 2 (trading + withdraw)
        self.total_bought_sym2 = 0 #Without fees (trading + withdraw)
        self.initial_bid_price = 0
        self.initial_ask_price = 0


        self.selling_exchange = ""
        self.expected_amount_selling_sym2 = 0
        self.expected_total_sold_sym1 = 0  # With trading fees taken into account
        self.expected_selling_fees = 0

        self.opp_initial_time = 0 
        self.entry_spread = 0
        self.is_trade_open = False

    def set_exchange_pair(self, exchange_pair):
        self.exchange_pair = exchange_pair

    def set_traded_symbol(self, traded_symbol):
        self.traded_symbol = traded_symbol

    def set_buying_exchange(self, buying_exchange):
        self.buying_exchange = buying_exchange

    def get_buying_exchange(self):
        return self.buying_exchange

    def set_selling_exchange(self, selling_exchange):
        self.selling_exchange = selling_exchange

    def get_selling_exchange(self):
        return self.selling_exchange

    def set_amount_bought_symbol1(self, amount_bought_symbol1):
        self.amount_bought_symbol1 = amount_bought_symbol1

    def get_amount_bought_symbol1(self):
        return self.amount_bought_symbol1

    def set_expected_amount_selling_sym2(self, expected_amount_selling_sym2):
        self.expected_amount_selling_sym2 = expected_amount_selling_sym2

    def get_expected_amount_selling_sym2(self):
        return self.expected_amount_selling_sym2

    def set_total_fees_buying_exchange(self, total_fees_buying_exchange):
        self.total_fees_buying_exchange = total_fees_buying_exchange

    def get_total_fees_buying_exchange(self):
        return self.total_fees_buying_exchange

    def set_expected_total_sold_sym1(self, expected_total_sold_sym1):
        self.expected_total_sold_sym1 = expected_total_sold_sym1

    def get_expected_total_sold_sym1(self):
        return self.expected_total_sold_sym1

    def set_entry_spread(self, entry_spread):
        self.entry_spread = entry_spread

    def get_entry_spread(self):
        return self.entry_spread

    def set_is_trade_open(self, is_trade_open):
        self.is_trade_open = is_trade_open

    def get_is_trade_open(self):
        return self.is_trade_open

    def set_total_bought_sym2(self, total_bought_sym2):
        self.total_bought_sym2 = total_bought_sym2

    def get_total_bought_sym2(self):
        return self.total_bought_sym2

    def set_expected_selling_fees(self, expected_selling_fees):
        self.expected_selling_fees = expected_selling_fees

    def get_expected_selling_fees(self):
        return self.expected_selling_fees

    def set_opp_initial_time(self, opp_initial_time):
        self.opp_initial_time = opp_initial_time

    def get_opp_initial_time(self):
        return self.opp_initial_time

    def set_initial_bid_price(self, initial_bid_price):
        self.initial_bid_price = initial_bid_price

    def get_initial_bid_price(self):
        return self.initial_bid_price

    def set_initial_ask_price(self, initial_ask_price):
        self.initial_ask_price = initial_ask_price

    def get_initial_ask_price(self):
        return self.initial_ask_price



    def __str__(self):
        result = f"exchange_pair = {self.exchange_pair}, "
        result += f"traded_symbol = {self.traded_symbol}, "
        result += f"buying_exchange = {self.buying_exchange}, "
        result += f"amount_bought_symbol1 = {self.amount_bought_symbol1}, "
        result += (
            f"total_fees_buying_exchange = {self.total_fees_buying_exchange}, "
        )
        result += f"total_bought_sym2 = {self.total_bought_sym2}, "
        result += f"selling_exchange = {self.selling_exchange}, "
        result += f"expected_amount_selling_sym2 = {self.expected_amount_selling_sym2}, "
        result += (
            f"expected_total_sold_sym1 = {self.expected_total_sold_sym1}, "
        )
        result += f"entry_spread = {self.entry_spread}, "
        result += f"is_trade_open = {self.is_trade_open}"
        return result

    def __repr__(self):
        return "Trade('{}', '{}', '{}', {:.2f}, {:.2f}, '{}', {:.2f}, {:.2f}, {})".format(
            self.exchange_pair,
            self.traded_symbol,
            self.buying_exchange,
            self.amount_bought_symbol1,
            self.total_fees_buying_exchange,
            self.selling_exchange,
            self.expected_amount_selling_sym2,
            self.expected_total_sold_sym1,
            self.is_trade_open,
        )
