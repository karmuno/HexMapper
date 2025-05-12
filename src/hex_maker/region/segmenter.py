#!/usr/bin/env python3
"""
Map Region Segmenter Module

This module divides the hex map into regions based on spatial partitioning,
ensuring that each region is contiguous.
"""

import logging
import random
import math
from typing import Dict, List, Tuple, Optional, Set, Any
from collections import defaultdict, deque

import numpy as np
from sklearn.cluster import KMeans

from ..grid.grid import Hex, HexGrid
from ..grid.hex_math import CubeHex

# Set up logging
logger = logging.getLogger(__name__)


class RegionSegmenter:
    """Divides the hex map into regions based on spatial partitioning."""
    
    def __init__(self):
        """Initialize the region segmenter."""
        pass
    
    def segment_by_kmeans(self, grid: HexGrid, num_regions: int, 
                          seed: Optional[int] = 42) -> Dict[int, List[Hex]]:
        """
        Divide the grid into regions using K-means clustering.
        
        This method uses the geographic coordinates of the hexes to divide them
        into clusters based on proximity. It is the primary method for region segmentation.
        
        Args:
            grid: The hex grid to segment
            num_regions: Number of regions to create
            seed: Random seed for reproducible results
        
        Returns:
            Dictionary mapping region IDs to lists of hexes
        """
        logger.info(f"Segmenting grid into {num_regions} regions using K-means")
        
        # Extract coordinates for clustering
        coords = []
        hexes = []
        
        for hex_obj in grid:
            if hex_obj.center_latlon:
                # Use the geographic coordinates for clustering
                coords.append([hex_obj.lat, hex_obj.lon])
                hexes.append(hex_obj)
        
        if len(coords) == 0:
            logger.error("No hexes with coordinates found")
            return {}
        
        # Convert to numpy array
        coords = np.array(coords)
        
        # Apply K-means clustering
        kmeans = KMeans(n_clusters=min(num_regions, len(coords)), 
                        random_state=seed, 
                        n_init=10)  # Multiple initializations for better results
        clusters = kmeans.fit_predict(coords)
        
        # Assign hexes to regions
        regions = defaultdict(list)
        for i, hex_obj in enumerate(hexes):
            region_id = int(clusters[i])
            regions[region_id].append(hex_obj)
            hex_obj.set_region(region_id)
        
        logger.info(f"Created {len(regions)} regions with K-means")
        return dict(regions)
    
    def ensure_contiguous_regions(self, grid: HexGrid) -> Dict[int, List[Hex]]:
        """
        Ensure that all regions in the grid are contiguous.
        
        This method checks each region for continuity. If a region is not
        contiguous, it splits it into multiple contiguous regions.
        
        Args:
            grid: The hex grid to process
        
        Returns:
            Dictionary mapping region IDs to lists of hexes
        """
        logger.info("Ensuring all regions are contiguous")
        
        # Get the current regions
        current_regions = defaultdict(list)
        for hex_obj in grid:
            if hex_obj.region_id is not None:
                current_regions[hex_obj.region_id].append(hex_obj)
        
        # Check each region for continuity
        new_regions = {}
        next_region_id = max(current_regions.keys()) + 1 if current_regions else 0
        
        for region_id, hexes in current_regions.items():
            # Find all contiguous subregions
            subregions = self._find_contiguous_subregions(grid, hexes)
            
            if len(subregions) == 1:
                # Region is already contiguous
                new_regions[region_id] = hexes
            else:
                # Region is not contiguous, split it
                logger.info(f"Region {region_id} is not contiguous, splitting into {len(subregions)} regions")
                
                # Keep the largest subregion with the original ID
                largest_subregion = max(subregions, key=len)
                new_regions[region_id] = largest_subregion
                
                # Assign new IDs to the other subregions
                for subregion in subregions:
                    if subregion is not largest_subregion:
                        new_id = next_region_id
                        next_region_id += 1
                        new_regions[new_id] = subregion
                        
                        # Update the region IDs in the hexes
                        for hex_obj in subregion:
                            hex_obj.set_region(new_id)
        
        logger.info(f"Final number of contiguous regions: {len(new_regions)}")
        return new_regions
    
    def _find_contiguous_subregions(self, grid: HexGrid, hexes: List[Hex]) -> List[List[Hex]]:
        """
        Find all contiguous subregions within a set of hexes.
        
        Args:
            grid: The hex grid
            hexes: List of hexes to check
        
        Returns:
            List of lists, where each inner list is a contiguous subregion
        """
        # Create a set of hex coordinates for quick lookup
        hex_coords = {hex_obj.cube_coord for hex_obj in hexes}
        
        # Keep track of which hexes we've visited
        visited = set()
        
        # Find all contiguous subregions
        subregions = []
        
        for hex_obj in hexes:
            if hex_obj.cube_coord in visited:
                continue
            
            # Start a new subregion with this hex
            subregion = []
            queue = deque([hex_obj])
            visited.add(hex_obj.cube_coord)
            
            # Breadth-first search to find all contiguous hexes
            while queue:
                current_hex = queue.popleft()
                subregion.append(current_hex)
                
                # Check all neighbors
                for neighbor in grid.neighbors(current_hex.cube_coord):
                    if (neighbor.cube_coord in hex_coords and 
                        neighbor.cube_coord not in visited):
                        queue.append(neighbor)
                        visited.add(neighbor.cube_coord)
            
            subregions.append(subregion)
        
        return subregions
    
    def segment_grid(self, grid: HexGrid, num_regions: int, 
                     ensure_contiguous: bool = True) -> Dict[int, List[Hex]]:
        """
        Segment the grid into regions using K-means clustering.
        
        Args:
            grid: The hex grid to segment
            num_regions: Number of regions to create
            ensure_contiguous: Whether to ensure that regions are contiguous
        
        Returns:
            Dictionary mapping region IDs to lists of hexes
        """
        # Use K-means clustering to segment the grid
        regions = self.segment_by_kmeans(grid, num_regions)
        
        # Optionally ensure that all regions are contiguous
        if ensure_contiguous:
            regions = self.ensure_contiguous_regions(grid)
        
        return regions