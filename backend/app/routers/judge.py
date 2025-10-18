from fastapi import APIRouter

from ..schemas import JudgeRequest, JudgeResponse
from ..judge import judge_pair


router = APIRouter(prefix="/judge", tags=["judge"])


@router.post("")
def judge(req: JudgeRequest) -> JudgeResponse:
    winner, tags, jtype, conf = judge_pair(req.a, req.b, req.context)
    return JudgeResponse(winner=winner, tags=tags, judge_type=jtype, confidence=conf)

