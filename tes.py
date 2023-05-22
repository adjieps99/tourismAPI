import csv

data = []
with open('exploreasy-dataset-ready.csv', 'r', newline='', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    for row in reader:
        data.append([
            row['name'],
            float(row['rating']) if row['rating'] else 0.0,
            float(row['latitude']) if row['latitude'] else 0.0,
            float(row['longitude']) if row['longitude'] else 0.0,
            row['address'],
            row['review']
        ])

print(data)