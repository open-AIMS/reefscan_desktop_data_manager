import logging
import shutil
import os
from datetime import datetime
from joblib import Parallel, delayed
from reefscanner.basic_model.progress_queue import ProgressQueue

logger = logging.getLogger(__name__)


class Synchroniser:
    def __init__(self, progress_queue: ProgressQueue):
        self.files_to_copy: list[tuple[str]] = []
        self.total_files = 0
        # self.cancelled = False
        self.progress_queue = progress_queue

    def cancel(self):
        self.cancelled = True

    def _ignore_copy(self, path, names):
        if self.cancelled:
            return names   # everything ignored
        else:
            return []   # nothing will be ignored

    def prepare_copy(self, src, dst):
        if self.cancelled:
            print("cancelled")
        else:
            cnt = len(self.files_to_copy)
            if cnt % 100 == 0:
                message = f'Counting files. So far {cnt}'
                self.progress_queue.set_progress_label(message)
            # print(message)
            self.files_to_copy.append((src, dst))

    # def copy2_verbose(self, src, dst):
    #     logger.debug(f"copy2 {src}")
    #     if self.cancelled:
    #         print("cancelled")
    #     else:
    #         if os.path.exists(dst) and (os.stat(src).st_size == os.stat(dst).st_size):
    #             message = f'skipping {src}'
    #             self.progress_queue.set_progress_label(message)
    #         else:
    #             message = f'copying  {src}'
    #             self.progress_queue.set_progress_label(message)
    #             shutil.copy2(src, dst)
    #     self.progress_queue.set_progress_value()
    #     # logger.info("produced " + src)

    # def copytree_parallel(self, l_surveys_folder, s_surveys_folder):
    #     self.files_to_copy = []
    #     self.total_files = 0
    #     self.cancelled = False
    #     start = datetime.now()
    #     shutil.copytree(l_surveys_folder, s_surveys_folder, dirs_exist_ok=True, copy_function=self.prepare_copy,
    #                     ignore=self._ignore_copy)
    #     self.total_files = len(self.files_to_copy)
    #     logger.info(f"total files = {self.total_files}")
    #     self.progress_queue.set_progress_max(self.total_files)
    #     result = Parallel(n_jobs=50, require='sharedmem')(
    #         delayed(self.copy2_verbose)(src, dst) for src, dst in self.files_to_copy)
    #
    #     # for src, dst in self.files_to_copy:
    #     #     self.copy2_verbose(src, dst)
    #
    #     finish = datetime.now()
    #     logger.info(f'copy took {(finish - start).total_seconds()} seconds')
