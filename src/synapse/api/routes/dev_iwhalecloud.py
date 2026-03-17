from __future__ import annotations

import logging
from datetime import datetime, timedelta

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from synapse.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

DEV_IWHALECLOUD_BASE_URL = "https://dev.iwhalecloud.com"  # 研发云地址
DEV_IWHALECLOUD_AUTHORIZATION = "Bearer 524a0e0b1d6545dcaf60a0d8e7cd12a8"  # 研发云API Token
DEV_IWHALECLOUD_PROJECT_SAPCE_ID = 562722  # xmjfbss 项目空间ID
DEV_IWHALECLOUD_ONLINE_PROJECT_ID = 162423 # 在线项目ID [162423]国内-BSS-2026-在线研发-计费-计费账务电信域在线研发项目
DEV_IWHALECLOUD_CONTRACT_PROJECT_ID = 161616 # 合同项目ID [161616]中国电信2026年北京公司计费中心平台升级研发工程

def _forward_response(resp: httpx.Response) -> JSONResponse:
    """统一处理上游响应：200 透传 JSON，429/503 抛异常，其余 502。"""
    if resp.status_code == 200:
        try:
            return JSONResponse(status_code=200, content=resp.json())
        except ValueError:
            return JSONResponse(status_code=200, content={"code": "200", "msg": "OK", "data": resp.text})
    if resp.status_code in (429, 503):
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    raise HTTPException(
        status_code=502,
        detail=f"上游接口返回非预期状态码 {resp.status_code}: {resp.text}",
    )


def _headers(content_type: str | None = "application/json") -> dict:
    h = {"Authorization": DEV_IWHALECLOUD_AUTHORIZATION}
    if content_type:
        h["Content-Type"] = content_type
    return h

# {
#   "taskTitle": "",
#   "comments": "",
#   "zmpProjectId": 0,
#   "ownerUserCode": "",
#   "createUserCode": "",
#   "expectPublishDate": "2025-07-01",
#   "expectOnlineDate": "2025-07-02",
#   "taskPri": 0,
#   "taskClassification": "",
#   "attachList": [
#     {
#       "fileName": "",
#       "filePath": "",
#       "fileSize": 0
#     }
#   ],
#   "taskSrc": "",
#   "projectId": "可以在研发云首页右上角点击项目空间名称进入详情界面查看该标志",
#   "productVersionId": 0,
#   "contractProjectId": 0
# }
class CreateRequirementRequest(BaseModel):
    taskTitle: str = Field(..., description="需求标题") # 必填
    comments: str = Field(..., description="需求描述") # 必填
    zmpProjectId: int = Field(..., description="鲸加项目ID") # 必填-在线项目ID
    ownerUserCode: str = Field(..., description="负责人工号") # 必填
    createUserCode: str = Field(..., description="创建人工号") # 必填
    expectPublishDate: str | None = Field(None, description="计划发布时间") # 可选
    expectOnlineDate: str | None = Field(None, description="计划上线时间") # 可选
    taskPri: int | None = Field(None, description="优先级") # 可选
    taskClassification: str | None = Field(None, description="领域") # 可选
    attachList: list[dict] | None = Field(None, description="附件列表") # 可选
    taskSrc: str = Field(..., description="需求类型") # 必填
    projectId: int = Field(..., description="项目空间ID") # 必填
    productVersionId: int | None = Field(None, description="产品版本ID") # 可选
    contractProjectId: int | None = Field(None, description="合同项目ID") # 可选

