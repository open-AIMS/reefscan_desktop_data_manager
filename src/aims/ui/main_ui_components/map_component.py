import logging
from PyQt5.QtCore import Qt

from PyQt5.QtCore import QObject
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QCheckBox
from reefscanner.basic_model.survey import Survey

from aims.model.cots_display_params import CotsDisplayParams
from aims.ui.main_ui_components.cots_display_component import CotsDisplayComponent
from aims.ui.map_html import map_html_str
logger = logging.getLogger("MapComponent")


class MapComponent(QObject):
    def __init__(self, map_widget, cots_display_params):
        super().__init__()
        self.map_widget = map_widget
        self.cots_display_params:CotsDisplayParams = cots_display_params
        eod_check_box: QCheckBox = self.map_widget.eod_check_box
        eod_check_box.stateChanged.connect(self.draw_map)
        self.map_widget.refreshButton.clicked.connect(self.draw_map)
        self.survey = None

    def show(self, survey: Survey):
        if self.cots_display_params.eod:
            self.map_widget.eod_check_box.setCheckState(Qt.Checked)
        else:
            self.map_widget.eod_check_box.setCheckState(Qt.Unchecked)
        self.map_widget.minimumScoreTextBox.setText(str(self.cots_display_params.minimum_score))

        self.survey = survey
        self.draw_map()

    def draw_map(self):
        eod_check_box: QCheckBox = self.map_widget.eod_check_box
        self.cots_display_params.eod = eod_check_box.checkState() == Qt.Checked
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
                    if score_ > self.cots_display_params.minimum_score:
                        cots_waypoints.append(waypoint)

            except Exception as e:
                logger.error("error getting cots waypoints", e)
                cots_waypoints = []

            html_str = map_html_str(folder, cots_waypoints, False)
            # logger.info(html_str)
            if html_str is not None:
                view: QWebEngineView = self.map_widget.mapView
                # view.stop()
                view.setHtml(html_str)

