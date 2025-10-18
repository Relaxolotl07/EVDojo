from fastapi import APIRouter

from ..schemas import AbuseReportRequest, AbuseReportResponse
from ..storage import db


router = APIRouter(prefix="/abuse", tags=["abuse"])


@router.post("/report")
def abuse_report(req: AbuseReportRequest) -> AbuseReportResponse:
    rid = db._next_id("abuse_reports")
    db.abuse_reports[rid] = {
        "id": rid,
        "item_id": req.item_id,
        "reporter_id": req.reporter_id,
        "reason": req.reason,
        "created_at": db.now(),
    }
    return AbuseReportResponse(report_id=rid)

