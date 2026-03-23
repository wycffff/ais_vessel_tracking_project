# AIS Vessel Tracking and Prediction Platform

This project is an AIS vessel tracking and prediction system built for a data engineering course project. The main idea is simple: collect real vessel movement data, store it in PostgreSQL, provide API access to the stored data, and show vessel positions and short-term predicted movement on a live interactive map.

The system supports both a stable demo mode with sample data and a live mode with real AIS data from Digitraffic MQTT. In the final version, the live map supports filtering by MMSI, vessel name, and area. It also uses WebSocket updates so the browser can receive fresh map data without normal page polling.

## What this project does

The project covers these main parts:

- collect AIS vessel data
- store vessel positions and latest vessel state in PostgreSQL
- provide API endpoints for querying vessel data
- export vessel track history as CSV
- show vessels on an interactive sea map
- predict short-term vessel movement based on recent track points
- support live map filtering and WebSocket updates

The prediction in this version is intentionally simple. It uses recent vessel movement data and extrapolates a short-term future position from the current direction and speed. It is not a machine learning model. For this course project, this is still enough to demonstrate the prediction requirement in a clear and testable way.

## Project structure

```text
ais_vessel_tracking_project/
│
├── app/
│   ├── api/
│   │   └── main.py
│   ├── ingestion/
│   │   └── fetch_ais.py
│   ├── services/
│   │   ├── export.py
│   │   └── predict.py
│   ├── visualization/
│   │   └── map_latest.py
│   ├── db.py
│   ├── models.py
│   ├── schemas.py
│   └── settings.py
│
├── docs/
├── scripts/
│   ├── init_db.py
│   └── seed_sample_data.py
│
├── tests/
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── README.md
└── requirements.txt
```

## Main technologies

- Python 3.12
- FastAPI
- PostgreSQL
- SQLAlchemy
- Pydantic
- Paho MQTT
- Leaflet
- WebSocket
- Uvicorn

## Data source

The live AIS data comes from Digitraffic marine traffic MQTT.

In live mode, the ingestion service subscribes to:

```text
vessels-v2/#
```

and stores incoming vessel messages in the project database.

## Database design

The final version uses two main tables:

- `vessel_track`
- `vessel_state`

### `vessel_track`
This table stores historical vessel position points.

Typical fields include:

- MMSI
- event time
- latitude
- longitude
- speed over ground
- course over ground
- heading
- source topic

### `vessel_state`
This table stores the latest known state of each vessel.

Typical fields include:

- MMSI
- vessel name
- call sign
- IMO
- vessel type
- destination
- latest event time
- latest latitude and longitude
- latest speed, course, and heading

This separation makes sense for the project because:

- `vessel_track` is useful for history and prediction
- `vessel_state` is useful for fast API queries and live map display

## API endpoints

After starting the API, Swagger documentation is available at:

```text
http://127.0.0.1:8000/docs
```

Main endpoints:

- `GET /health`
- `GET /vessels/latest`
- `GET /vessels/{mmsi}/latest`
- `GET /vessels/{mmsi}/track`
- `GET /vessels/{mmsi}/predict`
- `GET /export/vessels/{mmsi}/track.csv`
- `GET /map`
- `GET /map/data`
- `WS /ws/map`

## Map features in the final version

The final live map is one of the main parts of the project.

It supports:

- showing live vessels directly in the browser
- filtering by MMSI
- filtering by vessel name
- filtering by latitude and longitude area
- showing predicted future position
- stable live tracking through WebSocket
- manual refresh of the selected vessel set
- optional auto-fit when the selection changes

This means the user does not need to generate and open a separate HTML file for the final live map. The browser can open the live map directly from the API application.

## Prediction logic

The prediction logic is simple and transparent.

The system takes recent vessel track points and estimates a short future position based on the current movement direction and speed. In practice, this means the predicted point usually continues in roughly the same direction as the recent vessel movement.

This is not meant to be a production-grade maritime forecasting model. The goal here is to satisfy the course requirement with a method that is:

- easy to explain
- easy to test
- stable in live demonstration
- clearly connected to the available AIS data

## How to run the project locally

### 1. Go to the project folder

```powershell
cd D:\study\ais_vessel_tracking_project
```

### 2. Create and activate a virtual environment

