import logging
import os

from PyQt5 import uic
from PyQt5.QtCore import Qt

from PyQt5.QtCore import QObject
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QCheckBox, QComboBox, QFileDialog
from reefscanner.basic_model.photo_csv_maker import track
from reefscanner.basic_model.survey import Survey

from aims.state import state
from aims.ui.main_ui_components.utils import clearLayout
from aims.ui.map_html import map_html_str
logger = logging.getLogger("MapComponent")


def parse_sequences_string_to_sequence_ids(seq_str):
    seq_str_values = seq_str.replace("sequences: ", "")
    seq_id_list = [int(id.strip()) for id in seq_str_values.split(",") if id.strip().replace("-", "").isdigit()]
    return seq_id_list


class MapComponent(QObject):
    def __init__(self, parent_widget, cots_display_params, aims_status_dialog):
        super().__init__()
        self.aims_status_dialog = aims_status_dialog
        self.map_widget = uic.loadUi(f'{state.meipass}resources/map.ui')

        clearLayout(parent_widget.layout())
        parent_widget.layout().addWidget(self.map_widget)

        self.map_widget.refreshButton.clicked.connect(self.draw_map)
        self.map_widget.export_kml_button.clicked.connect(self.export_kml)
        self.surveys = []


        by_class_combo_box: QComboBox = self.map_widget.filter_by_class_combo_box
        by_class_combo_box.addItem(self.tr("Show COTS and Scars"), userData="both")
        by_class_combo_box.addItem(self.tr("Show COTS"), userData="COTS")
        by_class_combo_box.addItem(self.tr("Show Scars"), userData="Scars")

        camera_combo_box: QComboBox = self.map_widget.camera_combo_box
        camera_combo_box.addItem(self.tr("Camera 1"), userData="cam_1")
        camera_combo_box.addItem(self.tr("Camera 2"), userData="cam_2")
        camera_combo_box.addItem(self.tr("Both"), userData="both")


        if cots_display_params is not None:
            from aims.model.cots_display_params import CotsDisplayParams
            self.cots_display_params:CotsDisplayParams = cots_display_params
        else:
            self.cots_display_params = None
            self.map_widget.cots_controls_widget.setVisible(False)

        self.cots_waypoints = []

    def show(self, surveys):
        if self.cots_display_params is not None:
            if self.cots_display_params.eod:
                self.map_widget.eod_check_box.setCheckState(Qt.Checked)
            else:
                self.map_widget.eod_check_box.setCheckState(Qt.Unchecked)

            if self.cots_display_params.only_show_confirmed:
                self.map_widget.confirmed_check_box.setCheckState(Qt.Checked)
            else:
                self.map_widget.confirmed_check_box.setCheckState(Qt.Unchecked)

            self.map_widget.minimumScoreTextBox.setText(str(self.cots_display_params.minimum_score))

        self.surveys = surveys
        self.draw_map()

    def draw_map(self):
        tracks = self.make_tracks()

        html_str = map_html_str(tracks, self.cots_waypoints)
        # html_str = map_html_str(tracks, [])
        # logger.info(html_str)
        if html_str is not None:
                # view.stop()
            self.map_widget.mapView.setHtml(html_str)

    def make_tracks(self):
        tracks = []
        self.cots_waypoints = []
        for survey in self.surveys:
            folder = survey.camera_dirs[1]
            try:
                _track = track(folder, False)
                tracks.extend(_track)
            except Exception as e:
                logger.error("Unable to make map", e)
                _track = None

            try:
                if self.cots_display_params is not None:
                    self.cots_display_params.read_data(self.aims_status_dialog, f"{survey.folder}", False)
                    eod_check_box: QCheckBox = self.map_widget.eod_check_box
                    self.cots_display_params.eod = eod_check_box.checkState() == Qt.Checked
                    self.cots_display_params.only_show_confirmed = self.map_widget.confirmed_check_box.checkState() == Qt.Checked
                    camera = self.map_widget.camera_combo_box.currentData(role=Qt.UserRole)
                    self.cots_display_params.camera = camera

                    try:
                        self.cots_display_params.minimum_score = float(self.map_widget.minimumScoreTextBox.text())
                    except Exception as e:
                        logger.warn("error getting minimum score", e)
                        self.cots_display_params.minimum_score = 0
                    # logger.info("draw map")
                    self.cots_waypoints.extend(self.cots_waypoints_for_survey())
            except Exception as e:
                logger.error("Unable to addn COTS to map", e)
                _track = None
        return tracks

    def cots_waypoints_for_survey(self):
        waypoints = []
        if self.cots_display_params.camera == "both":
            waypoints = self.cots_waypoints_for_survey_camera("cam_1")
            waypoints.extend(self.cots_waypoints_for_survey_camera("cam_2"))
        else:
            waypoints = self.cots_waypoints_for_survey_camera()

