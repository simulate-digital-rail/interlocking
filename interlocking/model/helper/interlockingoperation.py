from enum import Enum


class InterlockingOperationType(Enum):
    EXIT = 0
    RESET = 1
    PRINT_STATE = 2

    # Route Operations
    SET_ROUTE = 10
    FREE_ROUTE = 11
    RESET_ROUTE = 12

    # TDS Operations
    TDS_COUNT_IN = 20
    TDS_COUNT_OUT = 21


class InterlockingOperation(object):

    def __init__(self,
                 operation_type: InterlockingOperationType,
                 train_id: str = None,
                 yaramo_route=None,
                 infrastructure_provider=None,
                 segment_id=""):
        self.operation_type = operation_type
        self.train_id = train_id
        self.yaramo_route = yaramo_route
        self.infrastructure_provider = infrastructure_provider
        self.segment_id = segment_id
