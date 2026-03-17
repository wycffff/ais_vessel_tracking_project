# Data Management Plan

## 1. Data description

This project collects vessel AIS data from a public marine traffic source. The data includes:

- MMSI
- timestamps
- latitude and longitude
- speed over ground
- course over ground
- heading
- navigation status
- selected vessel metadata such as vessel name, destination, call sign, and IMO number

The dataset is machine-generated telemetry data rather than manually entered user data.

## 2. Data source

The source is Digitraffic Marine Traffic open data.

The ingestion pipeline uses the official MQTT over WebSockets vessel topics and can also be extended to use the REST AIS endpoints.

## 3. Storage and organization

The data is stored in PostgreSQL with the following structure:

- `vessel_track` for historical movement records
- `vessel_state` for the latest known position and state per vessel
- `vessel_metadata` for metadata snapshots

Indexes are added for MMSI and timestamp fields to support efficient querying.

## 4. Data quality

Data quality risks include:

- missing message fields
- duplicated messages
- time gaps in transmission
- invalid coordinates

Mitigation in this version:

- ignore malformed records
- log ingestion errors
- store raw values consistently
- keep timestamps in UTC-derived datetime format

## 5. Legal and ethical considerations

The project uses public open marine traffic data. No personal user accounts or private customer information are stored.

Even so, responsible handling still matters:

- do not claim stronger accuracy than the model delivers
- document limitations clearly
- keep deployment access controlled if the project is published online

## 6. Backup and retention

For a course project, the practical retention policy is:

- keep PostgreSQL data during active project work
- export important result samples to CSV when needed
- version all code and documentation with Git

For a larger deployment, database backups should be scheduled regularly.

## 7. Sharing and reproducibility

The project is reproducible because it includes:

- complete source code
- dependency file
- Docker configuration
- sample seed data
- project documentation
- API endpoints for data extraction

## 8. Responsibilities

In a group setting, recommended responsibilities are:

- ingestion and data storage
- API and prediction
- visualization and presentation
- documentation and deployment
