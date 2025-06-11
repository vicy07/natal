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

    # Calculate house rulers and their positions
    # Zodiac order: Aries, Taurus, Gemini, Cancer, Leo, Virgo, Libra, Scorpio, Sagittarius, Capricorn, Aquarius, Pisces
    sign_rulers = [
        'Mars',    # Aries
        'Venus',   # Taurus
        'Mercury', # Gemini
        'Moon',    # Cancer
        'Sun',     # Leo
        'Mercury', # Virgo
        'Venus',   # Libra
        'Pluto',   # Scorpio (modern), use 'Mars' for traditional
        'Jupiter', # Sagittarius
        'Saturn',  # Capricorn
        'Uranus',  # Aquarius (modern), use 'Saturn' for traditional
        'Neptune'  # Pisces (modern), use 'Jupiter' for traditional
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

    # Draw house rulers (управители домов)
    import inspect
    house_rulers = None
    # Try to get house_rulers from the calling frame (API context)
    frame = inspect.currentframe()
    while frame:
        if 'house_rulers' in frame.f_locals:
            house_rulers = frame.f_locals['house_rulers']
            break
        frame = frame.f_back
    # If not found, try to get from global context (for API usage)
    if house_rulers is None and 'house_rulers' in globals():
        house_rulers = globals()['house_rulers']
    # Draw house rulers on the chart
    if house_rulers:
        for hr in house_rulers:
            if hr['ruler_degree'] is not None:
                ang = np.deg2rad(hr['ruler_degree'])
                ax.plot(ang, 1.13, marker='*', color='purple', markersize=10, zorder=10)
                ax.text(ang, 1.16, hr['ruler'], ha='center', va='bottom', fontsize=9, color='purple', fontweight='bold')
                ax.text(ang, 1.19, f"{hr['house']}", ha='center', va='bottom', fontsize=7, color='purple')

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

@app.get("/synastry")
def synastry(
    date1: str = Query(..., description="Birth date of person 1 (YYYY-MM-DD)"),
    time1: str = Query(..., description="Birth time of person 1 (HH:MM)"),
    place1: str = Query(..., description="Birth place of person 1 (city, country)"),
    tz_offset1: int = Query(..., description="Time zone offset for person 1 (e.g., 2 for UTC+2)"),
    date2: str = Query(..., description="Birth date of person 2 (YYYY-MM-DD)"),
    time2: str = Query(..., description="Birth time of person 2 (HH:MM)"),
    place2: str = Query(..., description="Birth place of person 2 (city, country)"),
    tz_offset2: int = Query(..., description="Time zone offset for person 2 (e.g., 2 for UTC+2)")
):
    # Calculate both charts
    chart1, err1 = calculate_chart(date1, time1, place1, tz_offset1)
    chart2, err2 = calculate_chart(date2, time2, place2, tz_offset2)
    if err1:
        return err1
    if err2:
        return err2

    # Define orb for aspects (can be improved for different planets)
    orb_luminaries = 8  # Sun, Moon
    orb_planets = 6
    aspect_defs = [
        (0, "Conjunction", "☌"),
        (60, "Sextile", "✶"),
        (90, "Square", "□"),
        (120, "Trine", "△"),
        (180, "Opposition", "☍")
    ]
    personal_planets = ["Sun", "Moon", "Mercury", "Venus", "Mars"]

    synastry_aspects = []
    for p1, d1 in chart1["planet_degrees"].items():
        for p2, d2 in chart2["planet_degrees"].items():
            diff = abs((d1 - d2 + 180) % 360 - 180)
            orb = orb_luminaries if p1 in ["Sun", "Moon"] or p2 in ["Sun", "Moon"] else orb_planets
            for ang, name, sym in aspect_defs:
                if abs(diff - ang) <= orb:
                    synastry_aspects.append({
                        "between": f"{p1} (1) - {p2} (2)",
                        "type": name,
                        "symbol": sym,
                        "angle": round(diff, 2),
                        "personal": p1 in personal_planets and p2 in personal_planets,
                        "harmonious": name in ["Trine", "Sextile"],
                        "tense": name in ["Square", "Opposition"]
                    })

    # Count summary
    summary = {
        "harmonious": sum(1 for a in synastry_aspects if a["harmonious"]),
        "tense": sum(1 for a in synastry_aspects if a["tense"]),
        "personal_harmonious": sum(1 for a in synastry_aspects if a["harmonious"] and a["personal"]),
        "personal_tense": sum(1 for a in synastry_aspects if a["tense"] and a["personal"]),
        "total": len(synastry_aspects)
    }

    return {
        "person1": {"planet_degrees": chart1["planet_degrees"]},
        "person2": {"planet_degrees": chart2["planet_degrees"]},
        "synastry_aspects": synastry_aspects,
        "summary": summary
    }

@app.get("/synastry/analytics")
def synastry_analytics(
    date1: str = Query(..., description="Birth date of person 1 (YYYY-MM-DD)"),
    time1: str = Query(..., description="Birth time of person 1 (HH:MM)"),
    place1: str = Query(..., description="Birth place of person 1 (city, country)"),
    tz_offset1: int = Query(..., description="Time zone offset for person 1 (e.g., 2 for UTC+2)"),
    date2: str = Query(..., description="Birth date of person 2 (YYYY-MM-DD)"),
    time2: str = Query(..., description="Birth time of person 2 (HH:MM)"),
    place2: str = Query(..., description="Birth place of person 2 (city, country)"),
    tz_offset2: int = Query(..., description="Time zone offset for person 2 (e.g., 2 for UTC+2)")
):
    chart1, err1 = calculate_chart(date1, time1, place1, tz_offset1)
    chart2, err2 = calculate_chart(date2, time2, place2, tz_offset2)
    if err1:
        return err1
    if err2:
        return err2

    # Prepare synastry aspects (reuse logic from /synastry)
    orb_luminaries = 8
    orb_planets = 6
    aspect_defs = [
        (0, "Conjunction", "☌"),
        (60, "Sextile", "✶"),
        (90, "Square", "□"),
        (120, "Trine", "△"),
        (180, "Opposition", "☍")
    ]
    personal_planets = ["Sun", "Moon", "Mercury", "Venus", "Mars"]
    synastry_aspects = []
    for p1, d1 in chart1["planet_degrees"].items():
        for p2, d2 in chart2["planet_degrees"].items():
            diff = abs((d1 - d2 + 180) % 360 - 180)
            orb = orb_luminaries if p1 in ["Sun", "Moon"] or p2 in ["Sun", "Moon"] else orb_planets
            for ang, name, sym in aspect_defs:
                if abs(diff - ang) <= orb:
                    synastry_aspects.append({
                        "between": f"{p1} (1) - {p2} (2)",
                        "type": name,
                        "symbol": sym,
                        "angle": round(diff, 2),
                        "personal": p1 in personal_planets and p2 in personal_planets,
                        "harmonious": name in ["Trine", "Sextile"],
                        "tense": name in ["Square", "Opposition"]
                    })

    # Extended analytics
    # 1. Matrix of all aspects (by planet)
    aspect_matrix = {}
    for asp in synastry_aspects:
        p1, p2 = asp["between"].split(" (1) - ")
        if p1 not in aspect_matrix:
            aspect_matrix[p1] = {}
        aspect_matrix[p1][p2.replace(" (2)","")] = asp["symbol"]

    # 2. List of all personal-to-personal aspects
    personal_aspects = [a for a in synastry_aspects if a["personal"]]

    # 3. Most exact aspect (smallest angle diff from exact)
    if synastry_aspects:
        most_exact = min(synastry_aspects, key=lambda a: min(abs(a["angle"]-x[0]) for x in aspect_defs if a["symbol"]==x[2]))
    else:
        most_exact = None

    # 4. Count by aspect type
    aspect_type_count = {}
    for asp in synastry_aspects:
        aspect_type_count[asp["type"]] = aspect_type_count.get(asp["type"], 0) + 1

    # 5. List of all harmonious/tense aspects with details
    harmonious_details = [a for a in synastry_aspects if a["harmonious"]]
    tense_details = [a for a in synastry_aspects if a["tense"]]

    return {
        "aspect_matrix": aspect_matrix,
        "personal_aspects": personal_aspects,
        "most_exact_aspect": most_exact,
        "aspect_type_count": aspect_type_count,
        "harmonious_details": harmonious_details,
        "tense_details": tense_details,
        "total_aspects": len(synastry_aspects)
    }

@app.get("/synastry/image")
def synastry_image(
    date1: str = Query(..., description="Birth date of person 1 (YYYY-MM-DD)"),
    time1: str = Query(..., description="Birth time of person 1 (HH:MM)"),
    place1: str = Query(..., description="Birth place of person 1 (city, country)"),
    tz_offset1: int = Query(..., description="Time zone offset for person 1 (e.g., 2 for UTC+2)"),
    date2: str = Query(..., description="Birth date of person 2 (YYYY-MM-DD)"),
    time2: str = Query(..., description="Birth time of person 2 (HH:MM)"),
    place2: str = Query(..., description="Birth place of person 2 (city, country)"),
    tz_offset2: int = Query(..., description="Time zone offset for person 2 (e.g., 2 for UTC+2)")
):
    chart1, err1 = calculate_chart(date1, time1, place1, tz_offset1)
    chart2, err2 = calculate_chart(date2, time2, place2, tz_offset2)
    if err1:
        return err1
    if err2:
        return err2

    import matplotlib.pyplot as plt
    import numpy as np
    import io

    # Prepare double wheel: inner (person 1), outer (person 2)
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='polar')
    ax.set_theta_zero_location("E")
    ax.set_theta_direction(-1)
    ax.set_rticks([])

    # Draw zodiac
    zodiac = [
        ('\u2648', 'Aries', 'red'), ('\u2649', 'Taurus', 'green'), ('\u264A', 'Gemini', 'gold'),
        ('\u264B', 'Cancer', 'blue'), ('\u264C', 'Leo', 'red'), ('\u264D', 'Virgo', 'green'),
        ('\u264E', 'Libra', 'gold'), ('\u264F', 'Scorpio', 'blue'), ('\u2650', 'Sagittarius', 'red'),
        ('\u2651', 'Capricorn', 'green'), ('\u2652', 'Aquarius', 'gold'), ('\u2653', 'Pisces', 'blue')
    ]
    for i, (sym, name, color) in enumerate(zodiac):
        angle = np.deg2rad(i * 30 + 15)
        ax.text(angle, 1.33, f"{sym}\n{name}", ha='center', va='center', fontsize=13, color=color)

    # Draw houses for person 1 (inner)
    for i in range(12):
        a = np.deg2rad(chart1['houses'][i])
        ax.plot([a, a], [0, 1.08], color='grey', lw=1, linestyle='--', alpha=0.7)
        ax.text(a, 0.7, str(i+1), ha='center', va='center', fontsize=10, color='dimgray')
    # Draw houses for person 2 (outer, slightly further)
    for i in range(12):
        a = np.deg2rad(chart2['houses'][i])
        ax.plot([a, a], [1.09, 1.18], color='slateblue', lw=1, linestyle=':', alpha=0.7)
        ax.text(a, 1.21, str(i+1), ha='center', va='center', fontsize=9, color='slateblue')

    # Draw planets for person 1 (inner)
    planet_symbols = {
        'Sun': '\u2609', 'Moon': '\u263D', 'Mercury': '\u263F', 'Venus': '\u2640', 'Mars': '\u2642',
        'Jupiter': '\u2643', 'Saturn': '\u2644', 'Uranus': '\u2645', 'Neptune': '\u2646', 'Pluto': '\u2647'
    }
    for idx, (name, deg) in enumerate(chart1['planet_degrees'].items()):
        ang = np.deg2rad(deg)
        r = 0.98 - idx * 0.01
        ax.text(ang, r, planet_symbols[name], ha='center', va='center', fontsize=13, color='navy', fontweight='bold')
        ax.text(ang, r-0.045, name, ha='center', va='top', fontsize=8, color='navy')
        ax.text(ang, r-0.075, f"{deg:.1f}°", ha='center', va='top', fontsize=5, color='navy')

    # Draw planets for person 2 (outer)
    for idx, (name, deg) in enumerate(chart2['planet_degrees'].items()):
        ang = np.deg2rad(deg)
        r = 1.12 - idx * 0.01
        ax.text(ang, r, planet_symbols[name], ha='center', va='center', fontsize=13, color='crimson', fontweight='bold')
        ax.text(ang, r+0.045, name, ha='center', va='bottom', fontsize=8, color='crimson')
        ax.text(ang, r+0.075, f"{deg:.1f}°", ha='center', va='bottom', fontsize=5, color='crimson')

    # Draw synastry aspects (between charts)
    orb_luminaries = 8
    orb_planets = 6
    aspect_defs = [
        (0, "Conjunction", "☌", 'gray'),
        (60, "Sextile", "✶", 'green'),
        (90, "Square", "□", 'orange'),
        (120, "Trine", "△", 'blue'),
        (180, "Opposition", "☍", 'red')
    ]
    for p1, d1 in chart1['planet_degrees'].items():
        for p2, d2 in chart2['planet_degrees'].items():
            diff = abs((d1 - d2 + 180) % 360 - 180)
            orb = orb_luminaries if p1 in ['Sun', 'Moon'] or p2 in ['Sun', 'Moon'] else orb_planets
            for ang, name, sym, color in aspect_defs:
                if abs(diff - ang) <= orb:
                    a1 = np.deg2rad(d1)
                    a2 = np.deg2rad(d2)
                    ax.plot([a1, a2], [0.98, 1.12], color=color, lw=1.5, alpha=0.7)
                    mid = (a1 + a2) / 2
                    ax.text(mid, 1.05, sym, fontsize=15, ha='center', va='center', color=color, weight='bold', alpha=0.7)

    # Add legend for synastry aspects
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
    ax.legend(handles=legend_handles, loc='upper right', bbox_to_anchor=(1.25, 1.05), fontsize=12, frameon=True, title='Synastry Aspects')

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return Response(content=buf.read(), media_type="image/png")
