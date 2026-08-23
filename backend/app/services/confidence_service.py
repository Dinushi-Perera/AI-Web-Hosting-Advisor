def label(value:float)->str:
    return "HIGH" if value>=0.80 else "MEDIUM" if value>=0.60 else "LOW" if value>=0.40 else "INSUFFICIENT_DATA"
def calculate(ml_certainty:float,input_completeness:float,technology_evidence:float,performance_evidence:float,workload_evidence:float,pricing_freshness:float)->dict:
    value=0.35*ml_certainty+0.20*input_completeness+0.15*technology_evidence+0.15*performance_evidence+0.10*workload_evidence+0.05*pricing_freshness
    value=max(0,min(1,value)); return {"value":round(value,3),"label":label(value)}
