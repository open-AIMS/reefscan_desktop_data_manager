from absl import logging

from aims.operations.inference_operation import InferenceOperation

logger = logging.getLogger("")
if __name__=='__main__':
    op = InferenceOperation()
    op.set_msg_function(lambda msg: logger.info(msg))
    op.run()