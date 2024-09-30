from enum import Enum


class IsRouteSetResult(Enum):
    ROUTE_SET_CORRECTLY = 0
    ROUTE_NOT_SET = 1  # The route wasn't set at all
    ROUTE_NOT_SET_CORRECTLY = 2  # Route should be set but state is corrupted
    ROUTE_SET_FOR_WRONG_TRAIN = 3
