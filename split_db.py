import json
from datetime import datetime
from rich import print

with open('data/database.json', 'r') as f:
    data = json.load(f)
old_season = {}
new_season = {}

split_date = datetime(2024, 4, 1)

for gamemode, matches in data.items():
    old_season[gamemode] = {}
    new_season[gamemode] = {}
    for index, match in matches.items():
        date = datetime.strptime(match['date'], '%Y-%m-%d %H:%M:%S')
        # if the date is before April 2024, it's in the previous season, pop it
        if date >= split_date:
            new_season[gamemode][str(len(new_season[gamemode]))] = match
        else:
            old_season[gamemode][str(len(old_season[gamemode]))] = match

print(old_season)

json.dump(old_season, open('data/season-7.6.json', 'w'))
json.dump(new_season, open('data/season-7.7.json', 'w'))


