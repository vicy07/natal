# logic_forecast.py
import swisseph as swe
from astro_core import calculate_chart
from datetime import datetime

def get_week_transits(natal, start_jd: float, days: int = 7):
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
    orb = 6
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

def weekly_forecast(date, time, place, tz_offset, start_date):
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
