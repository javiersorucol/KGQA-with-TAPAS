def get_precision(TP, FP):
    if TP == 0:
        return 0
    return TP/(TP + FP)

def get_recall(TP, FN):
    if TP == 0:
        return 0
    return TP/(TP + FN)

def get_f1(TP, FP, FN):
    if TP == 0:
        return 0
    return TP/(TP + 0.5*(FP + FN))