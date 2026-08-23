def questions(payload:dict):
    q=[]
    checks=[("concurrentUsers","How many users may use the site at the same time?","NUMBER"),("budget","What is the maximum monthly hosting budget in USD?","NUMBER"),("storage","How much storage will the application need in GB?","NUMBER"),("dbWorkload","How database-intensive is the application?","SELECT")]
    for key,text,kind in checks:
        if payload.get(key) in (None,"","Unknown","Not Decided","Unsure"): q.append({"key":key,"question":text,"input_type":kind,"required_for_confidence":True})
    return q
