from fastapi import FastAPI, Query, Response
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
import swisseph as swe
import matplotlib.pyplot as plt
import numpy as np
import io
from geopy.geocoders import Nominatim

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
orb = 6  # degrees of tolerance for aspects

def calculate_chart(date: str, time: str, place: str, tz_offset: int):
    geo = Nominatim(user_agent="astro_api").geocode(place)
    if not geo:
        return None, JSONResponse(status_code=400, content={"error": "Invalid place name"})
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
    return {"jd": jd, "lat": lat, "lon": lon,
            "planet_degrees": planet_degrees, "houses": houses, "aspects": aspects, "retrograde_planets": retrograde_planets}, None

def draw_chart(planet_degrees, houses, aspects, retrograde_planets=None):
    import matplotlib.pyplot as plt
    import numpy as np
    import io

    if retrograde_planets is None:
        retrograde_planets = []

    planet_symbols = {
        'Sun': '☉', 'Moon': '☽', 'Mercury': '☿', 'Venus': '♀', 'Mars': '♂',
        'Jupiter': '♃', 'Saturn': '♄', 'Uranus': '♅', 'Neptune': '♆', 'Pluto': '♇'
    }

    aspect_colors = {
        '☌': 'gray',
        '✶': 'green',
        '△': 'blue',
        '□': 'orange',
        '☍': 'red'
    }

    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='polar')
    ax.set_theta_zero_location("E")
    ax.set_theta_direction(-1)
    ax.set_rticks([])

    # Zodiac signs with color coding by element
    zodiac = [
        ('♈', 'Aries', 'red'),      # Fire
        ('♉', 'Taurus', 'green'),   # Earth
        ('♊', 'Gemini', 'gold'),    # Air
        ('♋', 'Cancer', 'blue'),    # Water
        ('♌', 'Leo', 'red'),        # Fire
        ('♍', 'Virgo', 'green'),    # Earth
        ('♎', 'Libra', 'gold'),     # Air
        ('♏', 'Scorpio', 'blue'),   # Water
        ('♐', 'Sagittarius', 'red'),# Fire
        ('♑', 'Capricorn', 'green'),# Earth
        ('♒', 'Aquarius', 'gold'),  # Air
        ('♓', 'Pisces', 'blue')     # Water
    ]
    for i, (sym, name, color) in enumerate(zodiac):
        angle = np.deg2rad(i * 30 + 15)
        ax.text(angle, 1.33, f"{sym}\n{name}", ha='center', va='center', fontsize=13, color=color)

    # Houses and angles
    key_points = {0: "ASC", 3: "IC", 6: "DSC", 9: "MC"}
    for i in range(12):
        a = np.deg2rad(houses[i])
        label = key_points.get(i, str(i+1))
        ax.plot([a, a], [0, 1.08], color='grey', lw=1, linestyle='--')
        ax.text(a, 0.7, label, ha='center', va='center', fontsize=11, color='dimgray', weight='bold')

    # Outer circle
    circle = plt.Circle((0, 0), 1.08, transform=ax.transData._b, fill=False, color="black", lw=1.5)
    ax.add_artist(circle)

    # Planets
    mapping = {}
    for idx, (name, deg) in enumerate(planet_degrees.items()):
        ang = np.deg2rad(deg)
        is_retro = name in retrograde_planets
        r_offset = 1.0 - idx * 0.04  # Increase spacing between planets
        # Draw planet symbol at the exact location (no dot)
        ax.text(ang, r_offset, planet_symbols[name], ha='center', va='center', fontsize=10, color='darkred' if is_retro else 'navy', fontweight='bold', rotation=0, rotation_mode='anchor')
        # Draw planet name below the symbol (font size 8), with more vertical offset
        ax.text(ang, r_offset - 0.06, name, ha='center', va='top', fontsize=8, color='darkred' if is_retro else 'navy', rotation=0, rotation_mode='anchor')
        # Draw planet degree below the name (font size 4), with more vertical offset
        ax.text(ang, r_offset - 0.10, f"{deg:.1f}°", ha='center', va='top', fontsize=4, color='darkred' if is_retro else 'navy', rotation=0, rotation_mode='anchor')
        # Draw retrograde symbol if needed (font size 7, below degree)
        if is_retro:
            ax.text(ang, r_offset - 0.135, "℞", ha='center', va='top', fontsize=7, color='darkred', rotation=0, rotation_mode='anchor')
        mapping[name] = ang

    # Aspects
    for asp in aspects:
        p1, p2 = [s.strip() for s in asp["between"].split("-")]
        a1, a2 = mapping.get(p1), mapping.get(p2)
        if a1 is not None and a2 is not None:
            color = aspect_colors.get(asp["symbol"], 'black')
            ax.plot([a1, a2], [1.0, 1.0], color=color, lw=1, alpha=0.8)
            mid = (a1 + a2) / 2
            ax.text(mid, 0.9, asp["symbol"], fontsize=14, ha='center', va='center', color=color, weight='bold')

    # Remove aspect legend from inside the circle
    # Add standard legend box outside the plot
    import matplotlib
    legend_items = [
        ("☌ Conjunction", 'gray'),
        ("✶ Sextile", 'green'),
        ("△ Trine", 'blue'),
        ("□ Square", 'orange'),
        ("☍ Opposition", 'red')
    ]
    legend_handles = [
        matplotlib.pyplot.Line2D([0], [0], color=color, lw=2, label=label)
        for label, color in legend_items
    ]
    ax.legend(handles=legend_handles, loc='upper right', bbox_to_anchor=(1.25, 1.05), fontsize=12, frameon=True)

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
    data, err = calculate_chart(date, time, place, tz_offset)
    return err or data

