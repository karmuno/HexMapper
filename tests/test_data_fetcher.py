#!/usr/bin/env python3
"""
Test script for the environmental data fetcher.
"""

import sys
import os
import json
import logging
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import Normalize

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.hex_maker.grid.grid import create_hex_grid
from src.hex_maker.geocoder.geocoder import assign_geographic_coordinates
from src.hex_maker.data_fetcher.data_fetcher import EnvironmentalDataFetcher


def plot_elevation_data(grid, output_file='output/elevation_data.png'):
    """Plot elevation data for the grid."""
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # Extract coordinates and elevation
    lons = []
    lats = []
    elevations = []
    
    for hex_obj in grid:
        if hex_obj.center_latlon and hex_obj.elevation is not None:
            lons.append(hex_obj.lon)
            lats.append(hex_obj.lat)
            elevations.append(hex_obj.elevation)
    
    if not elevations:
        print("No elevation data to plot")
        return
    
    # Create a scatter plot with elevation as color
    sc = ax.scatter(lons, lats, c=elevations, cmap='terrain', s=100, marker='h', edgecolors='black', linewidths=0.5)
    
    # Add a color bar
    cbar = plt.colorbar(sc, ax=ax)
    cbar.set_label('Elevation (m)')
    
    # Set labels and title
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_title('Hex Grid Elevation Data')
    
    # Save the figure
    plt.savefig(output_file)
    plt.close()


def plot_climate_data(grid, output_file='output/climate_data.png'):
    """Plot climate data for the grid."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7))
    
    # Extract coordinates and climate data
    lons = []
    lats = []
    precipitation = []
    humidity = []
    
    for hex_obj in grid:
        if hex_obj.center_latlon and hex_obj.precipitation is not None and hex_obj.humidity is not None:
            lons.append(hex_obj.lon)
            lats.append(hex_obj.lat)
            precipitation.append(hex_obj.precipitation)
            humidity.append(hex_obj.humidity)
    
    if not precipitation or not humidity:
        print("No climate data to plot")
        return
    
    # Plot precipitation
    sc1 = ax1.scatter(lons, lats, c=precipitation, cmap='Blues', s=100, marker='h', edgecolors='black', linewidths=0.5)
    cbar1 = plt.colorbar(sc1, ax=ax1)
    cbar1.set_label('Precipitation (mm)')
    ax1.set_xlabel('Longitude')
    ax1.set_ylabel('Latitude')
    ax1.set_title('Precipitation Data')
    
    # Plot humidity
    sc2 = ax2.scatter(lons, lats, c=humidity, cmap='BuGn', s=100, marker='h', edgecolors='black', linewidths=0.5)
    cbar2 = plt.colorbar(sc2, ax=ax2)
    cbar2.set_label('Humidity (proxy)')
    ax2.set_xlabel('Longitude')
    ax2.set_ylabel('Latitude')
    ax2.set_title('Humidity Data')
    
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()


def test_data_fetcher():
    """Test the environmental data fetcher."""
    # Create a smaller grid for testing
    center_lat = 45.0   # Minneapolis, MN (approximately)
    center_lon = -93.0
    hex_miles = 10
    
    grid = create_hex_grid(
        center_lat=center_lat,
        center_lon=center_lon,
        hex_miles=hex_miles,
        width=5,
        height=5
    )
    
    # Assign geographic coordinates to each hex
    assign_geographic_coordinates(grid)
    
    # Create data fetcher
    data_fetcher = EnvironmentalDataFetcher(
        config_path='config/api_keys.json',
        cache_dir='data/cache'
    )
    
    try:
        # Fetch all environmental data
        data_fetcher.fetch_all_data(grid)
        
        # Print some statistics
        elevation_values = [hex_obj.elevation for hex_obj in grid if hex_obj.elevation is not None]
        precipitation_values = [hex_obj.precipitation for hex_obj in grid if hex_obj.precipitation is not None]
        humidity_values = [hex_obj.humidity for hex_obj in grid if hex_obj.humidity is not None]
        
        print(f"Number of hexes: {len(grid)}")
        print(f"Hexes with elevation data: {len(elevation_values)}")
        print(f"Hexes with precipitation data: {len(precipitation_values)}")
        print(f"Hexes with humidity data: {len(humidity_values)}")
        
        if elevation_values:
            print(f"Elevation range: {min(elevation_values):.1f} - {max(elevation_values):.1f} m")
        
        if precipitation_values:
            print(f"Precipitation range: {min(precipitation_values):.1f} - {max(precipitation_values):.1f} mm")
        
        if humidity_values:
            print(f"Humidity range: {min(humidity_values):.1f} - {max(humidity_values):.1f}")
        
        # Plot the data
        plot_elevation_data(grid)
        plot_climate_data(grid)
        
        print("Data fetching and plotting complete.")
    except Exception as e:
        print(f"Error during data fetching: {e}")
    
    return grid


if __name__ == "__main__":
    print("Testing environmental data fetcher...")
    grid = test_data_fetcher()