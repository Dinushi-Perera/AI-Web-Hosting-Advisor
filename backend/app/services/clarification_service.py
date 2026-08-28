UNKNOWN_VALUES=(None,"","Unknown","Not Decided","Unsure","Not sure")

QUESTION_DEFINITIONS=(
    ("concurrentUsers","How many users may use the site at the same time?","NUMBER",None),
    ("budget","What is the maximum monthly hosting budget in USD?","NUMBER",None),
    ("storage","How much storage will the application need in GB?","NUMBER",None),
    ("dbWorkload","How database-intensive is the application?","SELECT",["Low","Medium","High","Very High","Unknown"]),
)

def questions(payload:dict):
    result=[]
    for key,text,kind,options in QUESTION_DEFINITIONS:
        if payload.get(key) in UNKNOWN_VALUES:
            item={"key":key,"question":text,"input_type":kind,"required_for_confidence":True}
            if options:item["options"]=options
            result.append(item)
    return result

def apply_answers(payload:dict)->dict:
    """Promote answers to their canonical fields so sizing uses them."""
    merged=dict(payload)
    answers=payload.get("clarifications")
    if not isinstance(answers,dict):return merged
    allowed={item[0] for item in QUESTION_DEFINITIONS}
    for key,value in answers.items():
        if key in allowed and value not in UNKNOWN_VALUES:merged[key]=value
    return merged
