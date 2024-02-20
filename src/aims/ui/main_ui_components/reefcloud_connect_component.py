import logging
from time import process_time

logger = logging.getLogger("")
logger.info(f"reefcloud connect start {process_time()}")

from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QApplication

from aims.state import state

logger.info(f"reefcloud connect imports done {process_time()}")

class ReefcloudConnectComponent(QObject):
    def __init__(self, hint_function):
        super().__init__()
        self.login_widget = None
        self.aims_status_dialog = None
        self.time_zone = None
        self.hint_function = hint_function

    def load(self, aims_status_dialog, time_zone):
        self.aims_status_dialog = aims_status_dialog
        self.time_zone = time_zone

        self.login_widget.cancel_button.clicked.connect(self.cancel)
        self.login_widget.cancel_button.setEnabled(False)
        self.set_hint()

    def cancel(self):
        logger.info("cancel")
        if state.reefcloud_session is not None:
            state.reefcloud_session.cancel()


    def logged_in(self):
        return state.reefcloud_session is not None and state.reefcloud_session.is_logged_in

    def set_hint(self):
        if self.logged_in():
            user_info = state.reefcloud_session.current_user
            if user_info.authorized:
                message = self.tr("you are authorised to upload data to reefcloud.")
            else:
                message = self.tr("you are not authorised to upload data to reefcloud.")

            self.login_widget.username_label.setText(self.tr("Hello ") + f" {user_info.name}.  " + message)

        else:
            self.hint_function(self.tr("Press the login button"))
            self.login_widget.username_label.setText(self.tr("Not logged in."))


    def update(self):
        from aims2.reefcloud2.reefcloud_utils import update_reefcloud_projects, update_reefcloud_sites

        self.login_widget.username_label.setText(self.tr("Downloading projects"))
        QApplication.processEvents()

        projects_response = update_reefcloud_projects(state.reefcloud_session)
        state.load_reefcloud_projects()
        self.login_widget.username_label.setText(self.tr("Downloading sites"))
        QApplication.processEvents()

        sites_response = update_reefcloud_sites(state.reefcloud_session)
        state.load_reefcloud_sites()

        # msg_box = QtWidgets.QMessageBox()
        # msg_box.setText(self.tr("Download finished"))
        # msg_box.setDetailedText(f"{projects_response}\n{sites_response}")
        # msg_box.exec_()

    def login(self):

        if not self.logged_in():
            from aims2.reefcloud2.reefcloud_session import ReefCloudSession

            logger.info("*******************************************About to attempt login")
            self.hint_function(self.tr("Log in to Reefcloud using the browser window which just popped up; or press the cancel button."))
            state.reefcloud_session = ReefCloudSession(state.config.client_id, state.config.cognito_uri)

            result = self.aims_status_dialog.threadPool.apply_async(state.reefcloud_session.login)
            self.login_widget.login_button.setEnabled(False)
            self.login_widget.cancel_button.setEnabled(True)
            logger.info("waiting")
            self.login_widget.username_label.setText(self.tr("Waiting for log in"))

            while not result.ready():
                QApplication.processEvents()

            logger.info("logged in")

            self.login_widget.login_button.setEnabled(True)
            self.login_widget.cancel_button.setEnabled(False)

        if self.logged_in():
            self.update()

        self.set_hint()
        return self.logged_in()
