'''
This is the main file. Run this to start the server.
'''

import analytics

from collections import namedtuple
from nicegui import ui

from team import players, player_names
from game import games, team_games, ffa_games
from time import time
from form import Form

def refresh_charts():
    '''
    Refreshes the data in all the charts, tables, and player stat cards.
    '''

    for chart, update_method in page.charts:
        chart.options['series'] = update_method()
        chart.update()

    for player in players:
        player.refresh()
        if player.name == 'Grayson':
            print(player.matches_per_side)

    for i, log in enumerate(page.logs):
        log.options['rowData'] = analytics.db.table(games[i].name).all()
        log.update()

@ui.page('/')
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
    refresh_btn_classes = 'mt-10 bg-blue-400'
    with ui.tab_panels(tabs, value='Graphs').classes('w-full'):
        with ui.tab_panel('Graphs'):
            with ui.card():
                page.charts = analytics.render_charts()
                ui.button('Refresh', on_click=refresh_charts).classes('w-full').classes(refresh_btn_classes)
        with ui.tab_panel('Players'):
            page.logs = analytics.stats()
            ui.button('Refresh', on_click=refresh_charts).classes('w-full').classes(refresh_btn_classes)
        with ui.tab_panel('Logs'):
            page.logs = analytics.logs()
            ui.button('Refresh', on_click=refresh_charts).classes('w-full').classes(refresh_btn_classes)
        with ui.tab_panel('Add'):
            with ui.column().classes(panel_classes):
                Form().render()

if __name__ in {"__main__", "__mp_main__"}:
    class Page(): pass
    page = Page()
    ui.run(port=6969, title="Server", favicon="data/paddle.png")
