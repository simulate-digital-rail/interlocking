
class SignalController(object):

    def __init__(self, infrastructure_providers):
        self.signals = None
        self.infrastructure_providers = infrastructure_providers

    def reset(self):
        for signal_id in self.signals:
            self.set_signal_halt(self.signals[signal_id])

    def set_route(self, route):
        self.set_signal_go(route.start_signal)

    def set_signal_halt(self, signal):
        print(f"--- Set signal {signal.yaramo_signal.name} to halt")
        signal.state = "halt"
        for infrastructure_provider in self.infrastructure_providers:
            infrastructure_provider.set_signal_state(signal.yaramo_signal, "halt")

    def set_signal_go(self, signal):
        print(f"--- Set signal {signal.yaramo_signal.name} to go")
        signal.state = "go"
        for infrastructure_provider in self.infrastructure_providers:
            infrastructure_provider.set_signal_state(signal.yaramo_signal, "go")

    def print_state(self):
        print("State of Signals:")
        for signal_uuid in self.signals:
            signal = self.signals[signal_uuid]
            print(f"{signal.yaramo_signal.name}: {signal.state}")
