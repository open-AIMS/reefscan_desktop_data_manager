import filecmp
import os
import shutil

from PyQt5.QtWidgets import QApplication

from aims.operations.abstract_operation import AbstractOperation

exclude = {'thumbnails'}


def dir_with_counts(dir):
    result = {}
    for root, dirs, files in os.walk(dir, topdown=True):
        dirs[:] = [d for d in dirs if d not in exclude]
        root2 = root.replace(dir, "")
        result[root2] = {"original_file": root, "count": len(files)}
    return result


def check_all_files_except_photos(dir1, dir2, fix):
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
                        messages.append(f"file {file_name.replace(dir1, '')} is different")
                        total_differences += 1
                        if fix:
                            os.makedirs(os.path.dirname(second_file_name), exist_ok=True)
                            shutil.copy(file_name, second_file_name)
                else:
                    messages.append(f"file {file_name.replace(dir1, '')} is missing")
                    if fix:
                        os.makedirs(os.path.dirname(second_file_name), exist_ok=True)
                        shutil.copy2(file_name, second_file_name)
                    print(second_file_name)
    return total_differences, messages


def compare(dir1, dir2, fix, aims_status_dialog):
    counts1 = dir_with_counts(dir1)
    print(counts1)
    counts2 = dir_with_counts(dir2)
    print(counts2)
    total_differences, messages = check_all_files_except_photos(dir1, dir2, fix)
    for folder in counts1:
        src_folder = counts1[folder]["original_file"]
        if folder not in counts2:
            messages.append(f"folder {folder} is missing completely")
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
                messages.append(f"folder {folder} is missing {difference} files")
                total_differences += abs(difference)
                if fix:
                    dst_folder = counts2[folder]["original_file"]
                    copy_folder(src_folder, dst_folder, aims_status_dialog)

    message_str = "\n".join(messages)
    message_str = f"There are a total of {total_differences} differences.\n{message_str}"

    return total_differences, messages, message_str


def copy_folder(src_folder, dst_folder, aims_status_dialog):
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
        self.progress_queue.set_progress_label(f"Copying files from {self.src}")
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



# if __name__ == "__main__":
#     compare("D:\LTMP-Whitsunday-2", "F:\LTMP-Whitsunday-2", True)
