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

planet_names = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars',
                'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']
planet_codes = [swe.SUN, swe.MOON, swe.MERCURY, swe.VENUS, swe.MARS,
                swe.JUPITER, swe.SATURN, swe.URANUS, swe.NEPTUNE, swe.PLUTO]
aspect_types = {
    0: ("Conjunction", "☌"),
    60: ("Sextile", "✶"),
    90: ("Square", "□"),
    120: ("Trine", "△"),
    180: ("Opposition", "☍")
}
orb = 6  # допустимый орбис для аспектов

def calculate_chart(date: str, time: str, place: str, tz_offset: int):
    geolocator = Nominatim(user_agent="astro_api")
    location = geolocator.geocode(place)
    if not location:
        return None, JSONResponse(status_code=400, content={"error": "Invalid place name"})
    lat, lon = location.latitude, location.longitude

    birth_local = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    birth_utc = birth_local - timedelta(hours=tz_offset)
    jd = swe.julday(birth_utc.year, birth_utc.month, birth_utc.day,
                    birth_utc.hour + birth_utc.minute / 60)

    planet_degrees = {}
    for code, name in zip(planet_codes, planet_names):
        pos, _ = swe.calc_ut(jd, code)
        planet_degrees[name] = round(pos[0], 2)

    cusps, ascmc = swe.houses(jd, lat, lon, b'P')
    houses = [round(c, 2) for c in cusps]  # список домов 1–12

    return {"jd": jd, "lat": lat, "lon": lon,
            "planet_degrees": planet_degrees, "houses": houses}, None

def draw_chart(planet_degrees, houses, aspects):
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={'projection': 'polar'})
    ax.set_theta_zero_location("E")
    ax.set_theta_direction(-1)
    ax.set_rticks([])

    zodiac_signs = [
        ('♈︎', 'Aries'), ('♉︎', 'Taurus'), ('♊︎', 'Gemini'), ('♋︎', 'Cancer'),
        ('♌︎', 'Leo'), ('♍︎', 'Virgo'), ('♎︎', 'Libra'), ('♏︎', 'Scorpio'),
        ('♐︎', 'Sagittarius'), ('♑︎', 'Capricorn'), ('♒︎', 'Aquarius'), ('♓︎', 'Pisces')
    ]
    for i, (symbol, name) in enumerate(zodiac_signs):
        angle = np.deg2rad(i * 30 + 15)
        ax.text(angle, 1.16, f"{symbol}\n{name}", ha='center', va='center', fontsize=13)

    for i in range(12):
        house_angle = np.deg2rad(houses[i])
        ax.plot([house_angle, house_angle], [0, 1.08], color='grey', lw=1, linestyle='--')
        ax.text(house_angle, 1.09, str(i + 1), ha='center', va='center', fontsize=11,
                color='grey', weight='bold')

    circle = plt.Circle((0, 0), 1.08, transform=ax.transData._b, fill=False,
                        color="black", lw=1.5)
    ax.add_artist(circle)

    angles = [np.deg2rad(planet_degrees[n]) for n in planet_names]
    for angle, name in zip(angles, planet_names):
        ax.plot(angle, 1.0, 'o', color='navy')
        ax.text(angle, 0.94, name, fontsize=10, ha='center', va='center',
                color='navy', weight='bold')

    name_to_angle = {n: a for n, a in zip(planet_names, angles)}
    for asp in aspects:
        p1, p2 = asp["between"].split(" - ")
        p1, p2 = p1.strip(), p2.strip()
        if asp["symbol"]:
            a1, a2 = name_to_angle.get(p1), name_to_angle.get(p2)
            if a1 is not None and a2 is not None:
                ax.plot([a1, a2], [1.0, 1.0], color="red", lw=1, alpha=0.7)

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf.read()

@app.get("/natal_chart/calc")
def natal_chart_calc(
    date: str = Query(..., description="Birth date in format YYYY-MM-DD"),
    time: str = Query(..., description="Birth time in format HH:MM"),
    place: str = Query(..., description="Place of birth (city, country)"),
    tz_offset: int = Query(..., description="Time zone offset from UTC (e.g., 2 for UTC+2)")
):
    data, error = calculate_chart(date, time, place, tz_offset)
    if error:
        return error
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
    img = draw_chart(data["planet_degrees"], data["houses"], [])
    return Response(content=img, media_type="image/png")

def get_week_transits(natal, start_jd, days: int = 7):
    week = []
    for i in range(days):
        jd = start_jd + i
        trans = {n: round(swe.calc_ut(jd, c)[0][0], 2)
                 for n, c in zip(planet_names, planet_codes)}
        aspects = []
        for t_name, t_deg in trans.items():
            for n_name, n_deg in natal["planet_degrees"].items():
                diff = abs((t_deg - n_deg + 180) % 360 - 180)
                for ang, (nm, sym) in aspect_types.items():
                    if abs(diff - ang) <= orb:
                        aspects.append({
                            "transit": t_name, "natal": n_name,
                            "type": nm, "symbol": sym, "angle": round(diff, 2)
                        })
        houses = {}
        for p in ["Sun", "Mars", "Jupiter"]:
            deg = trans[p]
            for idx, cusp in enumerate(natal["houses"]):
                next_c = natal["houses"][(idx + 1) % 12]
                if cusp <= deg < next_c or (idx == 11 and (deg >= cusp or deg < natal["houses"][0])):
                    houses[p] = idx + 1
                    break
        week.append({
            "jd": round(jd, 5),
            "transits": trans,
            "aspects": aspects,
            "houses": houses
        })
    return week

@app.get("/weekly_forecast")
def weekly_forecast(
    date: str = Query(..., description="Birth date in format YYYY-MM-DD"),
    time: str = Query(..., description="Birth time in format HH:MM"),
    place: str = Query(..., description="Place of birth (city, country)"),
    tz_offset: int = Query(..., description="Time zone offset from UTC (e.g., 2 for UTC+2)")
):
    natal, error = calculate_chart(date, time, place, tz_offset)
    if error:
        return error

    transits = get_week_transits(natal, natal["jd"])
    focus_house = transits[0]["houses"].get("Sun")
    focus = {"planet": "Sun", "house": focus_house}

    zodiac_signs = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]

    moon_by_day = []
    for i, day in enumerate(transits):
        moon_deg = day["transits"]["Moon"]
        sign_index = int(moon_deg // 30) % 12
        moon_by_day.append({
            "day_index": i,
            "degree": moon_deg,
            "sign": zodiac_signs[sign_index]
        })

    aspects = [asp for day in transits for asp in day["aspects"]]
    slow = [
        asp for asp in aspects
        if asp["transit"] in ["Jupiter","Saturn","Uranus","Neptune","Pluto"]
    ]
    active = sorted({
        h for day in transits for h in day["houses"].values()
    })

    return {
        "start_of_week": date,
        "focus": focus,
        "moon_by_day": moon_by_day,
        "aspects": aspects,
        "slow_planets": slow,
        "active_houses": [{"house": h} for h in active]
    }
