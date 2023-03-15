
class SignalController(object):

    def __init__(self, set_signal_state_callback):
        self.signals = None
        self.set_signal_state_callback = set_signal_state_callback

    def reset(self):
        for signal_id in self.signals:
            self.set_signal_halt(self.signals[signal_id])

    def set_route(self, route):
        self.set_signal_go(route.start_signal)

    def set_signal_halt(self, signal):
        print(f"--- Set signal {signal.yaramo_signal.name} to halt")
        signal.state = "halt"
        self.set_signal_state_callback(signal, "halt")

    def set_signal_go(self, signal):
        print(f"--- Set signal {signal.yaramo_signal.name} to go")
        signal.state = "go"
        self.set_signal_state_callback(signal, "go")

    def print_state(self):
        print("State of Signals:")
        for signal_uuid in self.signals:
            signal = self.signals[signal_uuid]
            print(f"{signal.yaramo_signal.name}: {signal.state}")
