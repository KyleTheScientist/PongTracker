from game import games
import analytics
from tinydb import Query

player_names = [
    'Adams',
    'Bret',
    'Huseyin',
    'Jacob',
    'Zack',
    'Kyle',
    'Danny',
    'Shrey',
    'Shammi',
    'Alonzo',
    'Perry',
    'Cinu',
    'Boris',
    'Grayson',
    'Kate',
    'Yan'
]
player_names.sort()

class Team():
    def __init__(self, players):
        self.players = players
        self.score = 0

    def __str__(self) -> str:
        return f'[{",".join(self.players)}]-{self.score}'


def sorted_by_value(d):
    return {k: v for k, v in sorted(d.items(), key=lambda item: item[1])}

class Player():
    def __init__(self, name) -> None:
        self.name = name
        self.reset()

    def reset(self):
        self.wins = 0
        self.losses = 0
        self.games = 0
        self.perfects = 0
        self.server_wins = 0
        self.receiver_wins = 0
        self.wins_with = {p: 0 for p in player_names if p != self.name}
        self.wins_against = {p: 0 for p in player_names if p != self.name}

    def __getattribute__(self, name: str):
        if name == 'win_rate':
            if self.games == 0: return 0
            return f'{int(self.wins/self.games * 100)}%'

        if name == 'best_position':
            if self.server_wins + self.receiver_wins == 0:
                return None
            best_position = 'Server' if self.server_wins > self.receiver_wins else "Receiver"
            best_position = 'Either' if self.server_wins == self.receiver_wins else best_position
            return best_position

        if name == 'best_mate_str':
            if self.games == 0 or set(self.wins_with.values()) == {0}:
                return None
            return f'{self.best_mate} ({self.wins_with[self.best_mate]})'

        if name == 'worst_mate_str':
            if self.games == 0 or set(self.wins_with.values()) == {0}:
                return None
            return f'{self.worst_mate} ({self.wins_with[self.worst_mate]})'

        if name == 'nemesis_str':
            if self.games == 0 or set(self.wins_against.values()) == {0}:
                return None
            return f'{self.nemesis} ({self.wins_against[self.nemesis]})'

        if name == 'antinemesis_str':
            if self.games == 0 or set(self.wins_against.values()) == {0}:
                return None
            return f'{self.antinemesis} ({self.wins_against[self.antinemesis]})'

        return super(Player, self).__getattribute__(name)

    def refresh(self):
        self.reset()
        for game in games:
            table = analytics.db.table(game.name)
            match = Query()
            all_matches = table.search(match.team1.any(self.name) | (match.team2.any(self.name)))
            self.games += len(all_matches)
            for match in all_matches:
                # Player Won
                if self.name in match['team1']:
                    self.wins += 1
                    # Which position did they win in?
                    if len(match['team1']) == 2:
                        if match['team1'][0] == self.name:
                            self.server_wins += 1
                        else:
                            self.receiver_wins += 1

                    # Did they get a free lunch?
                    if match['score2'] == 0:
                        self.perfects += 1

                    # Mark who they won with/against
                    for teammate in match['team1']:
                        if teammate != self.name:
                            self.wins_with[teammate] += 1
                    for opponent in match['team2']:
                        self.wins_against[opponent] += 1

                # self lost
                if self.name in match['team2']:
                    self.losses += 1
                    # Mark who they lost with/against
                    for teammate in match['team2']:
                        if teammate != self.name:
                            self.wins_with[teammate] -= 1
                    for opponent in match['team1']:
                        self.wins_against[opponent] -= 1


        self.wins_with = sorted_by_value(self.wins_with)
        self.wins_against = sorted_by_value(self.wins_against)

        self.best_mate = list(self.wins_with.keys())[-1]
        self.worst_mate = list(self.wins_with.keys())[0]
        self.nemesis = list(self.wins_against.keys())[0]
        self.antinemesis = list(self.wins_against.keys())[-1]

players = [Player(name) for name in player_names]

