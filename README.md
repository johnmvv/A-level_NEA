
# UK Train Tracker & Route Planner

A Python application for visualising UK railway services, estimating train positions and finding journeys using graph-search and public transport routing algorithms.

Developed independently as part of my A-level Computer Science NEA.

## Overview

The application combines live railway timetable data, asynchronous API requests and an interactive map to help users explore the UK rail network.

It supports two route-finding approaches: breadth-first search (BFS) and a modified implementation of the Round-Based Public Transit Routing (RAPTOR) algorithm.

The project focuses on algorithm design, asynchronous programming, geographical data processing and interactive visualisation.

## Features

- **Interactive railway map:** View railway infrastructure using OpenRailwayMap tiles, with zooming and panning.
- **Train tracking:** Estimate train positions using timetable information and interpolation along railway geometry.
- **Route planning:** Search for journeys between stations using BFS or modified RAPTOR.
- **Asynchronous data retrieval:** Fetch multiple railway services concurrently using `asyncio` and `aiohttp`.
- **Station searches:** Retrieve services using three-letter station CRS codes.
- **Train information:** Display service identifiers, operators, origins, destinations and estimated delays.
- **Interactive interface:** Navigate between maps, search results and train information using Pygame.

## Technologies

**Language:** Python

**Libraries:**
- `pygame` — graphical interface and map rendering
- `asyncio` — asynchronous task scheduling
- `aiohttp` — HTTP requests
- `csv` — station data processing
- `datetime` — timetable and journey calculations

**External data sources:**
- RealTimeTrains API
- OpenRailwayMap
- Railway geometry data from trainmap.ntag.fr

## Route-Finding Algorithms

### Breadth-First Search (BFS)

The application uses a modified BFS approach to explore possible journeys between railway stations.

It retrieves onward services, identifies potential interchange stations and searches for connections to the destination.

The implementation is intended to find candidate journeys quickly, rather than guarantee the earliest possible arrival.

### Round-Based Public Transit Routing (RAPTOR)

The second approach is based on the RAPTOR algorithm for public transport journey planning.

RAPTOR searches for journeys in successive rounds, considering routes with increasing numbers of transfers.

My implementation adapts this approach to retrieve railway timetable information dynamically through API requests.

It is an experimental adaptation and has not been formally verified to preserve all optimality guarantees of the original algorithm.

## Train Position Estimation

RealTimeTrains provides timetable and running information rather than continuous GPS coordinates.

The application estimates positions by:

1. Identifying the stations surrounding a train's estimated current location.
2. Retrieving railway geometry between those stations.
3. Calculating the proportion of scheduled or estimated journey time elapsed.
4. Interpolating a position along the railway geometry.
5. Rendering the estimated position on the map.

These positions are approximations, not direct GPS measurements.

## Project Structure

```text
.
├── main.py
├── managers.py
├── objects.py
├── retrive.py
├── routefinder.py
├── staticmethods.py
├── trainfinder.py
├── uk-train-stations.csv
├── stations-gb-id-name.csv
└── README.md
```

| File | Purpose |
|------|---------|
| `main.py` | Application entry point and main event loop |
| `managers.py` | Map rendering, train management and user interaction |
| `objects.py` | GUI components, buttons, input fields and tables |
| `retrive.py` | External API requests and railway data retrieval |
| `routefinder.py` | BFS and RAPTOR-based journey searches |
| `staticmethods.py` | Geographical coordinate transformations |
| `trainfinder.py` | Train discovery, position estimation and train objects |

## Installation

### Requirements

- Python 3.10 or later
- Pygame
- aiohttp
- RealTimeTrains API credentials
- Station reference CSV files

Install the external dependencies:

```bash
python -m pip install pygame aiohttp
```

### API Configuration

The original application requires RealTimeTrains API credentials.

The published source has the credentials removed. The original `retrive.py` contains placeholder credential references, so these must be configured before the live application can run.

Credentials should never be committed to a public repository.

### Running

Once the required dependencies, data files and credentials are configured:

```bash
python main.py
```

**Note:** This repository contains the original coursework implementation. Some API calls, asynchronous operations and timetable calculations require further maintenance. The complete application has not been verified against current external services.

## Testing and Evaluation

The original project was evaluated against objectives covering:

- Map navigation and rendering
- Train discovery and position updates
- Station and service searches
- Journey planning
- Interface responsiveness

The coursework report includes implementation details, testing observations and an evaluation of the project's limitations.

## Known Limitations

- Live functionality depends on external APIs and valid credentials.
- Estimated train positions are not GPS measurements.
- Timetable interpolation does not fully account for varying speeds or operational disruption.
- The route-finding algorithms require further correctness and performance validation.
- Some original asynchronous operations and API references need maintenance.
- The project does not currently include a fully verified offline demonstration integrated into the original application.

## Future Improvements

- Add a reproducible offline mode with sample timetable data.
- Introduce automated tests for route finding and train positioning.
- Improve timetable calculations across midnight.
- Implement API response caching and more robust error handling.
- Benchmark route-search algorithms using reproducible datasets.
- Separate the graphical interface from the routing and data-processing components.

## Background

This project was developed independently for my A-level Computer Science NEA at Exeter Mathematics School.

It provided practical experience in asynchronous Python, object-oriented programming, graph algorithms, API integration and geographical visualisation.
