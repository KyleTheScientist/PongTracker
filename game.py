class Game():
    '''
    Class that defines a game and its playstyle
    '''
    def __init__(self, name, ppt, ffa, bounds, index, color) -> None:
        self.name = name
        self.ppt = ppt
        self.ffa = ffa
        self.bounds = bounds # Score range
        self.color = color
        self.index = index

    def __str__(self) -> str:
        return self.name

games = [
    Game('Singles', 1, False, (0, 99), 1, '#e9c46a'),
    Game('Doubles', 2, False, (0, 99), 2, '#2a9d8f'),
    Game('Triples', 3, False, (0, 99), 3, '#e76f51'),
    Game('Ping Around The Rosie', 1, True, (1, 3), 4, '#db697c'),
]

ffa_games = [g for g in games if g.ffa]
team_games = [g for g in games if not g.ffa]

def get_game(string):
    for g in games:
        if g.name == string:
            return g
    return None
