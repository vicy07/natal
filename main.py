from fastapi import FastAPI, Query, Response, Request
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import swisseph as swe
import numpy as np
import io
from geopy.geocoders import Nominatim
import urllib.parse

app = FastAPI()

def calculate_chart(date: str, time: str, place: str, tz_offset: int):
    geolocator = Nominatim(user_agent="astro_api")
    location = geolocator.geocode(place)
    if not location:
        return None, JSONResponse(status_code=400, content={"error": "Invalid place name"})

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

    data = {
        "input": {
            "date": date,
            "time": time,
            "place": place,
            "coordinates": {"lat": lat, "lon": lon},
            "tz_offset": tz_offset
        },
        "planet_positions": planet_positions,
        "planet_degrees": planet_degrees,
        "aspects": aspects,
        "houses": houses,
        "ascendant": asc,
        "midheaven": mc
    }
    return data, None

def draw_chart(planet_degrees, houses, aspects):
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={'projection': 'polar'})
    ax.set_theta_zero_location("E")
    ax.set_theta_direction(-1)
    ax.set_rticks([])

    # 1. Круг зодиака с подписями
    zodiac_signs = [
        ('♈︎', 'Aries'), ('♉︎', 'Taurus'), ('♊︎', 'Gemini'), ('♋︎', 'Cancer'),
        ('♌︎', 'Leo'), ('♍︎', 'Virgo'), ('♎︎', 'Libra'), ('♏︎', 'Scorpio'),
        ('♐︎', 'Sagittarius'), ('♑︎', 'Capricorn'), ('♒︎', 'Aquarius'), ('♓︎', 'Pisces')
    ]
    for i, (symbol, name) in enumerate(zodiac_signs):
        angle = np.deg2rad(i * 30 + 15)
        ax.text(angle, 1.16, f"{symbol}\n{name}", ha='center', va='center', fontsize=13, color='black')

    # 2. Дома — линии и подписи
    for i in range(12):
        house_angle = np.deg2rad(houses[f'House {i+1}'])
        ax.plot([house_angle, house_angle], [0, 1.08], color='grey', lw=1, linestyle='--')
        ax.text(house_angle, 1.09, str(i+1), ha='center', va='center', fontsize=11, color='grey', weight='bold')

    # 3. Круговой контур
    circle = plt.Circle((0, 0), 1.08, transform=ax.transData._b, fill=False, color="black", lw=1.5)
    ax.add_artist(circle)

    # 4. Планеты
    planet_names = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars',
                    'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']
    planet_angles = [np.deg2rad(deg) for deg in planet_degrees]
    for angle, name in zip(planet_angles, planet_names):
        ax.plot(angle, 1.0, 'o', color='navy')
        ax.text(angle, 0.94, name, fontsize=10, ha='center', va='center', color='navy', weight='bold')

    # 5. Аспекты между планетами
    aspect_type_color = {
        "Conjunction": "red",
        "Opposition": "red",
        "Square": "red",
        "Trine": "red",
        "Sextile": "red"
    }
    name_to_angle = {name: ang for name, ang in zip(planet_names, planet_angles)}
    for asp in aspects:
        p1, p2 = asp["between"].split(" - ")
        typ = asp["type"]
        if typ in aspect_type_color:
            angle1 = name_to_angle.get(p1.strip())
            angle2 = name_to_angle.get(p2.strip())
            if angle1 is not None and angle2 is not None:
                ax.plot([angle1, angle2], [1.0, 1.0], color=aspect_type_color[typ], lw=1, alpha=0.7)

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf.read()

@app.get("/natal_chart/calc")
def natal_chart_calc(
    request: Request,
    date: str = Query(..., description="Birth date in format YYYY-MM-DD"),
    time: str = Query(..., description="Birth time in format HH:MM"),
    place: str = Query(..., description="Place of birth (city, country)"),
    tz_offset: int = Query(..., description="Time zone offset from UTC (e.g., 2 for UTC+2)")
):
    data, error = calculate_chart(date, time, place, tz_offset)
    if error:
        return error

    # Формируем относительный URL для /natal_chart/image
    params = {
        "date": date,
        "time": time,
        "place": place,
        "tz_offset": tz_offset
    }
    query = urllib.parse.urlencode(params)
    image_url = f"/natal_chart/image?{query}"

    data["image_url"] = image_url
    return data

@app.get("/natal_chart/image")
def natal_chart_image(
    date: str = Query(..., description="Birth date in format YYYY-MM-DD"),
    time: str = Query(..., description="Birth time in format HH:MM"),
    place: str = Query(..., description="Place of birth (city, country)"),
    tz_offset: int = Query(..., description="Time zone offset from UTC (e.g., 2 for UTC+2)")
):
    data, error = calculate_chart(date, time, place, tz_offset)
    if error:
        return error
    img_bytes = draw_chart(data["planet_degrees"], data["houses"], data["aspects"])
    return Response(content=img_bytes, media_type="image/png")
