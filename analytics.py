"""
This is were all the magic happens, baby. All the
logic regarding statistics occurs here.
"""

from game import games, team_games
from player import players, player_names
from tinydb import TinyDB
from nicegui import ui
from utils import ratio_safe, CallLater
import os

db = None

# Load a reference to the database
def load_db(path):
    global db
    db = TinyDB(path)

def get_teammate_series(player):
    '''
    Formats the teammate data so it can be rendered by ui.highchart()
    '''
    participants = [p for p in players if p != player and player.games_with[p.name] > 0]
    series = [
        {
            'name': 'Wins With', 'index': 2, 'color': '#2a9d8f', 'data': [
                player.wins_with[teammate.name] for teammate in participants
            ]
        },
        {
            'name': 'Losses With', 'index': 1, 'color': '#d40427', 'data': [
                player.losses_with[teammate.name] for teammate in participants
            ]
        },
    ]
    return series, [p.name for p in participants]

def get_opponent_series(player):
    '''
    Formats the teammate data so it can be rendered by ui.highchart()
    '''
    participants = [p for p in players if p != player and player.games_against[p.name] > 0]
    series = [
        {
            'name': 'Win Against', 'index': 2, 'color': '#2a9d8f', 'data': [
                player.wins_against[opponent.name] for opponent in participants
            ]
        },
        {
            'name': 'Losses Against', 'index': 1, 'color': '#d40427', 'data': [
                player.losses_against[opponent.name] for opponent in participants
            ]
        },
    ]
    return series, [p.name for p in participants]

def get_win_rate_series():
    '''
    Formats the win rate data so it can be rendered by ui.highchart()
    '''
    participants = [player for player in players if player.matches > 0]
    series = [
        {
            'name': game.name,
            'index': game.index,
            'color': game.color + '99',
            'pointPadding': game.index / 10,
            'data': [
                ratio_safe(player.games[game.name]['wins'], player.games[game.name]['matches'], 50, True) \
                    for player in participants
            ]
        } for game in games
    ]
    return series, [p.name for p in participants]

def get_win_loss_series():
    '''
    Formats the win/loss data so it can be rendered by ui.highchart()
    '''
    participants = [player for player in players if player.matches > 0]
    series = [
        {
            'name': 'Wins',
            'index': 1,
            'color': '#2a9d8f',
            'data': [player.wins for player in participants]
        },
        {
            'name': 'Losses',
            'index': 0,
            'color': '#e76f51',
            'data': [player.losses for player in participants]
        },
    ]
    return series, [p.name for p in participants]

def get_ppg_series():
    '''
    Formats the win/loss data so it can be rendered by ui.highchart()
    '''
    participants = [player for player in players if player.matches > 0]
    series = [
        {
            'name': game.name,
            'index': -game.index,
            'color': game.color + '99',
            'pointPadding': (len(games) - game.index) / 10,
            'data': [
                ratio_safe(player.games[game.name]['points'], player.games[game.name]['matches'], 5) \
                    for player in participants
            ]
        } for game in games if not game.ffa
    ]
    return series, [p.name for p in participants]

def get_perfect_series():
    '''
    Formats the perfect game data so it can be rendered by ui.highchart()
    '''
    data = []
    for player in players:
        data.append(player.perfects)
    return [{"showInLegend": False, 'data': data}]

