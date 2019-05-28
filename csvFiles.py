import csv

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


# with open("test.csv", "r") as csv_file:
#     csv_reader = csv.reader(csv_file)

#     # Takes the first line out
#     # next(csv_reader)

#     with open("new.csv", "w") as new_file:
#         csv_writer = csv.writer(new_file, lineterminator="\n")

#         for line in csv_reader:
#             csv_writer.writerow(line)

