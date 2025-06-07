from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import swisseph as swe
import numpy as np
import io
import base64
from geopy.geocoders import Nominatim

app = FastAPI()

@app.get("/natal_chart")
def natal_chart(
    date: str = Query(..., description="Birth date in format YYYY-MM-DD"),
    time: str = Query(..., description="Birth time in format HH:MM"),
    place: str = Query(..., description="Place of birth (city, country)"),
    tz_offset: int = Query(..., description="Time zone offset from UTC (e.g., 2 for UTC+2)")
):
    geolocator = Nominatim(user_agent="astro_api")
    location = geolocator.geocode(place)
    if not location:
        return JSONResponse(status_code=400, content={"error": "Invalid place name"})

    lat = location.latitude
    lon = location.longitude

    birth_local = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    birth_utc = birth_local - timedelta(hours=tz_offset)
    jd = swe.julday(birth_utc.year, birth_utc.month, birth_utc.day,
                    birth_utc.hour + birth_utc.minute / 60)

    planet_names = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars',
                    'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']
    planet_codes = [swe.SUN, swe.MOON, swe.MERCURY, swe.VENUS, swe.MARS,
                    swe.JUPITER, swe.SATURN, swe.URANUS, swe.NEPTUNE, swe.PLUTO]

    planet_degrees = []
    planet_positions = {}
    for code, name in zip(planet_codes, planet_names):
        pos, _ = swe.calc_ut(jd, code)
        deg = pos[0]
        planet_degrees.append(deg)
        planet_positions[name] = round(deg, 2)

    aspects = []
    aspect_types = {
        0: "Conjunction",
        60: "Sextile",
        90: "Square",
        120: "Trine",
        180: "Opposition"
    }
    orb = 6
    for i in range(len(planet_degrees)):
        for j in range(i + 1, len(planet_degrees)):
            diff = abs(planet_degrees[i] - planet_degrees[j]) % 360
            for asp_deg, asp_name in aspect_types.items():
                if abs(diff - asp_deg) <= orb:
                    aspects.append({
                        "between": f"{planet_names[i]} - {planet_names[j]}",
                        "type": asp_name,
                        "angle": round(diff, 2)
                    })

    cusps, ascmc = swe.houses(jd, lat, lon, b'P')
    houses = {f"House {i+1}": round(cusps[i], 2) for i in range(12)}
    asc = round(ascmc[0], 2)
    mc = round(ascmc[1], 2)

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={'projection': 'polar'})
    ax.set_theta_zero_location("E")
    ax.set_theta_direction(-1)
    ax.set_rticks([])
    zodiac_signs = ['♈︎', '♉︎', '♊︎', '♋︎', '♌︎', '♍︎', '♎︎', '♏︎', '♐︎', '♑︎', '♒︎', '♓︎']

    for i in range(12):
        theta = np.deg2rad(i * 30 + 15)
        ax.text(theta, 1.05, zodiac_signs[i], ha='center', va='center', fontsize=14)

    for deg, name in zip(planet_degrees, planet_names):
        theta = np.deg2rad(deg)
        ax.plot(theta, 1.0, 'o')
        ax.text(theta, 1.03, name, fontsize=9, ha='center', va='center')

    circle = plt.Circle((0, 0), 1.0, transform=ax.transData._b, fill=False, color="black")
    ax.add_artist(circle)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')

    return {
        "input": {
            "date": date,
            "time": time,
            "place": place,
            "coordinates": {"lat": lat, "lon": lon},
            "tz_offset": tz_offset
        },
        "planet_positions": planet_positions,
        "aspects": aspects,
        "houses": houses,
        "ascendant": asc,
        "midheaven": mc
    }
