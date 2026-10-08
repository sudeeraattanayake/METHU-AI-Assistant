
import os
import secrets
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from backend.agents.coding_agent import request_code_edit, apply_approved_code_edit
from backend.security.approvals import approval_manager

load_dotenv()


def require_approval_token(x_methu_token: str | None = Header(default=None)):
    expected = os.getenv("METHU_APPROVAL_TOKEN")
    if not expected or not x_methu_token or not secrets.compare_digest(x_methu_token, expected):
        raise HTTPException(status_code=403, detail="Unauthorized")


router = APIRouter(
    prefix="/api/coding",
    tags=["Coding Agent"],
    dependencies=[Depends(require_approval_token)]
)


class EditProposal(BaseModel):
    path: str
    code: str


class EditApproval(BaseModel):
    approval_id: str
    code: str


@router.post("/propose")
def propose_edit(data: EditProposal):
    try:
        return request_code_edit(data.path, data.code)
    except (ValueError, FileNotFoundError, PermissionError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/approval/{approval_id}")
def get_approval(approval_id: str):
    request = approval_manager.get(approval_id)
    if not request:
        raise HTTPException(status_code=404, detail="Approval not found")
    return request


@router.post("/approve")
def approve_edit(data: EditApproval):
    import hashlib

    request = approval_manager.get(data.approval_id)
    if not request or request["status"] != "pending":
        raise HTTPException(status_code=400, detail="Invalid approval")
    if request["action"] != "edit_file":
        raise HTTPException(status_code=400, detail="Invalid action")

    expected = request["tool_input"]["sha256"]
    actual = hashlib.sha256(data.code.encode("utf-8")).hexdigest()
    if not secrets.compare_digest(expected, actual):
        raise HTTPException(
            status_code=409, detail="Code does not match proposal")

    approval_manager.approve(data.approval_id)
    try:
        return {"message": apply_approved_code_edit(data.approval_id, data.code)}
    except (ValueError, FileNotFoundError, PermissionError) as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/reject/{approval_id}")
def reject_edit(approval_id: str):
    request = approval_manager.reject(approval_id)
    if not request:
        raise HTTPException(status_code=400, detail="Invalid approval")
    return request
