# logic_synastry.py
from fastapi import Response
from astro_core import calculate_chart
import matplotlib.pyplot as plt
import numpy as np
import io

def synastry(date1, time1, place1, tz_offset1, date2, time2, place2, tz_offset2):
    chart1, err1 = calculate_chart(date1, time1, place1, tz_offset1)
    chart2, err2 = calculate_chart(date2, time2, place2, tz_offset2)
    if err1:
        return err1
    if err2:
        return err2
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

def synastry_analytics(date1, time1, place1, tz_offset1, date2, time2, place2, tz_offset2):
    chart1, err1 = calculate_chart(date1, time1, place1, tz_offset1)
    chart2, err2 = calculate_chart(date2, time2, place2, tz_offset2)
    if err1:
        return err1
    if err2:
        return err2
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
    aspect_matrix = {}
    for asp in synastry_aspects:
        p1, p2 = asp["between"].split(" (1) - ")
        if p1 not in aspect_matrix:
            aspect_matrix[p1] = {}
        aspect_matrix[p1][p2.replace(" (2)","")] = asp["symbol"]
    personal_aspects = [a for a in synastry_aspects if a["personal"]]
    if synastry_aspects:
        most_exact = min(synastry_aspects, key=lambda a: min(abs(a["angle"]-x[0]) for x in aspect_defs if a["symbol"]==x[2]))
    else:
        most_exact = None
    aspect_type_count = {}
    for asp in synastry_aspects:
        aspect_type_count[asp["type"]] = aspect_type_count.get(asp["type"], 0) + 1
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

def synastry_image(date1, time1, place1, tz_offset1, date2, time2, place2, tz_offset2):
    chart1, err1 = calculate_chart(date1, time1, place1, tz_offset1)
    chart2, err2 = calculate_chart(date2, time2, place2, tz_offset2)
    if err1:
        return err1
    if err2:
        return err2
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='polar')
    ax.set_theta_zero_location("E")
    ax.set_theta_direction(-1)
    ax.set_rticks([])
    zodiac = [
        ('\u2648', 'Aries', 'red'), ('\u2649', 'Taurus', 'green'), ('\u264A', 'Gemini', 'gold'),
        ('\u264B', 'Cancer', 'blue'), ('\u264C', 'Leo', 'red'), ('\u264D', 'Virgo', 'green'),
        ('\u264E', 'Libra', 'gold'), ('\u264F', 'Scorpio', 'blue'), ('\u2650', 'Sagittarius', 'red'),
        ('\u2651', 'Capricorn', 'green'), ('\u2652', 'Aquarius', 'gold'), ('\u2653', 'Pisces', 'blue')
    ]
    for i, (sym, name, color) in enumerate(zodiac):
        angle = np.deg2rad(i * 30 + 15)
        ax.text(angle, 1.33, f"{sym}\n{name}", ha='center', va='center', fontsize=13, color=color)
    for i in range(12):
        a = np.deg2rad(chart1['houses'][i])
        ax.plot([a, a], [0, 1.08], color='grey', lw=1, linestyle='--', alpha=0.7)
        ax.text(a, 0.7, str(i+1), ha='center', va='center', fontsize=10, color='dimgray')
    for i in range(12):
        a = np.deg2rad(chart2['houses'][i])
        ax.plot([a, a], [1.09, 1.18], color='slateblue', lw=1, linestyle=':', alpha=0.7)
        ax.text(a, 1.21, str(i+1), ha='center', va='center', fontsize=9, color='slateblue')
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
    for idx, (name, deg) in enumerate(chart2['planet_degrees'].items()):
        ang = np.deg2rad(deg)
        r = 1.12 - idx * 0.01
        ax.text(ang, r, planet_symbols[name], ha='center', va='center', fontsize=13, color='crimson', fontweight='bold')
        ax.text(ang, r+0.045, name, ha='center', va='bottom', fontsize=8, color='crimson')
        ax.text(ang, r+0.075, f"{deg:.1f}°", ha='center', va='bottom', fontsize=5, color='crimson')
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
