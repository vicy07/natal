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
orb = 6  # градусов допуска для аспектов

def calculate_chart(date: str, time: str, place: str, tz_offset: int):
    geo = Nominatim(user_agent="astro_api").geocode(place)
    if not geo:
        return None, JSONResponse(status_code=400, content={"error": "Invalid place name"})
    lat, lon = geo.latitude, geo.longitude

    local = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    utc_time = local - timedelta(hours=tz_offset)
    jd = swe.julday(utc_time.year, utc_time.month, utc_time.day,
                    utc_time.hour + utc_time.minute / 60)

    planet_degrees = {name: round(swe.calc_ut(jd, code)[0][0], 2)
                      for name, code in zip(planet_names, planet_codes)}
    cusps, _ = swe.houses(jd, lat, lon, b'P')
    houses = [round(c, 2) for c in cusps]

    return {"jd": jd, "lat": lat, "lon": lon,
            "planet_degrees": planet_degrees, "houses": houses}, None

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
        '☌': 'grey',
        '✶': 'green',
        '△': 'green',
        '□': 'red',
        '☍': 'red'
    }

    fig = plt.figure(figsize=(9, 10))
    ax = fig.add_subplot(211, projection='polar')
    ax.set_theta_zero_location("E")
    ax.set_theta_direction(-1)
    ax.set_rticks([])

    # Знаки зодиака
    zodiac = [
        ('♈︎', 'Aries'), ('♉︎', 'Taurus'), ('♊︎', 'Gemini'), ('♋︎', 'Cancer'),
        ('♌︎', 'Leo'), ('♍︎', 'Virgo'), ('♎︎', 'Libra'), ('♏︎', 'Scorpio'),
        ('♐︎', 'Sagittarius'), ('♑︎', 'Capricorn'), ('♒︎', 'Aquarius'), ('♓︎', 'Pisces')
    ]
    for i, (sym, name) in enumerate(zodiac):
        angle = np.deg2rad(i * 30 + 15)
        ax.text(angle, 1.16, f"{sym}\n{name}", ha='center', va='center', fontsize=13)

    # Дома и углы
    key_points = {0: "ASC", 3: "IC", 6: "DSC", 9: "MC"}
    for i in range(12):
        a = np.deg2rad(houses[i])
        label = key_points.get(i, str(i+1))
        ax.plot([a, a], [0, 1.08], color='grey', lw=1, linestyle='--')
        ax.text(a, 0.85, label, ha='center', va='center', fontsize=10, color='grey', weight='bold')  # внутрь круга

    # Внешний круг
    circle = plt.Circle((0, 0), 1.08, transform=ax.transData._b, fill=False, color="black", lw=1.5)
    ax.add_artist(circle)

    # Планеты
    mapping = {}
    for idx, (name, deg) in enumerate(planet_degrees.items()):
        ang = np.deg2rad(deg)
        is_retro = name in retrograde_planets
        label = f"{planet_symbols[name]} {name}\n{deg:.1f}°{' ℞' if is_retro else ''}"
        color = 'darkred' if is_retro else 'navy'
        r_offset = 1.0 - idx * 0.005  # чуть-чуть сдвигаем внутрь для читаемости
        ax.plot(ang, r_offset, 'o', color=color)
        ax.text(ang, r_offset - 0.05, label, ha='center', va='center', fontsize=9, color=color)
        mapping[name] = ang

    # Аспекты
    for asp in aspects:
        p1, p2 = [s.strip() for s in asp["between"].split("-")]
        a1, a2 = mapping.get(p1), mapping.get(p2)
        if a1 is not None and a2 is not None:
            color = aspect_colors.get(asp["symbol"], 'black')
            ax.plot([a1, a2], [1.0, 1.0], color=color, lw=1, alpha=0.7)
            mid = (a1 + a2) / 2
            ax.text(mid, 1.02, asp["symbol"], fontsize=12, ha='center', va='center', color=color)

    # Легенда аспектов в нижней части
    ax_legend = fig.add_subplot(212)
    ax_legend.axis("off")
    legend_text = "\n".join([
        "☌ Conjunction — нейтральный (серый)",
        "✶ Sextile — гармоничный (зелёный)",
        "△ Trine — гармоничный (зелёный)",
        "□ Square — напряжённый (красный)",
        "☍ Opposition — напряжённый (красный)"
    ])
    ax_legend.text(0.5, 0.5, legend_text, fontsize=10, ha="center", va="center", family='monospace')

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
    img = draw_chart(data["planet_degrees"], data["houses"], [])
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