@app.get("/natal_chart/image")
def natal_chart_image(
    date: str = Query(..., description="Birth date in format YYYY-MM-DD"),
    time: str = Query(..., description="Birth time in format HH:MM"),
    place: str = Query(..., description="Place of birth (city, country)"),
    tz_offset: int = Query(..., description="Time zone offset from UTC (e.g., 2 for UTC+2)")
):
    data, err = calculate_chart(date, time, place, tz_offset)
    if err:
        return err
    img = draw_chart(
        data["planet_degrees"],
        data["houses"],
        data["aspects"],
        data["retrograde_planets"]
    )
    return Response(content=img, media_type="image/png")

def get_week_transits(natal, start_jd: float, days: int = 7):
    week = []
    for i in range(days):
        jd = start_jd + i
        trans = {n: round(swe.calc_ut(jd, c)[0][0], 2)
                 for n,c in zip(planet_names, planet_codes)}
        aspects = []
        for tn,td in trans.items():
            for nn,nd in natal["planet_degrees"].items():
                diff = abs((td-nd+180)%360 -180)
                for ang,(nm,sym) in aspect_types.items():
                    if abs(diff-ang) <= orb:
                        aspects.append({
                            "transit": tn,
                            "natal": nn,
                            "type": nm,
                            "symbol": sym,
                            "angle": round(diff,2)
                        })
        houses = {}
        for p in ["Sun","Mars","Jupiter"]:
            pd = trans[p]
            for idx,cusp in enumerate(natal["houses"]):
                nc = natal["houses"][(idx+1)%12]
                if cusp<=pd<nc or (idx==11 and (pd>=cusp or pd<natal["houses"][0])):
                    houses[p] = idx+1
                    break
        week.append({"jd":round(jd,5),"transits":trans,"aspects":aspects,"houses":houses})
    return week

@app.get("/weekly_forecast")
def weekly_forecast(
    date: str = Query(..., description="Birth date in format YYYY-MM-DD"),
    time: str = Query(..., description="Birth time in format HH:MM"),
    place: str = Query(..., description="Place of birth (city, country)"),
    tz_offset: int = Query(..., description="Time zone offset from UTC (e.g., 2 for UTC+2)"),
    start_date: str = Query(..., description="Start date for forecast in format YYYY-MM-DD")
):
    natal, err = calculate_chart(date, time, place, tz_offset)
    if err:
        return err

    sd = datetime.strptime(start_date, "%Y-%m-%d")
    start_jd = swe.julday(sd.year, sd.month, sd.day, 0)
    transits = get_week_transits(natal, start_jd)

    focus = {"planet":"Sun","house": transits[0]["houses"].get("Sun")}
    zodiac = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
              "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
    moon_by = []
    for i, day in enumerate(transits):
        md = day["transits"]["Moon"]
        sign = zodiac[int(md // 30) % 12]
        moon_by.append({"day_index":i, "degree":md, "sign":sign})

    all_as = [a for day in transits for a in day["aspects"]]
    slow = [a for a in all_as if a["transit"] in
            ["Jupiter","Saturn","Uranus","Neptune","Pluto"]]
    active = sorted({h for day in transits for h in day["houses"].values()})

    return {
        "start_of_week": start_date,
        "focus": focus,
        "moon_by_day": moon_by,
        "aspects": all_as,
        "slow_planets": slow,
        "active_houses": [{"house":h} for h in active]
    }
