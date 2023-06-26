def get_precision(TP, FP):
    return TP/(TP + FP)

def get_recall(TP, FN):
    return TP/(TP + FN)

def get_f1(TP, FP, FN):
    return TP/(TP + 0.5*(FP + FN))