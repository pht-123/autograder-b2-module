import asyncio
import logging
from typing import Dict, Any
from uuid import uuid4
import httpx
from pydantic import BaseModel, field_validator
from fastapi import APIRouter, FastAPI, BackgroundTasks, HTTPException, Request
import re

# ===================== 基础配置 =====================
router = APIRouter(prefix="/api/v1", tags=["代码提交与测评"])

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# B3/B4 接口地址模板
B3_EVALUATE_URL = "{base_url}/api/v1/b3/evaluate"
B3_RULES_URL = "{base_url}/api/v1/b3/rules/{question_id}"
B4_RESULT_WRITE_URL = "{base_url}/api/v1/submissions/{submission_id}/result"

# ===================== 请求模型定义 =====================
class SubmitRequest(BaseModel):
    question_id: str
    assignment_id: str
    code: str
    language: str
    student_user_id: str

    @field_validator('code')
    def code_not_empty(cls, v):
        if not v or len(v.strip()) == 0:
            raise HTTPException(status_code=400, detail="提交的代码不能为空")
        return v

    @field_validator('student_user_id')
    def student_id_check(cls, v):
        if not re.match(r'^[0-9]+$', v):
            raise HTTPException(status_code=400, detail="学号必须为纯数字")
        return v


# ===================== 工具函数 =====================
async def async_http_request(
    method: str,
    url: str,
    timeout_s: int,
    retry_count: int,
    retry_interval: int = 1,
    **kwargs
) -> Dict[str, Any]:
    """通用异步HTTP请求工具，支持自定义超时/重试"""
    for retry in range(retry_count):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(method, url, timeout=timeout_s, **kwargs)
                logger.info(f"接口调用 | {method} {url} | 请求参数={kwargs.get('json', {})} | 状态码={response.status_code}")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            error_msg = f"第{retry + 1}次请求失败：{str(e)}"
            logger.error(error_msg)
            if retry == retry_count - 1:
                raise
            await asyncio.sleep(retry_interval)


# ===================== B3/B4 调用客户端 =====================
async def call_b3_evaluate(
    submission_id: str,
    question_id: str,
    code: str,
    language: str,
    base_url: str,
    timeout_s: int,
    retry_count: int
) -> Dict[str, Any]:
    """调用B3动态测评接口"""
    url = B3_EVALUATE_URL.format(base_url=base_url)
    payload = {
        "submission_id": submission_id,
        "question_id": question_id,
        "submitted_code": code,
        "language": language
    }
    return await async_http_request(
        "POST", url,
        timeout_s=timeout_s,
        retry_count=retry_count,
        json=payload
    )


async def get_question_rules(
    question_id: str,
    base_url: str,
    timeout_s: int,
    retry_count: int
) -> Dict[str, Any]:
    """调用B3获取题目规则（禁止模块/函数）"""
    url = B3_RULES_URL.format(base_url=base_url, question_id=question_id)
    return await async_http_request(
        "GET", url,
        timeout_s=timeout_s,
        retry_count=retry_count
    )


async def write_result_to_b4(
    submission_id: str,
    result_data: Dict[str, Any],
    base_url: str,
    timeout_s: int,
    retry_count: int
) -> bool:
    """将测评结果回写到B4系统"""
    url = B4_RESULT_WRITE_URL.format(base_url=base_url, submission_id=submission_id)
    await async_http_request(
        "PATCH", url,
        timeout_s=timeout_s,
        retry_count=retry_count,
        json=result_data
    )
    logger.info(f"任务ID={submission_id} | B4结果回写成功")
    return True


# ===================== API 接口 =====================
@router.post("/submission", summary="提交代码进行测评")
async def submit_code(data: SubmitRequest, request: Request):
    """
    接收代码提交，保存到文件，加入异步测评队列
    """
    from models.submission import SubmissionCreateRequest

    app_state = request.app.state.b2

    create_req = SubmissionCreateRequest(
        student_user_id=data.student_user_id,
        question_id=data.question_id,
        assignment_id=data.assignment_id,
        code=data.code,
        language=data.language
    )

    response = await app_state.submission_service.create_submission(create_req)

    logger.info(f"接收到新提交 | 任务ID={response.submission_id} | 学生ID={data.student_user_id}")
    return {
        "submission_id": response.submission_id,
        "status": response.status,
        "message": "代码接收成功，测评任务已在后台启动"
    }



