from interlocking.infrastructureprovider import LoggingInfrastructureProvider, InfrastructureProvider
from typing import Type


class Settings(object):

    def __init__(self,
                 max_number_of_points_at_same_time: int = 5,
                 default_interlocking_provider: Type[InfrastructureProvider] | None = LoggingInfrastructureProvider,
                 activate_flank_protection: bool = True):
        self.max_number_of_points_at_same_time = max(max_number_of_points_at_same_time, 1)

        # For all elements that are not covered by an infrastructure provider, an instance of this default provider will
        # be created. This default provider can be None.
        self.default_interlocking_provider: Type[InfrastructureProvider] | None = default_interlocking_provider

        self.activate_flank_protection: bool = activate_flank_protection
