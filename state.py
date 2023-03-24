from game import games, get_game
from team import Team, player_names
from datetime import datetime


class State:
    def __init__(self):
        self.game = games[0]
        for game in games:
            setattr(self, game.name, game == games[0])
        self.teams = [Team([]), Team([])]
        self.winner = player_names[0]
        self.lives_remaining = 3
        self.set_game(None)
        self.player_selects = []
        self.score_inputs = []

    def set_player(self, args):
        team, index = args.sender.metadata
        self.teams[team].players[index] = args.value
        print(self)

    def set_score(self, args):
        team = args.sender.metadata
        self.teams[team].score = args.value
        print(self)

    def pick_game(self, args):
        game = get_game(args.value)
        self.set_game(game)

    def set_game(self, game):
        self.game = game
        for g in games:
            setattr(self, g.name, g == self.game)
        if not self.game:
            return

        for t in self.teams:
            t.players = [player_names[0] for _ in range(self.game.ppt)]
        for select in self.player_selects:
            select.value = player_names[0]
        for input in self.score_inputs:
            input.value = self.game.bounds[0]

        print(self)

    def set_winner(self, args):
        self.winner = args.value
        print(self)

    def set_lives_remaining(self, args):
        self.lives_remaining = args.value
        print(self)

    def __str__(self) -> str:
        if self.game.ffa:
            return f'Winner: {self.winner} | Lives remaining: {self.lives_remaining}'
        else:
            return '|'.join([str(t) for t in self.teams])

    def __call__(self):
        data = {
            'game': self.game.name,
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'ffa': self.game.ffa
        }
        if self.game.ffa:
            data.update({
                'winner': self.winner,
                'lives': self.lives_remaining,
            })
        else:
            teams = sorted(self.teams, key=lambda team: -team.score)
            data.update({
                'team1': teams[0].players,
                'score1': teams[0].score,
                'team2': teams[1].players,
                'score2': teams[1].score,
            })
        return data

    def validate(self):
        try:
            g = self.game
            assert g is not None
            if self.game.ffa:
                assert g.bounds[0] <= self.lives_remaining <= g.bounds[1]
            else:
                assert g.bounds[0] <= self.teams[0].score <= g.bounds[1]
                assert g.bounds[0] <= self.teams[1].score <= g.bounds[1]
        except Exception as e:
            print(e)
            return False
        return True

