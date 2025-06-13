from datetime import datetime, timedelta
import swisseph as swe
from geopy.geocoders import Nominatim

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
orb = 6  # degrees of tolerance for aspects

def calculate_chart(date: str, time: str, place: str, tz_offset: int):
    geo = Nominatim(user_agent="astro_api").geocode(place)
    if not geo:
        return None, {"error": "Invalid place name"}
    lat, lon = geo.latitude, geo.longitude
    local = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    utc_time = local - timedelta(hours=tz_offset)
    jd = swe.julday(utc_time.year, utc_time.month, utc_time.day,
                    utc_time.hour + utc_time.minute / 60)
    planet_degrees = {}
    retrograde_planets = []
    for name, code in zip(planet_names, planet_codes):
        pos, ret = swe.calc_ut(jd, code)[0][0], swe.calc_ut(jd, code)[0][3]
        planet_degrees[name] = round(pos, 2)
        if ret < 0:
            retrograde_planets.append(name)
    cusps, _ = swe.houses(jd, lat, lon, b'P')
    houses = [round(c, 2) for c in cusps]
    # Calculate aspects
    aspects = []
    for i, (p1, d1) in enumerate(planet_degrees.items()):
        for j, (p2, d2) in enumerate(planet_degrees.items()):
            if j <= i:
                continue
            diff = abs((d1 - d2 + 180) % 360 - 180)
            for ang, (nm, sym) in aspect_types.items():
                if abs(diff - ang) <= orb:
                    aspects.append({
                        "between": f"{p1} - {p2}",
                        "type": nm,
                        "symbol": sym,
                        "angle": round(diff, 2)
                    })
    # Calculate house rulers
    sign_rulers = [
        'Mars', 'Venus', 'Mercury', 'Moon', 'Sun', 'Mercury', 'Venus', 'Pluto',
        'Jupiter', 'Saturn', 'Uranus', 'Neptune'
    ]
    house_rulers = []
    for i, cusp in enumerate(houses):
        sign_index = int((cusp // 30) % 12)
        ruler = sign_rulers[sign_index]
        ruler_pos = planet_degrees.get(ruler)
        house_rulers.append({
            "house": i+1,
            "sign": sign_index+1,
            "ruler": ruler,
            "ruler_degree": ruler_pos
        })
    return {"jd": jd, "lat": lat, "lon": lon,
            "planet_degrees": planet_degrees, "houses": houses, "aspects": aspects, "retrograde_planets": retrograde_planets, "house_rulers": house_rulers}, None
