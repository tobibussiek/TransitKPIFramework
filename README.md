# TransitKPIFramework

Graduate research project exploring how sensitive On-Time Performance (OTP) metrics are to reasonable measurement choices, using SEPTA (Philadelphia) bus data.

## Research Question

How much does measured On-Time Performance vary across reasonable definitional choices — specifically lateness threshold, stop selection, and cancellation handling — on SEPTA bus Routes 23 and 47 on weekday service?


## Project Structure

```
TransitKPIFramework/
├── docs/                        # Presentations and paper drafts
├── notebooks/
│   ├── 01_explore_gtfs_static.ipynb    # GTFS static data exploration, route scoping
│   ├── 02_parse_gtfsrt.ipynb           # Parse GTFS-RT protobuf archive into DuckDB
│   └── 03_trip_matching.ipynb      # Trip matching, delay calculation, OTP
└── septa-archive/               # Dockerized GTFS-RT archiver (deployed to DigitalOcean)
    ├── Dockerfile
    ├── docker-compose.yml
    └── src/
        └── fetch_gtfsrt.py
```

## Data Sources

- **GTFS Static** — SEPTA schedule, stops, and trips via [OpenDataPhilly](https://opendataphilly.org/datasets/septa-gtfs/)
- **GTFS-RT** — SEPTA live bus trip updates, self-archived via polling archiver at 60-second intervals

## Pipeline

1. `septa-archive/` polls SEPTA's GTFS-RT endpoint every 60 seconds and stores raw protobuf files on a DigitalOcean droplet
2. `02_parse_gtfsrt.ipynb` parses raw `.pb` files into a DuckDB table with proper Eastern timezone handling via pytz
3. `03_build_trip_delays.ipynb` matches GTFS-RT trip updates to static schedules, deduplicates to one record per stop event, and computes delay in minutes

## Setup

```bash
# Install dependencies
pip install duckdb pandas gtfs-realtime-bindings pytz jupyter

# Run notebooks in order
# 01 → 02 → 03
```

GTFS static files go in `data/google_bus/`. Raw `.pb` files go in `data/raw/gtfs_rt/`. Neither is included in this repo — see data sources above.

## Status

- [x] Phase 1 — GTFS static exploration, route scoping (Routes 23 and 47)
- [x] Phase 2 — GTFS-RT parsing, trip matching, baseline OTP calculation
- [ ] Phase 3 — Full robustness specification set, sensitivity analysis
- [ ] Phase 4 — Power BI dashboard, research paper
