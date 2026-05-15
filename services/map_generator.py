"""
Genera el mapa PNG de la Ciénaga Grande de Santa Marta.
Estilo cartografía natural (Natural Earth / QGIS) — matplotlib sin tiles.
"""
import uuid
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import MultipleLocator
from pathlib import Path
from datetime import datetime
from config import MEDIA_DIR

# ---------------------------------------------------------------------------
# Geografía — polígono Ciénaga Grande (lon, lat)
# ---------------------------------------------------------------------------
_CIENAGA = np.array([
    [-74.22, 11.03], [-74.20, 11.00], [-74.18, 10.97],
    [-74.19, 10.93], [-74.19, 10.90], [-74.20, 10.86],
    [-74.21, 10.82], [-74.24, 10.77], [-74.27, 10.72],
    [-74.32, 10.66], [-74.36, 10.62], [-74.42, 10.58],
    [-74.48, 10.57], [-74.54, 10.57], [-74.60, 10.58],
    [-74.65, 10.61], [-74.70, 10.65], [-74.74, 10.70],
    [-74.76, 10.76], [-74.77, 10.82], [-74.76, 10.88],
    [-74.73, 10.94], [-74.68, 10.99], [-74.61, 11.03],
    [-74.55, 11.05], [-74.47, 11.07], [-74.40, 11.08],
    [-74.34, 11.07], [-74.28, 11.06], [-74.24, 11.04],
    [-74.22, 11.03],
])

_CANO_CLARIN = np.array([
    [-74.76, 10.82], [-74.80, 10.83], [-74.85, 10.84], [-74.90, 10.85],
])
_RIO_FUNDACION = np.array([
    [-74.36, 10.62], [-74.35, 10.55], [-74.33, 10.47],
])
_RIO_ARACATACA = np.array([
    [-74.48, 10.57], [-74.46, 10.49], [-74.44, 10.42],
])
_RIO_SEVILLA = np.array([
    [-74.27, 10.72], [-74.26, 10.63], [-74.25, 10.55],
])

# ---------------------------------------------------------------------------
# Comunidades pesqueras
# ---------------------------------------------------------------------------
_COMMUNITIES = [
    (-74.21, 10.920, "Tasajera",       "carretera"),
    (-74.20, 10.865, "Puebloviejo",    "carretera"),
    (-74.73, 10.836, "Caño Clarín",    "carretera"),
    (-74.66, 10.902, "Sevillano",      "carretera"),
    (-74.48, 10.930, "Nueva Venecia",  "palafitico"),
    (-74.58, 10.780, "Buenavista",     "palafitico"),
    (-74.37, 10.768, "Bcs. Aracataca", "palafitico"),
    (-74.55, 10.625, "Pivijay",        "suroccidente"),
]

# ---------------------------------------------------------------------------
# Zonas de análisis — coordenadas del centroide para el mapa
# ---------------------------------------------------------------------------
_ZONE_COORDS = {
    "Boca de la Barra / Zona Marina":               (-74.21, 11.01, "Boca\nde la Barra"),
    "Nueva Venecia – Palafíticos Norte":             (-74.48, 10.94, "N. Venecia\nNorte"),
    "Buenavista – Palafíticos Sur":                  (-74.58, 10.78, "Buena-\nvista Sur"),
    "Caño Clarín – Sector Carretera Norte":          (-74.70, 10.86, "Caño\nClarín"),
    "Tasajera / Puebloviejo – Sector Carretera Sur": (-74.22, 10.89, "Tasajera /\nPuebloviejo"),
    "Suroccidente – Pivijay / Santa Rita":           (-74.56, 10.63, "Suroc-\ncidente"),
}

