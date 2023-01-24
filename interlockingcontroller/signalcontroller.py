
class SignalController(object):

    def __init__(self,set_signal_state_callback):
        self.signals = None
        self.set_signal_state_callback = set_signal_state_callback

    def reset(self):
        for signal in self.signals:
            self.set_signal_halt(signal)

    def set_route(self, route):
        self.set_signal_go(route.start_signal)

    def set_signal_halt(self, signal):
        print(f"--- Set signal {signal.id} to halt")
        signal.state = "halt"
        self.set_signal_state_callback(signal.id,"halt",signal.wirkrichtung)
       

    def set_signal_go(self, signal):
        print(f"--- Set signal {signal.id} to go")
        signal.state = "go"
        self.set_signal_state_callback(signal.id,"go",signal.wirkrichtung)

    def print_state(self):
        print("State of Signals:")
        for signal in self.signals:
            print(f"{signal.id}: {signal.state}")
