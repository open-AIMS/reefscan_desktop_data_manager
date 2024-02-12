import filecmp
import logging
import os
import shutil
from time import sleep, process_time

from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QApplication

from aims.operations.abstract_operation import AbstractOperation
from aims.operations.aims_status_dialog import AimsStatusDialog

exclude = {'thumbnails'}

logger = logging.getLogger("")

def compare(dir1, dir2, fix, aims_status_dialog: AimsStatusDialog):
    operation = DiskDriveCompareOperation(dir1, dir2, fix)
    operation.update_interval = 100
    aims_status_dialog.set_operation_connections(operation)
    result = aims_status_dialog.threadPool.apply_async(operation.run)
    while not result.ready():
        QApplication.processEvents()
    logger.info("Close the status dialog")
    aims_status_dialog.close()
    return operation.total_differences, operation.fixable_messages, operation.unfixable_messages, operation.message_str


class DiskDriveCompareOperation(AbstractOperation):
    def __init__(self, dir1, dir2, fix):
        super().__init__()
        self._file = None
        self._files = None
        self._is_missing_completely = None
        self._is_missing = None
        self._is_different = None
        self._copying_files_from = None
        self._folder = None
        self._there_are_a_total_of = None
        self._differences = None
        self.dir1 = dir1
        self.dir2 = dir2
        self.fix = fix
        self.total_differences = None
        self.fixable_messages = None
        self.unfixable_messages = None
        self.message_str = None


    def init_translations(self):
        self._file = self.tr('file')
        self._files = self.tr('files')
        self._is_missing_completely = self.tr('is missing completely')
        self._is_missing = self.tr('is missing')
        self._is_different = self.tr('is different')
        self._copying_files_from = self.tr("Copying files from")
        self._folder = self.tr('folder')
        self._there_are_a_total_of = self.tr('There are a total of')
        self._differences = self.tr('differences')

    def dir_with_counts(self, dir):
        result = {}
        for root, dirs, files in os.walk(dir, topdown=True):
            dirs[:] = [d for d in dirs if d not in exclude]
            root2 = root.replace(dir, "")
            file_count = 0
            for name in files:
                if name.upper().endswith(".JSON") or name.upper().endswith(".CSV") or \
                        name.upper().endswith(".JPEG") or name.upper().endswith(".JPG"):
                    file_count+=1

            result[root2] = {"original_file": root, "count": file_count}
        return result

    def check_all_files_except_photos(self, dir1, dir2, fix):
        fixable_messages = []
        total_differences = 0
        for root, dirs, files in os.walk(dir1, topdown=False):
            dirs[:] = [d for d in dirs if d not in exclude]
            self.progress_queue.set_progress_label(f"Counting files for {root}")
            self.progress_queue.reset()
            self.progress_queue.set_progress_max(len(files))

            second_root = root.replace(dir1, dir2)
            for name in files:
                self.progress_queue.set_progress_value()
                if name.upper().endswith(".JSON") or name.upper().endswith(".CSV"):
                    second_file_name = os.path.join(second_root, name)
                    file_name = os.path.join(root, name)
                    if os.path.exists(second_file_name):
                        if not filecmp.cmp(file_name, second_file_name, shallow=False):
                            fixable_messages.append(f"{self._file} {file_name.replace(dir1, '')} {self._is_different}")
                            total_differences += 1
                            if fix:
                                os.makedirs(os.path.dirname(second_file_name), exist_ok=True)
                                shutil.copy(file_name, second_file_name)
                    else:
                        fixable_messages.append(f"{self._file} {file_name.replace(dir1, '')} {self._is_missing}")
                        if fix:
                            os.makedirs(os.path.dirname(second_file_name), exist_ok=True)
                            shutil.copy2(file_name, second_file_name)

        return total_differences, fixable_messages

    def _run(self):
        logger.info(f"_runs start {process_time()}")
        self.progress_queue.reset()

        self.init_translations()
        self.progress_queue.set_progress_label(f"Counting files on primary disk")
        logger.info(f"before counts1: {process_time()}")
        counts1 = self.dir_with_counts(self.dir1)
        logger.info(f"counts1: {process_time()}")
        self.progress_queue.set_progress_label(f"Counting files on secondary disk")
        counts2 = self.dir_with_counts(self.dir2)
        logger.info(f"counts2: {process_time()}")

        self.progress_queue.set_progress_label(f"Finding differences")
        total_differences, fixable_messages = self.check_all_files_except_photos(self.dir1, self.dir2, self.fix)
        self.progress_queue.set_progress_label(f"Finalising")

        unfixable_messages = []

        for folder in counts1:
            src_folder = counts1[folder]["original_file"]
            if folder not in counts2:
                fixable_messages.append(f"{self._folder} {folder} {self._is_missing_completely}")
                total_differences += counts1[folder]["count"]
                if self.fix:
                    dst_folder = src_folder.replace(self.dir1, self.dir2)
                    os.makedirs(dst_folder, exist_ok=True)
                    self.copy_folder(src_folder, dst_folder)
            else:
                count1 = counts1[folder]["count"]
                count2 = counts2[folder]["count"]
                if count1 != count2:
                    difference = count1 - count2
                    total_differences += abs(difference)
                    if difference < 0:
                        unfixable_messages.append(
                            f"{self._folder} {folder} {self._is_missing} {abs(difference)} {self._files} from the primary disk")
                    else:
                        fixable_messages.append(f"{self._folder} {folder} {self._is_missing} {difference} {self._files}")
                        if self.fix:
                            dst_folder = counts2[folder]["original_file"]
                            self.copy_folder(src_folder, dst_folder)

        message_str = f"{self._there_are_a_total_of} {total_differences} {self._differences}."

        self.total_differences = total_differences
        self.fixable_messages = fixable_messages
        self.unfixable_messages = unfixable_messages
        self.message_str = message_str

    def copy_folder(self, src_folder, dst_folder):
        print("Starting copy")
        self.progress_queue.reset()
        self.progress_queue.set_progress_label(f"copying folder {src_folder}")
        src_files = os.listdir(src_folder)
        self.progress_queue.set_progress_max(len(src_files) + 1)

        for file in src_files:
            src_file = f"{src_folder}/{file}"
            dst_file = f"{dst_folder}/{file}"
            if not os.path.isfile(dst_file) and os.path.isfile(src_file):
                shutil.copy2(src_file, dst_file)
            self.progress_queue.set_progress_value()
            if self.cancelled:
                break
        self.finished = True


