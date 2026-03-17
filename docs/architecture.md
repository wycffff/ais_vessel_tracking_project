# Architecture Overview

This project follows a simple and clear data engineering architecture.

## Layers

### 1. Data ingestion layer

The ingestion service connects to the Digitraffic Marine MQTT over WebSockets endpoint and subscribes to AIS vessel topics.

It consumes two main message types:

- vessel location messages
- vessel metadata messages

### 2. Storage layer

PostgreSQL stores three logical datasets:

- `vessel_track`: historical AIS position records
- `vessel_state`: latest known state per vessel
- `vessel_metadata`: historical metadata snapshots

### 3. Processing layer

The processing logic performs three jobs:

- parse incoming JSON messages
- upsert the latest vessel state
- predict future position from recent points

### 4. API layer

FastAPI exposes the stored data through REST endpoints for:

- latest vessel list
- vessel detail lookup
- vessel track history
- short-term prediction
- CSV export

### 5. Visualization layer

A Folium-based script generates an HTML sea map with vessel markers and heading lines.

## Design choices

This architecture is intentionally lightweight.

It is suitable for a course project because it is:

- easy to run locally
- easy to explain in a final presentation
- modular enough for future extension
- realistic enough to demonstrate ingestion, storage, API design, and analytics

## Future scaling path

If the project continues beyond the course, the next architecture step would be:

- MQTT ingestion -> Kafka topic -> stream processing -> PostgreSQL/TimescaleDB -> API/dashboard
