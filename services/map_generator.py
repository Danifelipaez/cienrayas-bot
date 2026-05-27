"""
Genera el mapa PNG de la Ciénaga Grande de Santa Marta.
Estilo cartografía natural (Natural Earth / QGIS) — matplotlib sin tiles.
"""
import threading
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

# Un solo thread genera el mapa a la vez — evita que 50 usuarios concurrentes
# lancen 50 generaciones matplotlib simultáneas (thundering herd)
_map_generation_lock = threading.Lock()

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


_map_cache_filename: str | None = None
_map_cache_ts: datetime | None = None
_MAP_CACHE_TTL_MINUTES = 10


def _cache_hit() -> str | None:
    """Retorna el filename cacheado si sigue vigente, o None."""
    if _map_cache_filename is not None and _map_cache_ts is not None:
        age = datetime.now() - _map_cache_ts
        if age.total_seconds() < _MAP_CACHE_TTL_MINUTES * 60:
            cached_path = Path(MEDIA_DIR) / _map_cache_filename
            if cached_path.exists():
                return _map_cache_filename
    return None


def generate_map(
    semaphore_color: str,
    sst: float,
    chlorophyll: float,
    water_quality: dict | None = None,
    zone_ranking: list | None = None,
) -> str:
    global _map_cache_filename, _map_cache_ts

    # Fast path: sin lock para no bloquear
    hit = _cache_hit()
    if hit:
        return hit

    with _map_generation_lock:
        # Re-check dentro del lock: otro thread puede haber generado mientras esperábamos
        hit = _cache_hit()
        if hit:
            return hit
        filename = _render_map(semaphore_color, sst, chlorophyll, water_quality, zone_ranking)
        _map_cache_filename = filename
        _map_cache_ts = datetime.now()
        return filename


def _render_map(
    semaphore_color: str,
    sst: float,
    chlorophyll: float,
    water_quality: dict | None = None,
    zone_ranking: list | None = None,
) -> str:
    """Genera el PNG del mapa sin tocar el caché — llamar solo desde dentro del lock."""
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



# ─────────────────────────────────────────────────────────────────────────────
# generar_mapa — versión mejorada: tile satelital + panel lateral (1000 × 600 px)
# ─────────────────────────────────────────────────────────────────────────────

_SEM_COL_V2 = {
    "verde":    "#00C851",
    "amarillo": "#FFB300",
    "rojo":     "#FF4444",
}


def _basemap_or_fallback(ax) -> None:
    """Tile CartoDB Dark Matter; si falla, polígonos oscuros hardcodeados."""
    ax.set_facecolor("#0d1b2a")
    try:
        import contextily as ctx
        ctx.add_basemap(
            ax,
            crs="EPSG:4326",
            source=ctx.providers.CartoDB.DarkMatter,
            zoom="auto",
            attribution=False,
        )
        return
    except Exception:
        pass

    # Fallback visual: tierra + cuerpo de agua a mano
    ax.add_patch(plt.Polygon(
        [[-74.9, 10.6], [-74.2, 10.6], [-74.2, 11.1], [-74.9, 11.1]],
        closed=True, facecolor="#2d3d22", edgecolor="none", zorder=0,
    ))
    ax.add_patch(MplPolygon(
        _CIENAGA, closed=True,
        facecolor="#1a5c8a", edgecolor="#2a7ab8",
        linewidth=1.0, alpha=0.88, zorder=2,
    ))
    for rv in [_CANO_CLARIN, _RIO_FUNDACION, _RIO_ARACATACA, _RIO_SEVILLA]:
        ax.plot(rv[:, 0], rv[:, 1],
                color="#1a7ab5", lw=1.4, alpha=0.6, zorder=3)
    ax.text(-74.55, 10.84, "CIÉNAGA GRANDE\nDE SANTA MARTA",
            ha="center", va="center", color="white",
            fontsize=6.5, fontstyle="italic", alpha=0.28, zorder=4)


