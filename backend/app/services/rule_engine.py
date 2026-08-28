def evaluate(payload:dict,workload:dict)->list[dict]:
    del payload, workload
    # Runtime rules used to modify option scores. They are intentionally disabled:
    # the trained Logistic Regression classifier is the only hosting selector.
    return []