def render_charts():
    '''
    Renders the charts (win rate/win losses) and a dropdown to switch between them.
    Returns a list of `ui.highchart`'s and their associated update methods as tuples.
    '''
    chart_select = ui.select(
        ['Win Rate', 'Wins/Losses', 'Points Per Game'],
        label='Graph',
    ).classes('w-full items-center text-xl')

    # Win rates per game
    with ui.column().bind_visibility_from(chart_select, 'value', backward=chart_lambda('Win Rate')).classes('w-full'):
        series, participants = get_win_rate_series()
        win_rates = ui.highchart(
        {
            'title': {'text': 'Win Rates'},
            'chart': {'type': 'column', 'height': '1000px', 'maxPadding': 0, 'minPadding': 0},
            'plotOptions': {
                'series': {
                    'threshold': 50
                },
                'column': {
                    'grouping': False,
                    'shadow': 'False'
                }
            },
            'xAxis': {'categories': participants},
            'yAxis': {
                'title': False,
                'allowDecimals': True,
            },
            'series': series,
        }
    ).classes('w-full h-full')

    # Overall wins/losses
    with ui.column().bind_visibility_from(chart_select, 'value', backward=chart_lambda('Wins/Losses')).classes('w-full'):
        series, participants = get_win_loss_series()
        win_loss = ui.highchart(
        {
            'title': {'text': 'Overall Wins/Losses'},
            'chart': {'type': 'bar', 'height': '660px'},
            'plotOptions': {
                'series': {
                    'stacking': 'normal',
                    'dataLabels': {
                        'enabled': True,
                        'style': {
                            'textOutline': {
                                'width': 0
                            },
                            'color': 'white'
                        }
                    }
                },
            },
            'xAxis': {'categories': participants},
            'yAxis': {'title': False, 'allowDecimals': False},
            'series': series,
        }
    ).classes('w-full h-full')

    with ui.column().bind_visibility_from(chart_select, 'value', backward=chart_lambda('Points Per Game')).classes('w-full'):
        series, participants = get_ppg_series()
        ppg = ui.highchart(
        {
            'title': {'text': 'Points Per Game'},
            'chart': {'type': 'column'},
            'plotOptions': {
                'series': {
                    'threshold': 5
                },
                'column': {
                    'grouping': False,
                    'shadow': 'False'
                }
            },
            'xAxis': {
                'categories': participants
            },
            'yAxis': {
                'title': False, 'allowDecimals': True,
            },
            'series': series,
        }
    ).classes('w-full h-full')
    return [
        (win_rates, CallLater(get_win_rate_series)),
        (win_loss, CallLater(get_win_loss_series)),
        (ppg, CallLater(get_ppg_series))
    ]

def render_player_charts(player):
    '''
    Renders the charts (win rate/win losses) and a dropdown to switch between them.
    Returns a list of `ui.highchart`'s and their associated update methods as tuples.
    '''
    chart_select = ui.select(
        ['Teammates', 'Opponents'],
        label='Graph',
    ).classes('w-full items-center text-xl')

    # Win rates per game
    with ui.column().bind_visibility_from(chart_select, 'value', backward=chart_lambda('Teammates')).classes('w-full'):
        series, participants = get_teammate_series(player)
        teammates = ui.highchart(
        {
            'title': {'text': 'Teammates'},
            'chart': {'type': 'bar', 'height': '800px'},
            'plotOptions': {
                'series': {
                    'stacking': 'normal',
                    'dataLabels': {
                        'enabled': True,
                        'style': {
                            'textOutline': {
                                'width': 0
                            },
                            'color': 'white'
                        }
                    }
                },
            },
            'xAxis': {'categories': participants},
            'yAxis': {'title': False, 'allowDecimals': True},
            'series': series,
        }
    ).classes('w-full h-full')

    # Overall wins/losses
    with ui.column().bind_visibility_from(chart_select, 'value', backward=chart_lambda('Opponents')).classes('w-full'):
        series, participants = get_opponent_series(player)
        opponents = ui.highchart(
        {
            'title': {'text': 'Opponents'},
            'chart': {'type': 'bar', 'height': '800px'},
            'plotOptions': {
                'series': {
                    'stacking': 'normal',
                    'dataLabels': {
                        'enabled': True,
                        'style': {
                            'textOutline': {
                                'width': 0
                            },
                            'color': 'white'
                        }
                    }
                },
            },
            'xAxis': {'categories': participants},
            'yAxis': {'title': False, 'allowDecimals': False},
            'series': series,
        }
    ).classes('w-full h-full')

    return [
        (teammates, CallLater(get_teammate_series, player)),
        (opponents, CallLater(get_opponent_series, player)),
    ]

# HACK The lambda functions weirdly cross-contaminate unless defined
# in a separate scope
def game_lambda(game):
    return lambda g: g == game.name

def player_lambda(player):
    return lambda p: p == player

def chart_lambda(chart):
    return lambda c: c == chart