```powershell
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example file:

```powershell
Copy-Item .env.example .env
```

Then edit `.env` so it matches your local PostgreSQL settings.

A typical local configuration looks like this:

```env
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/ais_tracking
LOCAL_DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/ais_tracking
APP_NAME=AIS Vessel Tracking and Prediction Platform
API_HOST=0.0.0.0
API_PORT=8000
MQTT_HOST=meri.digitraffic.fi
MQTT_PORT=443
MQTT_PATH=/mqtt
MQTT_TOPIC=vessels-v2/#
MQTT_CLIENT_ID=ais-tracking-demo-client
PREDICTION_DEFAULT_MINUTES=15
MAP_OUTPUT_DIR=output
```

### 5. Create the database

Create a PostgreSQL database named:

```text
ais_tracking
```

### 6. Initialize the database tables

```powershell
python -m scripts.init_db
```

## Demo mode

Demo mode is useful for stable testing and presentation, because it always inserts known sample vessels.

Run:

```powershell
python -m scripts.seed_sample_data
uvicorn app.api.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/map
```

In demo mode, the map shows sample vessels stored by the seed script.

## Live mode

Live mode is the main final version for demonstrating real AIS capability.

Open terminal 1:

```powershell
cd D:\study\ais_vessel_tracking_project
venv\Scripts\activate
python -m app.ingestion.fetch_ais
```

Open terminal 2:

```powershell
cd D:\study\ais_vessel_tracking_project
venv\Scripts\activate
uvicorn app.api.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/map
```

In this mode:

- real AIS messages are received from MQTT
- vessel positions are stored in PostgreSQL
- the map shows live vessel positions
- filters can be applied in the browser
- WebSocket pushes updated map data to the page

## Suggested testing steps

These are the basic checks used for the final version.

### API checks

Open Swagger:

```text
http://127.0.0.1:8000/docs
```

Test these endpoints:

- `/health`
- `/vessels/latest`
- `/vessels/{mmsi}/latest`
- `/vessels/{mmsi}/track`
- `/vessels/{mmsi}/predict`
- `/export/vessels/{mmsi}/track.csv`

### Live map checks

Open:

```text
http://127.0.0.1:8000/map
```

Then verify:

- vessels appear on the map
- WebSocket connection shows as connected
- filtering by MMSI works
- filtering by vessel name works
- area filtering works
- predicted lines appear
- the visible vessel set stays stable until filters are changed or refreshed

## Example use cases

### 1. Search for one vessel by MMSI
Enter the MMSI in the filter panel and apply filters. The map should focus on that vessel only.

### 2. Show vessels in a selected area
Enter latitude and longitude bounds and apply filters. The map should show only vessels inside the selected area.

### 3. Download vessel history
Use:

```text
/export/vessels/{mmsi}/track.csv
```

to export historical track data for one vessel.

## Testing the Agent and MCP Endpoints

The project now includes an AI agent that can answer natural language queries about vessels using local LLM and database tools. You can test this functionality through the FastAPI interactive documentation.

### How to test

1. **Start the server** (as described in the "How to run the project locally" section):

   ```powershell
   uvicorn app.api.main:app --reload
   ```

2. **Open the API documentation**:

   Visit `http://127.0.0.1:8000/docs` in your browser.

3. **Test the Agent Query endpoint**:

   - Expand the `POST /agent/query` section.
   - Click "Try it out".
   - In the request body, enter a JSON query like:

     ```json
     {
       "query": "玛丽港有哪些船只？"
     }
     ```

   - Click "Execute".
   - Check the response: it should include `tool_used`, `tool_params`, `tool_result`, and a natural language `answer`.

4. **Test the MCP Execute endpoint**:

   - Expand the `POST /mcp/execute` section.
   - Click "Try it out".
   - In the request body, enter a JSON call like:

     ```json
     {
       "tool_name": "find_vessels_by_port",
       "params": {
         "port_name": "玛丽港"
       }
     }
     ```

   - Click "Execute".
   - Check the response: it should include `tool_name`, `status`, `tool_response`, and `meta`.

### Example queries to try

- `"玛丽港有哪些船只？"` (Find vessels heading to Mariehamn)
- `"Turku 最近的船是哪一条？"` (Find the nearest vessel to Turku)
- `"Viking Line 的哪艘船在哪里？"` (Find Viking Line vessels)

### Notes

- The agent uses rule-based tool selection for simplicity, but can be enhanced with LLM-based intent recognition.
- If no local LLM model is configured, the agent falls back to simple text generation.
- Ensure the database has vessel data for meaningful results (use demo mode or live mode).

## Limitations

There are still some limitations in this final version.

- The prediction logic is simple and based on short-term extrapolation.
- The map is intended for course project scale, not very large global vessel loads.
- Vessel metadata depends on what has already been received from AIS messages.
- Live vessel availability depends on the external MQTT source and current traffic.

These limitations are acceptable for the course project because the core technical requirements are still met.

## Possible future improvements

If this project were extended later, these would be sensible next steps:

- use a stronger trajectory prediction method
- add vessel clustering for dense map views
- add authentication and user accounts
- add historical time-range filtering
- add Docker-first deployment testing
- build a richer frontend dashboard
- add anomaly detection or route deviation alerts

## Course relevance

This project fits the course well because it combines several data engineering tasks into one system:

- data ingestion
- database design
- storage of live data
- API development
- data export
- visualization
- real-time updates
- simple predictive analytics

So even though the prediction itself is simple, the whole system demonstrates an end-to-end data engineering workflow.

## Author

Wei Yechuan, Gong Wenhan，Mackowska Alicja
Turku University of Applied Sciences  
ICT – Data Engineering & AI

## License

This project was created for academic use.
