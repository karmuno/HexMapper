#!/usr/bin/env python3
"""
Test script for the Mapbox elevation API.
"""

import sys
import os
import logging
import matplotlib.pyplot as plt
import numpy as np

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.hex_maker.data_fetcher.api_client import load_api_config, MapboxElevationAPI


def test_mapbox_elevation():
    """Test the Mapbox elevation API client."""
    print("Testing Mapbox elevation API...")
    
    # Test location (Mount Everest)
    test_lat = 27.9881
    test_lon = 86.9250
    
    # Load the API config
    try:
        config = load_api_config('config/api_keys.json')
        print("API config loaded successfully")
    except Exception as e:
        print(f"Failed to load API config: {e}")
        return
    
    # Check if Mapbox API key is configured
    if "elevation_api" not in config or config["elevation_api"]["provider"] != "mapbox":
        print("Mapbox elevation API is not configured")
        return
    
    # Create the Mapbox API client
    mapbox_key = config["elevation_api"]["key"]
    if not mapbox_key or mapbox_key == "MAPBOX_API_KEY_HERE":
        print("Mapbox API key is not set")
        return
    
    mapbox_client = MapboxElevationAPI(mapbox_key)
    print(f"Mapbox client created with key: {mapbox_key[:10]}...")
    
    # Get elevation data for a single point
    try:
        elevation = mapbox_client.get_elevation(test_lat, test_lon)
        print(f"Elevation for ({test_lat}, {test_lon}): {elevation} meters")
    except Exception as e:
        print(f"Failed to get elevation: {e}")
        return
    
    # Test with batch processing
    test_locations = [
        (27.9881, 86.9250),  # Mount Everest
        (39.7392, -104.9903),  # Denver, CO
        (36.1069, -112.1129),  # Grand Canyon
        (19.8240, -155.4681),  # Mauna Kea
        (44.0048, -71.0066),   # Mt. Washington
    ]
    
    try:
        print("\nTesting batch elevation fetching...")
        elevations = mapbox_client.get_elevations_batch(test_locations)
        
        for location, elevation in elevations.items():
            lat, lon = location
            print(f"Elevation for ({lat}, {lon}): {elevation} meters")
        
        print("\nMapbox elevation API test completed successfully")
    except Exception as e:
        print(f"Failed to get batch elevations: {e}")
        return


if __name__ == "__main__":
    test_mapbox_elevation()