def _north_arrow_v2(ax) -> None:
    """Flecha de norte en la esquina inferior derecha del eje del mapa."""
    ax.annotate(
        "N", xy=(0.955, 0.07), xycoords="axes fraction",
        ha="center", va="center", fontsize=8, fontweight="bold",
        color="white",
        path_effects=[pe.withStroke(linewidth=2, foreground="#0d1b2a")],
    )
    ax.annotate(
        "", xy=(0.955, 0.13), xytext=(0.955, 0.07),
        xycoords="axes fraction", textcoords="axes fraction",
        arrowprops=dict(arrowstyle="-|>", color="white", lw=1.4),
    )


def generar_mapa(zonas: list, condiciones: dict, fecha, out_path: str | None = None) -> str:
    """
    Mapa PNG mejorado de la CGSM con tile satelital y panel lateral de condiciones.

    Args:
        zonas:       [{nombre, lat, lon, semaforo, ipp}]
        condiciones: {sst, chl, viento_vel, viento_nombre, salinidad, od, luna}
        fecha:       datetime del pronóstico
        out_path:    ruta de salida; si None usa /tmp/mapa_cienrayas.png

    Returns:
        ruta absoluta al PNG generado
    """
    DPI = 150

    # Habilitar emojis si el sistema tiene Segoe UI Emoji (Win) o Noto (Linux)
    _prev_sans = matplotlib.rcParams.get("font.sans-serif", [])
    matplotlib.rcParams["font.sans-serif"] = [
        "DejaVu Sans", "Segoe UI Emoji", "Noto Color Emoji", "Noto Emoji",
    ] + list(_prev_sans)

    fig = plt.figure(figsize=(1000 / DPI, 600 / DPI),
                     dpi=DPI, facecolor="#1a1a2e")

    # ── Eje del mapa (izquierda ~64%) ─────────────────────────────────────────
    ax = fig.add_axes([0.01, 0.07, 0.63, 0.80])
    ax.set_xlim(-74.9, -74.2)
    ax.set_ylim(10.6, 11.1)
    ax.tick_params(colors="#4a5a6a", labelsize=5.5, length=2)
    for sp in ax.spines.values():
        sp.set_edgecolor("#2a3a4a")
        sp.set_linewidth(0.5)

    _basemap_or_fallback(ax)

    ax.xaxis.set_major_locator(MultipleLocator(0.2))
    ax.yaxis.set_major_locator(MultipleLocator(0.1))
    ax.grid(True, color="white", alpha=0.05, linestyle="--", linewidth=0.35)

    # Puntos de zonas — color semáforo, tamaño proporcional al IPP
    for zona in zonas:
        color  = _SEM_COL_V2.get(zona.get("semaforo", "verde"), "#00C851")
        ipp    = float(zona.get("ipp", 50))
        size   = 55 + (ipp / 100) * 270   # 55–325 pt²
        lon    = float(zona["lon"])
        lat    = float(zona["lat"])

        ax.scatter(lon, lat, s=size, c=color,
                   edgecolors="white", linewidths=0.9,
                   zorder=10, alpha=0.92)
        ax.annotate(
            str(zona["nombre"]), (lon, lat),
            xytext=(0, 9), textcoords="offset points",
            ha="center", va="bottom",
            color="white", fontsize=8, fontweight="bold", zorder=11,
            path_effects=[pe.withStroke(linewidth=2.0, foreground="#0d1b2a")],
        )

    _north_arrow_v2(ax)

    # ── Encabezado del mapa ───────────────────────────────────────────────────
    hora = fecha.strftime("%I:%M")
    ampm = "p.m." if fecha.hour >= 12 else "a.m."
    fstr = f"{fecha.strftime('%d %b %Y')} · {hora} {ampm}"

    fig.text(0.01, 0.990, "Mapa de zonas para hoy",
             color="white", fontsize=9.5, fontweight="bold",
             va="top", ha="left")
    fig.text(0.01, 0.945, "Ciénaga Grande de Santa Marta",
             color="#8aaabb", fontsize=7.5, va="top", ha="left")
    fig.text(0.01, 0.910, fstr,
             color="#607090", fontsize=6.5, va="top", ha="left")

    # ── Pie del mapa ──────────────────────────────────────────────────────────
    fig.text(0.01, 0.015, "Datos: NASA · IDEAM · clima en tiempo real",
             color="#5a6070", fontsize=6, va="bottom", ha="left")

    # ── Panel lateral (derecha ~33%) ──────────────────────────────────────────
    ax_p = fig.add_axes([0.655, 0.0, 0.335, 1.0])
    ax_p.axis("off")
    ax_p.set_xlim(0, 1)
    ax_p.set_ylim(0, 1)
    ax_p.set_facecolor("#13132a")
    ax_p.patch.set_alpha(0.87)

    # Borde izquierdo del panel (separador visual)
    ax_p.plot([0.0, 0.0], [0.0, 1.0],
              color="#2a3a5a", lw=1.5, transform=ax_p.transData, zorder=20)

    def T(x, y, s, **kw):  # texto en axes fraction del panel
        ax_p.text(x, y, s, transform=ax_p.transAxes, **kw)

    def H(y):  # separador horizontal
        ax_p.plot([0.05, 0.95], [y, y],
                  color="#2a3a5a", lw=0.7, transform=ax_p.transAxes)

    # Fecha/hora en el encabezado del panel
    T(0.5, 0.965, fstr,
      ha="center", va="top", color="#8aaabb",
      fontsize=7.0, fontweight="bold")
    H(0.910)

    # Sección Semáforo
    T(0.5, 0.897, "Semáforo",
      ha="center", va="top", color="white",
      fontsize=8.5, fontweight="bold")

    for k, (color, label) in enumerate([
        ("#00C851", "Buenas condiciones"),
        ("#FFB300", "Precaución"),
        ("#FF4444", "No salir hoy"),
    ]):
        y = 0.835 - k * 0.078
        T(0.11, y, "●", ha="center", va="center", color=color, fontsize=13)
        T(0.23, y, label, ha="left", va="center", color="white", fontsize=7.5)

    H(0.595)

    # Sección Condiciones ambientales
    T(0.5, 0.583, "Condiciones ambientales",
      ha="center", va="top", color="white",
      fontsize=8.0, fontweight="bold")

    sst  = condiciones.get("sst",           "–")
    chl  = condiciones.get("chl",           "–")
    vel  = condiciones.get("viento_vel",    "–")
    nom  = condiciones.get("viento_nombre", "viento")
    sal  = condiciones.get("salinidad",     "–")
    od   = condiciones.get("od",            "–")
    luna = condiciones.get("luna",          "–")

    # Símbolos DejaVu Sans (evita cuadros en sistemas sin fuentes emoji)
    rows = [
        ("⊙", "T. superficial:",  f"{sst}°C"),
        ("✦", "Clorofila:",       f"{chl} mg/m³"),
        ("≋", f"Viento ({nom}):", f"{vel} km/h"),
        ("◇", "Salinidad:",       f"{sal} PSU"),
        ("◉", "Oxígeno dis.:",   f"{od} mg/L"),
        ("☽", "Luna:",            str(luna)),
    ]
    for j, (icon, label, value) in enumerate(rows):
        y = 0.520 - j * 0.082
        T(0.06, y, icon,  ha="left",  va="center", fontsize=9.5)
        T(0.22, y, label, ha="left",  va="center", color="#8aaabb", fontsize=7.0)
        T(0.97, y, value, ha="right", va="center", color="white",
          fontsize=7.5, fontweight="bold")

    # ── Guardar ───────────────────────────────────────────────────────────────
    import tempfile
    out = out_path or str(Path(tempfile.gettempdir()) / "mapa_cienrayas.png")
    plt.savefig(out, dpi=DPI, bbox_inches=None,
                facecolor=fig.get_facecolor())
    plt.close(fig)
    return out
