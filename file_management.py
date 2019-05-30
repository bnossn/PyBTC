import csv, os

trading_field_names = [
    "Timestamp",
    "trading Symbol",
    "buy on",
    "buy price",
    "sell on",
    "sell price",
]


def init_files():

    file_check = "trading.csv"
    if not os.path.isfile(file_check):

        with open(file_check, "w") as new_file:

            csv_writer = csv.DictWriter(
                new_file, fieldnames=trading_field_names, lineterminator="\n"
            )

            csv_writer.writeheader()


def register_trade(
    pair, symbol, buying_exchange, amount_bought, selling_exchange, amount_sold
):

    file_name = "trading.csv"
    with open(file_name, "a") as file_scr:

        csv_writer = csv.DictWriter(
            file_scr, fieldnames=trading_field_names, lineterminator="\n"
        )

        csv_writer.writerow(
            {
                "Timestamp": "2",
                "trading Symbol": symbol,
                "buy on": buying_exchange,
                "buy price": amount_bought,
                "sell on": selling_exchange,
                "sell price": amount_sold,
            }
        )


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
