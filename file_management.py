import csv, os, datetime, pickle


trading_field_names = [
    "Timestamp",
    "Trading Symbol",
    "Opening/Closing",
    "Spread",
    "Amount Sym 2",
    "Bought On",
    "Ask Price (Sym 1)",
    "Total Spent Sym 1",
    "Total Buying Fees",
    "Selling On",
    "Amount to be received Sym 2",
    "Bid Price (Sym 1)",
    "Total Expected Sym 1",
    "Total Selling Fees",
    "Opportunity Profit",
]

real_balance_initial_value = 10000
margin_balance_initial_value = 0
reserve_balance_initial_value = 0


def init_all_files(all_exchanges):

    file_name = "./csvFiles/trading.csv"
    init_file(file_name, trading_field_names)

    file_name = "./csvFiles/real_balance.csv"
    field_name = ["Timestamp"] + all_exchanges
    if not init_file(
        file_name, field_name
    ):  # if file was just created, assign initial values
        assign_balance_initial_value(all_exchanges, "real_balance")

    # file_name = "./csvFiles/margin_balance.csv"
    # field_name = ["Timestamp"] + all_exchanges
    # if not init_file(
    #     file_name, field_name
    # ):  # if file was just created, assign initial values
    #     assign_balance_initial_value(all_exchanges, "margin_balance")

    # file_name = "./csvFiles/reserve_balance.csv"
    # field_name = ["Timestamp"] + all_exchanges
    # if not init_file(
    #     file_name, field_name
    # ):  # if file was just created, assign initial values
    #     assign_balance_initial_value(all_exchanges, "reserve_balance")


def init_file(
    file_name, field_name
):  # returns false if filas wasn`t found and new file has been created

    file_check = file_name
    if not os.path.isfile(file_check):

        with open(file_check, "w") as new_file:

            csv_writer = csv.DictWriter(
                new_file, fieldnames=field_name, lineterminator="\n"
            )

            csv_writer.writeheader()

        return False

    else:
        return True


def register_trade(
    symbol,
    opening_closing,
    spread,
    amount_sym2,
    bought_on,
    ask_price_sym1,
    total_spent_sym1,
    total_buying_fees,
    sold_on,
    amount_received_sym2,
    bid_price_sym1,
    total_sold_sym1,
    total_selling_fees,
    total_profit
):

    file_name = "./csvFiles/trading.csv"
    with open(file_name, "a") as file_scr:

        csv_writer = csv.DictWriter(
            file_scr, fieldnames=trading_field_names, lineterminator="\n"
        )

        csv_writer.writerow(
            {
                "Timestamp": get_timestamp(),
                "Trading Symbol": symbol,
                "Opening/Closing": opening_closing,
                "Spread": spread,
                "Amount Sym 2": amount_sym2,
                "Bought On": bought_on,
                "Ask Price (Sym 1)": ask_price_sym1,
                "Total Spent Sym 1": total_spent_sym1,
                "Total Buying Fees": total_buying_fees,
                "Selling On": sold_on,
                "Amount to be received Sym 2": amount_received_sym2,
                "Bid Price (Sym 1)": bid_price_sym1,
                "Total Expected Sym 1": total_sold_sym1,
                "Total Selling Fees": total_selling_fees,
                "Opportunity Profit": total_profit,
            }
        )


def updt_balance_files(all_exchanges, real_balance):

    updt_balance_file(all_exchanges, "real_balance", real_balance)

    # updt_balance_file(all_exchanges, "margin_balance", margin_balance)

    # updt_balance_file(all_exchanges, "reserve_balance", reserve_balance)


def updt_balance_file(all_exchanges, balance_type, balance):

    if balance_type == "real_balance":
        file_name = "./csvFiles/real_balance.csv"
    elif balance_type == "margin_balance":
        file_name = "./csvFiles/margin_balance.csv"
    elif balance_type == "reserve_balance":
        file_name = "./csvFiles/reserve_balance.csv"
    else:
        return

    with open(file_name, "a") as file_scr:

        field_name = ["Timestamp"] + all_exchanges

        csv_writer = csv.DictWriter(
            file_scr, fieldnames=field_name, lineterminator="\n"
        )

        temp_dict = {}
        temp_dict["Timestamp"] = get_timestamp()

        for i in range(len(all_exchanges)):
            temp_dict[all_exchanges[i]] = balance[all_exchanges[i]]

        csv_writer.writerow(temp_dict)


def fetch_stored_balances():
    temp_dict = {}

    temp_dict["real_balance"] = last_row("./csvFiles/real_balance.csv")
    # temp_dict["margin_balance"] = last_row("./csvFiles/margin_balance.csv")
    # temp_dict["reserve_balance"] = last_row("./csvFiles/reserve_balance.csv")

    return temp_dict


def assign_balance_initial_value(all_exchanges, balance_type):

    if balance_type == "real_balance":
        file_name = "./csvFiles/real_balance.csv"
        balance_value = real_balance_initial_value
    elif balance_type == "margin_balance":
        file_name = "./csvFiles/margin_balance.csv"
        balance_value = margin_balance_initial_value
    elif balance_type == "reserve_balance":
        file_name = "./csvFiles/reserve_balance.csv"
        balance_value = reserve_balance_initial_value
    else:
        return

    with open(file_name, "a") as file_scr:

        field_name = ["Timestamp"] + all_exchanges

        csv_writer = csv.DictWriter(
            file_scr, fieldnames=field_name, lineterminator="\n"
        )

        temp_dict = {}
        temp_dict["Timestamp"] = get_timestamp()

        for i in range(len(all_exchanges)):
            temp_dict[all_exchanges[i]] = balance_value

        csv_writer.writerow(temp_dict)


def last_row(file_name):
    data = ()
    with open(file_name, "r") as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            if row:  # avoid blank lines
                data = row
    return data


def get_timestamp():
    return datetime.datetime.now()

    # datetime.datetime.fromtimestamp(
    #         datetime.datetime.now().timestamp()
    #     ).isoformat()


def file_exists(file_name):

    if os.path.isfile(file_name):
        return True
    else:
        return False


def create_file(file_name):
    with open(file_name, "w") as new_file:
        new_file.close()


def save_trades_data(trade_data):
    with open("tradesData.bin", "wb") as trades_data_file:
        pickle.dump(trade_data, trades_data_file)


def load_trades_data():

    file_name = "tradesData.bin"
    with open(file_name, "rb") as trades_data_file:
        trades_data = pickle.load(trades_data_file)
        return trades_data


def files_examples():

    with open("trading.csv", "r") as csv_file:
        csv_reader = csv.DictReader(csv_file)

        # Takes the first line out
        # next(csv_reader)

        with open("trading2.csv", "w") as new_file:
            field_names = [
                "Timestamp",
                "trading Symbol",
                "buy on",
                "buy price",
                "sell on",
                "sell price",
            ]

            csv_writer = csv.DictWriter(
                new_file, fieldnames=field_names, lineterminator="\n"
            )

            csv_writer.writeheader()

            for line in csv_reader:
                csv_writer.writerow(line)
            csv_writer.writerow(
                {
                    "trading Symbol": "1",
                    "Timestamp": "2",
                    "buy on": "3",
                    "buy price": "4",
                    "sell on": "5",
                    "sell price": "6",
                }
            )

    # filename = 'some.csv'
    # with open(filename, newline='') as f:
    #     reader = csv.reader(f)
    #     try:
    #         for row in reader:
    #             print(row)
    #     except csv.Error as e:
    #         sys.exit('file {}, line {}: {}'.format(filename, reader.line_num, e))
