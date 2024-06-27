from enum import Enum


class OccupancyState(Enum):
    FREE = 0
    RESERVED = 1
    RESERVED_OVERLAP = 2
    OCCUPIED = 3
    FLANK_PROTECTION = 10
    FLANK_PROTECTION_TRANSPORT = 11
