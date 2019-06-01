def buy_token(buying_exchange, amount, symbol):
    pass


def sell_token(selling_exchange, amount, symbol):
    pass


class TradeData:
    def __init__(self, exchanges_pair):
        self.exchanges_pair = exchanges_pair
        self.traded_symbol = ""
        self.buying_exchange = ""
        self.selling_exchange = ""
        self.trade_amount = 0
        self.fee_reserved_amount = 0
        self.is_trade_open = False

    def set_exchange_pair(self, exchanges_pair):
        self.exchanges_pair = exchanges_pair

    def set_traded_symbol(self, traded_symbol):
        self.traded_symbol = traded_symbol

    def set_buying_exchange(self, buying_exchange):
        self.buying_exchange = buying_exchange

    def set_selling_exchange(self, selling_exchange):
        self.selling_exchange = selling_exchange

    def set_trade_amount(self, trade_amount):
        self.trade_amount = trade_amount

    def set_fee_reserved_amount(self, fee_reserved_amount):
        self.fee_reserved_amount = fee_reserved_amount

    def set_is_trade_open(self, is_trade_open):
        self.is_trade_open = is_trade_open

    def get_is_trade_open(self):
        return self.is_trade_open

    def __str__(self):
        result = f"exchanges_pair = {self.exchanges_pair}, "
        result += f"traded_symbol = {self.traded_symbol}, "
        result += f"buying_exchange = {self.buying_exchange}, "
        result += f"selling_exchange = {self.selling_exchange}, "
        result += f"trade_amount = {self.trade_amount:.2f}, "
        result += f"fee_reserved_amount = {self.fee_reserved_amount:.2f}, "
        result += f"is_trade_open = {self.is_trade_open}"
        return result

    def __repr__(self):
        return "Trade('{}', '{}', '{}', '{}', {:.2f}, {:.2f}, {})".format(
            self.exchanges_pair,
            self.traded_symbol,
            self.buying_exchange,
            self.selling_exchange,
            self.trade_amount,
            self.fee_reserved_amount,
            self.is_trade_open,
        )

