import filecmp
import os
import shutil

from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QApplication

from aims.operations.abstract_operation import AbstractOperation

exclude = {'thumbnails'}


class DiskDriveUtils(QObject):
    def __init__(self):
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
            result[root2] = {"original_file": root, "count": len(files)}
        return result


    def check_all_files_except_photos(self, dir1, dir2, fix):
        messages = []
        total_differences = 0
        for root, dirs, files in os.walk(dir1, topdown=False):
            dirs[:] = [d for d in dirs if d not in exclude]

            second_root = root.replace(dir1, dir2)
            for name in files:
                if not name.upper().endswith(".JPG"):
                    second_file_name = os.path.join(second_root, name)
                    file_name = os.path.join(root, name)
                    if os.path.exists(second_file_name):
                        if not filecmp.cmp(file_name, second_file_name, shallow=False):
                            messages.append(f"{self._file} {file_name.replace(dir1, '')} {self._is_different}")
                            total_differences += 1
                            if fix:
                                os.makedirs(os.path.dirname(second_file_name), exist_ok=True)
                                shutil.copy(file_name, second_file_name)
                    else:
                        messages.append(f"{self._file} {file_name.replace(dir1, '')} {self._is_missing}")
                        if fix:
                            os.makedirs(os.path.dirname(second_file_name), exist_ok=True)
                            shutil.copy2(file_name, second_file_name)
                        print(second_file_name)
        return total_differences, messages

    def compare(self, dir1, dir2, fix, aims_status_dialog):
        self.init_translations()
        counts1 = self.dir_with_counts(dir1)
        print(counts1)
        counts2 = self.dir_with_counts(dir2)
        print(counts2)
        total_differences, messages = self.check_all_files_except_photos(dir1, dir2, fix)
        for folder in counts1:
            src_folder = counts1[folder]["original_file"]
            if folder not in counts2:
                messages.append(f"{self._folder} {folder} {self._is_missing_completely}")
                total_differences += counts1[folder]["count"]
                if fix:
                    dst_folder = src_folder.replace(dir1, dir2)
                    os.makedirs(dst_folder, exist_ok=True)
                    shutil.copytree(src_folder, dst_folder, dirs_exist_ok=True)
            else:
                count1 = counts1[folder]["count"]
                count2 = counts2[folder]["count"]
                if count1 != count2:
                    difference = count1 - count2
                    messages.append(f"{self._folder} {folder} {self._is_missing} {difference} {self._files}")
                    total_differences += abs(difference)
                    if fix:
                        dst_folder = counts2[folder]["original_file"]
                        self.copy_folder(src_folder, dst_folder, aims_status_dialog)

        message_str = "\n".join(messages)
        message_str = f"{self._there_are_a_total_of} {total_differences} {self._differences}.\n{message_str}"

        return total_differences, messages, message_str


    def copy_folder(self, src_folder, dst_folder, aims_status_dialog):
        copy_folder_operation = CopyFolderOperation(src_folder, dst_folder)
        copy_folder_operation.update_interval = 1
        aims_status_dialog.set_operation_connections(copy_folder_operation)
        result = aims_status_dialog.threadPool.apply_async(copy_folder_operation.run)
        while not result.ready():
            QApplication.processEvents()
        aims_status_dialog.close()


class CopyFolderOperation(AbstractOperation):
    def __init__(self, src, dst):
        super().__init__()
        self.finished = False
        self.message = ""
        self.src = src
        self.dst = dst
        self.sync = self
        self.cancelled = False

    def cancel(self):
        self.cancelled = True

    def _run(self):
        print ("Starting copy")
        self.progress_queue.reset()
        self.progress_queue.set_progress_label(f"{self._copying_files_from} {self.src}")
        src_files = os.listdir(self.src)
        self.progress_queue.set_progress_max(len(src_files) + 1)

        i = 0
        for file in src_files:
            print(i)
            i += 1
            src_file = f"{self.src}/{file}"
            dst_file = f"{self.dst}/{file}"
            if not os.path.isfile(dst_file) and os.path.isfile(src_file):
                shutil.copy2(src_file, dst_file)
            self.progress_queue.set_progress_value()
            if self.cancelled:
                break
        self.finished = True

disk_drive_utils = DiskDriveUtils()

# if __name__ == "__main__":
#     compare("D:\LTMP-Whitsunday-2", "F:\LTMP-Whitsunday-2", True)
