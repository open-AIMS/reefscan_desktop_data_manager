import logging
import traceback

from PyQt5 import QtWidgets
# from fbs_runtime.excepthook import ExceptionHandler

# from fbs_runtime.application_context.PyQt5 import ApplicationContext, cached_property
import sys
import glob

# from uncaught_hook import UncaughtHook
from aims.ui.start import Start

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
    try:
        meipass = sys._MEIPASS + "/"
    except:
        meipass=""
    print(meipass)
    files = glob.glob(meipass + '**/*', recursive=True)
    print (files)


    # app= App(meipass)
    try:
        start = Start(meipass)
    except Exception:
        logger.exception("Error")

    print("main done")


