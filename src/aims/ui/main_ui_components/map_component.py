from PyQt5.QtCore import QObject
from PyQt5.QtWebEngineWidgets import QWebEngineView
from reefscanner.basic_model.survey import Survey

from aims.ui.map_html import map_html_str


class MapComponent(QObject):
    def __init__(self, map_widget, realtime_cots_component):
        super().__init__()
        self.map_widget = map_widget

    def draw_map(self, survey: Survey, samba):
        # logger.info("draw map")
        if survey is not None:
            folder = survey.folder
            try:
                cots_waypoints = self.realtime_cots_component.realtime_cots_detection_list.cots_waypoints
            except:
                cots_waypoints = []

            html_str = map_html_str(folder, cots_waypoints, samba)
            # logger.info(html_str)
            if html_str is not None:
                view: QWebEngineView = self.map_widget.mapView
                # view.stop()
                view.setHtml(html_str)

