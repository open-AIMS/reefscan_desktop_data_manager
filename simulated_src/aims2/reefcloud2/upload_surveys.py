from aims.operations.load_data import reefcloud_upload_survey


def upload_surveys(surveys, aims_status_dialog):
    for survey in surveys:
        success, message = reefcloud_upload_survey(survey, None, None, None,
                                                   aims_status_dialog)

    aims_status_dialog.close()