# ---------------------------------------------------------------------------
# Puntos de pesca locales — memoria territorial de Sr. Adelmo (Tasajera)
# Fuente: trabajo de campo Seminario Aluna IA — mayo 2026.
# Coordenadas estimadas a partir del polígono de la CGSM y zonas de referencia.
# ---------------------------------------------------------------------------
_FISHING_POINT_COORDS: dict[str, tuple[float, float]] = {
    # Boca del Mar norte
    "Boquerón":                    (-74.21, 11.005),
    "Barra Vieja":                 (-74.20, 10.975),
    "Punta Blanca":                (-74.23, 10.965),
    "Punta Gruesa":                (-74.26, 10.950),
    # Orilla este / carretera sur
    "Rincón Cagao":                (-74.24, 10.908),
    "Tasajera":                    (-74.21, 10.922),
    "Majahualito":                 (-74.22, 10.878),
    "La Punta de Majahualito":     (-74.22, 10.862),
    "Flamenquito":                 (-74.23, 10.843),
    "Santa Rosa":                  (-74.24, 10.823),
    "Punta de Burro":              (-74.25, 10.800),
    "La Pared de Punta de Burro":  (-74.26, 10.788),
    "La Punta del Tambor":         (-74.27, 10.772),
    "Rincón del Hospitalito":      (-74.27, 10.758),
    "La Rinconá":                  (-74.28, 10.746),
    "Caimán":                      (-74.29, 10.734),
    "El Torno":                    (-74.30, 10.722),
    # Franja central-este
    "Río Frío":                    (-74.31, 10.948),
    "Las Palomas":                 (-74.36, 10.928),
    "López":                       (-74.40, 10.902),
    "Guapo":                       (-74.42, 10.882),
    "Bongo":                       (-74.38, 10.892),
    "La Punta de Chino":           (-74.33, 10.862),
    "Rincón de Chino":             (-74.34, 10.845),
    # Palafíticos norte (zona Nueva Venecia)
    "Boca del Pájaro":             (-74.40, 10.960),
    "Palancar":                    (-74.45, 10.958),
    "Los Micos":                   (-74.50, 10.950),
    "Los Medios":                  (-74.47, 10.924),
    "El Rincón de las Garzas":     (-74.54, 10.885),
    "Pancú":                       (-74.48, 10.978),
    "Riají":                       (-74.44, 10.940),
    "Palenque":                    (-74.52, 10.968),
    # Zona media / central
    "Palo Blanco":                 (-74.55, 10.865),
    "Los Murciélagos":             (-74.56, 10.840),
    "Los Muertos":                 (-74.48, 10.848),
    "La Ahuyama":                  (-74.50, 10.808),
    "El Chivato":                  (-74.47, 10.778),
    "Palo Quemado":                (-74.53, 10.672),
    # Palafíticos sur (zona Buenavista)
    "Las Mujeres":                 (-74.60, 10.822),
    "La Bodega":                   (-74.62, 10.793),
    "Rincón de Veranillo":         (-74.58, 10.762),
    "Caño Grande":                 (-74.67, 10.802),
    # Caño Clarín / carretera noroeste
    "Boca del Caño":               (-74.72, 10.852),
    "Punta del Caño":              (-74.71, 10.872),
    "Mahoma":                      (-74.64, 10.896),
    # Zona sur (Bocas de Aracataca)
    "Troja de Aracataca":          (-74.38, 10.742),
    "La Lata":                     (-74.42, 10.705),
    "Corralito":                   (-74.60, 10.635),
    "La Punta de Corralito":       (-74.62, 10.645),
    "Jaguey":                      (-74.52, 10.662),
    "La Punta de Jaguey":          (-74.51, 10.672),
}

# ---------------------------------------------------------------------------
# Paleta — estilo carta náutica oscura (original CienRayas)
# ---------------------------------------------------------------------------
_BG        = "#0b1826"   # fondo general (azul noche)
_PANEL_BG  = "#0d1b2a"   # panel de datos
_OCEAN     = "#12304d"   # Mar Caribe
_WATER     = "#1a5c8a"   # agua de la ciénaga
_LAND      = "#2d3d22"   # tierra
_LAND_EDGE = "#1e2c18"   # borde tierra
_RIVER     = "#1a7ab5"   # ríos y caños
_GRID      = "#ffffff"   # grilla

_SEMAPHORE_COLORS = {
    "verde":    "#2ecc71",
    "amarillo": "#f39c12",
    "rojo":     "#e74c3c",
}
_SEMAPHORE_LABELS = {
    "verde":    "VERDE — Buen dia pa' la faena",
    "amarillo": "PRECAUCION — Salir con cuidado",
    "rojo":     "NO SALIR — Quedate en tierra",
}

_IPP_CMAP = LinearSegmentedColormap.from_list(
    "ipp", ["#e74c3c", "#f39c12", "#2ecc71"]
)


