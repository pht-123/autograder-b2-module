import asyncio
import logging
from typing import Dict, Any
from uuid import uuid4
import httpx
from pydantic import BaseModel, field_validator
from fastapi import APIRouter, FastAPI, BackgroundTasks, HTTPException
import re

# ===================== 基础配置 =====================
router = APIRouter(prefix="/api/v1", tags=["代码提交与测评"])

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# 修正：移除硬编码，改为从外部配置注入（配合 core/config.py）
B3_EVALUATE_URL = "{base_url}/api/v1/b3/evaluate"
B3_RULES_URL = "{base_url}/api/v1/b3/rules/{question_id}"  # 新增：获取题目规则的接口
B4_RESULT_WRITE_URL = "{base_url}/api/v1/submissions/{submission_id}/result"

# 重试与超时配置：改为可配置（从外部传入）
task_list = []

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
# 修正：支持传入超时、重试参数
async def async_http_request(method: str, url: str, timeout_s: int, retry_count: int, retry_interval: int = 1, **kwargs) -> Dict[str, Any]:
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

# =====================  核心业务逻辑 =====================
# 修正：新增 base_url/timeout_s/retry_count 参数，支持配置注入
async def call_b3_evaluate(
        submission_id: str,
        question_id: str,
        code: str,
        language: str,
        base_url: str,
        timeout_s: int,
        retry_count: int
) -> Dict[str, Any]:
    """调用B3动态测评接口（支持配置注入）"""
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

# 新增：获取题目规则（配合 evaluation_service.py 中的 get_question_rules 调用）
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

# 修正：支持配置注入
async def write_result_to_b4(
        submission_id: str,
        result_data: Dict[str, Any],
        base_url: str,
        timeout_s: int,
        retry_count: int
) -> bool:
    """将测评结果回写到B4系统（支持配置注入）"""
    url = B4_RESULT_WRITE_URL.format(base_url=base_url, submission_id=submission_id)
    await async_http_request(
        "PATCH", url,
        timeout_s=timeout_s,
        retry_count=retry_count,
        json=result_data
    )
    logger.info(f"任务ID={submission_id} | B4结果回写成功")
    return True

async def execute_evaluation_flow(task: Dict[str, Any]):
    """完整的测评流程：调用B3测评 -> 回写结果到B4"""
    submission_id = task["submission_id"]
    try:
        # 补充：此处需从配置读取 B3/B4 地址（示例）
        b3_base_url = "http://localhost:8003"
        b4_base_url = "http://localhost:8004"
        timeout_s = 10
        retry_count = 3

        # 步骤1：调用B3进行测评
        b3_result = await call_b3_evaluate(
            submission_id=submission_id,
            question_id=task["question_id"],
            code=task["code"],
            language=task["language"],
            base_url=b3_base_url,
            timeout_s=timeout_s,
            retry_count=retry_count
        )

        # 步骤2：构造回写B4的数据
        write_data = {
            "status": "COMPLETED",
            "overall_score": b3_result.get("score", 0),
            "passed_count": b3_result.get("passed_count", 0),
            "total_count": b3_result.get("total_count", 0),
            "overall_comment": b3_result.get("comment", "测评完成"),
            "static_issues": b3_result.get("static_issues", []),
            "case_results": b3_result.get("case_results", [])
        }

        # 步骤3：回写结果到B4
        await write_result_to_b4(
            submission_id=submission_id,
            result_data=write_data,
            base_url=b4_base_url,
            timeout_s=timeout_s,
            retry_count=retry_count
        )

    except Exception as e:
        error_data = {"status": "ERROR", "error_msg": str(e)}
        await write_result_to_b4(
            submission_id=submission_id,
            result_data=error_data,
            base_url="http://localhost:8004",
            timeout_s=10,
            retry_count=3
        )
        logger.error(f"任务ID={submission_id} | 测评流程执行失败：{str(e)}")

    if task in task_list:
        task_list.remove(task)

# =====================  API 接口 =====================
@router.post("/submission", summary="提交代码进行测评")
def submit_code(data: SubmitRequest, background_tasks: BackgroundTasks):
    submission_id = str(uuid4())
    task = {
        "submission_id": submission_id,
        "question_id": data.question_id,
        "assignment_id": data.assignment_id,
        "code": data.code,
        "language": data.language,
        "student_user_id": data.student_user_id
    }
    task_list.append(task)

    background_tasks.add_task(execute_evaluation_flow, task)

    logger.info(f"接收到新提交 | 任务ID={submission_id} | 学生ID={data.student_user_id}")
    return {
        "submission_id": submission_id,
        "status": "RECEIVED",
        "message": "代码接收成功，测评任务已在后台启动"
    }

if __name__ == "__main__":
    import uvicorn
    app = FastAPI(title="B2 代码提交与测评", version="1.0")
    app.include_router(router)
    uvicorn.run(app, host="0.0.0.0", port=8002, reload=True)