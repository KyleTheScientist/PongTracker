from nicegui import ui


class Test:
    def __init__(self) -> None:
        self.value = 1

    def increment(self):
        self.value += 1

test = Test()

ui.label('0').bind_text_from(test, 'value')
ui.button('Increment', on_click=test.increment)


ui.run(port=6970)


