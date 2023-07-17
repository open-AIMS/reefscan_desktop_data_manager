from aims.state import state
from aims.operations.load_data import reefcloud_subsample, reefcloud_upload_survey
from aims2.reefcloud2.reefcloud_utils import upload_file, write_reefcloud_photos_json


def upload_surveys(surveys, aims_status_dialog):
    for survey in surveys:
        survey_id = survey.id
        survey_folder = survey.folder
        if survey.reefcloud is not None and survey.reefcloud.total_photo_count == survey.photos:
            # photos are already uploaded just upload the metadata
            upload_file(oauth2_session=state.reefcloud_session, survey_id=survey_id, folder=survey_folder,
                        file_name="survey.json")

        else:
            subsampled_image_folder = survey.folder.replace("/reefscan/", "/reefscan_reefcloud/")

            success, selected_photo_infos = reefcloud_subsample(survey_folder, subsampled_image_folder,
                                                                aims_status_dialog)
            if not success:
                aims_status_dialog.close()
                raise Exception("Cancelled")

            print(selected_photo_infos)
            write_reefcloud_photos_json(survey_id=survey_id,
                                        outputfile=f"{subsampled_image_folder}/photos.json",
                                        selected_photo_infos=selected_photo_infos
                                        )

            success, message = reefcloud_upload_survey(survey, survey_id, survey_folder, subsampled_image_folder,
                                                       aims_status_dialog)
            if not success:
                aims_status_dialog.close()
                if message is not None:
                    raise Exception(message)
                else:
                    raise Exception("Cancelled")
