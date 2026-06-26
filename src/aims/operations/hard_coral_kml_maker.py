import csv
import logging
import os

logger = logging.getLogger("")


def _sanitized_csv_dict_reader(csv_path):
    with open(csv_path, newline="", errors="replace") as csv_file:
        sanitized_lines = (line.replace("\0", "") for line in csv_file)
        yield from csv.DictReader(sanitized_lines)

# HC point count -> (KML aabbggrr color, percentage label)
_HC_STYLE = {
    0: ('ffffffff', '0%'),     # white
    1: ('ffcce6cc', '20%'),    # very light green
    2: ('ff99cc99', '40%'),    # light green
    3: ('ff66b366', '60%'),    # medium green
    4: ('ff339933', '80%'),    # green
    5: ('ff008000', '100%'),   # dark green
}

_HC_RGB = {
    0: (255, 255, 255),
    1: (204, 230, 204),
    2: (153, 204, 153),
    3: (102, 179, 102),
    4: (51, 153, 51),
    5: (0, 128, 0),
}

def _make_dot_png(output_path, rgb, size=24):
    """Generate a solid-color circle dot PNG. Returns True on success."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return False
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([0, 0, size - 1, size - 1], fill=rgb + (255,))
    img.save(output_path, "PNG")
    return True


def _make_legend_png(output_path):
    """Generate a legend PNG using Pillow. Returns True on success."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        logger.info("Pillow not available; skipping KML legend image")
        return False

    swatch = 18
    padding = 6
    row_height = swatch + padding
    title_height = 28
    width = 200
    height = title_height + len(_HC_STYLE) * row_height + padding

    img = Image.new("RGBA", (width, height), (30, 80, 160, 220))
    draw = ImageDraw.Draw(img)

    draw.text((padding, 5), "Hard Coral Cover", fill=(255, 255, 255, 255))

    for hc_count in range(6):
        rgb = _HC_RGB[hc_count]
        label = _HC_STYLE[hc_count][1]
        y = title_height + hc_count * row_height
        draw.rectangle([padding, y, padding + swatch, y + swatch], fill=rgb + (255,))
        draw.text(
            (padding + swatch + 6, y + 2),
            f"{hc_count} points  {label}",
            fill=(255, 255, 255, 255),
        )

    img.save(output_path, "PNG")
    return True


# Map pred_group values to column names for the per-image cover CSV
_GROUP_COL = {
    "Hard Coral":   "num_hard_coral",
    "Soft Coral":   "num_soft_coral",
    "Algae":        "num_algae",
    "Indeterminate": "num_indeterminate",
}
_OTHER_COL = "num_other"


