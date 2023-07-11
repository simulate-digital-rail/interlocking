from yaramo.model import Signal as YaramoSignal


class Signal(object):

    def __init__(self, yaramo_signal):
        from interlocking.model import Track

        self.yaramo_signal: YaramoSignal = yaramo_signal
        self.state: str = "halt"  # Either halt or go
        self.track: Track or None = None
