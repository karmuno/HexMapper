#!/usr/bin/env python3
"""
Environmental Data Fetcher

This module fetches environmental data (elevation, climate, etc.) for each
hex in the grid using various APIs.
"""

import os
import json
import logging
import time
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path

from ..grid.grid import Hex, HexGrid
from .api_client import create_api_clients, APIClient

# Set up logging
logger = logging.getLogger(__name__)


class DataCache:
    """Cache for API responses to avoid redundant requests."""
    
    def __init__(self, cache_dir: str = "data/cache"):
        """
        Initialize the data cache.
        
        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.memory_cache = {}
    
    def get(self, key: str, max_age_seconds: int = 86400) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            max_age_seconds: Maximum age of the cached value in seconds (default: 1 day)
        
        Returns:
            Cached value, or None if not found or expired
        """
        # Check memory cache first
        if key in self.memory_cache:
            timestamp, value = self.memory_cache[key]
            if time.time() - timestamp <= max_age_seconds:
                return value
        
        # Check file cache
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    timestamp = data.get("timestamp", 0)
                    value = data.get("value")
                    
                    # Check if the cache is still valid
                    if time.time() - timestamp <= max_age_seconds:
                        # Update memory cache
                        self.memory_cache[key] = (timestamp, value)
                        return value
            except Exception as e:
                logger.warning(f"Failed to read cache file {cache_file}: {e}")
        
        return None
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        timestamp = time.time()
        
        # Update memory cache
        self.memory_cache[key] = (timestamp, value)
        
        # Update file cache
        cache_file = self.cache_dir / f"{key}.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump({
                    "timestamp": timestamp,
                    "value": value
                }, f)
        except Exception as e:
            logger.warning(f"Failed to write cache file {cache_file}: {e}")
    
    def clear(self) -> None:
        """Clear all cached values."""
        # Clear memory cache
        self.memory_cache.clear()
        
        # Clear file cache
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete cache file {cache_file}: {e}")


