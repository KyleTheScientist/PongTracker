'''
This is the main file. Run this to start the server.
'''

import tomllib
import sys

import analytics

from collections import namedtuple
from nicegui import ui

from player import players, player_names
from game import games, team_games, ffa_games
from time import time
from form import Form

'classes',
'client',
'default_slot',
'id',
'options',
'parent_slot',
'props',
'slots',
'style',
'tag',
'tooltip',
'update',
'visible'

if len(sys.argv) != 2:
    print("Expected single arg for config TOML file")
    sys.exit(1)

with open(sys.argv[1], "rb") as config_file:
    config = tomllib.load(config_file)


def refresh_charts():
    '''
    Refreshes the data in all the charts, tables, and player stat cards.
    '''
    for player in players:
        player.refresh()

    # for chart, update_func in page.charts:
    #     before = (chart.options['series'])
    #     chart.options['series'], chart.options['xAxis']['categories'] = update_func()
    #     after = (chart.options['series'])

    #     if before != after:
    #         print(before, ('-' * 100) + '\n', after, '=' * 100)

    for chart, update_func in page.charts:
        chart.update()

    for i, log in enumerate(page.logs):
        log.options['rowData'] = analytics.db.table(games[i].name).all()
        log.update()

@ui.page(config.get("root_path") or "/")
def main_page():
    '''
    Renders the main page. This is the page that everyone is first
    routed to, and currently the only page.
    '''
    ui.colors(primary='#2a9d8f', secondary='#e9c46a', accent='#e76f51', info='#264653')
    ui.header()
    with ui.tabs() as tabs:
        ui.tab('Graphs', icon='analytics')
        ui.tab('Players', icon='groups')
        ui.tab('Logs', icon='list')
        ui.tab('Add', icon='note_add')
        # ui.tab('Perfects', icon='star')

    for player in players:
        player.refresh() # Make sure player stats are up-to-date with the DB

    panel_classes = 'gap w-full'
    # refresh_btn_classes = 'mt-10 bg-blue-400'
    with ui.tab_panels(tabs, value='Graphs').classes('w-full'):
        with ui.tab_panel('Graphs'):
            with ui.card():
                page.charts = analytics.render_charts()
                # ui.button('Refresh', on_click=refresh_charts).classes('w-full').classes(refresh_btn_classes)
        with ui.tab_panel('Players'):
            with ui.card():
                page.charts += analytics.stats()
                # ui.button('Refresh', on_click=refresh_charts).classes('w-full').classes(refresh_btn_classes)
        with ui.tab_panel('Logs'):
            with ui.card():
                page.logs = analytics.logs()
                # ui.button('Refresh', on_click=refresh_charts).classes('w-full').classes(refresh_btn_classes)
        with ui.tab_panel('Add'):
            with ui.card():
                with ui.column().classes(panel_classes):
                    Form(page).render()


if __name__ in {"__main__", "__mp_main__"}:
    analytics.load_db(config.get("db_file") or "data/database.json")

    class Page(): pass
    page = Page()
    page.refresh_charts = refresh_charts

    ui.run(
        title="TopSpin",
        favicon="data/paddle.png",
        port=int(config.get("port") or 6969),
        reload=config.get("reload") or True,
    )