# sort by photo sequence number then keep a maximum of one per ten photos
        waypoints.sort(key=lambda x: x[4])
        last_kept = 0
        keep = []
        for wp in waypoints:
            if wp[4] - last_kept > 10:
                last_kept = wp[4]
                keep.append(wp)
        return keep

    def cots_waypoints_for_survey_camera(self, camera=None):
        cots_waypoints = []
        if self.cots_display_params is not None:
            try:
                detection_list = self.cots_display_params.cots_detection_list(camera)

                for waypoint in detection_list.cots_waypoints:
                    if (abs(waypoint[0]) > 0.0001) and (abs(waypoint[1]) > 0.0001):
                        score_ = waypoint[3]
                        only_show_confirmed = self.map_widget.confirmed_check_box.checkState() == Qt.Checked

                        sequence_ids = parse_sequences_string_to_sequence_ids(waypoint[2])
                        sequence_ids = self.filter_id_array_by_class(sequence_ids, detection_list)

                        if only_show_confirmed:
                            sequence_ids = self.filter_id_array_by_confirmed(sequence_ids, detection_list)

                        if sequence_ids:
                            new_sequences_str = self.id_array_to_sequence_string(sequence_ids)
                            if score_ > self.cots_display_params.minimum_score:
                                cots_waypoints.append([waypoint[0],
                                                       waypoint[1],
                                                       new_sequences_str,
                                                       waypoint[3],
                                                       waypoint[4],
                                                       ])

            except Exception as e:
                logger.error("error getting cots waypoints", e)
                cots_waypoints = []
        return cots_waypoints

    def id_array_to_sequence_string(self, sequence_ids):
        id_list_str = ', '.join(str(i) for i in sequence_ids)
        return f'sequences: {id_list_str}'

    def filter_id_array_by_class(self, sequence_ids, detection_list):
        included_ids = []
        for id in sequence_ids:
            if id:
                detection = detection_list.get_detection_by_sequence_id(id)
                if detection:
                    if self.include_waypoint(detection):
                        included_ids.append(id)
        return included_ids
    
    def filter_id_array_by_confirmed(self, sequence_ids, detection_list):
        confirmed_ids = []
        for id in sequence_ids:
            if id: 
                if detection_list.get_confirmed_by_sequence_id(id):
                    confirmed_ids.append(id)
        return confirmed_ids
            
    def include_waypoint(self, detection):
        class_to_show = self.map_widget.filter_by_class_combo_box.currentData(role=Qt.UserRole)
        include = True
        if class_to_show == "COTS":
            include = include and detection.best_class_id == 0

        if class_to_show == "Scars":
            include = include and detection.best_class_id == 1

        include = include and (detection.best_score > self.cots_display_params.minimum_score)

        return include

    def export_kml(self):

        if not state.read_only:
            #from aims.operations.kml_maker import make_kml
            #
            # if self.cots_display_params is not None and len(self.surveys) == 1:
            #     # TODO use the cots_display_params configuration
            #     minimum_score = self.cots_display_params.minimum_score
            # else:
            #     minimum_score = 0
            # init_kml_folder = f"{state.primary_drive}/kml"
            # os.makedirs(init_kml_folder, exist_ok=True)
            # output_folder = QFileDialog.getExistingDirectory(self.map_widget, 'Folder to save KML file to?', directory=init_kml_folder)
            # if (output_folder is not None and output_folder != ""):
            #     for survey in self.surveys:
            #         make_kml(survey=survey, cots_waypoints=self.cots_waypoints, minimum_cots_score=minimum_score, output_folder=output_folder, depth=True)

            init_kml_folder = f"{state.primary_drive}/kml"
            os.makedirs(init_kml_folder, exist_ok=True)
            output_file, filter = QFileDialog.getSaveFileName(self.map_widget, 'Folder to save KML file to?', directory=f"{init_kml_folder}/reefscan.kml")
            if (output_file is not None and output_file != ""):
                from aims.operations.kml_maker import make_kml2
                tracks = self.make_tracks()
                make_kml2(output_file, tracks, self.cots_waypoints)

