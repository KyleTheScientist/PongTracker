"""
This is were all the magic happens, baby. All the
logic regarding statistics occurs here.
"""

from game import games, team_games
from team import players, player_names
from tinydb import TinyDB
from nicegui import ui

# Load a reference to the database
db = TinyDB('data/database.json')

def get_win_rate_series():
    '''
    Formats the win rate data so it can be rendered by ui.chart()
    '''
    series = []
    for game in games:
        data = []
        for player in players:
            per_game_stats = player.games[game.name]
            if per_game_stats['matches'] == 0:
                data.append(0)
            else:
                data.append((per_game_stats['wins'] / per_game_stats['matches']) * 100)
        series.append({'name': game.name, 'data': data})
    return series


class StatSeriesGenerator():
    def __getattribute__(self, name):
        data = []
        for player in players:
             data.append([player.name, getattr(player, name)])
        return {'name': name.replace('_', ' ').capitalize(), 'data': data}

def get_win_loss_series():
    '''
    Formats the win/loss data so it can be rendered by ui.chart()
    '''
    generator = StatSeriesGenerator()
    return [generator.wins, generator.losses]

def get_ppg_series():
    '''
    Formats the win/loss data so it can be rendered by ui.chart()
    '''
    generator = StatSeriesGenerator()
    series = generator.points_per_game
    series.update(dataSorting={'enabled': True})
    return [series]

def get_perfect_series():
    '''
    Formats the perfect game data so it can be rendered by ui.chart()
    '''
    data = []
    for player in players:
        data.append(player.perfects)
    return [{"showInLegend": False, 'data': data}]

def render_charts():
    '''
    Renders the charts (win rate/win losses) and a dropdown to switch between them.
    Returns a list of `ui.chart`'s and their associated update methods as tuples.
    '''
    charts = []
    chart_select = ui.select(
        ['Win Rate', 'Wins/Losses', 'Points Per Game'],
        label='Graph',
    ).classes('w-full items-center text-xl')
    # Win rates per game
    with ui.column().bind_visibility_from(chart_select, 'value', backward=chart_lambda('Win Rate')).classes('w-full'):
        win_rates = ui.chart(
        {
            'title': {'text': 'Win Rates'},
            'chart': {'type': 'bar', 'height': '1000px'},
            'plotOptions': {
                'series': {
                    'pointWidth': 10,
                    'centerInCategory': True
                },
            },
            'xAxis': {'categories': player_names},
            'yAxis': {'title': False, 'allowDecimals': True},
            'series': get_win_rate_series(),
        }
    ).classes('w-full h-full')

    # Overall wins/losses
    with ui.column().bind_visibility_from(chart_select, 'value', backward=chart_lambda('Wins/Losses')).classes('w-full'):
        win_loss = ui.chart(
        {
            'title': {'text': 'Overall Wins/Losses'},
            'chart': {'type': 'bar', 'height': '660px'},
            'plotOptions': {
                'series': {
                    'pointWidth': 10,
                    'centerInCategory': True,
                },
            },
            'xAxis': {'categories': player_names},
            'yAxis': {'title': False, 'allowDecimals': False},
            'series': get_win_loss_series(),
        }
    ).classes('w-full h-full')

    with ui.column().bind_visibility_from(chart_select, 'value', backward=chart_lambda('Points Per Game')).classes('w-full'):
        ppg = ui.chart(
        {
            'title': {'text': 'Points Per Game'},
            'chart': {'type': 'bar', 'height': '660px'},
            'plotOptions': {
                'series': {
                    'pointWidth': 10,
                    'centerInCategory': True,
                },
            },
            'xAxis': {'type': 'category'},
            'yAxis': {'title': False, 'allowDecimals': True},
            'series': get_ppg_series(),
        }
    ).classes('w-full h-full')
    return [
        (win_rates, get_win_rate_series),
        (win_loss, get_win_loss_series),
        (ppg, get_ppg_series)
    ]

def perfects():
    '''
    Renders the perfect game chart
    '''
    return ui.chart(
        {
            'title': {'text': 'Perfects'},
            'chart': {'type': 'bar'},
            'xAxis': {'categories': player_names},
            'yAxis': {'title': False, 'allowDecimals': False},
            'series': get_perfect_series(),
        }
    ).classes('w-full h-full')


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
        with ui.column().bind_visibility_from(game_select, 'value', backward=game_lambda(game)):
            if len(table) <= 0:
                ui.label('No data').classes('text-4xl w-full text-center').style('padding: 100px')
                continue
            columnDefs = [{'headerName': key.upper(), 'field': key} for key in table[0].keys() if key not in ignored_fields]
            grids.append(ui.aggrid({
                'columnDefs': columnDefs,
                'rowData': table,
                'rowSelection': 'multiple',
            }))
    return grids

# Some style definitions
card_classes = 'w-full gap-1 place-content-center bg-primary border-white border-4 rounded-lg'
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
    with ui.column().classes('w-full gap-5'):
        # Render player dropdown
        player_select = ui.select(
            player_names,
            label='Player',
        ).classes('w-full items-center text-xl')

        for player in players:
            with ui.column().bind_visibility_from(player_select, 'value', backward=player_lambda(player.name)).classes('w-full'):
                # Wins/Losses
                with ui.row().classes('w-full'):
                    stat_card('arrow_upward', 'Wins', player, 'wins')
                    stat_card('arrow_downward', 'Losses', player, 'losses')
                # Games/Win Rate
                with ui.row().classes('w-full'):
                    stat_card('tag', 'Games', player, 'matches')
                    stat_card('timelapse', 'Win Rate', player, 'win_rate')
                # Points per game
                with ui.row().classes('w-full'):
                    stat_card('calculate', 'Points Per Game', player, 'points_per_game')
                    stat_card('calculate', 'Point Diff. Per Game', player, 'difference_per_game')
                # Best Position
                with ui.row().classes('w-full'):
                    stat_card('group', 'Best Position', player, 'best_position')
                # Best/Worst Teammate
                with ui.row().classes('w-full'):
                    best_mate, worst_mate = player.best_mate, player.worst_mate
                    stat_card('handshake', 'Best Teammate', player, 'best_mate_str')
                    stat_card('handshake', 'Worst Teammate', player, 'worst_mate_str')
                # Nemesis/Anti-nemesis
                with ui.row().classes('w-full'):
                    nemesis, antinemesis = player.nemesis, player.antinemesis
                    stat_card('bolt', 'Nemesis', player, 'nemesis_str')
                    stat_card('emoji_events', 'Anti-Nemesis', player, 'antinemesis_str')
                # Lunches
                with ui.row().classes('w-full'):
                    stat_card('star', 'Lunches', player, 'perfects')


