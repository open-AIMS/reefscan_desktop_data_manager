import json
import os
import time

from reefscanner.basic_model.survey import Survey

from aims.state import state
import requests

from aims.operations.load_data import reefcloud_upload_survey

surveys_folder = "surveys"

def check_reefcloud_metadata(surveys: list[Survey]):
    pass


def write_reefcloud_photos_json(survey_id, outputfile, selected_photo_infos):
    time.sleep(1)


def upload_file(oauth2_session, survey_id, folder, file_name):
    time.sleep(1)


def update_reefcloud_projects(oauth2_session):
    time.sleep(1)


def create_reefcloud_site(project_name, site_name, latitude, longitude, depth):
    time.sleep(1)


def update_reefcloud_sites(oauth2_session):
    time.sleep(1)


def download_reefcloud_projects(oauth2_session):
    time.sleep(1)


def download_reefcloud_sites_for_project(oauth2_session, reefcloud_project):
    time.sleep(1)
