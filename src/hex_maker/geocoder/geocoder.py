#!/usr/bin/env python3
"""
Hex Center Geocoder Module

This module handles the conversion between hex grid coordinates and
geographical coordinates (latitude/longitude).
"""

import math
import geopy.distance
from typing import Dict, List, Tuple, Optional, Set

from ..grid.hex_math import CubeHex
from ..grid.grid import Hex, HexGrid


# Earth's radius in miles
EARTH_RADIUS_MILES = 3958.8

# Constants for conversion
MILES_PER_LATITUDE = 69.0  # Miles per degree of latitude (approximate)
# Miles per degree of longitude varies with latitude
# At the equator, it's approximately 69.0 miles per degree as well


def miles_per_longitude(latitude: float) -> float:
    """
    Calculate miles per degree of longitude at a given latitude.
    
    Args:
        latitude: Latitude in degrees
    
    Returns:
        Miles per degree of longitude at the specified latitude
    """
    # Convert latitude to radians
    lat_rad = math.radians(latitude)
    
    # Calculate miles per degree of longitude
    # This decreases as you move away from the equator
    return math.cos(lat_rad) * MILES_PER_LATITUDE


def calculate_bounding_box(center_lat: float, center_lon: float,
                           width_miles: float, height_miles: float) -> Tuple[float, float, float, float]:
    """
    Calculate the bounding box of coordinates based on a center point and dimensions.
    
    Args:
        center_lat: Center latitude
        center_lon: Center longitude
        width_miles: Width in miles
        height_miles: Height in miles
    
    Returns:
        Tuple of (min_lat, min_lon, max_lat, max_lon)
    """
    # Calculate the latitude range
    half_height_degrees = height_miles / (2 * MILES_PER_LATITUDE)
    min_lat = center_lat - half_height_degrees
    max_lat = center_lat + half_height_degrees
    
    # Calculate the longitude range
    # We use the center latitude to determine miles per degree of longitude
    miles_per_lon = miles_per_longitude(center_lat)
    half_width_degrees = width_miles / (2 * miles_per_lon)
    min_lon = center_lon - half_width_degrees
    max_lon = center_lon + half_width_degrees
    
    return (min_lat, min_lon, max_lat, max_lon)


def distance_between_coords(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the distance between two coordinate pairs in miles.
    
    Args:
        lat1: First latitude
        lon1: First longitude
        lat2: Second latitude
        lon2: Second longitude
    
    Returns:
        Distance in miles
    """
    # Use geopy's distance calculator
    return geopy.distance.distance((lat1, lon1), (lat2, lon2)).miles


def bearing_between_coords(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the bearing from one coordinate to another (initial compass heading).
    
    Args:
        lat1: Starting latitude
        lon1: Starting longitude
        lat2: Ending latitude
        lon2: Ending longitude
    
    Returns:
        Bearing in degrees (0-360)
    """
    # Convert coordinates to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Calculate the bearing
    y = math.sin(lon2_rad - lon1_rad) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - \
        math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(lon2_rad - lon1_rad)
    
    bearing_rad = math.atan2(y, x)
    bearing_deg = math.degrees(bearing_rad)
    
    # Convert to range 0-360
    return (bearing_deg + 360) % 360


def destination_coord(lat: float, lon: float, bearing: float, distance_miles: float) -> Tuple[float, float]:
    """
    Calculate the destination point given a starting point, bearing, and distance.
    
    Args:
        lat: Starting latitude
        lon: Starting longitude
        bearing: Bearing in degrees
        distance_miles: Distance in miles
    
    Returns:
        Tuple of (destination_lat, destination_lon)
    """
    # Use geopy's distance calculator
    origin = geopy.Point(lat, lon)
    destination = geopy.distance.distance(miles=distance_miles).destination(origin, bearing)
    
    return (destination.latitude, destination.longitude)


def assign_geographic_coordinates(grid: HexGrid) -> None:
    """
    Assign geographic coordinates (lat/lon) to each hex in the grid.
    
    This function calculates the real-world geographic coordinates of each hex center
    based on the grid's center coordinates and the hex size.
    
    Args:
        grid: The hex grid to update
    
    Returns:
        None (modifies the grid in place)
    """
    # Center hex is at the specified center coordinates
    center_hex = grid.get_hex_by_axial(0, 0)
    if center_hex:
        center_hex.set_geographic_center(grid.center_lat, grid.center_lon)
    
    # Calculate the horizontal and vertical spacing between hexes
    # For flat-topped hexes:
    hex_width_miles = grid.hex_size  # flat-to-flat width
    hex_height_miles = hex_width_miles * math.sqrt(3) / 2  # height is sqrt(3) * width / 2
    
    # Horizontal spacing between hex centers is 3/4 of the hex width
    horiz_spacing = hex_width_miles * 3/4
    
    # Vertical spacing between hex centers is the hex height
    vert_spacing = hex_height_miles
    
    # For each hex in the grid, calculate its geographical center
    for hex_obj in grid:
        # Skip the center hex (already assigned)
        if hex_obj.q == 0 and hex_obj.r == 0:
            continue
        
        # Convert from axial coordinates to distance and direction from center
        # This is an approximation and works best for smaller areas
        # For more accurate results over large areas, we'd need to use a proper projection
        
        # Calculate the offset in miles from the center
        # For axial coordinates with flat-topped hexes, move:
        # - q units horizontally
        # - r units diagonally (which has both horizontal and vertical components)
        x_offset_miles = hex_obj.q * horiz_spacing
        y_offset_miles = (hex_obj.r + hex_obj.q / 2) * vert_spacing
        
        # Convert to polar coordinates (angle and distance)
        distance = math.sqrt(x_offset_miles**2 + y_offset_miles**2)
        
        # Calculate the bearing
        # 0 degrees is north, increase clockwise
        bearing = math.degrees(math.atan2(x_offset_miles, -y_offset_miles)) % 360
        
        # Calculate the destination coordinates
        dest_lat, dest_lon = destination_coord(
            grid.center_lat, grid.center_lon, bearing, distance
        )
        
        # Assign the coordinates to the hex
        hex_obj.set_geographic_center(dest_lat, dest_lon)