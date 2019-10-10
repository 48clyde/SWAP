"""
A class for supporting the model that allows notifications of changes to the value
"""


class Observable:
    def __init__(self, initial_value=None):
        self.data = initial_value
        self.callbacks = {}

    def add_callback(self, func):
        self.callbacks[func] = 1

    def del_callback(self, func):
        del self.callbacks[func]

    def _docallbacks(self):
        for func in self.callbacks:
            func(self.data)

    def set(self, data):
        if (self.data != data):
            self.data = data
            self._docallbacks()

    def get(self):
        return self.data

    def unset(self):
        self.data = None
