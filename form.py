from nicegui import ui
from game import games, team_games, ffa_games, Game, get_game
from player import player_names
from time import time
from analytics import db
from datetime import datetime
from server import refresh_charts

def get_lambda(y):
    return lambda x: x == y

def oob_lambda(game):
    return lambda x: game.bounds[0] <= x <= game.bounds[1]

class TeamForm:

    def __init__(self, index, game) -> None:
        self.index = index
        self.game = game

    def render_player(self, label):
        '''
        Renders a dropdown with all the player names.
        '''
        select = ui.select(
            player_names,
            label=label,
        ).classes('w-full')
        return select

    def render_score(self, label, value, game):
        '''
        Renders a number field with different rules based on the game.
        '''
        input = ui.number(
            label=label,
            value=value,
            format='%.0f',
            validation={
                'Required': lambda x: x is not None,
                f'Out of Range: {game.bounds}': oob_lambda(game),
                'Integers only': lambda x: int(x) == x
            }
        )
        return input

    def render(self):
        self.player_dropdowns = []
        with ui.card().classes('w-full'):
            with ui.column().classes('w-full'):
                for i in range(self.game.ppt):
                    label = f"Player {i + 1}"
                    if self.game.ppt == 1:
                        label = "Player"
                    if self.game.ppt == 2:
                        label = "Left Player" if i == 0 else "Right Player"
                    self.player_dropdowns.append(
                        self.render_player(label)
                    )

                self.score_field = self.render_score(
                    label='Final score',
                    value=0,
                    game=self.game,
                ).classes('w-full')
            return self

    def players(self):
        return [dropdown.value for dropdown in reversed(self.player_dropdowns)]

    def score(self):
        return self.score_field.value

    def errors(self):
        if None in [dropdown.value for dropdown in self.player_dropdowns]:
            return "All players must be specified"
        if len(set(self.players())) != self.game.ppt:
            return "A player can only be added to a team once"
        if 0 > self.score() > 99:
            return "Score must be within range 0<x<100"
        return None

class FFAForm():

    def __init__(self, game) -> None:
        self.game = game

    def render(self):
        '''
        Renders a player dropdowns next to a "Lives Left" field
        '''
        with ui.card().classes('w-full'):
            with ui.column().classes('w-full'):
                self.winner_dropdown = ui.select(
                    player_names,
                    label="Winner",
                ).classes('w-full')

                self.score_field = ui.number(
                    label="Lives remaining",
                    value=3,
                    format='%.0f',
                    validation={
                        'Required': lambda x: x is not None,
                        f'Out of Range: {self.game.bounds}': oob_lambda(self.game),
                        'Integers only': lambda x: int(x) == x
                    }
                ).classes('w-full')
        return self

    def errors(self):
         if self.winner_dropdown.value is None:
             return "All players must be specified"
         if 0 > self.score() > 99:
            return "Score must be within range 0<x<100"

    def winner(self):
        return self.winner_dropdown.value

    def score(self):
        return self.score_field.value

class Form:
    SUBMISSION_RATE_LIMIT = 5 # How often people can submit data

    def __init__(self) -> None:
        self.last_submission = 0

    def errors(self):
        game = get_game(self.game_dropdown.value)
        form = self.forms[game.name]
        if game.ffa:
            errors = form.errors()
            if errors:
                return errors
            return None

        for team in form:
            errors = team.errors()
            if errors:
                return errors
            for team2 in form:
                if team == team2: continue
                if set(team.players()) & set(team2.players()): # Check for intersection
                    return "Teams must not have shared players"
                if team.score() == team2.score():
                    return "Match cannot end in a draw"
                if abs(team.score() - team2.score()) < 2:
                    return "Match must be won by 2"
        return None

    def __call__(self):
        game = get_game(self.game_dropdown.value)
        data = {
            'game': game.name,
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'ffa': game.ffa
        }
        if game.ffa:
            data.update({
                'winner': self.forms[game.name].winner(),
                'lives': self.forms[game.name].score(),
            })
        else:
            teams = sorted(self.forms[game.name], key=lambda team: -team.score())
            data.update({
                'team1': teams[0].players(),
                'score1': teams[0].score(),
                'team2': teams[1].players(),
                'score2': teams[1].score(),
            })
        return data

    def submit(self):
        errors = self.errors()
        if errors:
            ui.notify(errors, color="red")
            return
        duration = time() - self.last_submission
        if duration < Form.SUBMISSION_RATE_LIMIT:
            ui.notify(
                f'A submission was made recently. Please wait at least {Form.SUBMISSION_RATE_LIMIT - int(duration)}s',
                color='orange'
            )
            return
        table = db.table(self.game_dropdown.value)
        state = self()
        table.insert(state)
        self.last_submission = time()
        ui.notify('Submitted.')
        print(f'Submit {state}')
        refresh_charts()

    def on_game_changed(self):
        pass

    def render(self) -> None:
        self.game_dropdown = ui.select(
            [g.name for g in games],
            label='Gamemode',
            on_change=self.on_game_changed
        ).classes('w-full items-center')

        # Render team game forms
        self.forms = {}
        for game in team_games:
            with ui.column().bind_visibility_from(self.game_dropdown, "value", backward=get_lambda(game.name)).classes('w-full'):
                team_forms = []
                for i in range(2):
                    with ui.row().classes('w-full'):
                        team_forms.append(TeamForm(i, game).render())
                self.forms[game.name] = team_forms

        # Render free-for-all game forms
        for game in ffa_games:
            with ui.column().bind_visibility_from(self.game_dropdown, "value", backward=get_lambda(game.name)).classes('w-full'):
                self.forms[game.name] = FFAForm(game).render()

        ui.button('Submit', on_click=self.submit).classes('w-full')