def _build_create_requirement_payload(body: CreateRequirementRequest) -> dict:
    # 必填字段：直接从 body 取
    payload: dict = {
        "taskTitle": body.taskTitle,
        "comments": body.comments,
        "zmpProjectId": body.zmpProjectId,
        "ownerUserCode": body.ownerUserCode,
        "createUserCode": body.createUserCode,
        "taskSrc": body.taskSrc,
        "projectId": body.projectId,
    }

    # 可选字段：根据“是否传值 / 是否需要默认值”决定是否写入 payload
    today = datetime.utcnow().date()

    # expectPublishDate：前端未传则默认 当前时间 + 1 个月
    if body.expectPublishDate is not None:
        payload["expectPublishDate"] = body.expectPublishDate
    else:
        payload["expectPublishDate"] = (today + timedelta(days=30)).strftime("%Y-%m-%d")

    # expectOnlineDate：前端未传则默认 当前时间 + 1 个月 + 1 周
    if body.expectOnlineDate is not None:
        payload["expectOnlineDate"] = body.expectOnlineDate
    else:
        payload["expectOnlineDate"] = (today + timedelta(days=37)).strftime("%Y-%m-%d")

    # taskPri：未传则默认 2
    payload["taskPri"] = body.taskPri if body.taskPri is not None else 2

    # taskClassification / productVersionId / contractProjectId / attachList：未传则不下发，让对端按“空”处理
    if body.taskClassification is not None:
        payload["taskClassification"] = body.taskClassification

    if body.productVersionId is not None:
        payload["productVersionId"] = body.productVersionId

    if body.contractProjectId is not None:
        payload["contractProjectId"] = body.contractProjectId

    if body.attachList is not None:
        payload["attachList"] = body.attachList

    return payload

# --- 任务/评论/影响/变更/分支 请求体 ---
# CreateTaskRequest 全量请求样例：
# {
#   "taskNo": "",
#   "taskTitle": "",
#   "comments": "",
#   "ownerUserCode": "",
#   "projectId": 0,
#   "productModuleName": "",
#   "branchVersionName": "",
#   "mainBranchVersionTaskNo": "",
#   "taskClassification": "FUNCTION",
#   "taskPri": 5
# }
class CreateTaskRequest(BaseModel):
    taskNo: str= Field(..., description="需求单号")
    taskTitle: str = Field(..., description="标题")
    comments: str = Field(..., description="描述信息")
    ownerUserCode: str = Field(..., description="负责人工号")
    projectId: int | None = Field(None, description="项目空间标志:与productModuleName必须二选一传值")
    productModuleName: str | None = Field(None, description="应用模块名称:与projectId必须二选一传值")
    branchVersionName: str | None = Field(None, description="产品分支名称:可以是主产品分支,也可以是Trunk产品分支")
    mainBranchVersionTaskNo: str | None = Field(None, description="Trunk分支关联的主分支单号")
    taskClassification: str | None = Field(None, description="领域:TECH-技术,FUNCTION-功能,SECURITY-安全,PERFORMANCE-性能,USE_OPTIMIZATION-体验,示例值(FUNCTION)")
    taskPri: int | None = Field(None, description="优先级:5-较低,6-普通,7-紧急,8-非常紧急,示例值(5)")


def _build_create_task_payload(body: CreateTaskRequest) -> dict:
    payload: dict = {
        "taskTitle": body.taskTitle,
        "comments": body.comments,
        "ownerUserCode": body.ownerUserCode,
    }
    if body.projectId is not None:
        payload["projectId"] = body.projectId
    if body.productModuleName is not None:
        payload["productModuleName"] = body.productModuleName
    if body.branchVersionName is not None:
        payload["branchVersionName"] = body.branchVersionName
    if body.mainBranchVersionTaskNo is not None:
        payload["mainBranchVersionTaskNo"] = body.mainBranchVersionTaskNo
    if body.taskClassification is not None:
        payload["taskClassification"] = body.taskClassification
    if body.taskPri is not None:
        payload["taskPri"] = body.taskPri
    return payload


# UpdateTaskPatchRequest 全量请求样例：
# {
#   "taskNo": "",
#   "patchName": ""
# }
class UpdateTaskPatchRequest(BaseModel):
    taskNo: str = Field(..., description="任务单号")
    patchName: str = Field(..., description="补丁计划名称")


