import csv

with open('/Users/sunil/Documents/myprojects/fde_oct_1/data/homework_invoices.csv', mode='r') as file:
    reader = csv.DictReader(file)
    for row in reader:
       # print(row)
        print(type(row['amount']))
        try:
            amount = float(row['amount'])
            print(f"The amount as a float is: {amount}")
        except ValueError:
            print(f"Skipping row — could not convert '{row['amount']}' to float")
        