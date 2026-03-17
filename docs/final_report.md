# Final Report: AIS Vessel Tracking and Prediction Platform

## 1. Project idea

The goal of this project is to build a small but complete data engineering system around live AIS vessel data. The system collects vessel movement data, stores it in a database, visualizes movement on a sea map, predicts short-term future positions, and exposes the collected data through an API.

This project was chosen because it is realistic, technically interesting, and suitable for demonstrating the full path from live data ingestion to storage, processing, analytics, and user-facing access.

## 2. Objectives

The project objectives were the following:

- collect live AIS data
- store historical vessel movement records
- maintain the latest state of each vessel
- visualize vessel movement and heading on a map
- predict short-term ship trajectories
- provide an API for querying and downloading collected data
- prepare the project in a form that is easy to run, explain, and report

## 3. System implementation

### 3.1 Data ingestion

The ingestion service is implemented in Python using the Paho MQTT client. It connects to the Digitraffic Marine MQTT WebSocket service and subscribes to vessel topics.

Two message categories are handled:

- location messages
- metadata messages

Location messages are stored in `vessel_track`, while the latest known values are also written to `vessel_state`.

### 3.2 Database design

The PostgreSQL schema contains three tables:

- `vessel_track`
- `vessel_state`
- `vessel_metadata`

This design separates full history from the current snapshot, which makes both analytics and API queries easier.

### 3.3 Prediction

The prediction method in this version is a linear extrapolation model based on the most recent points. The purpose is not to build a production-grade route intelligence model yet. Instead, the purpose is to show a correct and understandable prediction pipeline inside a complete data product.

### 3.4 API

The project API is implemented with FastAPI. The main endpoints provide:

- health check
- latest vessel list
- vessel track history
- short-term prediction
- CSV export

This makes the collected data directly usable by other services, notebooks, dashboards, or external tools.

### 3.5 Visualization

The map visualization is generated with Folium. The script places vessel markers on the map and draws a short heading line from each position. This gives a quick visual understanding of direction and movement.

## 4. Results

The final system demonstrates the full end-to-end pipeline:

- live or seeded data enters the system
- data is stored in PostgreSQL
- data is accessible through a documented REST API
- trajectory prediction is available per vessel
- map output can be generated for presentation

This means the project satisfies the core technical requirements of a compact data engineering application.

## 5. Strengths

The strongest parts of the project are:

- clear architecture
- modular code structure
- reproducible setup with Docker
- realistic public data source
- practical API output
- simple but working prediction logic

## 6. Limitations

The current version still has some limitations:

- the prediction model is intentionally basic
- no advanced route-learning model is included yet
- no frontend dashboard is included in this version
- no message broker such as Kafka is placed between ingestion and storage

These are acceptable limits for a final course project, especially because the architecture leaves room for later expansion.

## 7. Future work

The next improvements would be:

- add historical model evaluation
- add map dashboard frontend
- add geofence alerts
- add anomaly detection
- add TimescaleDB or another time-series optimization layer
- add stream processing through Kafka or a similar tool

## 8. Conclusion

This project successfully turns live AIS vessel data into a complete data engineering pipeline. It includes ingestion, database storage, visualization, prediction, and API access in one coherent system.

Because the project is complete, reproducible, and easy to demonstrate, it is suitable as a final submission version.
