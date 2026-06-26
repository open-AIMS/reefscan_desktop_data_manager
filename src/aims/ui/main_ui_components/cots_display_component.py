import logging
import os

from PyQt5.QtCore import QObject, QItemSelection, Qt, QRect, QByteArray
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QImage, QPixmap, QPainter, QPen, QColor, QFont, QBitmap, \
    qRgb, QKeySequence
from PyQt5.QtWidgets import QHeaderView, QTableView, QAbstractItemView, QLabel, QCheckBox, QSizePolicy, QComboBox, \
    QShortcut, QFileDialog
from photoenhancer.photoenhance import processImage, EnhancerParameters
from reefscanner.basic_model.model_utils import replace_last

from aims import utils
from aims.model.cots_detection import CotsDetection
from aims.model.image_with_score import ImageWithScore
from aims.model.proportional_rectangle import ProportionalRectangle

from functools import partial

# This class handles the visualisation of COTS detections as a table
# it shows photos of COTS for each COTS sequence
from aims.ui.photo_viewer import PhotoViewer
from aims.utils import read_binary_file_support_samba
logger = logging.getLogger("CotsDisplayComponent")


class CotsDisplayComponent(QObject):
    def __init__(self, cots_widget, cots_display_params):
        super().__init__()
        self.cots_widget = cots_widget
        self.item_model = QStandardItemModel(self)
        self.photos=None
        self.selected_photo = 0
        self.sequence_id = None
        self.cots_widget.button_next.clicked.connect(self.next)
        self.cots_widget.button_previous.clicked.connect(self.previous)
        self.cots_widget.highlight_scars_check_box.stateChanged.connect(self.redraw_photo)
        self.cots_widget.refreshButton.clicked.connect(self.create_cots_detections_table)
        self.cots_widget.openPhotoButton.clicked.connect(self.open_photo)
        self.cots_display_params = cots_display_params
        self.current_row = None

        self.cots_widget.button_yes.clicked.connect(partial(self.confirm_cots_detection, True))
        self.cots_widget.button_no.clicked.connect(partial(self.confirm_cots_detection, False))
        self.cots_widget.enhance_check_box.stateChanged.connect(self.enhance_check_box_state_changed)
        self.enhance_parameters = EnhancerParameters()
        self.enhance_parameters.dehazing = False
        self.enhance_parameters.denoising = False
        self.enhanced = False

        by_class_combo_box: QComboBox = self.cots_widget.filter_by_class_combo_box
        by_class_combo_box.addItem(self.tr("Show COTS and Scars"), userData="both")
        by_class_combo_box.addItem(self.tr("Show COTS"), userData="COTS")
        by_class_combo_box.addItem(self.tr("Show Scars"), userData="Scars")
        by_class_combo_box.setCurrentText(cots_display_params.by_class)

        camera_combo_box: QComboBox = self.cots_widget.camera_combo_box
        camera_combo_box.addItem(self.tr("Camera 1"), userData="cam_1")
        camera_combo_box.addItem(self.tr("Camera 2"), userData="cam_2")

        table_view: QTableView = self.cots_widget.tableView
        table_view.setModel(self.item_model)
        table_view.setSelectionMode(QAbstractItemView.SingleSelection)
        table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table_view.selectionModel().currentChanged.connect(self.selection_changed)

        self.shortcut1 = QShortcut(QKeySequence("F1"), self.cots_widget)
        self.shortcut1.activated.connect(partial(self.confirm_cots_detection, True))
        self.shortcut2 = QShortcut(QKeySequence("F2"), self.cots_widget)
        self.shortcut2.activated.connect(partial(self.confirm_cots_detection, False))
        self.shortcut3 = QShortcut(QKeySequence("F3"), self.cots_widget)
        self.shortcut3.activated.connect(self.toggle_highlight_scars)
        self.shortcut4= QShortcut(QKeySequence("F4"), self.cots_widget)
        self.shortcut4.activated.connect(self.toggle_enhance)

        self.cots_widget.exportButton.clicked.connect(self.export)

    def toggle_highlight_scars(self):
        print ("toggle highlight")
        check_box:QCheckBox = self.cots_widget.highlight_scars_check_box
        self.toggle_check_box(check_box)

    def toggle_enhance(self):
        print ("toggle enhance")
        check_box:QCheckBox = self.cots_widget.enhance_check_box
        self.toggle_check_box(check_box)

    def toggle_check_box(self, check_box:QCheckBox):
        if check_box.checkState() == Qt.Checked:
            check_box.setCheckState(Qt.Unchecked)
        else:
            check_box.setCheckState(Qt.Checked)
        self.redraw_photo()

    def confirmed_field_to_string(self, cots_detection: CotsDetection):
        if cots_detection.confirmed is None:
            confirmed_string = ''
        else:
            if cots_detection.confirmed:
                confirmed_string = 'Yes'
            else:
                confirmed_string = 'No'
        return confirmed_string


    def show(self):
        if self.cots_display_params.eod:
            self.cots_widget.eod_check_box.setCheckState(Qt.Checked)
        else:
            self.cots_widget.eod_check_box.setCheckState(Qt.Unchecked)

        if self.cots_display_params.only_show_confirmed:
            self.cots_widget.confirmed_check_box.setCheckState(Qt.Checked)
        else:
            self.cots_widget.confirmed_check_box.setCheckState(Qt.Unchecked)

        self.cots_widget.minimumScoreTextBox.setText(str(self.cots_display_params.minimum_score))
        self.create_cots_detections_table()
        self.cots_widget.graphicsView.setVisible(False)

    def include_row(self, row: CotsDetection):
        class_to_show = self.cots_widget.filter_by_class_combo_box.currentData(role=Qt.UserRole)
        include = True
        if class_to_show == "COTS":
            include = include and row.best_class_id == 0

        if class_to_show == "Scars":
            include = include and row.best_class_id == 1

        include = include and (row.best_score > self.cots_display_params.minimum_score)

        return include


    def create_cots_detections_table(self):
        eod_check_box: QCheckBox = self.cots_widget.eod_check_box
        self.cots_display_params.eod = eod_check_box.checkState() == Qt.Checked
        camera = self.cots_widget.camera_combo_box.currentData(role=Qt.UserRole)
        self.cots_display_params.camera = camera

        self.cots_display_params.only_show_confirmed = self.cots_widget.confirmed_check_box.checkState() == Qt.Checked

        try:
            self.cots_display_params.minimum_score = float(self.cots_widget.minimumScoreTextBox.text())
        except Exception as e:
            logger.warn(f"error getting minimum score: {e}")
            self.cots_display_params.minimum_score = 0

        self.item_model.clear()
        self.item_model.setHorizontalHeaderLabels(["Sequence", "Class", "Score", "Confirmed"])

        if self.cots_display_params.cots_detection_list().has_data:
            self.clear_photo()
            row: CotsDetection
            for row in self.cots_display_params.cots_detection_list().cots_detections_list:
                if self.include_row(row):
                    display_row = self.cots_display_params.only_show_confirmed and row.confirmed or not self.cots_display_params.only_show_confirmed
                    if display_row:
                        sequence_id_item = QStandardItem(str(row.sequence_id))
                        class_item = QStandardItem(str(row.best_class))
                        score_item = QStandardItem(str(row.best_score))
                        confirmed_item = QStandardItem(self.confirmed_field_to_string(row))
                        sequence_id_item.setData(row, Qt.UserRole)
                        class_item.setData(row, Qt.UserRole)
                        score_item.setData(row, Qt.UserRole)
                        confirmed_item.setData(row, Qt.UserRole)
                        self.item_model.appendRow([sequence_id_item,
                                                    class_item,
                                                    score_item,
                                                    confirmed_item
                                                    ])



    # When the user selects a row in the table, the photos for that sequence are displayed
    def selection_changed(self, current, previous):
        self.set_enhanced_false()

        current_data: CotsDetection = self.item_model.data(current, Qt.UserRole)
        self.current_row = current.row()
        self.sequence_id = current_data.sequence_id
        self.photos = current_data.images
        self.selected_photo = 0
        self.show_photo()

    def set_enhanced_false(self):
        self.enhanced = False
        self.cots_widget.enhance_check_box.setCheckState(Qt.Unchecked)

    # TODO not working need to google this when I have internet
    def clear_photo(self):
        table_view:QTableView = self.cots_widget.tableView
        table_view.sizePolicy().setVerticalPolicy(QSizePolicy.Policy.Expanding)
        self.cots_widget.graphicsView.setVisible(False)
        self.cots_widget.button_next.setVisible(False)
        self.cots_widget.button_previous.setVisible(False)

    # Redraw the photo at the current zoom leve. This is for toggling scars off and on
    def redraw_photo(self):
        self.show_photo(retain_zoom=True)

    # Show the current photo, highlight the COTS and enable the appropriate buttons
    # This could be from the disk or the camera so we need to allow for that
    def show_photo(self, retain_zoom = False):
        if self.photos is None:
            return

        table_view:QTableView = self.cots_widget.tableView
        table_view.sizePolicy().setVerticalPolicy(QSizePolicy.Policy.Preferred)
        graphics_view:PhotoViewer = self.cots_widget.graphicsView
        graphics_view.setVisible(True)
        self.cots_widget.button_next.setVisible(True)
        self.cots_widget.button_previous.setVisible(True)


        photo = self.photos[self.selected_photo].path
        if self.enhanced:
            photo_to_show = self.enhanced_photo(photo)
        else:
            photo_to_show = photo

        graphicsView: QLabel = graphics_view

        image = self.qimage_from_filename(photo_to_show)
        image_width = image.width()
        image_height = image.height()
        pixmap = QPixmap.fromImage(image)

        # Get rectangles for all the COTS in the photo
        rectangles = self.cots_display_params.cots_detection_list().image_rectangles_by_filename.get(photo)
        if rectangles is not None:
            self.draw_rectangles(pixmap, image_height, image_width, rectangles)

        print("photo")
        print(photo)
        scar_overlay_file = self.cots_display_params.cots_detection_list().get_scar_mask_file(photo)
        print(scar_overlay_file)
        if self.cots_widget.highlight_scars_check_box.checkState() == Qt.Checked:
            pixmap = self.highlight_scars(pixmap, image_height, image_width, scar_overlay_file)

        if retain_zoom:
            graphics_view.setPhotoRetainZoom(pixmap)
        else:
            graphics_view.setPhoto(pixmap)

        graphics_view.show()

        # enable appropriate buttons
        self.cots_widget.button_next.setEnabled(self.selected_photo < len(self.photos)-1)
        self.cots_widget.button_previous.setEnabled(self.selected_photo > 0)

    def qimage_from_filename(self, photo):
        file_contents = self.image_contents_from_filename(photo)
        image = QImage()
        image.loadFromData(file_contents, format='JPG')
        return image

    def image_contents_from_filename(self, photo):
        file_contents: bytes = read_binary_file_support_samba(photo,
                                                              self.cots_display_params.cots_detection_list().samba)
        return file_contents

    def highlight_scars(self, main_pixmap, image_height, image_width, scar_mask_file):
        if scar_mask_file is not None and os.path.exists(scar_mask_file):
            contents = self.image_contents_from_filename(scar_mask_file)
            mask_image = QImage(contents, 168, 96, QImage.Format_Indexed8)
            mask_image.loadFromData(contents)
            mask_image = mask_image.convertToFormat(QImage.Format_ARGB32);
            colors = {}
            for x in range(mask_image.width()):
                for y in range(mask_image.height()):
                    pixelColor = QColor(mask_image.pixel(x, y));
                    color = pixelColor.red()
                    if color < 10:
                        mask_image.setPixel(x, y, QColor(0,0,0,0).rgba())
                    else:
                        whiteness = 50-color
                        if whiteness <0:
                            whiteness = 0
                        mask_image.setPixel(x, y, QColor(255,whiteness, whiteness,70).rgba())

                    if color in colors:
                        c =colors[color]+1
                    else:
                        c=1
                    colors[color] = c
            print(colors)
            mask_image = mask_image.scaled(image_width, image_height)
            result = QPixmap(mask_image.width(), mask_image.height())
            result.fill(Qt.transparent)
            painter = QPainter(result)
            painter.drawPixmap(0, 0, main_pixmap)
            painter.drawImage(0, 0, mask_image)
            return result
        else:
            return main_pixmap


