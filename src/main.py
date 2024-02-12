import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("")
logger_smb = logging.getLogger('smbprotocol')
logger_smb.setLevel(level=logging.WARN)

import multiprocessing
import traceback
from logging.handlers import RotatingFileHandler

from PyQt5 import QtWidgets, QtCore, QtGui

import os
import sys
import glob

# from uncaught_hook import UncaughtHook

from aims.state import state
from aims.ui.main_ui import MainUi
from aims2 import simulated


config_folder = state.config.config_folder

if not os.path.isdir(config_folder):
    os.makedirs(config_folder)
path = f"{config_folder}/reefscan.log"
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
handler = RotatingFileHandler(path, maxBytes=1000000,
                              backupCount=5)
handler.setFormatter(formatter)
logger.addHandler(handler)


def gui_except_hook(exc_class, exc_value, tb):
    logger.info("except hook")
    traceback1 = ''.join(traceback.format_tb(tb))
    error_message = str(exc_value)

    logger.exception(exc_class)
    logger.exception(error_message)
    logger.exception(traceback1)


    if exc_class is not UserWarning:
        errorbox = QtWidgets.QMessageBox()
        errorbox.setText(error_message)
        # errorbox.setDetailedText(traceback1)
        errorbox.exec_()


sys.excepthook = gui_except_hook

# sys._excepthook = sys.excepthook


# def exception_hook(exctype, value, traceback):
#     logger.info(exctype, value, traceback)
#     sys._excepthook(exctype, value, traceback)
#     sys.exit(1)


# sys.excepthook = exception_hook

# qt_exception_hook = UncaughtHook()

# import cgitb
# cgitb.enable(format='text')




if __name__ == "__main__":
    translate = QtCore.QCoreApplication.translate


    multiprocessing.freeze_support()
    file_path = os.path.dirname(os.path.realpath(__file__))
    try:
        state.meipass = sys._MEIPASS + "/"
        state.meipass2 = state.meipass
        state.has_meipass = True
    except:
        state.meipass= file_path + os.sep
        state.meipass2 = file_path + os.sep
        state.has_meipass = False

    simulated.set_simulated()

    logger.info(state.meipass)

    app = QtWidgets.QApplication(sys.argv)
    logger.info(app.font().pointSize())
    font = app.font()
    font.setPointSize(12)
    app.setFont(font)
    logger.info(app.font().pointSize())

    app_icon = QtGui.QIcon()
    app_icon.addFile(f'{state.meipass}resources/aims-fish16.png', QtCore.QSize(16, 16))
    app_icon.addFile(f'{state.meipass}resources/aims-fish24.png', QtCore.QSize(24, 24))
    app_icon.addFile(f'{state.meipass}resources/aims-fish32.png', QtCore.QSize(32, 32))
    app_icon.addFile(f'{state.meipass}resources/aims-fish48.png', QtCore.QSize(48, 48))
    app_icon.addFile(f'{state.meipass}resources/aims-fish256.png', QtCore.QSize(256, 256))
    app.setWindowIcon(app_icon)

    # This makes the Icon show in the task bar on Windows
    try:
        import ctypes
        myappid = 'aims.reefscan.transom'  # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except:
        print ("Error setting up windows task bar. Probably not windows.")


    try:
        state.config.set_deep(sys.argv[0].lower().endswith("reefscan-deep.exe")
                              or (len(sys.argv) > 1 and sys.argv[1].lower() == "deep")
                              )

        dev = len(sys.argv) > 1 and "dev" in sys.argv
        clear_reefcloud = len(sys.argv) > 1 and "clear_reefcloud" in sys.argv

        if len(sys.argv) > 1 and "viet" in sys.argv:
            state.config.vietnemese=True
        state.config.set_dev(dev)
        state.config.clear_reefcloud = clear_reefcloud

        try:
            import pyi_splash

            # Update the text on the splash screen
            pyi_splash.update_text("PyInstaller is a great software!")
            pyi_splash.update_text("Second time's a charm!")

            # Close the splash screen. It does not matter when the call
            # to this function is made, the splash screen remains open until
            # this function is called or the Python program is terminated.
            pyi_splash.close()
        except:
            pass

        main_ui = MainUi()
        main_ui.show()
        app.exec()

    except Exception:
        logger.exception("Error")

    if state.model.local_data_loaded and not state.read_only:
        logger.info("will export")
        state.model.export()

    logger.info("main done")

