import folium
import folium.plugins
import csv
from typing import List

# Project Imports
from logger import logger
from models import Faculty
from constants import (
    GEOLOCATION_FILE,
    BACKUP_GEOLOCATION_FILE,
    UTF_SIG_ENCODING,
    COUNTRY_INFO_INSTITUTION_KEY,
    UNIVERSITY_MAP_FILE,
)
from groups import AREA_GROUPS, CONFERENCE_MAP


def load_backup_university_locations_map() -> dict[str, tuple[float, float]]:
    uni_coords: dict[str, tuple[float, float]] = {}
    if not BACKUP_GEOLOCATION_FILE.exists():
        logger.debug("⚠️ Backup geolocation file does not exist.")
        return uni_coords

    with BACKUP_GEOLOCATION_FILE.open(encoding=UTF_SIG_ENCODING) as f:
        for row in csv.DictReader(f):
            uni: str = row[COUNTRY_INFO_INSTITUTION_KEY].strip()
            uni_coords[uni] = (
                float(row["latitude"]),
                float(row["longitude"]),
            )

    return uni_coords


def load_university_locations() -> dict[str, tuple[float, float]]:
    uni_coords: dict[str, tuple[float, float]] = {}
    with GEOLOCATION_FILE.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["institution"].strip()
            try:
                uni_coords[name] = (float(row["latitude"]), float(row["longitude"]))
            except ValueError:
                continue  # Skip invalid rows

    return uni_coords


def group_faculty_by_university(faculty_list: List[Faculty]):
    faculty_map: dict[str, list[Faculty]] = {}
    for faculty in faculty_list:
        key = faculty.affiliation.strip()
        if key not in faculty_map:
            faculty_map[key] = []
        faculty_map[key].append(faculty)
    return faculty_map


def get_top_area_group(matched_areas: List[str]) -> str:
    for area_group, subgroups in AREA_GROUPS.items():
        for meta in subgroups.values():
            if any(area in matched_areas for area in meta["subareas"]):
                return area_group
    return "Other"


def generate_university_map(faculty_list: List[Faculty]):
    # Load and merge geolocation data
    university_locations = load_university_locations()
    university_locations.update(load_backup_university_locations_map())

    # Initialize map
    folium_map = folium.Map(location=[20, 0], zoom_start=2)
    folium.plugins.Fullscreen(position="topright").add_to(folium_map)
    minimap = folium.plugins.MiniMap(toggle_display=True)
    folium_map.add_child(minimap)

    area_colors = {
        "AI": "green",
        "Systems": "blue",
        "Theory": "purple",
        "Interdisciplinary": "orange",
        "Other": "gray",
    }

    faculty_by_uni = group_faculty_by_university(faculty_list)

    # Create one FeatureGroup per area
    area_groups = {
        area: folium.FeatureGroup(name=f"{area} Universities") for area in area_colors
    }

    for g in area_groups.values():
        folium_map.add_child(g)

    # Cluster inside each group
    clusters = {
        k: folium.plugins.MarkerCluster(
            options={
                "spiderfyOnMaxZoom": True,
                "showCoverageOnHover": True,
                "zoomToBoundsOnClick": True,
            }
        )
        for k in area_groups
    }
    for k, v in clusters.items():
        area_groups[k].add_child(v)

    for uni, faculty_members in faculty_by_uni.items():
        coords = university_locations.get(uni)
        if not coords:
            logger.warning(f"⚠️ No coordinates for university: {uni}")
            continue

        # Collect all matched areas to determine dominant area group
        all_areas = {area for f in faculty_members for area in f.matched_areas}
        top_area = get_top_area_group(list(all_areas))
        icon_color = area_colors.get(top_area, "gray")

        # Popup HTML content
        html = '<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css">'
        html += """
            <div style='
                font-family: Arial, sans-serif;
                max-width: 350px;
                max-height: 300px;
                overflow-y: auto;
                padding-right: 8px;
            '>
            """
        html += f"<h4 style='margin-bottom: 0.5em;'>{uni}</h4><hr><ul style='padding-left: 1em;'>"

        for f in faculty_members:
            homepage = (
                f'<a href="{f.homepage}" target="_blank" style="color:#007BFF;text-decoration:none;">{f.name}</a>'
                if f.homepage
                else f"<span>{f.name} - {f.homepage}</span>"
            )
            area_names = [CONFERENCE_MAP.get(a.lower(), a) for a in f.matched_areas]
            area_str: str = "<br>".join(f"• {a}" for a in area_names)
            html += f"<li style='margin-bottom: 0.6em;'>"
            html += f"<strong>{homepage}</strong><br>"
            if f.dept:
                html += f"<small>{f.dept}</small><br>"
            html += f"<em style='font-size: 0.9em;'>{area_str}</em></li>"

        html += "</ul></div>"

        # Add markers to specific layers instead of global cluster
        clusters[top_area].add_child(
            folium.Marker(
                location=coords,
                popup=folium.Popup(html, max_width=400),
                tooltip=f"{uni} ({len(faculty_members)} faculty)",
                icon=folium.Icon(color=icon_color, icon="university", prefix="fa"),
            )
        )

    folium_map.add_child(folium.LayerControl(collapsed=False))

    folium_map.save(UNIVERSITY_MAP_FILE)  # type: ignore

    logger.info(f"🗺️  Map saved to {UNIVERSITY_MAP_FILE}")
