import json,sys
from app.core.database import SessionLocal
from app.models import TestResult
def main(path):
    data=json.load(open(path,encoding="utf-8"));db=SessionLocal()
    try:
        for x in data:db.add(TestResult(test_type=x["test_type"],test_name=x["test_name"],status=x["status"],duration_ms=x.get("duration_ms"),details=x.get("details",{})))
        db.commit()
    finally:db.close()
if __name__=="__main__":main(sys.argv[1])
