# Data Architecture Diagram

```mermaid
flowchart LR
    A[Digitraffic Marine MQTT WebSocket]
    B[Python Ingestion Service\nfetch_ais.py]
    C[(PostgreSQL)]
    D[FastAPI Service]
    E[CSV Export]
    F[Prediction Service]
    G[Folium HTML Map]
    H[Browser / Swagger UI / Final Demo]

    A --> B
    B --> C
    C --> D
    C --> F
    C --> G
    D --> H
    E --> H
    F --> D
    G --> H
```

## Table version

| Component | Role |
|---|---|
| Digitraffic Marine MQTT | Source of live AIS messages |
| Ingestion service | Collects and parses AIS data |
| PostgreSQL | Stores history and latest vessel state |
| Prediction service | Estimates short-term future position |
| FastAPI | Makes data queryable and downloadable |
| Folium map | Creates sea map visualization |
| Browser/Swagger UI | Final user-facing demonstration |
