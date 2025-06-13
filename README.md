# 🧭 Natalia – Astrological Natal Chart Generator

**Natalia** is a simple and reliable Python library and API for calculating and visualizing natal (birth) charts by date, time, and place of birth.

---

## ✨ Features

- ✅ Calculates planetary positions (Sun, Moon, Mercury, etc.) using Swiss Ephemeris
- 🌐 Determines astrological houses (Placidus)
- 📐 Calculates aspects between planets
- 🖼️ Generates beautiful natal chart images (PNG)
- 🚀 REST API with FastAPI
- 🧪 Unit tests included

---

## 🚀 Quick Start

### Requirements

- Python ≥ 3.8
- Dependencies: `swisseph`, `matplotlib`, `numpy`, `geopy`, `fastapi`, `uvicorn`

### Installation

Clone the repository and install dependencies:

```bash
pip install -r requirements.txt
```

### Usage as a Library

```python
from main import calculate_chart, draw_chart

# Calculate chart data
chart, err = calculate_chart('1990-05-17', '14:30', 'Riga', 3)
if err:
    print(err)
else:
    # Draw chart image
    img_bytes = draw_chart(chart['planet_degrees'], chart['houses'], chart['aspects'], chart['retrograde_planets'])
    with open('chart.png', 'wb') as f:
        f.write(img_bytes)
```

### Usage as an API

Start the FastAPI server:

```bash
uvicorn main:app --reload
```

Then open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) for interactive API documentation.

#### Example API endpoints:
- `/natal_chart/calc` — Calculate chart data (JSON)
- `/natal_chart/image` — Get natal chart as PNG image

---

## 🧪 Running Unit Tests

Before running the tests make sure all dependencies are installed:

```bash
pip install -r requirements.txt
```

To run all unit tests locally:

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
```

Or using Docker (from the project root):

```bash
# Map the current folder as a volume to access generated files (e.g., test_chart.png):
docker build -t natalia-tests -f tests/Dockerfile .
docker run --rm -v ${PWD}:/app natalia-tests
```

> **Note:** Mapping the volume with `-v ${PWD}:/app` allows you to access files created by tests (like `test_chart.png`) on your host machine.

---

## 📦 Project Structure

- `main.py` — Main logic, FastAPI app, chart calculation and drawing
- `tests/` — Unit tests
- `requirements.txt` — Python dependencies
- `Dockerfile`, `docker-compose.yml` — For containerized usage

---

## License
MIT
