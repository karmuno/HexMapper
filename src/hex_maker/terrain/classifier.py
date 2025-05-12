#!/usr/bin/env python3
"""
Terrain Classifier Module

This module classifies hexes into terrain types based on environmental data
such as elevation, precipitation, and humidity.
"""

import logging
from enum import Enum, auto
from typing import Dict, List, Tuple, Optional, Set, Any
from dataclasses import dataclass

from ..grid.grid import Hex, HexGrid

# Set up logging
logger = logging.getLogger(__name__)


class TerrainType(Enum):
    """Enum of possible terrain types."""
    MOUNTAINS = "mountains"
    HILLS = "hills"
    FOREST = "forest"
    DESERT = "desert"
    SWAMP = "swamp"
    WATER = "water"
    OPEN = "open"  # Default/fallback terrain


@dataclass
class TerrainThresholds:
    """Thresholds for terrain classification."""
    # Elevation thresholds (meters)
    mountain_elevation: float = 2000.0
    hill_elevation: float = 500.0
    lowland_elevation: float = 100.0
    
    # Precipitation thresholds (mm)
    high_precipitation: float = 150.0
    medium_precipitation: float = 50.0
    low_precipitation: float = 25.0
    
    # Humidity thresholds (proxy values)
    high_humidity: float = 0.7
    medium_humidity: float = 0.4
    low_humidity: float = 0.2
    
    # Tree coverage thresholds (%)
    high_tree_coverage: float = 60.0


class TerrainClassifier:
    """Classifies hexes into terrain types based on environmental data."""
    
    def __init__(self, thresholds: Optional[TerrainThresholds] = None):
        """
        Initialize the terrain classifier.
        
        Args:
            thresholds: Custom thresholds for classification, or None to use defaults
        """
        self.thresholds = thresholds or TerrainThresholds()
    
    def classify_hex(self, hex_obj: Hex) -> TerrainType:
        """
        Classify a single hex based on its environmental data.
        
        Args:
            hex_obj: The hex to classify
        
        Returns:
            The terrain type for the hex
        """
        # Check if we have all the required data
        if hex_obj.elevation is None or hex_obj.precipitation is None or hex_obj.humidity is None:
            logger.warning("Missing environmental data for hex classification")
            return TerrainType.OPEN
        
        # Get the thresholds
        t = self.thresholds
        
        # Classify based on rules from the design document
        
        # Check for mountains (high elevation)
        if hex_obj.elevation >= t.mountain_elevation:
            return TerrainType.MOUNTAINS
        
        # Check for hills (moderate elevation)
        if hex_obj.elevation >= t.hill_elevation:
            return TerrainType.HILLS
        
        # Check for swamp (very low elevation + high humidity/precipitation)
        if (hex_obj.elevation <= t.lowland_elevation and 
            (hex_obj.humidity >= t.high_humidity or hex_obj.precipitation >= t.high_precipitation)):
            return TerrainType.SWAMP
        
        # Check for forest (medium precipitation + potentially high tree coverage)
        # We don't have direct tree coverage data, so we're inferring from precipitation and humidity
        if (hex_obj.precipitation >= t.medium_precipitation and 
            hex_obj.humidity >= t.medium_humidity):
            return TerrainType.FOREST
        
        # Check for desert (low precipitation/humidity)
        if (hex_obj.precipitation <= t.low_precipitation or 
            hex_obj.humidity <= t.low_humidity):
            return TerrainType.DESERT
        
        # Check for water (very high humidity + low elevation)
        if (hex_obj.humidity >= t.high_humidity and 
            hex_obj.elevation <= t.lowland_elevation):
            return TerrainType.WATER
        
        # Default to open terrain
        return TerrainType.OPEN
    
    def classify_grid(self, grid: HexGrid) -> None:
        """
        Classify all hexes in the grid.
        
        Args:
            grid: The hex grid to classify
        """
        logger.info("Classifying terrain for all hexes in the grid")
        
        classified_count = 0
        for hex_obj in grid:
            terrain_type = self.classify_hex(hex_obj)
            hex_obj.set_terrain(terrain_type.value)
            classified_count += 1
        
        logger.info(f"Classified {classified_count} hexes")
    
    def get_terrain_counts(self, grid: HexGrid) -> Dict[str, int]:
        """
        Count the number of hexes of each terrain type.
        
        Args:
            grid: The hex grid to analyze
        
        Returns:
            Dictionary mapping terrain types to counts
        """
        counts = {terrain_type.value: 0 for terrain_type in TerrainType}
        
        for hex_obj in grid:
            if hex_obj.terrain:
                counts[hex_obj.terrain] += 1
        
        return counts
    
    def calibrate_thresholds(self, grid: HexGrid, target_distribution: Dict[str, float]) -> None:
        """
        Adjust thresholds to achieve a target distribution of terrain types.
        
        Args:
            grid: The hex grid to classify
            target_distribution: Dictionary mapping terrain types to target percentages (0-1)
        """
        logger.info("Calibrating terrain classification thresholds")
        
        # Start with the current thresholds
        best_thresholds = self.thresholds
        
        # Function to evaluate a set of thresholds
        def evaluate_thresholds(thresholds):
            # Create a new classifier with these thresholds
            classifier = TerrainClassifier(thresholds)
            
            # Classify the grid
            for hex_obj in grid:
                terrain_type = classifier.classify_hex(hex_obj)
                hex_obj.set_terrain(terrain_type.value)
            
            # Get the counts and calculate the error
            counts = classifier.get_terrain_counts(grid)
            total = sum(counts.values())
            
            error = 0.0
            for terrain, target_pct in target_distribution.items():
                actual_pct = counts.get(terrain, 0) / total if total > 0 else 0
                error += (actual_pct - target_pct) ** 2
            
            return error
        
        # TODO: Implement a more sophisticated optimization algorithm
        # For now, we'll just return the original thresholds
        
        # Apply the best thresholds
        self.thresholds = best_thresholds
        self.classify_grid(grid)
        
        logger.info("Threshold calibration complete")
    
    def apply_fuzzy_classification(self, grid: HexGrid, transition_radius: int = 1) -> None:
        """
        Apply fuzzy classification to smooth terrain transitions.
        
        Args:
            grid: The hex grid to update
            transition_radius: Number of hex steps to consider for transitions
        """
        logger.info("Applying fuzzy classification to smooth terrain transitions")
        
        # Store the original terrain types
        original_terrain = {hex_obj.cube_coord: hex_obj.terrain for hex_obj in grid}
        
        # For each hex, check its neighbors
        for hex_obj in grid:
            # Skip hexes without a terrain type
            if not hex_obj.terrain:
                continue
            
            # Get this hex's neighbors
            neighbors = grid.neighbors(hex_obj.cube_coord)
            
            # Count the terrain types of neighbors
            neighbor_terrains = {}
            for neighbor in neighbors:
                if neighbor.terrain:
                    neighbor_terrains[neighbor.terrain] = neighbor_terrains.get(neighbor.terrain, 0) + 1
            
            # If all neighbors have the same terrain, no need to adjust
            if len(neighbor_terrains) <= 1:
                continue
            
            # Check if this hex is a terrain "island" (all neighbors have a different terrain)
            hex_terrain = hex_obj.terrain
            max_terrain = max(neighbor_terrains.items(), key=lambda x: x[1])[0]
            
            # If this hex is an isolated terrain and most neighbors have a different terrain,
            # adjust it to match the most common neighbor terrain
            if hex_terrain not in neighbor_terrains and max_terrain != hex_terrain:
                hex_obj.set_terrain(max_terrain)
        
        logger.info("Fuzzy classification complete")