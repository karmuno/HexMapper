#!/usr/bin/env python3
"""
Hex Grid Generator Module

This module handles the creation of hexagonal grids for the map.
It creates a grid centered at a geographic coordinate and provides
functions to access hexes by their coordinates.
"""

import math
from typing import Dict, List, Tuple, Optional, Set, Generator, Any
from dataclasses import dataclass, field

from .hex_math import CubeHex, axial_to_cube, offset_to_cube, hex_range, hex_spiral


@dataclass
class Hex:
    """
    A single hex in the grid, containing both coordinate and geographic data.
    """
    # Coordinate data
    cube_coord: CubeHex
    
    # Geographic data
    center_latlon: Tuple[float, float] = None
    elevation: float = None
    humidity: float = None
    precipitation: float = None
    
    # Classification data
    terrain: str = None
    region_id: int = None
    
    # Additional data
    properties: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def q(self) -> int:
        """Axial q coordinate."""
        return self.cube_coord.x
    
    @property
    def r(self) -> int:
        """Axial r coordinate."""
        return self.cube_coord.z
    
    @property
    def lat(self) -> Optional[float]:
        """Latitude of the hex center."""
        return self.center_latlon[0] if self.center_latlon else None
    
    @property
    def lon(self) -> Optional[float]:
        """Longitude of the hex center."""
        return self.center_latlon[1] if self.center_latlon else None
    
    def set_terrain(self, terrain_type: str) -> None:
        """Set the terrain type for this hex."""
        self.terrain = terrain_type
    
    def set_region(self, region_id: int) -> None:
        """Set the region ID for this hex."""
        self.region_id = region_id
    
    def set_geographic_center(self, lat: float, lon: float) -> None:
        """Set the geographic center coordinates of this hex."""
        self.center_latlon = (lat, lon)


@dataclass
class HexGrid:
    """
    A hexagonal grid of variable dimensions.
    """
    # Grid dimensions
    width: int  # Number of hexes horizontally
    height: int  # Number of hexes vertically
    hex_size: float  # Size of each hex in miles (flat-to-flat)
    
    # Geographic position
    center_lat: float
    center_lon: float
    
    # Generated data
    hexes: Dict[CubeHex, Hex] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize the grid with empty hexes."""
        # Create the grid using cube coordinates
        center = CubeHex(0, 0, 0)
        
        # Calculate the radius needed to cover the requested width and height
        # This is an approximation - we'll filter it to match width/height later
        radius = max(self.width, self.height) // 2 + 1
        
        # Get all hexes within the radius (in spiral order)
        all_hexes = hex_spiral(center, radius)
        
        # Filter to keep only the hexes within the desired width and height
        # We'll use a rectangular bounding box in axial coordinates
        kept_hexes = []
        
        half_width = self.width // 2
        half_height = self.height // 2
        
        for hex_coord in all_hexes:
            # Get axial coordinates
            q, r = hex_coord.x, hex_coord.z
            
            # Check if it's within our desired bounds
            if -half_width <= q <= half_width and -half_height <= r <= half_height:
                kept_hexes.append(hex_coord)
        
        # Create Hex objects for all the kept coordinates
        for hex_coord in kept_hexes:
            self.hexes[hex_coord] = Hex(cube_coord=hex_coord)
    
    def get_hex(self, cube_coord: CubeHex) -> Optional[Hex]:
        """Get the hex at the specified cube coordinates."""
        return self.hexes.get(cube_coord)
    
    def get_hex_by_axial(self, q: int, r: int) -> Optional[Hex]:
        """Get the hex at the specified axial coordinates."""
        cube_coord = axial_to_cube(q, r)
        return self.get_hex(cube_coord)
    
    def get_hex_by_offset(self, col: int, row: int) -> Optional[Hex]:
        """Get the hex at the specified offset coordinates."""
        cube_coord = offset_to_cube(col, row)
        return self.get_hex(cube_coord)
    
    def neighbors(self, hex_coord: CubeHex) -> List[Hex]:
        """Get all existing neighbors of the specified hex."""
        return [self.get_hex(neighbor) for neighbor in hex_coord.neighbors() 
                if neighbor in self.hexes]
    
    def __iter__(self) -> Generator[Hex, None, None]:
        """Iterate over all hexes in the grid."""
        for hex_obj in self.hexes.values():
            yield hex_obj
    
    def __len__(self) -> int:
        """Return the number of hexes in the grid."""
        return len(self.hexes)
    
    def to_dict(self) -> Dict:
        """Convert the grid to a dictionary representation."""
        return {
            "width": self.width,
            "height": self.height,
            "hex_size": self.hex_size,
            "center_lat": self.center_lat,
            "center_lon": self.center_lon,
            "hexes": [
                {
                    "q": hex_obj.q,
                    "r": hex_obj.r,
                    "lat": hex_obj.lat,
                    "lon": hex_obj.lon,
                    "terrain": hex_obj.terrain,
                    "region": hex_obj.region_id,
                    "elevation": hex_obj.elevation,
                    "humidity": hex_obj.humidity,
                    "precipitation": hex_obj.precipitation
                }
                for hex_obj in self.hexes.values()
            ]
        }


def create_hex_grid(center_lat: float, center_lon: float, hex_miles: int, 
                    width: int, height: int) -> HexGrid:
    """
    Create a new hexagonal grid centered at the given geographic coordinates.
    
    Args:
        center_lat: Central latitude of the map
        center_lon: Central longitude of the map
        hex_miles: Diameter (flat-to-flat) of each hex in miles
        width: Number of hexes horizontally
        height: Number of hexes vertically
    
    Returns:
        A HexGrid instance
    """
    grid = HexGrid(
        width=width,
        height=height,
        hex_size=hex_miles,
        center_lat=center_lat,
        center_lon=center_lon
    )
    
    return grid