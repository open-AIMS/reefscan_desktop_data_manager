import logging
from PyQt5.QtCore import Qt

from PyQt5.QtCore import QObject
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QCheckBox, QComboBox
from reefscanner.basic_model.survey import Survey

from functools import partial

from aims.model.cots_detection import CotsDetection
from aims.model.cots_detection_list import CotsDetectionList
from aims.model.cots_display_params import CotsDisplayParams
from aims.ui.main_ui_components.cots_display_component import CotsDisplayComponent
from aims.ui.map_html import map_html_str
logger = logging.getLogger("MapComponent")


def parse_sequences_string_to_sequence_ids(seq_str):
    seq_str_values = seq_str.replace("sequences: ", "")
    seq_id_list = [int(id.strip()) for id in seq_str_values.split(",") if id.strip().replace("-", "").isdigit()]
    return seq_id_list


class MapComponent(QObject):
    def __init__(self, map_widget, cots_display_params):
        super().__init__()
        self.map_widget = map_widget
        self.cots_display_params:CotsDisplayParams = cots_display_params
        eod_check_box: QCheckBox = self.map_widget.eod_check_box
        eod_check_box.stateChanged.connect(self.draw_map)
        confirmed_check_box: QCheckBox = self.map_widget.confirmed_check_box
        confirmed_check_box.stateChanged.connect(self.draw_map)
        self.map_widget.refreshButton.clicked.connect(self.draw_map)
        self.survey = None

        by_class_combo_box: QComboBox = self.map_widget.filter_by_class_combo_box
        by_class_combo_box.addItem(self.tr("Show COTS and Scars"), userData="both")
        by_class_combo_box.addItem(self.tr("Show COTS"), userData="COTS")
        by_class_combo_box.addItem(self.tr("Show Scars"), userData="Scars")
        by_class_combo_box.currentIndexChanged.connect(self.draw_map)


    def show(self, survey: Survey):
        if self.cots_display_params.eod:
            self.map_widget.eod_check_box.setCheckState(Qt.Checked)
        else:
            self.map_widget.eod_check_box.setCheckState(Qt.Unchecked)

        if self.cots_display_params.only_show_confirmed:
            self.map_widget.confirmed_check_box.setCheckState(Qt.Checked)
        else:
            self.map_widget.confirmed_check_box.setCheckState(Qt.Unchecked)

        self.map_widget.minimumScoreTextBox.setText(str(self.cots_display_params.minimum_score))

        self.survey = survey
        self.draw_map()

    def draw_map(self):
        eod_check_box: QCheckBox = self.map_widget.eod_check_box
        self.cots_display_params.eod = eod_check_box.checkState() == Qt.Checked
        self.cots_display_params.only_show_confirmed = self.map_widget.confirmed_check_box.checkState() == Qt.Checked
        try:
            self.cots_display_params.minimum_score = float(self.map_widget.minimumScoreTextBox.text())
        except Exception as e:
            logger.warn("error getting minimum score", e)
            self.cots_display_params.minimum_score = 0
        # logger.info("draw map")
        if self.survey is not None:
            folder = self.survey.folder
            try:
                detection_list = self.cots_display_params.cots_detection_list()
                cots_waypoints = []

                for waypoint in detection_list.cots_waypoints:
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
                                                   waypoint[3]])


            except Exception as e:
                logger.error("error getting cots waypoints", e)
                cots_waypoints = []

            html_str = map_html_str(folder, cots_waypoints, False)
            # logger.info(html_str)
            if html_str is not None:
                view: QWebEngineView = self.map_widget.mapView
                # view.stop()
                view.setHtml(html_str)

    def id_array_to_sequence_string(self, sequence_ids):
        id_list_str = ', '.join(str(i) for i in sequence_ids)
        return f'sequences: {id_list_str}'

    def filter_id_array_by_class(self, sequence_ids, detection_list: CotsDetectionList):
        included_ids = []
        for id in sequence_ids:
            if id:
                detection = detection_list.get_detection_by_sequence_id(id)
                if detection:
                    if self.include_waypoint(detection):
                        included_ids.append(id)
        return included_ids
    
    def filter_id_array_by_confirmed(self, sequence_ids, detection_list: CotsDetectionList):
        confirmed_ids = []
        for id in sequence_ids:
            if id: 
                if detection_list.get_confirmed_by_sequence_id(id):
                    confirmed_ids.append(id)
        return confirmed_ids
            
    def include_waypoint(self, detection: CotsDetection):
        class_to_show = self.map_widget.filter_by_class_combo_box.currentData(role=Qt.UserRole)
        include = True
        if class_to_show == "COTS":
            include = include and detection.best_class_id == 0

        if class_to_show == "Scars":
            include = include and detection.best_class_id == 1

        include = include and (detection.best_score > self.cots_display_params.minimum_score)

        return include

