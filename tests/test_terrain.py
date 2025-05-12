#!/usr/bin/env python3
"""
Test script for the terrain classifier.
"""

import sys
import os
import logging
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.hex_maker.grid.grid import create_hex_grid
from src.hex_maker.geocoder.geocoder import assign_geographic_coordinates
from src.hex_maker.data_fetcher.data_fetcher import EnvironmentalDataFetcher
from src.hex_maker.terrain.classifier import TerrainClassifier, TerrainType, TerrainThresholds


# Define colors for each terrain type
TERRAIN_COLORS = {
    'mountains': '#A0A0A0',  # Gray
    'hills': '#C0C080',      # Light brown
    'forest': '#008000',     # Green
    'desert': '#F0E68C',     # Khaki
    'swamp': '#2F4F4F',      # Dark slate gray
    'water': '#0000FF',      # Blue
    'open': '#90EE90'        # Light green
}

# Custom terrain thresholds for testing
# These are more permissive to ensure we get a variety of terrain types
# even with our simulated data
TEST_THRESHOLDS = TerrainThresholds(
    mountain_elevation=300.0,
    hill_elevation=200.0,
    lowland_elevation=100.0,
    high_precipitation=15.0,
    medium_precipitation=5.0,
    low_precipitation=2.0,
    high_humidity=0.5,
    medium_humidity=0.3,
    low_humidity=0.1,
    high_tree_coverage=30.0
)


def plot_terrain(grid, output_file='output/terrain_map.png'):
    """Plot the terrain types for the grid."""
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # Extract coordinates and terrain data
    lons = []
    lats = []
    colors = []
    
    for hex_obj in grid:
        if hex_obj.center_latlon and hex_obj.terrain:
            lons.append(hex_obj.lon)
            lats.append(hex_obj.lat)
            # Get the color for this terrain type
            color = TERRAIN_COLORS.get(hex_obj.terrain, '#FFFFFF')
            colors.append(color)
    
    if not colors:
        print("No terrain data to plot")
        return
    
    # Create a scatter plot with terrain colors
    for i in range(len(lons)):
        ax.scatter(lons[i], lats[i], color=colors[i], s=100, marker='h', edgecolors='black', linewidths=0.5)
    
    # Create a legend
    legend_elements = [plt.Line2D([0], [0], marker='h', color='w', markerfacecolor=color, 
                                markersize=10, label=terrain) 
                     for terrain, color in TERRAIN_COLORS.items()]
    ax.legend(handles=legend_elements, title="Terrain Types")
    
    # Set labels and title
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_title('Hex Grid Terrain Map')
    
    # Save the figure
    plt.savefig(output_file)
    plt.close()


def simulate_environmental_data(grid):
    """Simulate environmental data for testing."""
    import random
    
    print("Simulating environmental data for testing...")
    
    # Set random seed for reproducibility
    random.seed(42)
    
    # Generate elevation data
    # Mountains in the northeast, low elevation in the southwest
    for hex_obj in grid:
        if hex_obj.center_latlon:
            # Normalize coordinates to 0-1 range relative to the grid center
            lat, lon = hex_obj.center_latlon
            lat_norm = (lat - grid.center_lat + 0.25) / 0.5  # -0.25 to 0.25 -> 0 to 1
            lon_norm = (lon - grid.center_lon + 0.25) / 0.5
            
            # Higher elevation in the northeast
            elevation_base = 100 + 300 * (lat_norm + lon_norm) / 2.0
            # Add some noise
            elevation = elevation_base + random.uniform(-50, 50)
            hex_obj.elevation = max(0, elevation)
    
    # Generate precipitation data
    # Higher precipitation in the northwest
    for hex_obj in grid:
        if hex_obj.center_latlon:
            lat, lon = hex_obj.center_latlon
            lat_norm = (lat - grid.center_lat + 0.25) / 0.5
            lon_norm = (lon - grid.center_lon + 0.25) / 0.5
            
            # Higher precipitation in the northwest
            precip_base = 10 * (lat_norm - lon_norm + 1) / 2.0
            # Add some noise
            precipitation = precip_base + random.uniform(-2, 2)
            hex_obj.precipitation = max(0, precipitation)
    
    # Generate humidity data
    # Higher humidity in the south
    for hex_obj in grid:
        if hex_obj.center_latlon:
            lat, lon = hex_obj.center_latlon
            lat_norm = (lat - grid.center_lat + 0.25) / 0.5
            
            # Higher humidity in the south (lower latitude)
            humidity_base = 0.7 - 0.6 * lat_norm
            # Add some noise
            humidity = humidity_base + random.uniform(-0.1, 0.1)
            hex_obj.humidity = max(0, min(1, humidity))
    
    print("Environmental data simulation complete.")


def test_terrain_classifier():
    """Test the terrain classifier."""
    # Create a grid for testing
    center_lat = 45.0
    center_lon = -93.0
    hex_miles = 10
    
    grid = create_hex_grid(
        center_lat=center_lat,
        center_lon=center_lon,
        hex_miles=hex_miles,
        width=7,
        height=7
    )
    
    # Assign geographic coordinates to each hex
    assign_geographic_coordinates(grid)
    
    # Simulate environmental data for testing
    simulate_environmental_data(grid)
    
    # Create terrain classifier with custom thresholds for testing
    classifier = TerrainClassifier(thresholds=TEST_THRESHOLDS)
    
    # Classify the terrain
    classifier.classify_grid(grid)
    
    # Get terrain distribution
    terrain_counts = classifier.get_terrain_counts(grid)
    total_hexes = sum(terrain_counts.values())
    
    print("\nTerrain distribution:")
    for terrain, count in terrain_counts.items():
        percentage = (count / total_hexes) * 100 if total_hexes > 0 else 0
        print(f"  {terrain}: {count} hexes ({percentage:.1f}%)")
    
    # Apply fuzzy classification to smooth transitions
    classifier.apply_fuzzy_classification(grid)
    
    # Plot the terrain map
    plot_terrain(grid)
    
    print("Terrain classification and visualization complete.")
    return grid


if __name__ == "__main__":
    print("Testing terrain classifier...")
    grid = test_terrain_classifier()