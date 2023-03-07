import filecmp
import os
import shutil


def dir_with_counts(dir, replace_dir_name=None):
    result = {}
    for root, dirs, files in os.walk(dir, topdown=False):
        if replace_dir_name is None:
            root2 = root
        else:
            root2 = root.replace(dir, replace_dir_name)
        result[root2] = {"original_file": root, "count": len(files)}
    return result


def check_all_files_except_photos(dir1, dir2, fix):
    messages = []
    total_differences = 0
    for root, dirs, files in os.walk(dir1, topdown=False):
        second_root = root.replace(dir1, dir2)
        for name in files:
            if not name.upper().endswith(".JPG"):
                second_file_name = os.path.join(second_root, name)
                file_name = os.path.join(root, name)
                if os.path.exists(second_file_name):
                    if not filecmp.cmp(file_name, second_file_name, shallow=False):
                        messages.append(f"file {second_file_name} is different")
                        total_differences += 1
                        if fix:
                            os.makedirs(os.path.dirname(second_file_name), exist_ok=True)
                            shutil.copy(file_name, second_file_name)
                else:
                    messages.append(f"file {second_file_name} is missing")
                    if fix:
                        os.makedirs(os.path.dirname(second_file_name), exist_ok=True)
                        shutil.copy2(file_name, second_file_name)
                    print(second_file_name)
    return total_differences, messages


def copy_folder(src, dest):
    src_files = os.listdir(src)
    i=0
    for file in src_files:
        print (i)
        i+=1
        src_file = f"{src}/{file}"
        dst_file = f"{dest}/{file}"
        if not os.path.isfile(dst_file) and os.path.isfile(src_file):
            shutil.copy2(src_file, dst_file)


def compare(dir1, dir2, fix):
    counts1 = dir_with_counts(dir1, dir2)
    print(counts1)
    counts2 = dir_with_counts(dir2)
    print(counts2)
    total_differences, messages = check_all_files_except_photos(dir1, dir2, fix)
    for folder in counts1:
        src_folder = counts1[folder]["original_file"]
        dst_folder = counts2[folder]["original_file"]
        if folder not in counts2:
            messages.append(f"folder {folder} is missing completely")
            total_differences += counts1[folder]["count"]
            if fix:
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
                    copy_folder(src_folder, dst_folder)

    message_str = "\n".join(messages)
    message_str = f"There are a total of {total_differences} differences.\n{message_str}"

    return total_differences, messages, message_str

if __name__ == "__main__":
    compare("D:\LTMP-Whitsunday-2", "F:\LTMP-Whitsunday-2", True)


