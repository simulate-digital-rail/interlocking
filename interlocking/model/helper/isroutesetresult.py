from enum import Enum


class IsRouteSetResult(Enum):
    ROUTE_SET_CORRECTLY = 0
    ROUTE_NOT_SET = 1
    ROUTE_SET_FOR_WRONG_TRAIN = 2