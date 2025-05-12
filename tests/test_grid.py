#!/usr/bin/env python3
"""
Test script for the hex grid generator.
"""

import sys
import os
import math
import matplotlib.pyplot as plt
import numpy as np

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.hex_maker.grid.hex_math import CubeHex
from src.hex_maker.grid.grid import create_hex_grid, HexGrid


def plot_hex_grid(grid: HexGrid, show_coords: bool = False):
    """Plot a hex grid using matplotlib."""
    # Set up the figure
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_aspect('equal')
    
    # Calculate the size of hexes for display
    # This is just for visualization, not geographic accuracy
    size = 1.0
    width = size * 2
    height = size * math.sqrt(3)
    
    # Function to calculate the vertices of a hex for drawing
    def hex_corners(q, r):
        # Convert from axial to pixel coordinates
        # Flat-topped orientation
        x = size * 3/2 * q
        y = size * math.sqrt(3) * (r + q/2)
        
        corners = []
        for i in range(6):
            angle = 2 * math.pi / 6 * (i + 0.5)  # +0.5 for flat-topped
            corners.append((x + size * math.cos(angle), y + size * math.sin(angle)))
        return corners
    
    # Draw each hex
    for hex_obj in grid:
        q, r = hex_obj.q, hex_obj.r
        corners = hex_corners(q, r)
        
        # Draw the hex
        polygon = plt.Polygon(corners, fill=False, edgecolor='black', linewidth=1)
        ax.add_patch(polygon)
        
        # Optionally draw the coordinates
        if show_coords:
            # Convert from axial to pixel coords
            x = size * 3/2 * q
            y = size * math.sqrt(3) * (r + q/2)
            
            ax.text(x, y, f"({q},{r})", ha='center', va='center', fontsize=8)
    
    # Set the axis limits
    # This is an approximation, might need adjustment for different grid sizes
    margin = 2
    ax.set_xlim(-grid.width * size, grid.width * size)
    ax.set_ylim(-grid.height * size, grid.height * size)
    
    # Show the grid
    plt.title(f'Hex Grid ({grid.width}x{grid.height})')
    plt.grid(False)
    plt.savefig('output/hex_grid_test.png')
    plt.show()


def test_grid_creation():
    """Test the creation of a hex grid with various sizes."""
    # Create a hex grid centered at a geographic location
    # For testing, we'll just use a dummy location
    grid = create_hex_grid(
        center_lat=45.0,   # Arbitrary latitude
        center_lon=-93.0,  # Arbitrary longitude
        hex_miles=10,      # 10 miles per hex
        width=10,          # 10 hexes wide
        height=10          # 10 hexes tall
    )
    
    # Output some basic information
    print(f"Grid dimensions: {grid.width}x{grid.height}")
    print(f"Hex size: {grid.hex_size} miles")
    print(f"Center coords: {grid.center_lat}, {grid.center_lon}")
    print(f"Number of hexes: {len(grid.hexes)}")
    
    # Verify that the grid has approximately the right number of hexes
    expected_hex_count = grid.width * grid.height
    actual_hex_count = len(grid.hexes)
    print(f"Expected ~{expected_hex_count} hexes, got {actual_hex_count}")
    
    # Plot the grid
    plot_hex_grid(grid, show_coords=True)
    
    return grid


if __name__ == "__main__":
    print("Testing hex grid generation...")
    grid = test_grid_creation()