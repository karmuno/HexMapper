# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

HexMaker is a program designed to generate hexagonal grid maps centered on geographic coordinates, assign terrain types based on climate and elevation data, divide maps into regions, and identify settlements. The project is in the initial planning/setup phase.

## Project Structure

This is a Python-based project with the following planned components:

1. Hex Grid Generator - Creates hexagonal grids with geographic coordinates
2. Hex Center Geocoder - Calculates geographic coordinates for hex centers
3. Environmental Data Fetcher - Retrieves climate and elevation data from APIs
4. Terrain Classifier - Assigns terrain types based on environmental data
5. Map Region Segmenter - Divides the map into regions
6. Settlement Finder - Identifies settlements in each region
7. Hex Map Renderer - Visualizes the hex map with terrain and settlements

## Development Environment Setup

The project will likely require:
- Python 3.8+
- Virtual environment (venv or conda)
- Python packages for:
  - Geospatial calculations
  - API requests
  - Data processing
  - Visualization

## Expected Files and Directories

Once implemented, the project will likely have:
- `src/` - Source code for the components
- `config/` - Configuration files for API keys
- `tests/` - Unit and integration tests
- `requirements.txt` - Python dependencies
- `output/` - Generated maps and data

## External Dependencies and APIs

The project will use several external APIs:
- Elevation data: OpenTopography, Mapbox Terrain-RGB, or USGS
- Climate data: Copernicus, Open-Meteo, or NOAA
- Precipitation & humidity: OpenWeatherMap, WorldClim
- Settlement data: OpenStreetMap (OSM) via Overpass API or Geonames API