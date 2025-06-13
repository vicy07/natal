# logic_horary.py
from astro_core import calculate_chart

def horary_chart(date, time, place, tz_offset):
    data, err = calculate_chart(date, time, place, tz_offset)
    if err:
        return err
    return {
        "type": "horary",
        "question_time": f"{date} {time}",
        "place": place,
        "chart": data
    }
