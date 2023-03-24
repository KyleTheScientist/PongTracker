from game import games, team_games
from team import players, player_names
from tinydb import Query, TinyDB
from nicegui import ui

db = TinyDB('data/database.json')


def get_win_series():
    series = []
    for game in games:
        table = db.table(game.name)
        data = []
        for player in player_names:
            match = Query()
            wins = len(table.search(
                (match.team1.any([player])) | (match.winner == player)
            ))
            match = Query()
            losses = len(table.search(
                (match.team2.any([player])) | (match.winner != player)
            ))

            if wins + losses == 0:
                data.append(0)
            else:
                data.append(wins / (wins + losses))
        series.append({'name': game.name, 'data': data})
    return series


def get_perfect_series():
    for game in team_games:
        table = db.table(game.name)
        data = []
        perfects = []
        for player in player_names:
            match = Query()
            wins = len(table.search(
                (match.team1.all([player])) | (match.team2.score == 0)
            ))
            data.append(wins)
        perfects.append(data)

    # summing perfects across all team games
    totals = []
    for i in range(len(data)):
        sum = 0
        for p in perfects:
            sum += p[i]
        totals.append(sum)

    return [{"showInLegend": False, 'data': totals}]

def win_rate():
    return ui.chart(
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
            'series': get_win_series(),
        }
    ).classes('w-full h-full')


def perfects():
    return ui.chart(
        {
            'title': {'text': 'Perfects'},
            'chart': {'type': 'bar'},
            'xAxis': {'categories': player_names},
            'yAxis': {'title': False, 'allowDecimals': False},
            'series': get_perfect_series(),
        }
    ).classes('w-full h-full')


def game_lambda(game):
    return lambda g: g == game.name


def player_lambda(player):
    return lambda p: p == player


ignored_fields = ['game', 'ffa']
def logs():
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

card_classes = 'w-full gap-1 place-content-center bg-primary border-white border-4 rounded-lg'
icon_classes = 'text-2xl text-white fg-white padding p-1'
label_classes = 'text-2xl font-bold text-white'
value_classes = 'text-2xl font-semibold	w-full bg-accent padding p-1 text-center text-white border-white border-4 rounded-lg'

def stat_card(icon, label, player, stat):
    values = {}
    with ui.card().classes(card_classes):
        ui.icon(icon).classes(icon_classes)
        with ui.row().classes('w-full items-center place-content-center'):
            ui.label(label).classes(label_classes)
        with ui.row().classes('w-full'):
            values[label] = ui.label().classes(value_classes).bind_text_from(player, stat)


def stats():
    with ui.column().classes('w-full gap-5'):
        # Render player dropdown
        player_select = ui.select(
            player_names,
            label='Player',
        ).classes('w-full items-center text-xl')

        # Render table
        for player in players:
            player.refresh()
            matches = player.games
            best_position = 'Server' if player.server_wins > player.receiver_wins else "Receiver"
            best_position = 'Either' if player.server_wins == player.receiver_wins else best_position
            with ui.column().bind_visibility_from(player_select, 'value', backward=player_lambda(player.name)).classes('w-full'):
                # Wins/Losses
                with ui.row().classes('w-full'):
                    stat_card('arrow_upward', 'Wins', player, 'wins')
                    stat_card('arrow_downward', 'Losses', player, 'losses')
                # Games/Win Rate
                with ui.row().classes('w-full'):
                    stat_card('tag', 'Games', player, 'games')
                    stat_card('timelapse', 'Win Rate', player, 'win_rate')
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