# open the photo in the OS
    def open_photo(self):
        if self.photos is None:
            return

        photo:ImageWithScore = self.photos[self.selected_photo]
        utils.open_file(photo.path)

    # Draw the rectangles over the photo
    # The cots for the current sequence will have a red rectangle. Yellow rectangles for the others
    # solid lines for real detections dotted lines for phantom detections
    def draw_rectangles(self, pixmap, image_height, image_width, proportional_rectangles):
        painter = QPainter()
        painter.begin(pixmap)
        pen = QPen(Qt.red)
        pen.setWidth(15)
        pen.setStyle(Qt.SolidLine)
        painter.setPen(pen)
        rectangle: ProportionalRectangle
        for proportional_rectangle in proportional_rectangles:
            if proportional_rectangle.sequence_id == self.sequence_id:
                if self.get_confirmed_current_selection():
                    pen.setColor(Qt.green)
                else:
                    pen.setColor(Qt.red)
            else:
                pen.setColor(Qt.yellow)

            if proportional_rectangle.phantom:
                pen.setStyle(Qt.DotLine)
            else:
                pen.setStyle(Qt.SolidLine)
            painter.setPen(pen)
            painter.drawRect(self.make_rect(proportional_rectangle, image_width, image_height))
        painter.end()
        return pixmap

    # makes a rectangle of pixel values (integers) given a rectangle of proportions and the dimensions of the image
    def make_rect (self, proportional_rectangle: ProportionalRectangle, image_width: int, image_height: int) -> QRect:
        left = round(proportional_rectangle.left * image_width)
        top = round(proportional_rectangle.top * image_height)
        width = round(proportional_rectangle.width * image_width)
        height = round(proportional_rectangle.height * image_height)
        return QRect(left, top, width, height)


    def next(self):
        self.selected_photo += 1
        self.set_enhanced_false()
        self.show_photo()

    def previous(self):
        self.selected_photo -= 1
        self.set_enhanced_false()
        self.show_photo()

    def confirm_cots_detection(self, confirmed):
        cots_detection_list = self.cots_display_params.cots_detection_list()
        selected_detection_idx = cots_detection_list.get_index_by_sequence_id(self.sequence_id)

        if selected_detection_idx is not None:
            current_detection = cots_detection_list.cots_detections_list[selected_detection_idx]
            current_detection.confirmed = confirmed
            confirmed_item = QStandardItem(self.confirmed_field_to_string(current_detection))
            confirmed_item.setData(current_detection, Qt.UserRole)
            self.item_model.setItem(self.current_row, 3, confirmed_item)

            if self.current_selection_is_confirmed():
                is_eod = self.cots_widget.eod_check_box.checkState() == Qt.Checked
                cots_detection_list.write_confirmed_field_to_cots_sequence()


    def current_selection_is_confirmed(self):
        return self.get_confirmed_current_selection() is not None

    def get_confirmed_current_selection(self):
        cots_detection_list = self.cots_display_params.cots_detection_list()

        selected_detection_idx = cots_detection_list.get_index_by_sequence_id(self.sequence_id)
        return cots_detection_list.cots_detections_list[selected_detection_idx].confirmed

    def enhance_check_box_state_changed(self, state):
        if state == 2: # 2 = Checked, 0 = Unchecked
            self.enhanced = True
        else:
            self.enhanced = False
        self.show_photo(retain_zoom=True)

    def enhanced_photo(self, photo):
        enhanced_photo =  replace_last(photo, "/reefscan/", "/reefscan_enhanced/")
        enhanced_photo = enhanced_photo.replace(".jpg", "__enh.jpg")
        if not os.path.exists(enhanced_photo):
            directory = os.path.dirname(enhanced_photo)
            os.makedirs(directory, exist_ok=True)
            processImage(photo, enhanced_photo, self.enhance_parameters)

        return enhanced_photo

    def export(self):
        import csv
        import simplekml

        detection_list = self.cots_display_params.cots_detection_list()

        # Build suggested output folder from survey folder
        suggested_folder = ""
        if detection_list.folder:
            survey_folder = os.path.dirname(detection_list.folder).replace("\\", "/")
            modified = replace_last(survey_folder, "/reefscan/", "/reefscan_results/")
            base = modified + "/cots_detections"
            suggested_folder = base
            if os.path.exists(suggested_folder):
                i = 1
                while os.path.exists(f"{suggested_folder}_{i}"):
                    i += 1
                suggested_folder = f"{suggested_folder}_{i}"

        # Pre-create the suggested folder so the dialog opens directly inside it.
        # QFileDialog ignores a non-existent directory parameter.
        if suggested_folder:
            os.makedirs(suggested_folder, exist_ok=True)
            start_dir = suggested_folder
        elif detection_list.folder:
            start_dir = survey_folder
        else:
            start_dir = ""

        output_folder = QFileDialog.getExistingDirectory(
            self.cots_widget,
            'Choose folder to export COTS detections to',
            directory=start_dir
        )

        if not output_folder:
            return

        os.makedirs(output_folder, exist_ok=True)

        # Build lat/lon lookup: sequence_id -> (lat, lon) from the waypoints list
        latlon_by_sequence = {}
        for wp in detection_list.cots_waypoints:
            lat, lon, seq_str = wp[0], wp[1], wp[2]
            seq_str_values = seq_str.replace("sequences: ", "")
            seq_ids = [int(s.strip()) for s in seq_str_values.split(",") if s.strip().replace("-", "").isdigit()]
            for sid in seq_ids:
                latlon_by_sequence[sid] = (lat, lon)

        # Build depth/timestamp lookup from photo_log.csv: filename_string -> (altitude_m, depth_m, timestamp)
        import pandas as pd
        import math
        import datetime
        depth_by_filename = {}
        timestamp_by_filename = {}
        photo_log_path = detection_list.folder + "/photo_log.csv"
        if os.path.exists(photo_log_path):
            try:
                photo_log_df = pd.read_csv(photo_log_path)
                for _, row in photo_log_df.iterrows():
                    fname = str(row.get("filename_string", ""))
                    def _safe(v):
                        try:
                            f = float(v)
                            return None if math.isnan(f) else f
                        except (TypeError, ValueError):
                            return None
                    ping_raw = _safe(row.get("ping_depth"))
                    pressure = _safe(row.get("pressure_depth"))
                    altitude_m = ping_raw / 1000 if ping_raw is not None else None
                    depth_m = (altitude_m + pressure) if (altitude_m is not None and pressure is not None) else None
                    depth_by_filename[fname] = (altitude_m, depth_m)
                    t_secs = _safe(row.get("time_secs"))
                    t_msecs = _safe(row.get("time_msecs")) or 0
                    if t_secs is not None:
                        dt = datetime.datetime.fromtimestamp(t_secs + t_msecs / 1000.0).astimezone()
                        timestamp_by_filename[fname] = dt.isoformat(timespec='milliseconds')
            except Exception as e:
                logger.warning(f"Could not read photo_log.csv for depth data: {e}")

        # Build set of sequence_ids that pass the current filter criteria
        included_sequence_ids = {
            det.sequence_id
            for det in detection_list.cots_detections_list
            if self.include_row(det)
        }

        # Build per-detection rows with best photo resolved
        export_rows = []
        for det in detection_list.cots_detections_list:
            if self.include_row(det):
                confirmed_str = ""
                if det.confirmed is not None:
                    confirmed_str = "Yes" if det.confirmed else "No"
                lat, lon = latlon_by_sequence.get(det.sequence_id, (None, None))
                best_image = max(det.images, key=lambda img: img.score) if det.images else None
                best_photo = best_image.path if best_image else None
                all_rects = detection_list.image_rectangles_by_filename.get(best_photo, []) if best_photo else []
                cots_in_photo = len([r for r in all_rects if r.sequence_id in included_sequence_ids]) if best_photo else None
                fname_key = os.path.basename(best_photo) if best_photo else None
                altitude, depth = depth_by_filename.get(fname_key, (None, None))
                export_rows.append((det, lat, lon, best_photo, confirmed_str, cots_in_photo, altitude, depth))

        # Export KML
        from PIL import Image, ImageDraw

        COTS_COLOR = simplekml.Color.red
        SCAR_COLOR = "ff00a5ff"  # orange in KML AABBGGRR format

        kml = simplekml.Kml()
        cots_folder = kml.newfolder(name="cots")
        for det, lat, lon, best_photo, confirmed_str, cots_in_photo, altitude, depth in export_rows:
            if lat is not None and lon is not None:
                pnt = cots_folder.newpoint(name="", coords=[(lon, lat)])
                pnt.style.iconstyle.icon.href = 'https://maps.google.com/mapfiles/kml/paddle/wht-blank.png'
                pnt.style.iconstyle.color = COTS_COLOR if det.best_class_id == 0 else SCAR_COLOR
                alt_str = f"{altitude:.2f}" if altitude is not None else "N/A"
                depth_str = f"{depth:.2f}" if depth is not None else "N/A"
                if best_photo:
                    rel_photo = os.path.relpath(best_photo, output_folder)
                    rel_photo_uri = rel_photo.replace("\\", "/")
                    pnt.description = (
                        f"<![CDATA["
                        f"<img src=\"{rel_photo_uri}\" width=\"400\"/><br/>"
                        f"<b>Class:</b> {det.best_class}<br/>"
                        f"<b>Confidence Score:</b> {det.best_score:.4f}<br/>"
                        f"<b>COTS in photo:</b> {cots_in_photo}<br/>"
                        f"<b>Altitude (metres):</b> {alt_str}<br/>"
                        f"<b>Depth (metres):</b> {depth_str}<br/>"
                        f"<b>Photo:</b> {rel_photo}"
                        f"]]>"
                    )
                else:
                    pnt.description = (
                        f"<![CDATA["
                        f"<b>Class:</b> {det.best_class}<br/>"
                        f"<b>Confidence Score:</b> {det.best_score:.4f}<br/>"
                        f"<b>Altitude (metres):</b> {alt_str}<br/>"
                        f"<b>Depth (metres):</b> {depth_str}"
                        f"]]>"
                    )

        # Create and save legend image
        legend_img = Image.new("RGBA", (180, 90), (255, 255, 255, 220))
        draw = ImageDraw.Draw(legend_img)
        draw.text((10, 8), "Legend", fill=(0, 0, 0))
        draw.rectangle([15, 30, 35, 50], fill=(255, 0, 0), outline=(0, 0, 0))
        draw.text((45, 35), "COTS", fill=(0, 0, 0))
        draw.rectangle([15, 58, 35, 78], fill=(255, 165, 0), outline=(0, 0, 0))
        draw.text((45, 63), "Scar", fill=(0, 0, 0))
        legend_img.save(os.path.join(output_folder, "legend.png"))

        # Pin legend to top-left corner as a screen overlay
        screen = kml.newscreenoverlay(name="Legend")
        screen.icon.href = "legend.png"
        screen.overlayxy = simplekml.OverlayXY(x=0, y=1, xunits=simplekml.Units.fraction, yunits=simplekml.Units.fraction)
        screen.screenxy = simplekml.ScreenXY(x=0.01, y=0.99, xunits=simplekml.Units.fraction, yunits=simplekml.Units.fraction)
        screen.size = simplekml.Size(x=0, y=0, xunits=simplekml.Units.fraction, yunits=simplekml.Units.fraction)

        kml.save(os.path.join(output_folder, "cots_detections.kml"))

        # Open the output folder in file explorer
        utils.open_file(output_folder)

        # Export CSV
        csv_path = os.path.join(output_folder, "cots_detections.csv")
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["image_name", "timestamp", "image_path", "latitude", "longitude",
                             "altitude_metres", "depth_metres", "sequence_id", "class",
                             "confidence_score", "cots_in_photo", "confirmed"])
            for det, lat, lon, best_photo, confirmed_str, cots_in_photo, altitude, depth in export_rows:
                image_name = os.path.basename(best_photo) if best_photo else None
                rel_photo = os.path.relpath(best_photo, output_folder) if best_photo else None
                timestamp = timestamp_by_filename.get(image_name, "") if image_name else ""
                confirmed_out = confirmed_str if confirmed_str else "Unassessed"
                writer.writerow([image_name, timestamp, rel_photo, lat, lon, altitude, depth,
                                 det.sequence_id, det.best_class, det.best_score, cots_in_photo, confirmed_out])

        # Export YAML config
        config = {
            "eod": bool(self.cots_display_params.eod),
            "only_show_confirmed": bool(self.cots_display_params.only_show_confirmed),
            "camera": self.cots_display_params.camera,
            "minimum_score": float(self.cots_display_params.minimum_score),
            "by_class": self.cots_widget.filter_by_class_combo_box.currentData(role=Qt.UserRole),
        }
        yaml_path = os.path.join(output_folder, "export_parameters.yaml")
        with open(yaml_path, 'w') as f:
            for key, value in config.items():
                f.write(f"{key}: {value}\n")


