# CampusNav — Campus Navigation (Flask + Dijkstra)

Search any room / office / lab, get the shortest walking route, and follow it
**step by step on the map**. When the route goes up stairs (or a lift) or
into another building, the map switches automatically:
`Campus → 1st Floor → 2nd Floor → ...`

## Run (3 ways)

**Windows (easiest):** double-click `start_windows.bat`

**Any OS, terminal:**
```bash
pip install -r requirements.txt
python run.py
```
Open **http://127.0.0.1:5000**

**On a phone (same Wi-Fi):**
```powershell
$env:CAMPUS_HOST="0.0.0.0"; python run.py      # Windows PowerShell
CAMPUS_HOST=0.0.0.0 python run.py              # Mac / Linux
```
then open the `http://<your-pc-ip>:5000` address printed in the terminal
(this is also what you put in the QR code).

Requires Python 3.9+ and Flask only. The database (`database/campus.db`) is
created/repaired automatically on start.

## Features
- Smart search with aliases (`213`, `library`, `gate`, `physics` ...) and keyboard support
- Route drawn **on the real map drawings**, following corridors and roads
- **Next / Back** (also ← → keys): the route grows step by step, the map zooms to it
- Floor / building switching on stairs, lifts and doors, with a floor indicator
- Step-free mode (lifts only) for accessibility
- Emergency mode: nearest exit or medical room (never uses lifts)
- Zoom / pan / pinch, view tabs for every floor, building cross-section view
- Shareable links, e.g. `/?from=c_gate&to=r213`
- Responsive: works on desktop, tablet and phone

## Project structure
```
run.py                     start the server
backend/                   Flask app, pages, JSON API
navigation/                Dijkstra graph, location search, route + step builder
database/campus_data.py    ALL places, corridors, stairs, coordinates (edit here)
database/campus_db.py      builds / loads the SQLite database
frontend/templates/        index.html
frontend/static/           css, js (map engine), map drawings (PNG)
tests/                     python -m unittest discover -s tests -v
```

## Changing the campus
Everything (rooms, positions, connections, distances) lives in
`database/campus_data.py`. Coordinates are pixels of the PNG drawings
(2480 × 1753). After editing, raise `SCHEMA_VERSION` in
`database/campus_db.py` (or delete `database/campus.db`) and restart.

## API
| Endpoint | Purpose |
|---|---|
| `GET /api/locations` | all searchable places |
| `GET /api/search?q=lib` | search |
| `GET /api/route?from=r125&to=r301&accessible=1` | route + legs + steps |
| `GET /api/emergency?from=r213&type=exit\|medical` | nearest safe place |
