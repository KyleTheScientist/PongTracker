import json
import matplotlib.pyplot as plt

with open('data/database.json', 'r') as f:
    data = json.load(f)['Doubles']

win_rates = {}
win_loss = {}
last_date = None
for match in data.values():
    date = match['date'].split()[0]
    winners = match['team1']
    losers = match['team2']
    for player in winners:
        if player not in win_rates:
            win_rates[player] = {}
        if player not in win_loss:
            win_loss[player] = {
                'wins': 1,
                'losses': 0
            }
        else:
            win_loss[player]['wins'] += 1

        total_games = win_loss[player]['wins'] + win_loss[player]['losses']
        win_rates[player][date] = int(win_loss[player]['wins'] / total_games * 10000) / 100

    for player in losers:
        if player not in win_rates:
            win_rates[player] = {}
        if player not in win_loss:
            win_loss[player] = {
                'wins': 1,
                'losses': 0
            }
        else:
            win_loss[player]['losses'] += 1

        total_games = win_loss[player]['wins'] + win_loss[player]['losses']
        win_rates[player][date] = int(win_loss[player]['wins'] / total_games * 10000) / 100
    last_date = date

# Extract the dates and win rates for each player
for player in win_rates:
    dates = []
    player_rates = []
    for date, win_rate in win_rates[player].items():
        dates.append(date)
        player_rates.append(win_rate)
    plt.plot(dates, player_rates, label=player)

# Add labels and legend to the plot
plt.xlabel("Date")
plt.ylabel("Win Rate (%)")
plt.title("Players' Win Rates Over Time")
plt.legend()
plt.gcf().autofmt_xdate()

# Display the plot
plt.show()