def _build_update_task_patch_payload(body: UpdateTaskPatchRequest) -> dict:
    return {"patchName": body.patchName}


# TransferTaskStageRequest 全量请求样例：
# {
#   "taskNo": "",
#   "ownerUserCode": "",
#   "operateUserCode": "",
#   "taskFlowStageId": 0,
#   "comments": ""
# }
class TransferTaskStageRequest(BaseModel):
    taskNo: str = Field(..., description="任务单号")
    ownerUserCode: str = Field(..., description="目标处理人工号")
    operateUserCode: str = Field(..., description="当前操作人工号")
    taskFlowStageId: int = Field(..., description="目标状态ID")
    comments: str = Field("", description="转单备注")


def _build_transfer_task_stage_payload(body: TransferTaskStageRequest) -> dict:
    return {
        "ownerUserCode": body.ownerUserCode,
        "operateUserCode": body.operateUserCode,
        "taskFlowStageId": body.taskFlowStageId,
        "comments": body.comments or "",
    }


# CreateCommentRequest 全量请求样例：
# {
#   "taskNo": "",
#   "comments": ""
# }
class CreateCommentRequest(BaseModel):
    taskNo: str = Field(..., description="任务单号")
    comments: str = Field(..., description="评论内容")


def _build_create_comment_payload(body: CreateCommentRequest) -> dict:
    return {"comments": body.comments}


# CreateImpactDetailRequest 全量请求样例：
# {
#   "taskNo": "",
#   "changeContent": "",
#   "changeContentEn": "",
#   "bizImpact": "",
#   "bizImpactEn": "",
#   "projectImpact": "",
#   "projectImpactEn": ""
# }
class CreateImpactDetailRequest(BaseModel):
    taskNo: str = Field(..., description="任务单号")
    changeContent: str = Field(..., description="修改内容")
    changeContentEn: str = Field("", description="修改内容(英文)")
    bizImpact: str = Field(..., description="业务影响说明")
    bizImpactEn: str = Field("", description="业务影响说明(英文)")
    projectImpact: str = Field("", description="其他项目影响说明")
    projectImpactEn: str = Field("", description="其他项目影响说明(英文)")


def _build_create_impact_detail_payload(body: CreateImpactDetailRequest) -> dict:
    return {
        "changeContent": body.changeContent,
        "changeContentEn": body.changeContentEn,
        "bizImpact": body.bizImpact,
        "bizImpactEn": body.bizImpactEn,
        "projectImpact": body.projectImpact,
        "projectImpactEn": body.projectImpactEn,
    }


# CreateChangeDetailRequest 全量请求样例：
# {
#   "taskNo": "",
#   "comments": "",
#   "menuComments": "",
#   "apigComments": "",
#   "webuiComments": ""
# }
class CreateChangeDetailRequest(BaseModel):
    taskNo: str = Field(..., description="任务单号")
    comments: str = Field(..., description="配置变更描述")
    menuComments: str = Field("", description="菜单变更描述")
    apigComments: str = Field("", description="接口变更描述")
    webuiComments: str = Field("", description="页面变更描述")


def _build_create_change_detail_payload(body: CreateChangeDetailRequest) -> dict:
    return {
        "comments": body.comments,
        "menuComments": body.menuComments,
        "apigComments": body.apigComments,
        "webuiComments": body.webuiComments,
    }


# CreateFeatureBranchRequest 全量请求样例：
# {
#   "taskNo": "",
#   "branchName": ""
# }
class CreateFeatureBranchRequest(BaseModel):
    taskNo: str = Field(..., description="任务单号")
    branchName: str = Field(..., description="特性分支名称")


def _build_create_feature_branch_payload(body: CreateFeatureBranchRequest) -> dict:
    return {"taskNo": body.taskNo, "branchName": body.branchName}


