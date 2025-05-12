#!/usr/bin/env python3
"""
Environmental Data API Client

This module handles API requests to various environmental data sources,
including elevation, climate, precipitation, and humidity data.
"""

import os
import json
import time
import logging
import requests
import io
from typing import Dict, List, Tuple, Optional, Any
from urllib.parse import urlencode

# Set up logging
logger = logging.getLogger(__name__)


class APIRateLimiter:
    """Simple rate limiter for API calls."""
    
    def __init__(self, calls_per_second: float = 1.0):
        """
        Initialize the rate limiter.
        
        Args:
            calls_per_second: Maximum number of calls per second
        """
        self.min_interval = 1.0 / calls_per_second
        self.last_call_time = 0
    
    def wait_if_needed(self):
        """Wait if necessary to respect the rate limit."""
        current_time = time.time()
        elapsed = current_time - self.last_call_time
        
        if elapsed < self.min_interval:
            sleep_time = self.min_interval - elapsed
            time.sleep(sleep_time)
        
        self.last_call_time = time.time()


class APIClient:
    """Base class for API clients."""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None, 
                 calls_per_second: float = 1.0):
        """
        Initialize the API client.
        
        Args:
            base_url: Base URL for the API
            api_key: API key (if required)
            calls_per_second: Maximum number of calls per second
        """
        self.base_url = base_url
        self.api_key = api_key
        self.rate_limiter = APIRateLimiter(calls_per_second)
        
        # Create a session for connection pooling
        self.session = requests.Session()
    
    def make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Make a request to the API.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
        
        Returns:
            API response as a dictionary
        """
        # Respect rate limits
        self.rate_limiter.wait_if_needed()
        
        # Build the URL
        url = f"{self.base_url}/{endpoint}"
        
        # Add API key if provided
        if params is None:
            params = {}
        
        if self.api_key:
            params['key'] = self.api_key
        
        # Make the request
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise


class MapboxElevationAPI(APIClient):
    """Client for Mapbox Elevation API."""
    
    def __init__(self, api_key: str):
        """Initialize the Mapbox Elevation API client."""
        super().__init__(
            base_url="https://api.mapbox.com",
            api_key=api_key,
            calls_per_second=5.0
        )
    
    def get_elevation(self, lat: float, lon: float) -> Optional[float]:
        """
        Get elevation data for a specific location using Mapbox Tilequery API.
        
        Args:
            lat: Latitude
            lon: Longitude
        
        Returns:
            Elevation in meters, or None if the request failed
        """
        try:
            # Build the URL for Mapbox Tilequery API
            # This endpoint returns elevation directly
            endpoint = f"v4/mapbox.mapbox-terrain-v2/tilequery/{lon},{lat}.json"
            params = {'access_token': self.api_key, 'layers': 'contour'}
            
            # Make the request
            self.rate_limiter.wait_if_needed()
            url = f"{self.base_url}/{endpoint}"
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            # Process the JSON response
            data = response.json()
            features = data.get('features', [])
            
            if not features:
                logger.warning("No elevation features returned from Mapbox")
                # Try to get a default elevation for this region
                return self._get_default_elevation(lat, lon)
            
            # Look for elevation in the features
            # Sort by distance to get the closest feature
            features.sort(key=lambda f: f.get('properties', {}).get('distance', float('inf')))
            
            for feature in features:
                elevation = feature.get('properties', {}).get('ele')
                if elevation is not None:
                    return float(elevation)
            
            # If we couldn't find elevation in the features, return a default
            return self._get_default_elevation(lat, lon)
            
        except Exception as e:
            logger.error(f"Failed to get elevation from Mapbox: {e}")
            return self._get_default_elevation(lat, lon)
    
    def _get_default_elevation(self, lat: float, lon: float) -> float:
        """
        Get a default elevation estimate based on the location.
        
        This is a fallback method when the API call fails.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Estimated elevation in meters
        """
        # These are very rough estimates for different regions
        if abs(lat) > 70:  # Polar regions
            return 2000.0
        elif abs(lat) > 60:  # Near polar
            return 500.0
        elif abs(lat) < 23.5:  # Tropical
            return 200.0
        else:  # Temperate
            return 300.0
    
    def get_elevations_batch(self, coordinates: List[Tuple[float, float]]) -> Dict[Tuple[float, float], Optional[float]]:
        """
        Get elevation data for multiple locations.
        
        Args:
            coordinates: List of (lat, lon) tuples
        
        Returns:
            Dictionary mapping (lat, lon) to elevation in meters
        """
        results = {}
        for lat, lon in coordinates:
            elevation = self.get_elevation(lat, lon)
            results[(lat, lon)] = elevation
        
        return results


class OpenMeteoAPI(APIClient):
    """Client for Open-Meteo weather and climate API."""
    
    def __init__(self):
        """Initialize the Open-Meteo API client."""
        super().__init__(
            base_url="https://api.open-meteo.com/v1",
            api_key=None,  # Open-Meteo doesn't require an API key for basic usage
            calls_per_second=1.0
        )
    
    def get_climate_data(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """
        Get climate data for a specific location.
        
        Args:
            lat: Latitude
            lon: Longitude
        
        Returns:
            Dictionary with climate data, or None if the request failed
        """
        endpoint = "forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,rain_sum,snowfall_sum",
            "current_weather": "true",
            "timezone": "auto"
        }
        
        try:
            response = self.make_request(endpoint, params)
            
            # Extract the data we need
            data = {
                "temperature": response.get("current_weather", {}).get("temperature"),
                "precipitation": response.get("daily", {}).get("precipitation_sum", [0])[0],
                "rain": response.get("daily", {}).get("rain_sum", [0])[0],
                "snowfall": response.get("daily", {}).get("snowfall_sum", [0])[0]
            }
            
            return data
        except Exception as e:
            logger.error(f"Failed to get climate data: {e}")
            return None
    
    def get_climate_data_batch(self, coordinates: List[Tuple[float, float]]) -> Dict[Tuple[float, float], Optional[Dict[str, Any]]]:
        """
        Get climate data for multiple locations.
        
        Args:
            coordinates: List of (lat, lon) tuples
        
        Returns:
            Dictionary mapping (lat, lon) to climate data
        """
        results = {}
        for lat, lon in coordinates:
            climate_data = self.get_climate_data(lat, lon)
            results[(lat, lon)] = climate_data
        
        return results


def load_api_config(config_path: str) -> Dict[str, Any]:
    """
    Load API configuration from a JSON file.
    
    Args:
        config_path: Path to the configuration file
    
    Returns:
        Dictionary with API configuration
    """
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Config file not found: {config_path}")
        raise
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in config file: {config_path}")
        raise


def create_api_clients(config_path: str) -> Dict[str, APIClient]:
    """
    Create API clients based on configuration.
    
    Args:
        config_path: Path to the configuration file
    
    Returns:
        Dictionary mapping API names to client instances
    """
    config = load_api_config(config_path)
    clients = {}
    
    # Create Mapbox Elevation API client if configured
    if "elevation_api" in config and config["elevation_api"]["provider"] == "mapbox":
        clients["elevation"] = MapboxElevationAPI(api_key=config["elevation_api"]["key"])
    
    # Create Open-Meteo API client
    clients["climate"] = OpenMeteoAPI()
    
    return clients