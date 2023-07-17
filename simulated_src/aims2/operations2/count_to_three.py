import time

from aims.messages import messages


def count_to_three(progress_queue, message=messages.load_camera_data_message()):
    progress_queue.reset()
    progress_queue.set_progress_label(message)
    progress_queue.set_progress_max(3)
    for i in range(1, 3):
        time.sleep(1)
        progress_queue.set_progress_value()