def _ipp_color(score: float) -> str:
    rgba = _IPP_CMAP(score / 100)
    return "#{:02x}{:02x}{:02x}".format(
        int(rgba[0]*255), int(rgba[1]*255), int(rgba[2]*255)
    )


def _north_arrow(ax, x=0.955, y=0.935):
    ax.annotate(
        "N", xy=(x, y + 0.048), xycoords="axes fraction",
        ha="center", va="center", fontsize=9, fontweight="bold",
        color="white",
        path_effects=[pe.withStroke(linewidth=2, foreground=_BG)],
    )
    ax.annotate(
        "", xy=(x, y + 0.042), xytext=(x, y),
        xycoords="axes fraction", textcoords="axes fraction",
        arrowprops=dict(arrowstyle="-|>", color="white", lw=1.8),
    )


def _scale_bar(ax, lon_left=-74.88, lat_bot=10.44, length_deg=0.18):
    ax.plot([lon_left, lon_left + length_deg], [lat_bot, lat_bot],
            color="white", lw=2.5, solid_capstyle="butt", zorder=20)
    ax.plot([lon_left, lon_left],
            [lat_bot - 0.008, lat_bot + 0.008], color="white", lw=1.5, zorder=20)
    ax.plot([lon_left + length_deg, lon_left + length_deg],
            [lat_bot - 0.008, lat_bot + 0.008], color="white", lw=1.5, zorder=20)
    ax.text(lon_left + length_deg / 2, lat_bot - 0.020, "≈ 15 km",
            ha="center", va="top", color="white", fontsize=7,
            path_effects=[pe.withStroke(linewidth=1.5, foreground=_BG)], zorder=20)


