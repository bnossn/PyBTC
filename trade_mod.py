def buy_token(buying_exchange, amount, symbol):
    pass


def sell_token(selling_exchange, amount, symbol):
    pass


class TradeData:
    def __init__(self, exchange_pair):
        self.exchange_pair = exchange_pair
        self.traded_symbol = ""

        self.buying_exchange = ""
        self.amount_bought_symbol1 = 0
        self.fee_reserved_buying_exchange = 0 # given in symbol 1

        self.selling_exchange = ""
        self.amount_sold_symbol1 = 0
        self.fee_reserved_selling_exchange = 0 # given in symbol 1

        self.amount_traded_symbol2 = 0 #The same for both exchanges to keep market neutral
        self.opportunity_spread = 0
        self.is_trade_open = False

    def set_exchange_pair(self, exchange_pair):
        self.exchange_pair = exchange_pair

    def set_traded_symbol(self, traded_symbol):
        self.traded_symbol = traded_symbol

    def set_buying_exchange(self, buying_exchange):
        self.buying_exchange = buying_exchange

    def set_selling_exchange(self, selling_exchange):
        self.selling_exchange = selling_exchange

    def set_amount_bought_symbol1(self, amount_bought_symbol1):
        self.amount_bought_symbol1 = amount_bought_symbol1

    def set_amount_sold_symbol1(self, amount_sold_symbol1):
        self.amount_sold_symbol1 = amount_sold_symbol1

    def set_fee_reserved_buying_exchange(self, fee_reserved_buying_exchange):
        self.fee_reserved_buying_exchange = fee_reserved_buying_exchange

    def set_fee_reserved_selling_exchange(self, fee_reserved_selling_exchange):
        self.fee_reserved_selling_exchange = fee_reserved_selling_exchange

    def set_amount_traded_symbol2(self, amount_traded_symbol2):
        self.amount_traded_symbol2 = amount_traded_symbol2 

    def set_opportunity_spread(self, opportunity_spread):
        self.opportunity_spread = opportunity_spread

    def set_is_trade_open(self, is_trade_open):
        self.is_trade_open = is_trade_open        

    def get_is_trade_open(self):
        return self.is_trade_open

    def get_buying_exchange(self):
        return self.buying_exchange

    def get_selling_exchange(self):
        return self.selling_exchange

    def get_amount_traded_symbol2(self):
        return self.amount_traded_symbol2

    def get_opportunity_spread(self):
        return self.opportunity_spread

    def get_fee_reserved_buying_exchange(self):
        return self.fee_reserved_buying_exchange

    def get_fee_reserved_selling_exchange(self):
        return self.fee_reserved_selling_exchange

    def __str__(self):
        result = f"exchange_pair = {self.exchange_pair}, "
        result += f"traded_symbol = {self.traded_symbol}, "
        result += f"buying_exchange = {self.buying_exchange}, "
        result += f"amount_bought_symbol1 = {self.amount_bought_symbol1}, "
        result += f"fee_reserved_buying_exchange = {self.fee_reserved_buying_exchange}, "
        result += f"selling_exchange = {self.selling_exchange}, "
        result += f"amount_sold_symbol1 = {self.amount_sold_symbol1}, "
        result += f"fee_reserved_selling_exchange = {self.fee_reserved_selling_exchange}, "
        result += f"amount_traded_symbol2 = {self.amount_traded_symbol2}, "
        result += f"is_trade_open = {self.is_trade_open}"
        return result

    def __repr__(self):
        return "Trade('{}', '{}', '{}', {:.2f}, {:.2f}, '{}', {:.2f}, {:.2f}, {:.2f}, {})".format(
            self.exchange_pair,
            self.traded_symbol,
            self.buying_exchange,
            self.amount_bought_symbol1,
            self.fee_reserved_buying_exchange,
            self.selling_exchange,
            self.amount_sold_symbol1,
            self.fee_reserved_selling_exchange,
            self.amount_traded_symbol2,
            self.is_trade_open
        )