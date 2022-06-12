import logging
import multiprocessing
import traceback

from PyQt5 import QtWidgets



import sys
import glob

# from uncaught_hook import UncaughtHook
from aims import state
from aims.config import Config
from aims.ui.config_ui import ConfigUi
from aims.ui.surveys_tree import SurveysTree

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def gui_except_hook(exc_class, exc_value, tb):
    logger.info("except hook")
    traceback1 = ''.join(traceback.format_tb(tb))
    error_message = str(exc_value)

    print (error_message)
    print(traceback1)

    errorbox = QtWidgets.QMessageBox()
    errorbox.setText(error_message)
    errorbox.setDetailedText(traceback1)
    errorbox.exec_()


sys.excepthook = gui_except_hook

# sys._excepthook = sys.excepthook


# def exception_hook(exctype, value, traceback):
#     print(exctype, value, traceback)
#     sys._excepthook(exctype, value, traceback)
#     sys.exit(1)


# sys.excepthook = exception_hook

# qt_exception_hook = UncaughtHook()

# import cgitb
# cgitb.enable(format='text')


if __name__ == "__main__":
    multiprocessing.freeze_support()
    try:
        state.meipass = sys._MEIPASS + "/"
    except:
        state.meipass=""
    print(state.meipass)
    files = glob.glob(state.meipass + '**/*', recursive=True)
    print(files)

    app = QtWidgets.QApplication(sys.argv)

    try:
        config_ui = ConfigUi()
        state.surveys_tree = SurveysTree()

        config_ui.show()
        app.exec()

    except Exception:
        logger.exception("Error")

    if state.model.data_loaded:
        print("will export")
        state.model.export()

    print("main done")

