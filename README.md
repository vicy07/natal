# 🧭 Natalia – Астрологический генератор натальных карт

**Natal** — простая и надёжная библиотека на Python для расчёта и построения натальных карт по дате, времени и месту рождения. 

---

## ✨ Основные возможности

- ✅ Расчёт положения планет (Солнце, Луна, Меркурий и др.) по эфемеридам
- 🌐 Определение домов гороскопа (Placidus, Koch, Whole Sign и др.)
- 📐 Расчёт аспектов между планетами

---

## 🚀 Быстрый старт

### Требования

- Python ≥ 3.8  
- Основные зависимости: `pyswisseph`, `pytz`

### Установка

```bash
pip install natal
```

*Или вручную:*

```bash
git clone https://github.com/vicy07/natal.git
cd natal
pip install .
```

### Пример использования

```python
from natal import NatalChart

# Создание натальной карты по дате и месту рождения
chart = NatalChart(
    birth_datetime="1990-05-17T14:30:00",
    latitude=56.9496,
    longitude=24.1052,
    timezone="Europe/Riga"
)

# Расчёт положений планет и домов
chart.calculate()

# Вывод списка позиций и аспектов
print(chart.get_planetary_positions())
print(chart.get_aspects())

# Экспорт в JSON
with open("chart.json", "w") as f:
    f.write(chart.to_json(indent=2))
```
