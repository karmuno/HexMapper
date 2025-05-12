#!/usr/bin/env python3
"""
Test script for the hex center geocoder.
"""

import sys
import os
import math
import matplotlib.pyplot as plt
import numpy as np

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.hex_maker.grid.grid import create_hex_grid
from src.hex_maker.geocoder.geocoder import (
    assign_geographic_coordinates, 
    calculate_bounding_box,
    miles_per_longitude
)


def plot_geo_grid(grid, show_coords=False):
    """Plot the grid in geographic coordinates."""
    # Set up the figure
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # Extract lat/lon coordinates
    lats = []
    lons = []
    
    for hex_obj in grid:
        if hex_obj.center_latlon:
            lats.append(hex_obj.lat)
            lons.append(hex_obj.lon)
    
    # Plot the coordinates
    ax.scatter(lons, lats, marker='h', s=100, color='blue', alpha=0.7)
    
    # Highlight the center hex
    center_hex = grid.get_hex_by_axial(0, 0)
    if center_hex and center_hex.center_latlon:
        ax.scatter(center_hex.lon, center_hex.lat, marker='h', s=150, color='red')
    
    # Add labels
    if show_coords:
        for hex_obj in grid:
            if hex_obj.center_latlon:
                ax.text(hex_obj.lon, hex_obj.lat, f"({hex_obj.q},{hex_obj.r})", 
                        fontsize=8, ha='center', va='center')
    
    # Set labels and title
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_title('Hex Grid in Geographic Coordinates')
    
    # Save the figure
    plt.savefig('output/geo_grid_test.png')
    plt.show()


def test_geocoder():
    """Test the geocoder functions."""
    # Create a hex grid centered at a geographic location
    center_lat = 45.0   # Minneapolis, MN (approximately)
    center_lon = -93.0
    hex_miles = 10      # 10 miles per hex
    
    # Create a smaller grid to keep the distances reasonable
    grid = create_hex_grid(
        center_lat=center_lat,
        center_lon=center_lon,
        hex_miles=hex_miles,
        width=7,
        height=7
    )
    
    # Assign geographic coordinates to each hex
    assign_geographic_coordinates(grid)
    
    # Print some information
    print(f"Grid centered at {center_lat}, {center_lon}")
    print(f"Hex size: {hex_miles} miles")
    
    # Check the center hex
    center_hex = grid.get_hex_by_axial(0, 0)
    if center_hex and center_hex.center_latlon:
        print(f"Center hex coordinates: {center_hex.center_latlon}")
    
    # Calculate the bounding box
    grid_width_miles = grid.width * hex_miles * 0.75  # Approximate
    grid_height_miles = grid.height * hex_miles * 0.866  # Approximate
    min_lat, min_lon, max_lat, max_lon = calculate_bounding_box(
        center_lat, center_lon, grid_width_miles, grid_height_miles
    )
    print(f"Approximate bounding box: {min_lat}, {min_lon} to {max_lat}, {max_lon}")
    
    # Plot the grid
    plot_geo_grid(grid, show_coords=True)
    
    # Calculate and display some distance information
    # Miles per degree of longitude at this latitude
    mpdlon = miles_per_longitude(center_lat)
    print(f"Miles per degree of longitude at {center_lat}°: {mpdlon:.2f}")
    print(f"Miles per degree of latitude: 69.0 (approximate)")
    
    return grid


if __name__ == "__main__":
    print("Testing hex center geocoder...")
    grid = test_geocoder()