@router.post("/api/dev/iwhalecloud/create_requirement")
async def create_requirement(body: CreateRequirementRequest):
    """
    新增需求（国内）。
    转调：POST /portal/ai-gateway/devspace/rpc/v3/user-story/inner
    """
    url = f"{DEV_IWHALECLOUD_BASE_URL}/portal/ai-gateway/devspace/rpc/v3/user-story/inner"
    payload = _build_create_requirement_payload(body)
    logger.debug("create_requirement url:%s, payload:%s", url, payload)
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, headers=_headers(), json=payload)
    except httpx.RequestError as exc:
        logger.exception("调用研发云创建需求接口异常: %s", exc)
        raise HTTPException(status_code=503, detail=f"调用研发云接口异常: {exc}")

    return _forward_response(resp)


@router.post("/api/dev/iwhalecloud/create_task")
async def create_task(body: CreateTaskRequest):
    """
    新增任务（国内）。
    转调：POST /portal/ai-gateway/devspace/rpc/v3/user-story/{taskNo}/work-item/inner
    """
    if not body.taskNo:
        raise HTTPException(status_code=400, detail="taskNo 不能为空")
    if body.projectId is None and body.productModuleName is None:
        raise HTTPException(status_code=400, detail="projectId 与 productModuleName 必须二选一传值")
    url = f"{DEV_IWHALECLOUD_BASE_URL}/portal/ai-gateway/devspace/rpc/v3/user-story/{body.taskNo}/work-item/inner"
    payload = _build_create_task_payload(body)
    logger.debug("create_task url:%s, payload:%s", url, payload)
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, headers=_headers(), json=payload)
    except httpx.RequestError as exc:
        logger.exception("调用研发云创建任务接口异常: %s", exc)
        raise HTTPException(status_code=503, detail=f"调用研发云接口异常: {exc}")
    return _forward_response(resp)


@router.post("/api/dev/iwhalecloud/update_task_patch")
async def update_task_patch(body: UpdateTaskPatchRequest):
    """
    修改任务的补丁计划。
    转调：POST /portal/ai-gateway/devspace/rpc/v3/task/{taskNo}/patch
    """
    if not body.taskNo:
        raise HTTPException(status_code=400, detail="taskNo 不能为空")
    url = f"{DEV_IWHALECLOUD_BASE_URL}/portal/ai-gateway/devspace/rpc/v3/task/{body.taskNo}/patch"
    payload = _build_update_task_patch_payload(body)
    logger.debug("update_task_patch url:%s, payload:%s", url, payload)
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, headers=_headers(), json=payload)
    except httpx.RequestError as exc:
        logger.exception("调用研发云更新补丁接口异常: %s", exc)
        raise HTTPException(status_code=503, detail=f"调用研发云接口异常: {exc}")
    return _forward_response(resp)


@router.post("/api/dev/iwhalecloud/transfer_task_stage")
async def transfer_task_stage(body: TransferTaskStageRequest):
    """
    转单：将事务单流转到指定状态并指定处理人。
    转调：POST /portal/ai-gateway/devspace/rpc/v3/task/{taskNo}/stage
    """
    if not body.taskNo:
        raise HTTPException(status_code=400, detail="taskNo 不能为空")
    url = f"{DEV_IWHALECLOUD_BASE_URL}/portal/ai-gateway/devspace/rpc/v3/task/{body.taskNo}/stage"
    payload = _build_transfer_task_stage_payload(body)
    logger.debug("transfer_task_stage url:%s, payload:%s", url, payload)
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, headers=_headers(), json=payload)
    except httpx.RequestError as exc:
        logger.exception("调用研发云转单接口异常: %s", exc)
        raise HTTPException(status_code=503, detail=f"调用研发云接口异常: {exc}")
    return _forward_response(resp)