class EnvironmentalDataFetcher:
    """Fetches environmental data for hex grid cells."""
    
    def __init__(self, config_path: str, cache_dir: str = "data/cache"):
        """
        Initialize the data fetcher.
        
        Args:
            config_path: Path to the API configuration file
            cache_dir: Directory to store cache files
        """
        self.clients = create_api_clients(config_path)
        self.cache = DataCache(cache_dir)
    
    def fetch_elevation_data(self, grid: HexGrid) -> None:
        """
        Fetch elevation data for each hex in the grid.
        
        Args:
            grid: The hex grid to update
        """
        if "elevation" not in self.clients:
            logger.warning("No elevation API client available")
            return
        
        elevation_client = self.clients["elevation"]
        
        # Collect coordinates for all hexes that need elevation data
        coordinates = []
        for hex_obj in grid:
            if hex_obj.center_latlon and hex_obj.elevation is None:
                coordinates.append(hex_obj.center_latlon)
        
        if not coordinates:
            logger.info("No hexes need elevation data")
            return
        
        logger.info(f"Fetching elevation data for {len(coordinates)} hexes")
        
        # Fetch elevation data in batches
        batch_size = 50
        for i in range(0, len(coordinates), batch_size):
            batch = coordinates[i:i+batch_size]
            
            # Try to get data from cache first
            batch_to_fetch = []
            for lat, lon in batch:
                cache_key = f"elevation_{lat:.6f}_{lon:.6f}"
                elevation = self.cache.get(cache_key)
                
                if elevation is None:
                    batch_to_fetch.append((lat, lon))
                else:
                    # Update the hex with cached elevation
                    for hex_obj in grid:
                        if hex_obj.center_latlon == (lat, lon):
                            hex_obj.elevation = elevation
                            break
            
            if not batch_to_fetch:
                continue
            
            # Fetch elevation data for coordinates not in cache
            elevations = elevation_client.get_elevations_batch(batch_to_fetch)
            
            # Update hexes and cache
            for (lat, lon), elevation in elevations.items():
                if elevation is not None:
                    # Update the hex
                    for hex_obj in grid:
                        if hex_obj.center_latlon == (lat, lon):
                            hex_obj.elevation = elevation
                            break
                    
                    # Update the cache
                    cache_key = f"elevation_{lat:.6f}_{lon:.6f}"
                    self.cache.set(cache_key, elevation)
    
    def fetch_climate_data(self, grid: HexGrid) -> None:
        """
        Fetch climate data for each hex in the grid.
        
        Args:
            grid: The hex grid to update
        """
        if "climate" not in self.clients:
            logger.warning("No climate API client available")
            return
        
        climate_client = self.clients["climate"]
        
        # Collect coordinates for all hexes that need climate data
        coordinates = []
        for hex_obj in grid:
            if hex_obj.center_latlon and (hex_obj.humidity is None or hex_obj.precipitation is None):
                coordinates.append(hex_obj.center_latlon)
        
        if not coordinates:
            logger.info("No hexes need climate data")
            return
        
        logger.info(f"Fetching climate data for {len(coordinates)} hexes")
        
        # Fetch climate data in batches
        batch_size = 10
        for i in range(0, len(coordinates), batch_size):
            batch = coordinates[i:i+batch_size]
            
            # Try to get data from cache first
            batch_to_fetch = []
            for lat, lon in batch:
                cache_key = f"climate_{lat:.6f}_{lon:.6f}"
                climate_data = self.cache.get(cache_key)
                
                if climate_data is None:
                    batch_to_fetch.append((lat, lon))
                else:
                    # Update the hex with cached climate data
                    for hex_obj in grid:
                        if hex_obj.center_latlon == (lat, lon):
                            self._update_hex_climate(hex_obj, climate_data)
                            break
            
            if not batch_to_fetch:
                continue
            
            # Fetch climate data for coordinates not in cache
            climate_data_batch = climate_client.get_climate_data_batch(batch_to_fetch)
            
            # Update hexes and cache
            for (lat, lon), climate_data in climate_data_batch.items():
                if climate_data is not None:
                    # Update the hex
                    for hex_obj in grid:
                        if hex_obj.center_latlon == (lat, lon):
                            self._update_hex_climate(hex_obj, climate_data)
                            break
                    
                    # Update the cache
                    cache_key = f"climate_{lat:.6f}_{lon:.6f}"
                    self.cache.set(cache_key, climate_data)
    
    def _update_hex_climate(self, hex_obj: Hex, climate_data: Dict[str, Any]) -> None:
        """
        Update a hex with climate data.
        
        Args:
            hex_obj: The hex to update
            climate_data: Climate data from the API
        """
        # Calculate a humidity proxy from precipitation and temperature
        # This is a simplified model; in reality, humidity is more complex
        precipitation = climate_data.get("precipitation", 0)
        temperature = climate_data.get("temperature", 15)
        
        # More precipitation and lower temperatures generally mean higher humidity
        humidity_proxy = precipitation * (30 - temperature) / 100
        
        # Update hex properties
        hex_obj.precipitation = precipitation
        hex_obj.humidity = humidity_proxy
        
        # Store full climate data in properties
        hex_obj.properties["climate"] = climate_data
    
    def fetch_all_data(self, grid: HexGrid) -> None:
        """
        Fetch all environmental data for the grid.
        
        Args:
            grid: The hex grid to update
        """
        logger.info("Fetching all environmental data for the grid")
        
        # Ensure all hexes have geographic coordinates
        missing_coords = False
        for hex_obj in grid:
            if hex_obj.center_latlon is None:
                missing_coords = True
                break
        
        if missing_coords:
            logger.error("Some hexes are missing geographic coordinates")
            return
        
        # Fetch elevation data
        self.fetch_elevation_data(grid)
        
        # Fetch climate data
        self.fetch_climate_data(grid)