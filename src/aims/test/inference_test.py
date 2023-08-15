from aims.operations.inference_operation import InferenceOperation

if __name__=='__main__':
    op = InferenceOperation()
    op.set_msg_function(lambda msg: print(msg))
    op.run()