def generate_map(
    semaphore_color: str,
    sst: float,
    chlorophyll: float,
    water_quality: dict | None = None,
    zone_ranking: list | None = None,
) -> str:
    sem_color = _SEMAPHORE_COLORS.get(semaphore_color, _SEMAPHORE_COLORS["verde"])

    fig = plt.figure(figsize=(8, 10.2), facecolor=_BG)

    # Mapa principal — el panel ocupa 30% abajo
    ax = fig.add_axes([0.05, 0.32, 0.90, 0.655])
    ax.set_facecolor(_OCEAN)
    ax.set_xlim(-74.92, -74.08)
    ax.set_ylim(10.40, 11.18)

    # --- Tierra base ---
    land = plt.Polygon(
        [[-74.92, 10.40], [-74.08, 10.40], [-74.08, 11.18],
         [-74.92, 11.18], [-74.92, 10.40]],
        closed=True, facecolor=_LAND, edgecolor="none", zorder=0,
    )
    ax.add_patch(land)

    # Mar Caribe (franja norte)
    mar = plt.Polygon(
        [[-74.92, 11.04], [-74.08, 11.04], [-74.08, 11.18], [-74.92, 11.18]],
        closed=True, facecolor=_OCEAN, alpha=0.85, zorder=1,
    )
    ax.add_patch(mar)
    ax.text(-74.50, 11.12, "MAR CARIBE",
            ha="center", va="center", color="#5dade2",
            fontsize=8.5, fontstyle="italic", fontweight="bold",
            alpha=0.85, zorder=2)

    # --- Ríos y caños ---
    for river in [_CANO_CLARIN, _RIO_FUNDACION, _RIO_ARACATACA, _RIO_SEVILLA]:
        ax.plot(river[:, 0], river[:, 1],
                color=_RIVER, lw=2.0, alpha=0.75, zorder=3,
                solid_capstyle="round")

    # --- Cuerpo de agua principal ---
    cienaga = MplPolygon(
        _CIENAGA, closed=True,
        facecolor=_WATER, edgecolor="#2a7ab8", linewidth=1.4,
        alpha=0.90, zorder=4,
    )
    ax.add_patch(cienaga)

    # Sombra interior (efecto profundidad)
    cienaga_shadow = MplPolygon(
        _CIENAGA, closed=True,
        facecolor="none", edgecolor="#1a5a80", linewidth=3.0,
        alpha=0.18, zorder=5,
    )
    ax.add_patch(cienaga_shadow)

    ax.text(-74.50, 10.84, "CIÉNAGA GRANDE\nDE SANTA MARTA",
            ha="center", va="center", color="white",
            fontsize=7.5, fontstyle="italic", alpha=0.35, zorder=5)

    # --- Todos los puntos de pesca locales (capa base) ---
    for pt_name, (lon, lat) in _FISHING_POINT_COORDS.items():
        ax.scatter(lon, lat, s=8, marker=".", color="#2a7ab8",
                   alpha=0.35, zorder=6, edgecolors="none")

    # --- Zonas coloreadas por IPP ---
    medals = ["①", "②", "③", "④", "⑤", "⑥"]

    if zone_ranking:
        for i, zone in enumerate(zone_ranking):
            coords = _ZONE_COORDS.get(zone["name"])
            if not coords:
                continue
            lon, lat, label = coords
            score = zone["score"]
            color = _ipp_color(score)
            is_best = (i == 0)

            size = 560 if is_best else 300
            lw   = 2.8 if is_best else 1.4
            edge = "white" if is_best else "#dddddd"

            ax.scatter(lon, lat, s=size, color=color, zorder=10,
                       edgecolors=edge, linewidths=lw, alpha=0.88)
            ax.text(lon, lat, medals[i],
                    ha="center", va="center",
                    color="white", fontsize=9 if is_best else 7,
                    fontweight="bold", zorder=11,
                    path_effects=[pe.withStroke(linewidth=1.5, foreground=color)])

            species_short = zone["species"][0] if zone["species"] else ""
            full_label = f"{label}\n{species_short}"
            offset = (10, -14) if is_best else (8, -11)
            ax.annotate(
                full_label, (lon, lat),
                xytext=offset, textcoords="offset points",
                color="white", fontsize=6.5,
                fontweight="bold" if is_best else "normal",
                zorder=12,
                bbox=dict(boxstyle="round,pad=0.25",
                          facecolor=_BG, edgecolor=color,
                          linewidth=0.9, alpha=0.85),
            )

        # --- Puntos de Adelmo: resaltar los de las mejores zonas ---
        for rank_idx, zone in enumerate(zone_ranking):
            pts = zone.get("local_points", [])
            zone_score = zone.get("score", 50)
            pt_color = _ipp_color(zone_score)
            is_best = (rank_idx == 0)

            for pt_idx, pt_name in enumerate(pts):
                coords_pt = _FISHING_POINT_COORDS.get(pt_name)
                if not coords_pt:
                    continue
                lon, lat = coords_pt

                if is_best:
                    ax.scatter(lon, lat, s=60, marker="D", color="gold",
                               edgecolors="#555500", linewidths=0.5,
                               zorder=15, alpha=0.96)
                    if pt_idx < 3:
                        ax.annotate(
                            pt_name, (lon, lat),
                            xytext=(6, 4), textcoords="offset points",
                            color="gold", fontsize=5.8, fontweight="bold",
                            zorder=16,
                            path_effects=[pe.withStroke(linewidth=2.0,
                                                         foreground=_BG)],
                        )
                elif rank_idx == 1:
                    ax.scatter(lon, lat, s=28, marker="o", color=pt_color,
                               edgecolors="white", linewidths=0.4,
                               zorder=13, alpha=0.75)
                else:
                    ax.scatter(lon, lat, s=15, marker="o", color=pt_color,
                               edgecolors="none", zorder=12, alpha=0.55)
    else:
        for name, (lon, lat, label) in _ZONE_COORDS.items():
            ax.scatter(lon, lat, s=300, color=sem_color, zorder=10,
                       edgecolors="white", linewidths=1.4, alpha=0.88)
            ax.annotate(label, (lon, lat), xytext=(8, 4),
                        textcoords="offset points",
                        color="#1a1a1a", fontsize=6.5, zorder=11,
                        bbox=dict(boxstyle="round,pad=0.2",
                                  facecolor="white", alpha=0.80))

    # --- Comunidades pesqueras ---
    for lon, lat, nombre, sector in _COMMUNITIES:
        ax.scatter(lon, lat, s=28, color="white", zorder=8,
                   marker="o", edgecolors="#aaaaaa", linewidths=0.6)
        ax.annotate(nombre, (lon, lat),
                    xytext=(5, 4), textcoords="offset points",
                    color="#dddddd", fontsize=6.0, zorder=9,
                    path_effects=[pe.withStroke(linewidth=1.8,
                                                 foreground=_BG)])

    # --- Leyenda ---
    legend_items = [
        mpatches.Patch(color=_ipp_color(87), label="Zona excelente"),
        mpatches.Patch(color=_ipp_color(60), label="Zona buena"),
        mpatches.Patch(color=_ipp_color(33), label="Zona regular"),
        mpatches.Patch(color="none", label=""),
        plt.Line2D([0], [0], marker="D", color="w", markerfacecolor="gold",
                   markersize=7, label="Punto de pesca ★"),
        plt.Line2D([0], [0], marker="s", color="w", markerfacecolor="#444444",
                   markersize=6, label="Comunidad pesquera"),
    ]
    leg = ax.legend(
        handles=legend_items, loc="upper left",
        facecolor=_BG, edgecolor="#5dade2",
        labelcolor="white", fontsize=7.0,
        framealpha=0.88, borderpad=0.7,
    )

    # --- Grilla, escala y norte ---
    ax.xaxis.set_major_locator(MultipleLocator(0.2))
    ax.yaxis.set_major_locator(MultipleLocator(0.1))
    ax.grid(True, color=_GRID, alpha=0.06, linestyle="--", linewidth=0.5)
    ax.tick_params(colors="#666666", labelsize=6.2, length=3)
    for spine in ax.spines.values():
        spine.set_edgecolor("#334455")
        spine.set_linewidth(0.8)

    _north_arrow(ax)
    _scale_bar(ax)

    today = datetime.now().strftime("%d %b %Y  %H:%M")
    ax.set_title(
        f"CienRayas  ·  Ciénaga Grande de Santa Marta\n{today}",
        color="white", fontsize=10.5, fontweight="bold",
        pad=9, loc="center",
        path_effects=[pe.withStroke(linewidth=2, foreground=_BG)],
    )

    # -----------------------------------------------------------------------
    # Panel de datos (abajo) — 30% del alto de la figura
    # -----------------------------------------------------------------------
    ax_panel = fig.add_axes([0.0, 0.0, 1.0, 0.30])
    ax_panel.set_facecolor(_PANEL_BG)
    ax_panel.axis("off")

    # Línea divisoria superior
    ax_panel.plot([0.02, 0.98], [0.965, 0.965], color="#3a5a80",
                  linewidth=1.5, transform=ax_panel.transAxes)

    # Líneas divisorias verticales entre columnas
    ax_panel.plot([0.33, 0.33], [0.06, 0.96], color="#2a4a6a",
                  linewidth=0.8, transform=ax_panel.transAxes, alpha=0.6)
    ax_panel.plot([0.66, 0.66], [0.06, 0.96], color="#2a4a6a",
                  linewidth=0.8, transform=ax_panel.transAxes, alpha=0.6)

    # --- Columna izquierda: Semáforo ---
    ax_panel.add_patch(mpatches.FancyBboxPatch(
        (0.025, 0.08), 0.28, 0.84,
        boxstyle="round,pad=0.015",
        facecolor=sem_color, alpha=0.18,
        transform=ax_panel.transAxes, zorder=1,
    ))
    ax_panel.add_patch(mpatches.FancyBboxPatch(
        (0.025, 0.08), 0.28, 0.84,
        boxstyle="round,pad=0.015",
        facecolor="none", edgecolor=sem_color, linewidth=1.4,
        transform=ax_panel.transAxes, zorder=2,
    ))
    ax_panel.text(0.165, 0.90, "SEMÁFORO DEL DÍA",
                  transform=ax_panel.transAxes, zorder=5,
                  ha="center", va="top", color="#d0dce8", fontsize=8.2,
                  fontweight="bold")
    # Círculo de color del semáforo
    circle = plt.Circle((0.165, 0.58), 0.075,
                         color=sem_color, zorder=3,
                         transform=ax_panel.transAxes)
    ax_panel.add_patch(circle)
    ax_panel.text(0.165, 0.58, semaphore_color[0].upper(),
                  transform=ax_panel.transAxes, zorder=6,
                  ha="center", va="center",
                  color="white", fontsize=16, fontweight="bold")
    label_sem = _SEMAPHORE_LABELS.get(semaphore_color, "")
    # Partir el label en dos líneas si es largo
    partes = label_sem.split(" — ", 1)
    ax_panel.text(0.165, 0.30, partes[0],
                  transform=ax_panel.transAxes, zorder=5,
                  ha="center", va="center",
                  color=sem_color, fontsize=9.5, fontweight="bold")
    if len(partes) > 1:
        ax_panel.text(0.165, 0.16, partes[1],
                      transform=ax_panel.transAxes, zorder=5,
                      ha="center", va="center",
                      color="#e8e8e8", fontsize=8.5)

    # --- Columna central: Condiciones del agua ---
    wq = water_quality or {}
    od     = wq.get("dissolved_oxygen", "–")
    sal    = wq.get("salinity", "–")
    season = {"seca": "Época seca", "lluvias": "Lluvias",
              "transicion": "Transición"}.get(wq.get("season", ""), "–")

    ax_panel.text(0.495, 0.90, "CONDICIONES DEL AGUA",
                  transform=ax_panel.transAxes, zorder=5,
                  ha="center", va="top", color="#d0dce8",
                  fontsize=8.2, fontweight="bold")

    data_lines = [
        ("Temp. agua:", f"{sst} °C"),
        ("Clorofila:",  f"{chlorophyll} mg/m³"),
        ("Oxígeno:",    f"{od} mg/L"),
        ("Salinidad:",  f"{sal} PSU"),
        ("Temporada:",  season),
    ]
    for j, (label, value) in enumerate(data_lines):
        y = 0.76 - j * 0.145
        ax_panel.text(0.350, y, label,
                      transform=ax_panel.transAxes, zorder=5,
                      ha="left", va="center",
                      color="#8aaabb", fontsize=8.5)
        ax_panel.text(0.635, y, value,
                      transform=ax_panel.transAxes, zorder=5,
                      ha="right", va="center",
                      color="#ffffff", fontsize=8.8, fontweight="bold")

    # --- Columna derecha: Top zonas con puntos locales ---
    ax_panel.text(0.830, 0.90, "TOP ZONAS HOY",
                  transform=ax_panel.transAxes, zorder=5,
                  ha="center", va="top", color="#d0dce8",
                  fontsize=8.2, fontweight="bold")

    if zone_ranking:
        medals_panel = ["★", "②", "③"]
        cols_puntos  = ["gold",     "#e8e8e8", "#b8c8d8"]
        cols_detalle = ["#c8a800",  "#8aaabb", "#607080"]
        for j, z in enumerate(zone_ranking[:3]):
            y = 0.74 - j * 0.22
            puntos  = " · ".join(z.get("local_points", [])[:2])
            especie = z["species"][0] if z["species"] else ""
            score   = z.get("score", 0)

            ax_panel.text(0.675, y, medals_panel[j],
                          transform=ax_panel.transAxes, zorder=5,
                          ha="left", va="center",
                          color=cols_puntos[j], fontsize=11,
                          fontweight="bold")
            ax_panel.text(0.710, y + 0.06, puntos,
                          transform=ax_panel.transAxes, zorder=5,
                          ha="left", va="center",
                          color=cols_puntos[j], fontsize=8.5,
                          fontweight="bold" if j == 0 else "normal")
            ax_panel.text(0.710, y - 0.05, f"{especie}  ({score:.0f}/100)",
                          transform=ax_panel.transAxes, zorder=5,
                          ha="left", va="center",
                          color=cols_detalle[j], fontsize=7.8)

    # Créditos
    ax_panel.plot([0.02, 0.98], [0.055, 0.055], color="#2a4a6a",
                  linewidth=0.6, transform=ax_panel.transAxes, alpha=0.5)
    ax_panel.text(0.50, 0.025,
                  "NASA · IDEAM · Open-Meteo · INVEMAR  |  Universidad del Magdalena",
                  transform=ax_panel.transAxes, zorder=5,
                  ha="center", va="center", color="#6080a0", fontsize=7.2)

    # -----------------------------------------------------------------------
    filename = f"mapa_{uuid.uuid4().hex[:8]}.png"
    filepath = Path(MEDIA_DIR) / filename
    Path(MEDIA_DIR).mkdir(exist_ok=True)

    plt.savefig(str(filepath), dpi=165, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    return filename
