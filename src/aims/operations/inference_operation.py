import logging
import threading

import os

from aims.operations.abstract_operation import AbstractOperation

import inferencer.models 
from inferencer.models import ft_ext as reefscan_feature_extractor
from inferencer.models import classifier as reefscan_classifier
from inferencer.reefscan_inference import inference
from inferencer.batch_monitor import BatchMonitor

import csv

from aims.utils import replace_last

logger = logging.getLogger("")


def inference_result_folder(target):
    return replace_last(target, "/reefscan/", "/reefscan_inference/")


class InferenceOperation(AbstractOperation):
    msg_func = lambda msg: None

    feature_extractor_path = os.path.join(reefscan_feature_extractor.__path__[0], 'weights.best.hdf5')
    classifier_path = os.path.join(reefscan_classifier.__path__[0], 'reefscan.sav')
    group_labels_path = os.path.join(inferencer.models.__path__[0], 'reefscan_group_labels.csv')
    output_coverage_file = ''

    TEST_IMAGES_PATH = 'C:\\reefscan\\reefscan-inf-test-images'

    def __init__(self, target=TEST_IMAGES_PATH, results_folder=TEST_IMAGES_PATH, replace=False):
        super().__init__()
        self.target = target


        features_folder = os.path.join(results_folder, 'features')

        os.makedirs(results_folder, exist_ok=True)
        os.makedirs(features_folder, exist_ok=True)

        self.output_results_file = os.path.join(results_folder, 'results.csv')
 
        self.output_coverage_file = os.path.join(results_folder, 'coverage.csv')

        self.features_path = os.path.join(features_folder, 'features.csv')
        self.temp_features_path = os.path.join(features_folder, 'temp_features.csv')

        self.batch_monitor = BatchMonitor()


    def cancel(self):
        logger.info("inference operation says cancel")
        self.batch_monitor.set_cancelled()
        if self.msg_func is not None:
            if not self.batch_monitor.finished:
                self.msg_func("Stopping inference operation...") 
                self.msg_func("Waiting for the inferencer to finish shutting down.")

    def get_coverage_filepath(self):
        return self.output_coverage_file

    def set_msg_function(self, msg_func):
        self.msg_func = msg_func

    def _run(self):
        logger.info("InferenceOperation run")

        def retrieve_current_progress(completed, total):
            self.set_progress_max(total)
            self.set_progress_value(completed)
            if not self.batch_monitor.cancelled:
                self.set_progress_label(f'Inferencing: {completed} / {total} points done')
            else:
                self.set_progress_label("Shutting down inferencer")

        self.batch_monitor.set_callback_on_tick(retrieve_current_progress)

        import inferencer
        self.msg_func(inferencer.__file__)

        self.msg_func(f'Results will be saved at {self.output_results_file}')
        self.msg_func(f'Coverage will be saved at {self.output_coverage_file}')
        self.msg_func(f'Features will be saved at {self.features_path}')
        self.msg_func(f'Temp features file will be saved at {self.temp_features_path}')

        t = threading.Thread(target=self.run_inference)
        t.start()
        t.join()


    def run_inference(self):

        try:
            inference(feature_extractor=self.feature_extractor_path,
                  classifier=self.classifier_path,
                  group_labels_csv_file=self.group_labels_path,
                  local_image_dir=self.target,
                  output_results_file=self.output_results_file,
                  output_coverage_file=self.output_coverage_file,
                  intermediate_feature_outputs_path=self.features_path,
                  saved_state_file=self.temp_features_path,
                  saved_state_batch_size=31,
                  batch_monitor=self.batch_monitor
                  )
        except Exception as e:
            logger.info(repr(e))
            import traceback
            logger.info(traceback.print_exc())
            logger.info(e.__traceback__)
            logger.info(self.batch_monitor.alt_msg)
            self.exception.emit(e)

    # base method overriden to change the progress max and label at the start
    def run(self):
        try:
            logger.info("inference start")
            self.progress_value = 0
            self.finished = False
            # self.set_progress_max(10)
            # self.set_progress_value(1)
            self.set_progress_value(0)
            self.set_progress_max(1)
            self.set_progress_label("Initialising...")
            consumer_thread = threading.Thread(target=self.consumer, daemon=True)
            consumer_thread.start()
            logger.info("before run")
            result = self._run()
            logger.info("after run")
            self.set_progress_value(self.progress_max+1)
            self.finished = True
            logger.info("finish")
            consumer_thread.join()
            logger.info("t joined")
            # self.q.join()
            # logger.info("q joined")
            # self.after_run.emit(result)
            # logger.info("finished thread emitted after run")
        except Exception as e:
            logger.info(repr(e))
            import traceback
            logger.info(traceback.print_exc())
            logger.info(e.__traceback__)
            logger.info(self.batch_monitor.alt_msg)
            self.exception.emit(e)
