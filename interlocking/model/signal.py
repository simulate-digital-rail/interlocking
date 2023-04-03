class Signal(object):

    def __init__(self, yaramo_signal):
        self.yaramo_signal = yaramo_signal
        self.state = "halt"  # Either halt or go
        self.track = None