@router.post("/api/dev/iwhalecloud/create_comment")
async def create_comment(body: CreateCommentRequest):
    """
    新增评论。
    转调：POST /portal/ai-gateway/devspace/rpc/v3/task/task-no/{taskNo}/comment
    """
    if not body.taskNo:
        raise HTTPException(status_code=400, detail="taskNo 不能为空")
    url = f"{DEV_IWHALECLOUD_BASE_URL}/portal/ai-gateway/devspace/rpc/v3/task/task-no/{body.taskNo}/comment"
    payload = _build_create_comment_payload(body)
    logger.debug("create_comment url:%s, payload:%s", url, payload)
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, headers=_headers(), json=payload)
    except httpx.RequestError as exc:
        logger.exception("调用研发云新增评论接口异常: %s", exc)
        raise HTTPException(status_code=503, detail=f"调用研发云接口异常: {exc}")
    return _forward_response(resp)


@router.post("/api/dev/iwhalecloud/create_impact_detail")
async def create_impact_detail(body: CreateImpactDetailRequest):
    """
    新增影响说明。
    转调：POST /portal/ai-gateway/devspace/rpc/v3/task/{taskNo}/impact/create
    """
    if not body.taskNo:
        raise HTTPException(status_code=400, detail="taskNo 不能为空")
    url = f"{DEV_IWHALECLOUD_BASE_URL}/portal/ai-gateway/devspace/rpc/v3/task/{body.taskNo}/impact/create"
    payload = _build_create_impact_detail_payload(body)
    logger.debug("create_impact_detail url:%s, payload:%s", url, payload)
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, headers=_headers(), json=payload)
    except httpx.RequestError as exc:
        logger.exception("调用研发云新增影响说明接口异常: %s", exc)
        raise HTTPException(status_code=503, detail=f"调用研发云接口异常: {exc}")
    return _forward_response(resp)


@router.post("/api/dev/iwhalecloud/create_change_detail")
async def create_change_detail(body: CreateChangeDetailRequest):
    """
    新增变更说明。
    转调：POST /portal/ai-gateway/devspace/rpc/v3/task/{taskNo}/config/create
    """
    if not body.taskNo:
        raise HTTPException(status_code=400, detail="taskNo 不能为空")
    url = f"{DEV_IWHALECLOUD_BASE_URL}/portal/ai-gateway/devspace/rpc/v3/task/{body.taskNo}/config/create"
    payload = _build_create_change_detail_payload(body)
    logger.debug("create_change_detail url:%s, payload:%s", url, payload)
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, headers=_headers(), json=payload)
    except httpx.RequestError as exc:
        logger.exception("调用研发云新增变更说明接口异常: %s", exc)
        raise HTTPException(status_code=503, detail=f"调用研发云接口异常: {exc}")
    return _forward_response(resp)


@router.post("/api/dev/iwhalecloud/create_feature_branch")
async def create_feature_branch(body: CreateFeatureBranchRequest):
    """
    创建特性分支。
    转调：POST /portal/ai-gateway/devspace/rpc/v3/task-branch/feature/create
    """
    if not body.taskNo:
        raise HTTPException(status_code=400, detail="taskNo 不能为空")
    if not body.branchName:
        raise HTTPException(status_code=400, detail="branchName 不能为空")
    url = f"{DEV_IWHALECLOUD_BASE_URL}/portal/ai-gateway/devspace/rpc/v3/task-branch/feature/create"
    payload = _build_create_feature_branch_payload(body)
    logger.debug("create_feature_branch url:%s, payload:%s", url, payload)
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, headers=_headers(), json=payload)
    except httpx.RequestError as exc:
        logger.exception("调用研发云创建特性分支接口异常: %s", exc)
        raise HTTPException(status_code=503, detail=f"调用研发云接口异常: {exc}")
    return _forward_response(resp)


@router.post("/api/dev/iwhalecloud/login")
async def login(request: Request):
    """
    登录研发云。
    
    """
    return JSONResponse(status_code=200, content={"mesage": "登录成功"})