ignored_fields = ['game', 'ffa']
def logs():
    '''
    Renders the match history for each game into a table and renders
    the game dropdown that toggles them.
    '''
    global db

    grids = []
    # Render game dropdown
    game_select = ui.select(
        [g.name for g in games],
        label='Gamemode',
        value=games[0].name,
    ).classes('w-full items-center')

    # Render table
    for game in games:
        table = db.table(game.name).all()
        with ui.column().bind_visibility_from(game_select, 'value', backward=game_lambda(game)).classes('w-full'):
            if len(table) <= 0:
                ui.label('No data').classes('text-4xl w-full text-center').style('padding: 100px')
                continue
            columnDefs = [{'headerName': key.upper(), 'field': key, 'sortable': True} for key in table[0].keys() if key not in ignored_fields]
            grids.append(ui.aggrid({
                'columnDefs': columnDefs,
                'rowData': table,
                'rowSelection': 'multiple',
                'width': '100%'
            }, theme='alpine').classes('w-full'))
    return grids

# Some style definitions
card_classes = 'w-full col-span-1 gap-1 place-content-center bg-primary border-white border-4 rounded-lg'
icon_classes = 'text-2xl text-white fg-white padding p-1'
label_classes = 'text-2xl font-bold text-white'
value_classes = 'text-2xl font-semibold	w-full bg-accent padding p-1 text-center text-white border-white border-4 rounded-lg'

def stat_card(icon, label, player, stat):
    '''
    Renders an individual statistic card and binds it's value to the
    associated player object so that we don't need to update the label
    manually whenever a new game is submitted.
    '''
    values = {}
    with ui.card().classes(card_classes):
        ui.icon(icon).classes(icon_classes)
        with ui.row().classes('w-full items-center place-content-center'):
            ui.label(label).classes(label_classes)
        with ui.row().classes('w-full'):
            values[label] = ui.label().classes(value_classes).bind_text_from(player, stat)


def stats():
    '''
    Renders the stats page, including a player dropdown menu that
    toggles the stat cards for each player.
    '''

    charts = []
    with ui.column().classes('w-full gap-5'):
        # Render player dropdown
        player_select = ui.select(
            player_names,
            label='Player',
        ).classes('w-full items-center text-xl')

        for player in players:
            with ui.column().bind_visibility_from(player_select, 'value', backward=player_lambda(player.name)).classes('w-full'):
                # Wins/Losses
                row_classes = 'w-full grid-flow-col'
                with ui.grid().classes(row_classes):
                    stat_card('arrow_upward', 'Wins', player, 'wins')
                    stat_card('arrow_downward', 'Losses', player, 'losses')
                # Games/Win Rate
                with ui.grid().classes(row_classes):
                    stat_card('tag', 'Games', player, 'matches')
                    stat_card('timelapse', 'Win Rate', player, 'win_rate')
                # Points per game
                with ui.grid().classes(row_classes):
                    stat_card('calculate', 'Points Per Game (1s/2s/3s)', player, 'points_per_game')
                with ui.grid().classes(row_classes):
                    stat_card('calculate', 'Point Diff. Per Game (1s/2s/3s)', player, 'difference_per_game')
                # Best Position
                with ui.grid().classes(row_classes):
                    stat_card('group', 'Best Position', player, 'best_position')
                # Best/Worst Teammate
                with ui.grid().classes(row_classes):
                    best_mate, worst_mate = player.best_mate, player.worst_mate
                    stat_card('handshake', 'Best Teammate', player, 'best_mate_str')
                    stat_card('handshake', 'Worst Teammate', player, 'worst_mate_str')
                # Nemesis/Anti-nemesis
                with ui.grid().classes(row_classes):
                    nemesis, antinemesis = player.nemesis, player.antinemesis
                    stat_card('bolt', 'Nemesis', player, 'nemesis_str')
                    stat_card('emoji_events', 'Anti-Nemesis', player, 'antinemesis_str')
                # Lunches
                with ui.grid().classes(row_classes):
                    stat_card('star', 'Lunches', player, 'perfects')
                charts += render_player_charts(player)
    return charts


