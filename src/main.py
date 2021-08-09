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

# class GuiExceptionHandler(ExceptionHandler):
#     def handle(self, exc_type, exc_value, enriched_tb):
#         # Normally, we'd like to use sys.__excepthook__ here. But it doesn't
#         # work with our "fake" traceback (see add_missing_qt_frames(...)).
#         # The following call avoids this yet produces the same result:
#         # print ("GUI Exception")
#         # print("TYPE " + str(exc_type))
#         # print("VAL " + str(exc_value))
#         # print("ENR " + ''.join(traceback1))
#         # print ('GREG SAYS' + ('\n'.join([''.join(traceback.format_tb(enriched_tb)),
#         #                          '{0}: {1}'.format(exc_type.__name__, exc_value)])))
#         traceback1 = ''.join(traceback.format_tb(enriched_tb))
#         errorbox = QtWidgets.QMessageBox()
#         errorbox.setText(str(exc_value))
#         errorbox.setDetailedText(traceback1)
#         errorbox.exec_()

# class AppContext(ApplicationContext):
# class AppContext():

    # def run(self):
    #     self.window.resize(640, 480)
    #     self.window.show()
    #     return appctxt.app.exec_()

    # def get_app_ui(self):
    #     qtCreatorFile = self.get_resource("app.ui")
    #     return qtCreatorFile
    #
    # def get_sites_ui(self):
    #     qtCreatorFile = self.get_resource("sites.ui")
    #     return qtCreatorFile

    # @cached_property
    # def exception_handlers(self):
    #     result = super().exception_handlers
    #     result.append(GuiExceptionHandler())
    #     return (result)

    # @cached_property
    # def window(self):
    #     return App(self.get_app_ui(), self.get_sites_ui())

if __name__ == "__main__":
    # appctxt = AppContext()
    try:
        meipass = sys._MEIPASS + "/"
    except:
        meipass=""
    print(meipass)

    app= App(meipass)
    # app.ui.resize(640, 480)
    # app.ui.show()
    #     return appctxt.app.exec_()
    # exit_code = appctxt.run()
    # sys.exit(exit_code)


# app = app()
# app.setupUi()