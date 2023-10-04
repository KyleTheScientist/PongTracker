from game import games
import analytics
from tinydb import Query
from utils import ratio_safe

# The list of players.
# TODO import these from a file or something
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
    '''
    Used to more easily keep the players/score attributes bound together
    '''

    def __init__(self, players):
        self.players = players
        self.score = 0

    def __str__(self) -> str:
        return f'[{",".join(self.players)}]-{self.score}'


def sorted_by_value(d):
    return {k: v for k, v in sorted(d.items(), key=lambda item: item[1])}


class Player():
    '''
    Class that defines the attributes associated with a player so that
    we can just bind the stat card fields to the attributes here so that
    they update automatically.
    '''

    def __init__(self, name) -> None:
        self.name = name
        self.reset()

    def reset(self):
        self.wins = 0
        self.losses = 0
        self.matches = 0
        self.perfects = 0
        self.server_wins = 0
        self.receiver_wins = 0
        self.matches_per_side = [{'wins': 0, 'losses': 0, 'matches': 0}, {'wins': 0, 'losses': 0, 'matches': 0}]
        self.games_with = {p: 0 for p in player_names if p != self.name}
        self.wins_with = {p: 0 for p in player_names if p != self.name}
        self.losses_with = {p: 0 for p in player_names if p != self.name}
        self.games_against = {p: 0 for p in player_names if p != self.name}
        self.wins_against = {p: 0 for p in player_names if p != self.name}
        self.losses_against = {p: 0 for p in player_names if p != self.name}
        self.teammate_ranking = {p: 0 for p in player_names if p != self.name}
        self.opponent_ranking = {p: 0 for p in player_names if p != self.name}

        self.games = {game.name: {'wins': 0, 'losses': 0, 'matches': 0, 'points': 0, 'point_difference': 0} for game in games}

    def avg_points_ing(self, game):
        return ratio_safe(self.games[game]['points'], self.games[game]['matches'])

    def avg_point_difference_in(self, game):
        return ratio_safe(self.games[game]['point_difference'], self.games[game]['matches'])

    def __getattribute__(self, name: str):
        '''
        Because the bind_text_from() method only accepts attributes
        (not functions) I am overriding the getattr method to provide
        some of the more complex stats that are either computed from
        other fields or have text.
        '''
        if name == 'win_rate':
            if self.matches == 0:
                return 0
            return f'{int(self.wins/self.matches * 100)}%'

        if name == 'best_position':
            r = self.matches_per_side[1]
            l = self.matches_per_side[0]

            if self.games['Doubles']['matches'] == 0:
                return None

            r_win_rate = int(ratio_safe(r['wins'], r['matches']) * 100)
            l_win_rate = int(ratio_safe(l['wins'], l['matches']) * 100)
            best_position = 'Right ({left}% : {right}%)' if r_win_rate > l_win_rate else "Left ({left}% : {right}%)"
            best_position = 'Either' if r_win_rate == l_win_rate else best_position
            return best_position.format(left=l_win_rate, right=r_win_rate)

        if name == 'points_per_game':
            singles = self.avg_points_ing('Singles')
            doubles = self.avg_points_ing('Doubles')
            triples = self.avg_points_ing('Triples')
            return f'{singles:.2f}/{doubles:.2f}/{triples:.2f}'

        if name == 'difference_per_game':
            singles = self.avg_point_difference_in('Singles')
            doubles = self.avg_point_difference_in('Doubles')
            triples = self.avg_point_difference_in('Triples')
            return f'{singles:.2f}/{doubles:.2f}/{triples:.2f}'

        if name == 'best_mate_str':
            if self.games['Doubles']['matches'] + self.games['Triples']['matches'] == 0:
                return None
            return f'{self.best_mate} ({self.wins_with[self.best_mate]} : {self.losses_with[self.best_mate]})'

        if name == 'worst_mate_str':
            if self.games['Doubles']['matches'] + self.games['Triples']['matches'] == 0:
                return None
            return f'{self.worst_mate} ({self.wins_with[self.worst_mate]} : {self.losses_with[self.worst_mate]})'

        if name == 'nemesis_str':
            if self.games['Doubles']['matches'] + self.games['Triples']['matches'] == 0:
                return None
            return f'{self.nemesis} ({self.wins_against[self.nemesis]} : {self.losses_against[self.nemesis]})'

        if name == 'antinemesis_str':
            if self.games['Doubles']['matches'] + self.games['Triples']['matches'] == 0:
                return None
            return f'{self.antinemesis} ({self.wins_against[self.antinemesis]} : {self.losses_against[self.antinemesis]})'

        return super(Player, self).__getattribute__(name)

    def refresh(self):
        '''
        Re-scans the database and updates the player stats accordingly.
        The logic here relies heavily on the fact that Team 1 is always
        the winning team and Team 2 is always the losing team.
        '''
        self.reset()
        for game in games:
            table = analytics.db.table(game.name)
            match = Query()
            all_matches = table.search(match.team1.any(
                self.name) | (match.team2.any(self.name)))
            self.matches += len(all_matches)
            for match in all_matches:
                # Player Won
                if self.name in match['team1']:
                    team = 'team1'
                    self.wins += 1

                    # Did they get a free lunch?
                    if match['score2'] == 0:
                        self.perfects += 1

                    # Mark who they won with/against
                    for teammate in match['team1']:
                        if teammate != self.name:
                            self.wins_with[teammate] += 1
                            self.games_with[teammate] += 1
                    for opponent in match['team2']:
                        self.wins_against[opponent] += 1
                        self.games_against[opponent] += 1

                # Player lost
                if self.name in match['team2']:
                    team = 'team2'
                    self.losses += 1

                    # Mark who they lost with/against
                    for teammate in match['team2']:
                        if teammate != self.name:
                            self.losses_with[teammate] += 1
                            self.games_with[teammate] += 1
                    for opponent in match['team1']:
                        self.losses_against[opponent] += 1
                        self.games_against[opponent] += 1

                # Preparing some strings
                category =  'wins'   if team == 'team1' else 'losses'
                score =     'score1' if team == 'team1' else 'score2'
                opp_score = 'score2' if team == 'team1' else 'score1'

                # Update per-game stats
                self.games[game.name][category] += 1
                self.games[game.name]['points'] += match[score]
                self.games[game.name]['point_difference'] += match[score] - match[opp_score]

                # Which position did they lose in?
                if match['game'] == 'Doubles':
                    self.matches_per_side[int(match[team][1] == self.name)]['matches'] += 1
                    self.matches_per_side[int(match[team][1] == self.name)][category] += 1

            self.games[game.name]['matches'] = \
                self.games[game.name]['wins'] + self.games[game.name]['losses']

        for player in players:
            if player == self: continue
            self.teammate_ranking[player.name] = self.wins_with[player.name] - self.losses_with[player.name]
            self.opponent_ranking[player.name] = self.wins_against[player.name] - self.losses_against[player.name]

        self.wins_with = sorted_by_value(self.wins_with)
        self.wins_against = sorted_by_value(self.wins_against)
        self.losses_with = sorted_by_value(self.losses_with)
        self.losses_against = sorted_by_value(self.losses_against)
        self.teammate_ranking = sorted_by_value(self.teammate_ranking)
        self.opponent_ranking = sorted_by_value(self.opponent_ranking)

        ranked_played_with = [p for p in self.teammate_ranking.keys() if self.games_with[p] > 0]
        ranked_played_against = [p for p in self.opponent_ranking.keys() if self.games_with[p] > 0]
        self.best_mate = ranked_played_with[-1] if len(ranked_played_with) > 0 else None
        self.worst_mate = ranked_played_with[0] if len(ranked_played_with) > 0 else None
        self.nemesis = ranked_played_against[0] if len(ranked_played_against) > 0 else None
        self.antinemesis = ranked_played_against[-1] if len(ranked_played_against) > 0 else None

    def __str__(self) -> str:
        return self.name
# Define players
players = [Player(name) for name in player_names]