def create_inference_kml(results_csv_file, image_dir, output_kml_file,
                         csv_output_path=None, cover_csv_path=None):
    """Create a KML file from inference results.

    Places one coloured circle per photo that has exactly 5 annotation rows.
    Circle colour reflects the number of those rows where pred_group == 'Hard Coral'.
    Latitude/longitude are sourced from photo_log.csv in image_dir.
    """
    import math
    import datetime

    def _safe_float(v):
        try:
            f = float(v)
            return None if math.isnan(f) else f
        except (TypeError, ValueError):
            return None

    # Read photo_log.csv for lat/lon/depth/timestamp keyed by filename
    photo_coords = {}
    photo_depth = {}      # basename -> (altitude_m, depth_m)
    photo_timestamp = {}  # basename -> ISO timestamp string
    photo_log_path = os.path.join(image_dir, "photo_log.csv")
    if os.path.exists(photo_log_path):
        for row in _sanitized_csv_dict_reader(photo_log_path):
            try:
                filename = row.get("filename_string")
                if not filename:
                    continue
                lat = float(row["latitude"])
                lon = float(row["longitude"])
                if lat != 0 and lon != 0:
                    photo_coords[filename] = (lat, lon)
                ping_raw = _safe_float(row.get("ping_depth"))
                pressure = _safe_float(row.get("pressure_depth"))
                altitude_m = ping_raw / 1000 if ping_raw is not None else None
                depth_m = (altitude_m + pressure) if (altitude_m is not None and pressure is not None) else None
                photo_depth[filename] = (altitude_m, depth_m)
                t_secs = _safe_float(row.get("time_secs"))
                t_msecs = _safe_float(row.get("time_msecs")) or 0
                if t_secs is not None:
                    dt = datetime.datetime.fromtimestamp(t_secs + t_msecs / 1000.0).astimezone()
                    photo_timestamp[filename] = dt.isoformat(timespec='milliseconds')
            except (TypeError, ValueError, KeyError):
                pass
    else:
        logger.warning("photo_log.csv not found at %s", photo_log_path)

    # Group results by image basename, tracking per-group counts
    _all_group_cols = list(_GROUP_COL.values()) + [_OTHER_COL]
    image_hc = {}  # basename -> {'total', 'hc', group counts ...}
    for row in _sanitized_csv_dict_reader(results_csv_file):
        image_path = row.get("image_path")
        if not image_path:
            continue
        basename = os.path.basename(image_path)
        if basename not in image_hc:
            image_hc[basename] = {"total": 0, "hc": 0, "path": image_path,
                                   **{c: 0 for c in _all_group_cols}}
        image_hc[basename]["total"] += 1
        group = (row.get("pred_group") or "").strip()
        col = _GROUP_COL.get(group, _OTHER_COL)
        image_hc[basename][col] += 1
        if group == "Hard Coral":
            image_hc[basename]["hc"] += 1

    # Optionally generate legend PNG in resources subfolder
    kml_dir = os.path.dirname(output_kml_file)
    resources_dir = os.path.join(kml_dir, "resources")
    os.makedirs(resources_dir, exist_ok=True)
    legend_png_path = os.path.join(resources_dir, "legend.png")
    has_legend = _make_legend_png(legend_png_path)

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<kml xmlns="http://www.opengis.net/kml/2.2">',
        "<Document>",
        "<name>Hard Coral Cover</name>",
    ]

    # Generate solid-color dot icons for each HC count
    icon_hrefs = {}
    for hc_count, rgb in _HC_RGB.items():
        dot_path = os.path.join(resources_dir, f'hc_dot_{hc_count}.png')
        if _make_dot_png(dot_path, rgb):
            icon_hrefs[hc_count] = f'resources/hc_dot_{hc_count}.png'
        else:
            icon_hrefs[hc_count] = 'http://maps.google.com/mapfiles/kml/shapes/shaded_dot.png'

    # One point icon style per HC count
    for hc_count, (color, _) in _HC_STYLE.items():
        parts += [
            f'<Style id="hc{hc_count}">',
            f'  <IconStyle><scale>0.8</scale>',
            f'    <Icon><href>{icon_hrefs[hc_count]}</href></Icon>',
            '  </IconStyle>',
            '  <LabelStyle><scale>0</scale></LabelStyle>',
            "</Style>",
        ]

    # Legend ScreenOverlay (top-right corner)
    if has_legend:
        parts += [
            "<ScreenOverlay>",
            "  <name>Hard Coral Cover Legend</name>",
            "  <Icon><href>resources/legend.png</href></Icon>",
            '  <overlayXY x="1" y="1" xunits="fraction" yunits="fraction"/>',
            '  <screenXY x="0.99" y="0.99" xunits="fraction" yunits="fraction"/>',
            '  <size x="0" y="0" xunits="fraction" yunits="fraction"/>',
            "</ScreenOverlay>",
        ]

    parts.append("<Folder><name>Photos</name>")

    placed = 0
    skipped_not_5 = 0
    skipped_no_coords = 0

    for basename, counts in image_hc.items():
        if counts["total"] != 5:
            skipped_not_5 += 1
            continue
        if basename not in photo_coords:
            skipped_no_coords += 1
            continue

        lat, lon = photo_coords[basename]
        hc_count = min(counts["hc"], 5)
        pct_label = _HC_STYLE[hc_count][1]
        altitude, depth = photo_depth.get(basename, (None, None))
        alt_str = f"{altitude:.2f}" if altitude is not None else "N/A"
        depth_str = f"{depth:.2f}" if depth is not None else "N/A"
        rel_img = os.path.relpath(os.path.join(image_dir, basename), kml_dir).replace("\\", "/")
        total = counts["total"]
        def _pct(n): return f"{round(n / total * 100, 1)}%" if total > 0 else "0%"
        description = (
            f'<![CDATA['
            f'<b>Hard Coral:</b> {counts["num_hard_coral"]}/{total} ({_pct(counts["num_hard_coral"])})<br/>'
            f'<b>Soft Coral:</b> {counts["num_soft_coral"]}/{total} ({_pct(counts["num_soft_coral"])})<br/>'
            f'<b>Algae:</b> {counts["num_algae"]}/{total} ({_pct(counts["num_algae"])})<br/>'
            f'<b>Indeterminate:</b> {counts["num_indeterminate"]}/{total} ({_pct(counts["num_indeterminate"])})<br/>'
            f'<b>Other:</b> {counts["num_other"]}/{total} ({_pct(counts["num_other"])})<br/>'
            f'<b>Latitude:</b> {lat:.6f}<br/>'
            f'<b>Longitude:</b> {lon:.6f}<br/>'
            f'<b>Altitude (metres):</b> {alt_str}<br/>'
            f'<b>Depth (metres):</b> {depth_str}<br/>'
            f'<img src="{rel_img}" width="400"/>'
            f']]>'
        )

        parts += [
            "<Placemark>",
            f"  <name>{basename}</name>",
            f"  <description>{description}</description>",
            f"  <styleUrl>#hc{hc_count}</styleUrl>",
            f"  <Point><coordinates>{lon},{lat},0</coordinates></Point>",
            "</Placemark>",
        ]
        placed += 1

    parts += ["</Folder>", "</Document>", "</kml>"]

    with open(output_kml_file, "w") as f:
        f.write("\n".join(parts))

    logger.info(
        "KML written to %s: %d placemarks, %d skipped (not 5 rows), %d skipped (no coords)",
        output_kml_file, placed, skipped_not_5, skipped_no_coords,
    )

    if csv_output_path:
        BENTHIC_COLS = [
            "image_name", "timestamp", "image_path", "point_num", "point_coordinate",
            "latitude", "longitude", "altitude_metres", "depth_metres",
            "pred_class", "pred_desc", "pred_group",
        ]
        csv_dir = os.path.dirname(csv_output_path)
        with open(csv_output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(BENTHIC_COLS)
            for row in _sanitized_csv_dict_reader(results_csv_file):
                image_path = row.get("image_path", "")
                basename = os.path.basename(image_path)
                rel_path = os.path.relpath(os.path.join(image_dir, basename), csv_dir).replace("\\", "/") if basename else ""
                lat, lon = photo_coords.get(basename, (None, None))
                altitude, depth = photo_depth.get(basename, (None, None))
                timestamp = photo_timestamp.get(basename, "")
                extra = {"image_path": rel_path, "image_name": basename,
                         "timestamp": timestamp, "latitude": lat,
                         "longitude": lon, "altitude_metres": altitude, "depth_metres": depth}
                merged = {**row, **extra}
                writer.writerow([merged.get(c, "") for c in BENTHIC_COLS])
        logger.info("benthic_points.csv written to %s", csv_output_path)

    if cover_csv_path:
        COVER_COLS = [
            "image_name", "timestamp", "image_path", "latitude", "longitude",
            "altitude_metres", "depth_metres",
            "num_hard_coral", "num_soft_coral", "num_algae",
            "num_indeterminate", "num_other", "num_total_points",
            "perc_hard_coral", "perc_soft_coral", "perc_algae",
            "perc_indeterminate", "perc_other",
        ]
        cover_dir = os.path.dirname(cover_csv_path)
        with open(cover_csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(COVER_COLS)
            for basename, counts in image_hc.items():
                if counts["total"] != 5:
                    continue
                lat, lon = photo_coords.get(basename, (None, None))
                altitude, depth = photo_depth.get(basename, (None, None))
                timestamp = photo_timestamp.get(basename, "")
                rel_path = os.path.relpath(os.path.join(image_dir, basename), cover_dir).replace("\\", "/")
                total = counts["total"]
                def _p(n): return round(n / total * 100, 1) if total > 0 else 0
                writer.writerow([
                    basename, timestamp, rel_path, lat, lon,
                    altitude, depth,
                    counts["num_hard_coral"], counts["num_soft_coral"],
                    counts["num_algae"], counts["num_indeterminate"],
                    counts["num_other"], total,
                    _p(counts["num_hard_coral"]), _p(counts["num_soft_coral"]),
                    _p(counts["num_algae"]), _p(counts["num_indeterminate"]),
                    _p(counts["num_other"]),
                ])
        logger.info("benthic_cover.csv written to %s", cover_csv_path)