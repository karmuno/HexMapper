#!/usr/bin/env python3
"""
Hex Grid Math Utilities

This module provides functions for working with hexagonal grids using the cube coordinate system.
The cube coordinate system is preferable for most hex grid calculations since it simplifies
many operations compared to axial or offset coordinates.

References:
- https://www.redblobgames.com/grids/hexagons/
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Set, Generator


@dataclass(frozen=True)
class CubeHex:
    """
    Cube coordinate hex representation.
    In cube coordinates, x + y + z = 0 must be true for all valid hexes.
    """
    x: int
    y: int
    z: int

    def __post_init__(self):
        if self.x + self.y + self.z != 0:
            raise ValueError(f"Cube coordinates must sum to 0: {self.x} + {self.y} + {self.z} != 0")

    def __add__(self, other: 'CubeHex') -> 'CubeHex':
        return CubeHex(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: 'CubeHex') -> 'CubeHex':
        return CubeHex(self.x - other.x, self.y - other.y, self.z - other.z)

    def scale(self, factor: int) -> 'CubeHex':
        """Multiply this hex's coordinates by a factor."""
        return CubeHex(self.x * factor, self.y * factor, self.z * factor)

    def distance(self, other: 'CubeHex') -> int:
        """Calculate the distance between two hexes in grid steps."""
        diff = self - other
        return (abs(diff.x) + abs(diff.y) + abs(diff.z)) // 2

    def neighbor(self, direction: int) -> 'CubeHex':
        """Get the neighboring hex in a specific direction (0-5)."""
        # Directions: 0=E, 1=NE, 2=NW, 3=W, 4=SW, 5=SE
        neighbors = [
            CubeHex(1, -1, 0),   # E
            CubeHex(1, 0, -1),   # NE
            CubeHex(0, 1, -1),   # NW
            CubeHex(-1, 1, 0),   # W
            CubeHex(-1, 0, 1),   # SW
            CubeHex(0, -1, 1)    # SE
        ]
        return self + neighbors[direction % 6]

    def neighbors(self) -> List['CubeHex']:
        """Get all six neighboring hexes."""
        return [self.neighbor(i) for i in range(6)]

    def to_axial(self) -> Tuple[int, int]:
        """Convert to axial coordinates (q,r)."""
        return (self.x, self.z)

    def to_offset(self, odd_r: bool = True) -> Tuple[int, int]:
        """
        Convert to offset coordinates (col,row).
        Uses odd-r offset by default (odd rows are offset).
        """
        col = self.x + (self.z - (self.z & 1)) // 2 if odd_r else self.x + (self.z) // 2
        row = self.z
        return (col, row)


def axial_to_cube(q: int, r: int) -> CubeHex:
    """Convert axial coordinates (q,r) to cube coordinates."""
    x = q
    z = r
    y = -x - z
    return CubeHex(x, y, z)


def offset_to_cube(col: int, row: int, odd_r: bool = True) -> CubeHex:
    """
    Convert offset coordinates (col,row) to cube coordinates.
    Uses odd-r offset by default (odd rows are offset).
    """
    if odd_r:
        x = col - (row - (row & 1)) // 2
        z = row
    else:
        x = col - (row) // 2
        z = row
    y = -x - z
    return CubeHex(x, y, z)


def cube_round(x: float, y: float, z: float) -> CubeHex:
    """
    Round floating point cube coordinates to the nearest hex.
    This is used when converting from pixel to hex coordinates.
    """
    rx = round(x)
    ry = round(y)
    rz = round(z)

    x_diff = abs(rx - x)
    y_diff = abs(ry - y)
    z_diff = abs(rz - z)

    # If x was rounded more than the others, recalculate it to satisfy x+y+z=0
    if x_diff > y_diff and x_diff > z_diff:
        rx = -ry - rz
    # If y was rounded more, recalculate it
    elif y_diff > z_diff:
        ry = -rx - rz
    # If z was rounded more, recalculate it
    else:
        rz = -rx - ry

    return CubeHex(int(rx), int(ry), int(rz))


def hex_ring(center: CubeHex, radius: int) -> List[CubeHex]:
    """Get all hexes at a specific distance (radius) from the center."""
    if radius <= 0:
        return [center] if radius == 0 else []

    results = []
    # Start at a specific corner and walk around the ring
    hex = center + CubeHex(radius, -radius, 0)  # Start at the east corner
    
    # Each side of the ring has 'radius' hexes
    for side in range(6):
        for _ in range(radius):
            results.append(hex)
            # Move in the next direction to walk around the ring
            hex = hex.neighbor(side + 2)  # +2 to move in CW direction
    
    return results


def hex_spiral(center: CubeHex, radius: int) -> List[CubeHex]:
    """Get all hexes within a specific distance (radius) from the center, in spiral order."""
    results = [center]
    for r in range(1, radius + 1):
        results.extend(hex_ring(center, r))
    return results


def hex_range(center: CubeHex, radius: int) -> Set[CubeHex]:
    """Get all hexes within a specific distance (radius) from the center, as a set."""
    results = set()
    for dx in range(-radius, radius + 1):
        for dy in range(max(-radius, -dx - radius), min(radius, -dx + radius) + 1):
            dz = -dx - dy
            results.add(center + CubeHex(dx, dy, dz))
    return results


def hex_line(start: CubeHex, end: CubeHex) -> List[CubeHex]:
    """Draw a line from start to end, returning all hexes along the line."""
    n = start.distance(end)
    if n == 0:
        return [start]
    
    results = []
    for i in range(n + 1):
        t = i / n
        x = (1 - t) * start.x + t * end.x
        y = (1 - t) * start.y + t * end.y
        z = (1 - t) * start.z + t * end.z
        results.append(cube_round(x, y, z))
    
    return results