import traceback

from PyQt5 import QtWidgets
# from fbs_runtime.excepthook import ExceptionHandler

from aims.app import App
# from fbs_runtime.application_context.PyQt5 import ApplicationContext, cached_property
import sys



def gui_except_hook(exc_class, exc_value, tb):
    traceback1 = ''.join(traceback.format_tb(tb))
    error_message = str(exc_value)

    print (error_message)
    print(traceback1)

    errorbox = QtWidgets.QMessageBox()
    errorbox.setText(error_message)
    errorbox.setDetailedText(traceback1)
    errorbox.exec_()

sys.excepthook = gui_except_hook


if __name__ == "__main__":
    try:
        meipass = sys._MEIPASS + "/"
    except:
        meipass=""
    print(meipass)

    app= App(meipass)


