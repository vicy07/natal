from fastapi import FastAPI, Query, Response
from fastapi.responses import JSONResponse
from logic_natal import natal_chart_calc, natal_chart_image
from logic_synastry import synastry, synastry_analytics, synastry_image
from logic_transit import transits
from logic_horary import horary_chart
from astro_core import calculate_chart
from chart_draw import draw_chart
from datetime import datetime
import swisseph as swe
from logic_forecast import weekly_forecast

app = FastAPI()

@app.get("/natal_chart/calc")
def natal_chart_calc_endpoint(
    date: str = Query(..., description="Birth date in format YYYY-MM-DD"),
    time: str = Query(..., description="Birth time in format HH:MM"),
    place: str = Query(..., description="Place of birth (city, country)"),
    tz_offset: int = Query(..., description="Time zone offset from UTC (e.g., 2 for UTC+2)")
):
    return natal_chart_calc(date, time, place, tz_offset)

@app.get("/natal_chart/image")
def natal_chart_image_endpoint(
    date: str = Query(..., description="Birth date in format YYYY-MM-DD"),
    time: str = Query(..., description="Birth time in format HH:MM"),
    place: str = Query(..., description="Place of birth (city, country)"),
    tz_offset: int = Query(..., description="Time zone offset from UTC (e.g., 2 for UTC+2)")
):
    return natal_chart_image(date, time, place, tz_offset)

@app.get("/synastry")
def synastry_endpoint(
    date1: str = Query(..., description="Birth date of person 1 (YYYY-MM-DD)"),
    time1: str = Query(..., description="Birth time of person 1 (HH:MM)"),
    place1: str = Query(..., description="Birth place of person 1 (city, country)"),
    tz_offset1: int = Query(..., description="Time zone offset for person 1 (e.g., 2 for UTC+2)"),
    date2: str = Query(..., description="Birth date of person 2 (YYYY-MM-DD)"),
    time2: str = Query(..., description="Birth time of person 2 (HH:MM)"),
    place2: str = Query(..., description="Birth place of person 2 (city, country)"),
    tz_offset2: int = Query(..., description="Time zone offset for person 2 (e.g., 2 for UTC+2)")
):
    return synastry(date1, time1, place1, tz_offset1, date2, time2, place2, tz_offset2)

@app.get("/synastry/analytics")
def synastry_analytics_endpoint(
    date1: str = Query(..., description="Birth date of person 1 (YYYY-MM-DD)"),
    time1: str = Query(..., description="Birth time of person 1 (HH:MM)"),
    place1: str = Query(..., description="Birth place of person 1 (city, country)"),
    tz_offset1: int = Query(..., description="Time zone offset for person 1 (e.g., 2 for UTC+2)"),
    date2: str = Query(..., description="Birth date of person 2 (YYYY-MM-DD)"),
    time2: str = Query(..., description="Birth time of person 2 (HH:MM)"),
    place2: str = Query(..., description="Birth place of person 2 (city, country)"),
    tz_offset2: int = Query(..., description="Time zone offset for person 2 (e.g., 2 for UTC+2)")
):
    return synastry_analytics(date1, time1, place1, tz_offset1, date2, time2, place2, tz_offset2)

@app.get("/synastry/image")
def synastry_image_endpoint(
    date1: str = Query(..., description="Birth date of person 1 (YYYY-MM-DD)"),
    time1: str = Query(..., description="Birth time of person 1 (HH:MM)"),
    place1: str = Query(..., description="Birth place of person 1 (city, country)"),
    tz_offset1: int = Query(..., description="Time zone offset for person 1 (e.g., 2 for UTC+2)"),
    date2: str = Query(..., description="Birth date of person 2 (YYYY-MM-DD)"),
    time2: str = Query(..., description="Birth time of person 2 (HH:MM)"),
    place2: str = Query(..., description="Birth place of person 2 (city, country)"),
    tz_offset2: int = Query(..., description="Time zone offset for person 2 (e.g., 2 for UTC+2)")
):
    return synastry_image(date1, time1, place1, tz_offset1, date2, time2, place2, tz_offset2)

@app.get("/horary_chart")
def horary_chart_endpoint(
    date: str = Query(..., description="Date of the question (YYYY-MM-DD)"),
    time: str = Query(..., description="Time of the question (HH:MM)"),
    place: str = Query(..., description="Place where the question was asked (city, country)"),
    tz_offset: int = Query(..., description="Time zone offset from UTC (e.g., 3 for Moscow)")
):
    return horary_chart(date, time, place, tz_offset)

@app.get("/transits")
def transits_endpoint(
    natal_date: str = Query(..., description="Birth date (YYYY-MM-DD)"),
    natal_time: str = Query(..., description="Birth time (HH:MM)"),
    natal_place: str = Query(..., description="Birth place (city, country)"),
    natal_tz_offset: int = Query(..., description="Time zone offset for birth (e.g., 3 for Moscow)"),
    transit_date: str = Query(..., description="Date for transit (YYYY-MM-DD)"),
    transit_time: str = Query("00:00", description="Time for transit (HH:MM), default 00:00")
):
    return transits(natal_date, natal_time, natal_place, natal_tz_offset, transit_date, transit_time)

@app.get("/weekly_forecast")
def weekly_forecast_endpoint(
    date: str = Query(..., description="Birth date in format YYYY-MM-DD"),
    time: str = Query(..., description="Birth time in format HH:MM"),
    place: str = Query(..., description="Place of birth (city, country)"),
    tz_offset: int = Query(..., description="Time zone offset from UTC (e.g., 2 for UTC+2)"),
    start_date: str = Query(..., description="Start date for forecast in format YYYY-MM-DD")
):
    return weekly_forecast(date, time, place, tz_offset, start_date)
