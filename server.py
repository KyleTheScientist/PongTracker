import analytics

from collections import namedtuple
from nicegui import ui

from state import State
from team import players, player_names
from game import games, team_games, ffa_games
from time import time

# HACK The lambda functions weirdly cross-contaminate unless defined
# in a separate scope
def oob_lambda(game):
    return lambda x: game.bounds[0] <= x <= game.bounds[1]

def player_dropdown(label, on_change):
    select = ui.select(
        player_names,
        value=player_names[0],
        label=label,
        on_change=on_change,
    ).classes('w-full')
    state.player_selects.append(select)
    return select

def score_field(label, value, on_change, game):
    input = ui.number(
        label=label,
        value=value,
        format='%.0f',
        on_change=on_change,
        validation={
            'Required': lambda x: x is not None,
            f'Out of Range: {game.bounds}': oob_lambda(game),
            'Integers only': lambda x: int(x) == x
        }
    )
    state.score_inputs.append(input)
    return input

def render_ffa(game):
    with ui.row().classes('w-full'):
        player_dropdown(
            label=f"Winner",
            on_change=state.set_winner
        ).classes('w-full')
        score_field(
            'Lives left', value=3, game=game,
            on_change=state.set_lives_remaining,
        ).classes('w-full')

def render_team(team, game):
    with ui.column().classes('w-full'):
        for i in range(game.ppt):
            player_dropdown(
                label=f"Player {i + 1}",
                on_change=state.set_player,
            ).metadata = (team, i)

        score_field(
            'Final score', value=0, game=game,
            on_change=state.set_score,
        ).classes('w-full').metadata = team

def submit():
    if not state.validate():
        ui.notify(f'Please fix all errors before submitting.')
        return
    duration = time() - state.last_submission
    if duration < 60:
        ui.notify(f'A submission was made recently. Please wait at least {60 - int(duration)}s')
        return
    table = analytics.db.table(state.game.name)
    table.insert(state())
    state.last_submission = time()
    ui.notify('Submitted.')
    print(f'Submit {state()}')
    refresh_charts()

def refresh_charts():
    state.win_chart.options['series'] = analytics.get_win_series()
    state.win_chart.update()

    # state.perfect_chart.options['series'] = analytics.get_perfect_series()
    # state.perfect_chart.update()
    for player in players:
        player.refresh()

    for i, log in enumerate(state.logs):
        log.options['rowData'] = analytics.db.table(games[i].name).all()
        log.update()

@ui.page('/')
def main_page():
    ui.colors(primary='#2a9d8f', secondary='#e9c46a', accent='#e76f51', info='#264653')
    ui.header()
    with ui.tabs() as tabs:
        ui.tab('Graphs', icon='analytics')
        ui.tab('Players', icon='groups')
        ui.tab('Logs', icon='list')
        ui.tab('Add', icon='note_add')
        # ui.tab('Perfects', icon='star')

    panel_classes = 'gap w-full'
    refresh_btn_classes = 'mt-10 bg-blue-400'
    with ui.tab_panels(tabs, value='Graphs').classes('w-full'):
        with ui.tab_panel('Graphs'):
            with ui.card():
                state.win_chart = analytics.win_rate()
                ui.button('Refresh', on_click=refresh_charts).classes('w-full').classes(refresh_btn_classes)
        with ui.tab_panel('Players'):
            state.logs = analytics.stats()
            ui.button('Refresh', on_click=refresh_charts).classes('w-full').classes(refresh_btn_classes)
        with ui.tab_panel('Logs'):
            state.logs = analytics.logs()
            ui.button('Refresh', on_click=refresh_charts).classes('w-full').classes(refresh_btn_classes)
        with ui.tab_panel('Add'):
            with ui.column().classes(panel_classes):
                ui.select(
                    [g.name for g in games],
                    label='Gamemode',
                    on_change=state.pick_game
                ).classes('w-full items-center')

                # Render team game forms
                for game in team_games:
                    with ui.row().bind_visibility_from(state, game.name).classes('w-full'):
                        for index in range(2):
                            render_team(index, game)

                # Render free-for-all game forms
                for game in ffa_games:
                    # Only show form if this game is selected
                    with ui.row().bind_visibility_from(state, game.name).classes('w-full'):
                        render_ffa(game)

                ui.button('Submit', on_click=submit).bind_visibility(state, 'game').classes('w-full')
        # with ui.tab_panel('Perfects'):
        #     with ui.card():
        #         state.perfect_chart = analytics.perfects()
        #         ui.button('Refresh', on_click=refresh_charts).classes('w-full').classes(refresh_btn_classes)


if __name__ in {"__main__", "__mp_main__"}:

    state = State()
    state.last_submission = time() - 60

    ui.footer()
    ui.run(port=6969, title="Server", favicon="data/paddle.png")
