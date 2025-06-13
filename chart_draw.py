import matplotlib.pyplot as plt
import numpy as np
import io

def draw_chart(planet_degrees, houses, aspects, retrograde_planets=None, house_rulers=None):
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
    zodiac = [
        ('♈', 'Aries', 'red'), ('♉', 'Taurus', 'green'), ('♊', 'Gemini', 'gold'),
        ('♋', 'Cancer', 'blue'), ('♌', 'Leo', 'red'), ('♍', 'Virgo', 'green'),
        ('♎', 'Libra', 'gold'), ('♏', 'Scorpio', 'blue'), ('♐', 'Sagittarius', 'red'),
        ('♑', 'Capricorn', 'green'), ('♒', 'Aquarius', 'gold'), ('♓', 'Pisces', 'blue')
    ]
    for i, (sym, name, color) in enumerate(zodiac):
        angle = np.deg2rad(i * 30 + 15)
        ax.text(angle, 1.33, f"{sym}\n{name}", ha='center', va='center', fontsize=13, color=color)
    key_points = {0: "ASC", 3: "IC", 6: "DSC", 9: "MC"}
    for i in range(12):
        a = np.deg2rad(houses[i])
        label = key_points.get(i, str(i+1))
        ax.plot([a, a], [0, 1.08], color='grey', lw=1, linestyle='--')
        ax.text(a, 0.7, label, ha='center', va='center', fontsize=11, color='dimgray', weight='bold')
    circle = plt.Circle((0, 0), 1.08, transform=ax.transData._b, fill=False, color="black", lw=1.5)
    ax.add_artist(circle)
    mapping = {}
    for idx, (name, deg) in enumerate(planet_degrees.items()):
        ang = np.deg2rad(deg)
        is_retro = name in retrograde_planets
        r_offset = 1.0 - idx * 0.04
        ax.text(ang, r_offset, planet_symbols[name], ha='center', va='center', fontsize=10, color='darkred' if is_retro else 'navy', fontweight='bold', rotation=0, rotation_mode='anchor')
        ax.text(ang, r_offset - 0.06, name, ha='center', va='top', fontsize=8, color='darkred' if is_retro else 'navy', rotation=0, rotation_mode='anchor')
        ax.text(ang, r_offset - 0.10, f"{deg:.1f}°", ha='center', va='top', fontsize=4, color='darkred' if is_retro else 'navy', rotation=0, rotation_mode='anchor')
        if is_retro:
            ax.text(ang, r_offset - 0.135, "℞", ha='center', va='top', fontsize=7, color='darkred', rotation=0, rotation_mode='anchor')
        mapping[name] = ang
    for asp in aspects:
        p1, p2 = [s.strip() for s in asp["between"].split("-")]
        a1, a2 = mapping.get(p1), mapping.get(p2)
        if a1 is not None and a2 is not None:
            color = aspect_colors.get(asp["symbol"], 'black')
            ax.plot([a1, a2], [1.0, 1.0], color=color, lw=1, alpha=0.8)
            mid = (a1 + a2) / 2
            ax.text(mid, 0.9, asp["symbol"], fontsize=14, ha='center', va='center', color=color, weight='bold')
    if house_rulers:
        for hr in house_rulers:
            if hr['ruler_degree'] is not None:
                ang = np.deg2rad(hr['ruler_degree'])
                ax.plot(ang, 1.13, marker='*', color='purple', markersize=10, zorder=10)
                ax.text(ang, 1.16, hr['ruler'], ha='center', va='bottom', fontsize=9, color='purple', fontweight='bold')
                ax.text(ang, 1.19, f"{hr['house']}", ha='center', va='bottom', fontsize=7, color='purple')
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
