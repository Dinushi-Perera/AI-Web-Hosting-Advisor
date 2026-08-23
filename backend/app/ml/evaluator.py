def evaluation_summary(model):
    return {"accuracy":model.accuracy,"precision":model.precision,"recall":model.recall,"f1":model.f1,"confusion_matrix":model.confusion_matrix,"class_distribution":model.class_distribution,"feature_importance":model.feature_importance}
