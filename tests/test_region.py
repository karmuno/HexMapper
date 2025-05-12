#!/usr/bin/env python3
"""
Test script for the region segmenter.
"""

import sys
import os
import logging
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap, Normalize

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.hex_maker.grid.grid import create_hex_grid
from src.hex_maker.geocoder.geocoder import assign_geographic_coordinates
from src.hex_maker.terrain.classifier import TerrainClassifier, TerrainThresholds
from src.hex_maker.region.segmenter import RegionSegmenter
from tests.test_terrain import simulate_environmental_data, TEST_THRESHOLDS


def plot_regions(grid, output_file='output/region_map.png', title='Hex Grid Region Map'):
    """Plot the regions for the grid."""
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # Extract coordinates and region data
    lons = []
    lats = []
    regions = []
    
    for hex_obj in grid:
        if hex_obj.center_latlon and hex_obj.region_id is not None:
            lons.append(hex_obj.lon)
            lats.append(hex_obj.lat)
            regions.append(hex_obj.region_id)
    
    if not regions:
        print("No region data to plot")
        return
    
    # Get a list of unique region IDs
    unique_regions = sorted(set(regions))
    
    # Create a colormap with distinct colors
    cmap = plt.colormaps['tab20']
    
    # Create a scatter plot with region colors
    for i, region_id in enumerate(unique_regions):
        # Get all hexes in this region
        region_indices = [j for j, r in enumerate(regions) if r == region_id]
        region_lons = [lons[j] for j in region_indices]
        region_lats = [lats[j] for j in region_indices]
        
        # Plot with a unique color
        ax.scatter(region_lons, region_lats, color=cmap(i % 20), s=100, marker='h', 
                   edgecolors='black', linewidths=0.5, label=f"Region {region_id}")
    
    # Add a legend with region IDs
    ax.legend(title="Regions", loc="upper right")
    
    # Set labels and title
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_title(title)
    
    # Save the figure
    plt.savefig(output_file)
    plt.close()
    
    print(f"Region map saved to {output_file}")


def test_region_segmenter():
    """Test the region segmenter."""
    # Create a grid for testing
    center_lat = 45.0
    center_lon = -93.0
    hex_miles = 10
    
    grid = create_hex_grid(
        center_lat=center_lat,
        center_lon=center_lon,
        hex_miles=hex_miles,
        width=10,
        height=10
    )
    
    # Assign geographic coordinates to each hex
    assign_geographic_coordinates(grid)
    
    # Simulate environmental data for testing
    simulate_environmental_data(grid)
    
    # Classify terrain
    classifier = TerrainClassifier(thresholds=TEST_THRESHOLDS)
    classifier.classify_grid(grid)
    
    # Apply fuzzy classification to smooth transitions
    classifier.apply_fuzzy_classification(grid)
    
    # Create region segmenter
    segmenter = RegionSegmenter()
    
    # Test K-means segmentation with different numbers of regions
    num_regions_to_test = [3, 5, 7]
    
    for num_regions in num_regions_to_test:
        print(f"\nTesting K-means segmentation with {num_regions} regions...")
        
        # Reset the region IDs
        for hex_obj in grid:
            hex_obj.set_region(None)
            
        # Segment using K-means without ensuring contiguity
        kmeans_regions = segmenter.segment_by_kmeans(grid, num_regions)
        
        print(f"Number of regions created: {len(kmeans_regions)}")
        for region_id, hexes in kmeans_regions.items():
            print(f"  Region {region_id}: {len(hexes)} hexes")
        
        # Plot the K-means regions
        plot_regions(grid, 
                    output_file=f'output/kmeans_regions_{num_regions}.png',
                    title=f'K-means Clustering - {num_regions} Regions')
        
        # Reset the region IDs
        for hex_obj in grid:
            hex_obj.set_region(None)
            
        # Segment using K-means with contiguity enforcement
        kmeans_regions = segmenter.segment_grid(grid, num_regions, ensure_contiguous=True)
        
        print(f"Number of contiguous regions created: {len(kmeans_regions)}")
        for region_id, hexes in kmeans_regions.items():
            print(f"  Region {region_id}: {len(hexes)} hexes")
        
        # Plot the K-means regions with contiguity enforcement
        plot_regions(grid, 
                    output_file=f'output/kmeans_contiguous_regions_{num_regions}.png',
                    title=f'K-means Clustering (Contiguous) - {num_regions} Regions')
    
    print("\nRegion segmentation testing complete.")
    return grid


if __name__ == "__main__":
    print("Testing region segmenter...")
    grid = test_region_segmenter()