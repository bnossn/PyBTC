import csv

with open("test.csv", "r") as csv_file:
    csv_reader = csv.DictReader(csv_file)

    # Takes the first line out
    # next(csv_reader)

    with open("new.csv", "w") as new_file:
        field_names = ["column1", "column2"]

        csv_writer = csv.DictWriter(
            new_file, fieldnames=field_names, lineterminator="\n"
        )

        csv_writer.writeheader()

        for line in csv_reader:
            del line['column3']
            csv_writer.writerow(line)


# with open("test.csv", "r") as csv_file:
#     csv_reader = csv.reader(csv_file)

#     # Takes the first line out
#     # next(csv_reader)

#     with open("new.csv", "w") as new_file:
#         csv_writer = csv.writer(new_file, lineterminator="\n")

#         for line in csv_reader:
#             csv_writer.writerow(line)

