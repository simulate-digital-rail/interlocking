from enum import Enum


class OccupancyState(Enum):
    FREE = 0
    RESERVED = 1
    RESERVED_OVERLAP = 2
    OCCUPIED = 3
