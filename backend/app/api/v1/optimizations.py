from fastapi import APIRouter,Depends,Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.api.v1.helpers import owned_project,run_id_for
from app.core.database import get_db
from app.core.exceptions import AppError
from app.models import Optimization,Project
from app.schemas.analysis import OptimizationStatusRequest
router=APIRouter(tags=["Optimizations"])
def oj(o): return {"id":o.id,"priority":o.priority.title(),"category":o.category.replace("_"," ").title(),"title":o.title,"explanation":o.explanation,"impact":o.impact,"difficulty":o.difficulty.title(),"benefit":o.benefit,"status":o.status.replace("_"," ").title(),"steps":o.steps}
@router.get("/projects/{project_id}/optimizations")
def list_opts(project_id:str,priority:str|None=None,category:str|None=None,difficulty:str|None=None,status:str|None=None,user=Depends(get_current_user),db:Session=Depends(get_db)):
    p=owned_project(db,project_id,user); rid=run_id_for(p); q=select(Optimization).where(Optimization.analysis_run_id==rid)
    if priority:q=q.where(Optimization.priority==priority.upper())
    if category:q=q.where(Optimization.category==category.upper().replace(" ","_"))
    if difficulty:q=q.where(Optimization.difficulty==difficulty.upper())
    if status:q=q.where(Optimization.status==status.upper().replace(" ","_"))
    return [oj(o) for o in db.scalars(q.order_by(Optimization.created_at))]
@router.patch("/optimizations/{optimization_id}/status")
def patch_status(optimization_id:str,req:OptimizationStatusRequest,user=Depends(get_current_user),db:Session=Depends(get_db)):
    o=db.get(Optimization,optimization_id)
    if not o: raise AppError("OPTIMIZATION_NOT_FOUND","Optimization not found.",404)
    p=db.get(Project,o.project_id)
    if p.user_id!=user.id: raise AppError("FORBIDDEN","You do not have access to this optimization.",403)
    st=req.status.upper().replace(" ","_")
    if st not in {"OPEN","DONE","NOT_RELEVANT"}: raise AppError("VALIDATION_ERROR","Invalid optimization status.",422)
    o.status=st; db.commit(); return oj(o)
