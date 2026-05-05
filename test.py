import asyncio
import logging
from typing import Dict, Any
from uuid import uuid4
import httpx
from pydantic import BaseModel, field_validator
from fastapi import FastAPI, BackgroundTasks

from fastapi import HTTPException
import re

# ===================== 基础配置 =====================
# FastAPI 应用实例
app = FastAPI(title="B2 代码提交与测评", version="1.0")

# 日志配置：时间/级别/信息
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# 外部服务接口配置
B3_EVALUATE_URL = "http://localhost:8003/api/v1/b3/evaluate" #B3测评地址
B4_RESULT_WRITE_URL = "http://localhost:8004/api/v1/submissions/{submission_id}/result" #写回B4地址

# 重试与超时配置
MAX_RETRY_COUNT = 3  # 最大重试次数
RETRY_INTERVAL = 1   # 重试间隔（秒）
REQUEST_TIMEOUT = 10 # 请求超时时间（秒）

# 存储待处理的任务列表（b2全体从这里调用）
task_list = []

# ===================== 请求模型定义 =====================
class SubmitRequest(BaseModel):
    """代码提交请求的数据模型"""
    question_id: str
    assignment_id: str
    code: str
    language: str
    student_user_id: str

    # 校验：code 不能为空
    @field_validator('code')
    def code_not_empty(cls, v):
        if not v or len(v.strip()) == 0:
            raise HTTPException(status_code=400, detail="提交的代码不能为空")
        return v

    # 校验：student_user_id 格式合法（学号格式）
    @field_validator('student_user_id')
    def student_id_check(cls, v):
        if not re.match(r'^[0-9]+$', v):
            raise HTTPException(status_code=400, detail="学号必须为纯数字")
        return v

# ===================== 工具函数 =====================
async def async_http_request(method: str, url: str, **kwargs) -> Dict[str, Any]:
    """通用异步HTTP请求工具，具备重试机制和日志记录。"""
    for retry in range(MAX_RETRY_COUNT):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(method, url, timeout=REQUEST_TIMEOUT, **kwargs)
                # 记录接口调用日志
                logger.info(f"接口调用 | {method} {url} | 请求参数={kwargs.get('json', {})} | 状态码={response.status_code}")
                response.raise_for_status()  # 抛出HTTP异常
                return response.json()
        except Exception as e:
            error_msg = f"第{retry + 1}次请求失败：{str(e)}"
            logger.error(error_msg)
            if retry == MAX_RETRY_COUNT - 1:
                raise  # 最后一次重试失败，向外抛出异常
            await asyncio.sleep(RETRY_INTERVAL)

# =====================  核心业务逻辑 =====================
async def call_b3_evaluate(submission_id: str, question_id: str, code: str, language: str) -> Dict[str, Any]:
    """调用B3动态测评接口"""
    payload = {
        "submission_id": submission_id,
        "question_id": question_id,
        "submitted_code": code,
        "language": language
    }
    return await async_http_request("POST", B3_EVALUATE_URL, json=payload)

async def write_result_to_b4(submission_id: str, result_data: Dict[str, Any]) -> bool:
    """将测评结果回写到B4系统"""
    url = B4_RESULT_WRITE_URL.format(submission_id=submission_id)
    await async_http_request("PATCH", url, json=result_data)
    logger.info(f"任务ID={submission_id} | B4结果回写成功")
    return True

async def execute_evaluation_flow(task: Dict[str, Any]):
    """完整的测评流程：调用B3测评 -> 回写结果到B4"""
    submission_id = task["submission_id"]
    try:
        # 步骤1：调用B3进行测评
        b3_result = await call_b3_evaluate(
            submission_id=submission_id,
            question_id=task["question_id"],
            code=task["code"],
            language=task["language"]
        )

        # 步骤2：构造回写B4的数据(此处做为模拟，具体返回的评测须结合本模块的静态测评结果)
        write_data = {
            "status": "COMPLETED", #状态
            "overall_score": b3_result.get("score", 0), #总分
            "passed_count": b3_result.get("passed_count", 0), #正确用例数
            "total_count": b3_result.get("total_count", 0), #总用例数
            "overall_comment": b3_result.get("comment", "测评完成"), #评语
            "static_issues": b3_result.get("static_issues", []), #问题列表
            "case_results": b3_result.get("case_results", []) #详细结果
        }

        # 步骤3：回写结果到B4
        await write_result_to_b4(submission_id, write_data)

    except Exception as e:
        # 发生异常时，回写错误状态到B4
        error_data = {"status": "ERROR", "error_msg": str(e)}
        await write_result_to_b4(submission_id, error_data)
        logger.error(f"任务ID={submission_id} | 测评流程执行失败：{str(e)}")

    if task in task_list:
        task_list.remove(task) #处理完->删除

# =====================  API 接口 =====================
@app.post("/api/v1/submission", summary="提交代码进行测评")
def submit_code(data: SubmitRequest, background_tasks: BackgroundTasks):
    """
    接收代码提交请求，并在后台异步执行测评流程。
    """
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

    # 将测评任务添加到后台任务队列，立即返回响应
    background_tasks.add_task(execute_evaluation_flow, task)

    logger.info(f"接收到新提交 | 任务ID={submission_id} | 学生ID={data.student_user_id}")
    return {
        "submission_id": submission_id,
        "status": "RECEIVED",
        "message": "代码接收成功，测评任务已在后台启动"
    }

# ===================== 服务启动 =====================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("test:app", host="0.0.0.0", port=8002, reload=True)