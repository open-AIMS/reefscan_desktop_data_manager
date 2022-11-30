class UploadComponent:
    def __init__(self):
        self.login_widget = None
        self.aims_status_dialog = None

    def load_login_screen(self, aims_status_dialog):
        self.aims_status_dialog = aims_status_dialog
        self.existing_user_mode()
        self.login_widget.existing_user_mode_button.clicked.connect(self.existing_user_mode)
        self.login_widget.new_user_mode_button.clicked.connect(self.new_user_mode)
        self.login_widget.forgot_mode_button.clicked.connect(self.forgot_mode)

    def existing_user_mode(self):
        self.login_widget.existing_user_mode_button.setVisible(False)
        self.login_widget.new_user_mode_button.setVisible(True)
        self.login_widget.forgot_mode_button.setVisible(True)

        self.login_widget.login_button.setVisible(True)
        self.login_widget.create_user_button.setVisible(False)
        self.login_widget.request_password_button.setVisible(False)

        self.login_widget.email_label.setVisible(False)
        self.login_widget.email_edit.setVisible(False)

        self.login_widget.password_label.setVisible(True)
        self.login_widget.password_edit.setVisible(True)

    def new_user_mode(self):
        self.login_widget.existing_user_mode_button.setVisible(True)
        self.login_widget.new_user_mode_button.setVisible(False)
        self.login_widget.forgot_mode_button.setVisible(True)

        self.login_widget.login_button.setVisible(False)
        self.login_widget.create_user_button.setVisible(True)
        self.login_widget.request_password_button.setVisible(False)

        self.login_widget.email_label.setVisible(True)
        self.login_widget.email_edit.setVisible(True)

        self.login_widget.password_label.setVisible(False)
        self.login_widget.password_edit.setVisible(False)

    def forgot_mode(self):
        self.login_widget.existing_user_mode_button.setVisible(True)
        self.login_widget.new_user_mode_button.setVisible(True)
        self.login_widget.forgot_mode_button.setVisible(False)

        self.login_widget.login_button.setVisible(False)
        self.login_widget.create_user_button.setVisible(False)
        self.login_widget.request_password_button.setVisible(True)

        self.login_widget.email_label.setVisible(True)
        self.login_widget.email_edit.setVisible(True)

        self.login_widget.password_label.setVisible(False)
        self.login_widget.password_edit.setVisible(False)
