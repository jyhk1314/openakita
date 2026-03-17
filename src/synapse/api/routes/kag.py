"""KAG 知识库模块路由。"""

from __future__ import annotations

import asyncio
import base64
import io
import logging
import re
import sys
import tempfile
import time
from enum import Enum
from pathlib import Path
from typing import Optional

import httpx
import requests as _req
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from synapse.api.schemas import error_response, success_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/kag")

try:
    from knext.schema.model.base import ConstraintTypeEnum, PropertyGroupEnum
    from knext.schema.model.property import Property
    from knext.schema.model.spg_type import EntityType
except ImportError:
    EntityType = None  # type: ignore[assignment,misc]
    Property = None  # type: ignore[assignment]
    PropertyGroupEnum = None  # type: ignore[assignment]
    ConstraintTypeEnum = None  # type: ignore[assignment]


class DocType(str, Enum):
    """文档类型枚举"""
    PUBLIC_SPEC = "公共规范"
    PRODUCT_SPEC = "产品规范"
    PRODUCT_DELIVERY = "产品交付"
    PRODUCT_DESIGN = "产品设计"
    PRODUCT_REQUIREMENT = "产品需求文档"


class KAGDocType(str, Enum):
    """KAG 知识库文档类型"""
    REQUIREMENT = "需求"
    ARCHITECTURE = "架构"
    DESIGN = "设计"
    DELIVERY = "交付"
    MANUAL = "手册"

def get_requirement_schema_types(namespace: str):
    """获取需求文档的 schema 类型定义"""
    requirement = EntityType(
        name=f"{namespace}.Requirement",
        name_zh="需求",
        desc="软件系统中的需求",
        properties=[
            Property(
                name="name",
                object_type_name="Text",
                name_zh="需求名称",
                desc="需求的名称",
                property_group=PropertyGroupEnum.Subject,
                constraint={ConstraintTypeEnum.NotNull: None}
            ),
            Property(
                name="module",
                object_type_name="Text",
                name_zh="模块",
                desc="需求所属模块",
                property_group=PropertyGroupEnum.Subject
            ),
            Property(
                name="type",
                object_type_name="Text",
                name_zh="类型",
                desc="需求类型",
                property_group=PropertyGroupEnum.Subject
            ),
            Property(
                name="workload",
                object_type_name="Text",
                name_zh="工作量",
                desc="需求工作量评估",
                property_group=PropertyGroupEnum.Subject
            ),
            Property(
                name="devCount",
                object_type_name="Integer",
                name_zh="研发人数",
                desc="需求研发人数",
                property_group=PropertyGroupEnum.Subject
            ),
            Property(
                name="complexity",
                object_type_name="Text",
                name_zh="复杂度",
                desc="需求复杂度",
                property_group=PropertyGroupEnum.Subject
            ),
            Property(
                name="owner",
                object_type_name="Text",
                name_zh="负责人",
                desc="需求负责人",
                property_group=PropertyGroupEnum.Subject
            ),
        ],
        relations=[]
    )
    return [requirement]


def get_architecture_schema_types(namespace: str):
    """获取架构文档的 schema 类型定义"""
    architecture = EntityType(
        name=f"{namespace}.Architecture",
        name_zh="架构",
        desc="系统架构设计",
        properties=[
            Property(
                name="name",
                object_type_name="Text",
                name_zh="架构名称",
                desc="架构的名称",
                property_group=PropertyGroupEnum.Subject,
                constraint={ConstraintTypeEnum.NotNull: None}
            ),
            Property(
                name="module",
                object_type_name="Text",
                name_zh="模块",
                desc="所属模块",
                property_group=PropertyGroupEnum.Subject
            ),
            Property(
                name="layer",
                object_type_name="Text",
                name_zh="层次",
                desc="架构层次（如：应用层/服务层/数据层）",
                property_group=PropertyGroupEnum.Subject
            ),
            Property(
                name="component",
                object_type_name="Text",
                name_zh="组件",
                desc="涉及的核心组件或模块",
                property_group=PropertyGroupEnum.Subject
            ),
            Property(
                name="technology",
                object_type_name="Text",
                name_zh="技术栈",
                desc="使用的技术栈或框架",
                property_group=PropertyGroupEnum.Subject
            ),
            Property(
                name="pattern",
                object_type_name="Text",
                name_zh="架构模式",
                desc="采用的架构模式（如：微服务/单体/事件驱动）",
                property_group=PropertyGroupEnum.Subject
            ),
            Property(
                name="dependency",
                object_type_name="Text",
                name_zh="依赖关系",
                desc="组件间的依赖关系说明",
                property_group=PropertyGroupEnum.Subject
            ),
            Property(
                name="owner",
                object_type_name="Text",
                name_zh="负责人",
                desc="架构负责人",
                property_group=PropertyGroupEnum.Subject
            ),
        ],
        relations=[]
    )
    return [architecture]


def get_design_schema_types(namespace: str):
    """获取设计方案文档的 schema 类型定义"""
    design = EntityType(
        name=f"{namespace}.Design",
        name_zh="设计方案",
        desc="软件系统的设计方案",
        properties=[
            Property(
                name="name",
                object_type_name="Text",
                name_zh="方案名称",
                desc="设计方案的名称",
                property_group=PropertyGroupEnum.Subject,
                constraint={ConstraintTypeEnum.NotNull: None}
            ),
            Property(
                name="module",
                object_type_name="Text",
                name_zh="模块",
                desc="设计方案所属模块",
                property_group=PropertyGroupEnum.Subject
            ),
            Property(
                name="type",
                object_type_name="Text",
                name_zh="设计类型",
                desc="设计类型（如：概要设计/详细设计/数据库设计/接口设计）",
                property_group=PropertyGroupEnum.Subject
            ),
            Property(
                name="relatedRequirement",
                object_type_name="Text",
                name_zh="关联需求",
                desc="关联的需求编号或名称",
                property_group=PropertyGroupEnum.Subject
            ),
            Property(
                name="dataModel",
                object_type_name="Text",
                name_zh="数据模型",
                desc="涉及的数据模型或表结构说明",
                property_group=PropertyGroupEnum.Subject
            ),
            Property(
                name="configModel",
                object_type_name="Text",
                name_zh="配置说明",
                desc="涉及的配置说明",
                property_group=PropertyGroupEnum.Subject
            ),
            Property(
                name="interface",
                object_type_name="Text",
                name_zh="接口说明",
                desc="对外暴露的接口说明",
                property_group=PropertyGroupEnum.Subject
            ),
            Property(
                name="owner",
                object_type_name="Text",
                name_zh="负责人",
                desc="设计方案负责人",
                property_group=PropertyGroupEnum.Subject
            ),
        ],
        relations=[]
    )
    return [design]


def get_delivery_schema_types(namespace: str):
    """获取交付文档的 schema 类型定义"""
    delivery = EntityType(
        name=f"{namespace}.Delivery",
        name_zh="交付文档",
        desc="产品交付相关文档，包括版本发布、部署手册、复盘报告等",
        properties=[
            Property(
                name="name",
                object_type_name="Text",
                name_zh="文档名称",
                desc="交付文档的名称",
                property_group=PropertyGroupEnum.Subject,
                constraint={ConstraintTypeEnum.NotNull: None}
            ),
            Property(
                name="type",
                object_type_name="Text",
                name_zh="交付类型",
                desc="交付类型（如：版本发布/镜像/测试报告/部署手册/运维手册/复盘报告等）",
                property_group=PropertyGroupEnum.Subject
            ),
            Property(
                name="version",
                object_type_name="Text",
                name_zh="版本号",
                desc="对应的产品版本号",
                property_group=PropertyGroupEnum.Subject
            ),
            Property(
                name="releaseDate",
                object_type_name="Text",
                name_zh="发布日期",
                desc="版本或文档发布日期",
                property_group=PropertyGroupEnum.Subject
            ),
            Property(
                name="environment",
                object_type_name="Text",
                name_zh="部署环境",
                desc="适用的部署环境（如：开发/测试/生产）",
                property_group=PropertyGroupEnum.Subject
            ),
            Property(
                name="changeLog",
                object_type_name="Text",
                name_zh="变更记录",
                desc="版本变更或问题复盘的主要内容摘要",
                property_group=PropertyGroupEnum.Subject
            ),
            Property(
                name="owner",
                object_type_name="Text",
                name_zh="负责人",
                desc="交付文档负责人",
                property_group=PropertyGroupEnum.Subject
            ),
        ],
        relations=[]
    )
    return [delivery]


def get_manual_schema_types(namespace: str):
    """获取使用手册文档的 schema 类型定义"""
    manual = EntityType(
        name=f"{namespace}.Manual",
        name_zh="使用手册",
        desc="产品使用手册，包括操作指南、配置说明等",
        properties=[
            Property(
                name="name",
                object_type_name="Text",
                name_zh="手册名称",
                desc="使用手册的名称",
                property_group=PropertyGroupEnum.Subject,
                constraint={ConstraintTypeEnum.NotNull: None}
            ),
            Property(
                name="type",
                object_type_name="Text",
                name_zh="手册类型",
                desc="手册类型（如：使用手册/配置手册/运维手册/API手册）",
                property_group=PropertyGroupEnum.Subject
            ),
            Property(
                name="targetAudience",
                object_type_name="Text",
                name_zh="目标受众",
                desc="手册面向的用户群体（如：最终用户/运维人员/开发人员）",
                property_group=PropertyGroupEnum.Subject
            ),
            Property(
                name="version",
                object_type_name="Text",
                name_zh="版本号",
                desc="手册对应的产品版本",
                property_group=PropertyGroupEnum.Subject
            ),
            Property(
                name="chapter",
                object_type_name="Text",
                name_zh="章节",
                desc="手册的主要章节结构",
                property_group=PropertyGroupEnum.Subject
            ),
            Property(
                name="prerequisite",
                object_type_name="Text",
                name_zh="前置条件",
                desc="使用前需满足的环境或条件",
                property_group=PropertyGroupEnum.Subject
            ),
            Property(
                name="owner",
                object_type_name="Text",
                name_zh="负责人",
                desc="手册负责人",
                property_group=PropertyGroupEnum.Subject
            ),
        ],
        relations=[]
    )
    return [manual]


def get_schema_types_by_doc_type(doc_type: KAGDocType, namespace: str):
    """根据文档类型获取对应的 schema 类型列表"""
    mapping = {
        KAGDocType.REQUIREMENT: get_requirement_schema_types,
        KAGDocType.ARCHITECTURE: get_architecture_schema_types,
        KAGDocType.DESIGN: get_design_schema_types,
        KAGDocType.DELIVERY: get_delivery_schema_types,
        KAGDocType.MANUAL: get_manual_schema_types,
    }
    func = mapping.get(doc_type)
    return func(namespace) if func else []





def _parse_doc_type_from_name(name: str) -> KAGDocType:
    """从 name（格式：产品名称_文档类型）中解析文档类型。"""
    parts = name.rsplit("_", 1)
    if len(parts) != 2:
        raise ValueError(f"name 格式不正确，期望「产品名称_文档类型」，实际：{name!r}")
    doc_type_str = parts[1]
    try:
        return KAGDocType(doc_type_str)
    except ValueError:
        valid = [e.value for e in KAGDocType]
        raise ValueError(f"未知文档类型 {doc_type_str!r}，可选值：{valid}")


class CreateKagProjectRequest(BaseModel):
    name: str
    description: str | None = None


@router.post("/create_kag_project")
async def create_kag_project(req: CreateKagProjectRequest):
    """创建 KAG 知识库，并根据 name 中的文档类型初始化对应 Schema。name 格式：产品名称_文档类型"""
    import uuid

    from openakita.config import settings

    host_addr = settings.kag_api_base
    if not host_addr:
        logger.error("创建 KAG 知识库失败：未配置 kag_api_base")
        return JSONResponse(
            status_code=500,
            content=error_response(500, "KAG_API_BASE 未配置"),
        )

    try:
        doc_type = _parse_doc_type_from_name(req.name)
    except ValueError as e:
        logger.error(f"创建 KAG 知识库失败：解析文档类型出错，name={req.name!r}，{e}")
        return JSONResponse(
            status_code=400,
            content=error_response(400, str(e)),
        )

    #必须以字母开头
    raw = uuid.uuid4().hex
    namespace = raw if raw[0].isalpha() else "n" + raw[:-1]

    project_config = {
        "project": {
            "host_addr": host_addr,
            "id": None,
            "namespace": namespace,
            "language": "zh",
            "biz_scene": "default",
            "visibility": "PRIVATE",
            "tag": "PUBLIC-NET",
        },
        "chat_llm": {
            "type": settings.kag_chat_llm_type,
            "base_url": settings.kag_chat_llm_base_url,
            "api_key": settings.kag_chat_llm_api_key,
            "model": settings.kag_chat_llm_model,
            "enable_check": False,
        },
        "openie_llm": {
            "type": settings.kag_openie_llm_type,
            "base_url": settings.kag_openie_llm_base_url,
            "api_key": settings.kag_openie_llm_api_key,
            "model": settings.kag_openie_llm_model,
            "enable_check": False,
        },
        "vectorizer": {
            "type": settings.kag_vectorizer_type,
            "base_url": settings.kag_vectorizer_base_url,
            "api_key": settings.kag_vectorizer_api_key,
            "modelType": "embedding",
            "model": settings.kag_vectorizer_model,
            "vector_dimensions": settings.kag_vectorizer_dimensions,
            "enable_check": False,
        },
        "log": {"level": "INFO"},
    }

    try:
        from knext.project.client import ProjectClient
        from knext.schema.client import SchemaClient
    except ImportError as e:
        logger.error(f"创建 KAG 知识库失败：KAG 依赖未安装，{e}")
        return JSONResponse(
            status_code=500,
            content=error_response(500, "KAG 依赖未安装", str(e)),
        )

    try:
        project_client = ProjectClient(host_addr=host_addr)
        project = project_client.create(
            name=req.name,
            namespace=namespace,
            config=project_config,
            desc=req.description,
            tag="PUBLIC-NET",
        )
    except Exception as e:
        logger.error(f"创建 KAG 项目失败：name={req.name!r}, namespace={namespace!r}，{e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(500, "创建项目失败", str(e)),
        )

    project_id = str(project.id)

    try:
        schema_client = SchemaClient(host_addr=host_addr, project_id=project_id)
        session = schema_client.create_session()
        schema_types = get_schema_types_by_doc_type(doc_type, namespace)
        for spg_type in schema_types:
            session.create_type(spg_type)
        session.commit()
    except Exception as e:
        logger.error(f"初始化 KAG Schema 失败：project_id={project_id}, doc_type={doc_type}，{e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(500, "初始化 Schema 失败", str(e)),
        )

    logger.info(f"KAG 知识库创建成功：project_id={project_id}, name={req.name!r}, namespace={namespace!r}, doc_type={doc_type}")
    return success_response(
        data={
            "project_id": project_id,
            "name": req.name,
            "namespace": namespace,
            "doc_type": doc_type,
        },
        message="知识库创建成功",
    )


class SynDocToKagRequest(BaseModel):
    doc_id: int = Field(..., description="语雀文档 ID")
    project_id: str = Field(..., description="KAG 知识库 ID")


@router.post("/syn_doc_to_kag")
async def syn_doc_to_kag(req: SynDocToKagRequest):
    """从语雀下载 Markdown 文档，将图片转成文字描述，上传到 KAG 知识库。"""
    from openakita.config import settings

    # ── 前置校验 ──────────────────────────────────────────────────────────────
    if not settings.yuque_token:
        return JSONResponse(
            status_code=400,
            content=error_response(400, "未配置语雀 Token，请在系统设置中填写 yuque_token"),
        )
    if not settings.kag_api_base:
        return JSONResponse(
            status_code=500,
            content=error_response(500, "KAG_API_BASE 未配置"),
        )

    # ── Step 1: 从语雀下载 Markdown 文档 ─────────────────────────────────────
    api_base = settings.yuque_api_base
    headers = {
        "X-Auth-Token": settings.yuque_token,
        "Content-Type": "application/json",
        "User-Agent": "OpenAkita",
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{api_base}/repos/docs/{req.doc_id}",
                headers=headers,
                params={"raw": 1},
            )
            if resp.status_code == 401:
                return JSONResponse(
                    status_code=401,
                    content=error_response(401, "语雀 Token 无效或已过期"),
                )
            if resp.status_code == 404:
                return JSONResponse(
                    status_code=404,
                    content=error_response(404, f"语雀文档不存在：{req.doc_id}"),
                )
            if resp.status_code >= 400:
                return JSONResponse(
                    status_code=resp.status_code,
                    content=error_response(resp.status_code, f"获取语雀文档失败：{resp.text}"),
                )
            doc_data = resp.json()["data"]
    except httpx.TimeoutException:
        return JSONResponse(status_code=504, content=error_response(504, "请求语雀 API 超时"))
    except httpx.ConnectError as exc:
        return JSONResponse(status_code=502, content=error_response(502, f"无法连接语雀服务器：{exc}"))
    except Exception as exc:
        logger.error(f"获取语雀文档失败：{exc}", exc_info=True)
        return JSONResponse(status_code=500, content=error_response(500, f"获取语雀文档失败：{exc}"))

    doc_title: str = doc_data.get("title", f"doc_{req.doc_id}")
    md_content: str = doc_data.get("body", "")
    if not md_content:
        return JSONResponse(
            status_code=400,
            content=error_response(400, "文档内容为空，无法上传"),
        )
    logger.info(f"语雀文档下载成功：id={req.doc_id}, title={doc_title!r}, 字数={len(md_content)}")

    # ── Step 2: 清理语雀 Lake 格式残留的 HTML 标签 ────────────────────────────
    md_content = clean_lake_markdown(md_content)
    logger.debug(f"Lake 格式清理完成，清理后字数={len(md_content)}")

    # ── Step 3: 处理 Markdown 中的图片（下载 + Vision LLM 描述） ──────────────
    md_content = await asyncio.to_thread(
        _process_markdown_images,
        md_content,
        settings,
    )

    # ── Step 4: 上传到 KAG 知识库 ─────────────────────────────────────────────
    try:
        result = await asyncio.to_thread(
            _upload_markdown_to_kag,
            md_content,
            doc_title,
            req.project_id,
            settings,
        )
    except Exception as exc:
        logger.error(f"上传 KAG 失败：project_id={req.project_id}, doc_id={req.doc_id}, {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(500, f"上传 KAG 知识库失败：{exc}"),
        )

    logger.info(
        f"同步完成：doc_id={req.doc_id}, title={doc_title!r}, "
        f"project_id={req.project_id}, job_id={result.get('job_id')}"
    )
    return success_response(
        data={
            "doc_id": req.doc_id,
            "doc_title": doc_title,
            "project_id": req.project_id,
            "job_id": result.get("job_id"),
            "file_url": result.get("file_url"),
        },
        message="文档已提交到 KAG 知识库构建队列",
    )


# ── 图片处理辅助函数 ────────────────────────────────────────────────────────────

_IMG_PATTERN = re.compile(r'!\[([^\]]*)\]\((\S+?)(?:\s+"[^"]*")?\)')


def _process_markdown_images(md_content: str, settings) -> str:
    """下载 Markdown 中的图片，若启用 Vision LLM 则替换为文字描述，否则保留原引用。"""
    matches = _IMG_PATTERN.findall(md_content)
    if not matches:
        return md_content

    logger.info(f"检测到 {len(matches)} 张图片，开始处理…")
    url_to_desc: dict[str, str] = {}

    total = len(matches)
    unique_urls = {url for _, url in matches}
    logger.info(f"共 {total} 处图片引用，去重后 {len(unique_urls)} 张，逐一处理…")

    for idx, (alt, url) in enumerate(matches):
        if url in url_to_desc:
            logger.debug(f"[{idx + 1}/{total}] 跳过（已处理）：{url[:60]}")
            continue
        logger.info(f"[{idx + 1}/{total}] 下载图片：{url[:80]}")
        img_bytes = _download_image_bytes(url, idx)
        if img_bytes is None:
            logger.warning(f"[{idx + 1}/{total}] 下载失败，跳过：{url[:80]}")
            url_to_desc[url] = ""
            continue

        if settings.vision_enabled and settings.vision_api_key:
            logger.info(f"[{idx + 1}/{total}] 调用 Vision LLM 生成描述…")
            desc = _describe_image(img_bytes, idx, settings)
            url_to_desc[url] = desc
            if desc:
                logger.info(f"[{idx + 1}/{total}] 描述生成成功：{desc[:60]}…")
            else:
                logger.warning(f"[{idx + 1}/{total}] 描述生成为空，保留原图片引用")
        else:
            url_to_desc[url] = ""
        # 测试下载一张图片就可以
        break

    logger.info(f"图片处理完成：共 {len(unique_urls)} 张，有描述 {sum(1 for v in url_to_desc.values() if v)} 张")

    def _replace(m: re.Match) -> str:
        alt_text = m.group(1)
        url = m.group(2)
        desc = url_to_desc.get(url, "")
        if desc:
            return f"> 【图片描述】{desc}"
        return m.group(0)

    return _IMG_PATTERN.sub(_replace, md_content)


def _download_image_bytes(url: str, index: int) -> Optional[bytes]:
    """下载图片，返回字节数据；失败返回 None。"""
    try:
        import requests as _requests
        resp = _requests.get(url, timeout=30, stream=True)
        resp.raise_for_status()
        data = b"".join(resp.iter_content(chunk_size=8192))
        logger.debug(f"图片 [{index}] 下载成功：{url[:60]}, size={len(data)//1024}KB")
        return data
    except Exception as exc:
        logger.warning(f"图片 [{index}] 下载失败：{url[:60]}, {exc}")
        return None


def _compress_image_bytes(img_bytes: bytes, max_b64_bytes: int = 1 * 1024 * 1024) -> tuple[bytes, str]:
    """将图片字节压缩到 base64 后不超过 max_b64_bytes。"""
    try:
        from PIL import Image
        max_raw = int(max_b64_bytes * 0.75)
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        for quality in (85, 70, 55, 40):
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=quality, optimize=True)
            data = buf.getvalue()
            if len(data) <= max_raw:
                return data, "image/jpeg"
        w, h = img.size
        for scale in (0.75, 0.5, 0.35, 0.25):
            resized = img.resize((int(w * scale), int(h * scale)))
            buf = io.BytesIO()
            resized.save(buf, format="JPEG", quality=40, optimize=True)
            data = buf.getvalue()
            if len(data) <= max_raw:
                return data, "image/jpeg"
        return data, "image/jpeg"
    except Exception:
        return img_bytes, "image/jpeg"


def _describe_image(img_bytes: bytes, index: int, settings) -> str:
    """调用 Vision LLM 对图片生成中文描述；失败返回空字符串。"""
    try:
        import requests as _requests

        compressed, mime = _compress_image_bytes(img_bytes)
        b64 = base64.b64encode(compressed).decode()

        api_base = settings.vision_api_base or "https://api.openai.com/v1"
        if api_base.endswith("/chat/completions"):
            api_url = api_base
        elif api_base.endswith("/v1"):
            api_url = f"{api_base}/chat/completions"
        else:
            api_url = api_base.rstrip("/") + "/chat/completions"

        payload = {
            "model": settings.vision_model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                        {
                            "type": "text",
                            "text": (
                                "请用中文简洁描述图片的内容，"
                                "重点说明图片中展示的信息、界面元素或数据，不超过500字。"
                            ),
                        },
                    ],
                }
            ],
            "max_tokens": 1200,
        }
        resp = _requests.post(
            api_url,
            headers={"Authorization": f"Bearer {settings.vision_api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=120,
        )
        resp.raise_for_status()
        desc = resp.json()["choices"][0]["message"]["content"].strip()
        logger.debug(f"图片 [{index}] 描述生成成功：{desc[:50]}…")
        return desc
    except Exception as exc:
        logger.warning(f"图片 [{index}] Vision LLM 描述失败：{exc}")
        return ""

# ──清理语雀 Lake 格式残留的 HTML 标签--
def clean_lake_markdown(text: str) -> str:
    """
    清理语雀 Lake 格式残留的 HTML 标签，使输出成为干净的 Markdown。

    处理项：
    - <font style="...">文字</font>  → 文字
    - 表格行内 <br/> → " / "
    - 普通段落 <br/> → 换行
    - 空的 Markdown 强调符（去掉 font 标签后可能产生 __ ** `` 等空壳）
    - <u>文字</u> → 文字（Markdown 无下划线标准语法）
    """
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        is_table_row = re.search(r'(?<!\|)\|(?!\|)', line) is not None

        # <br/> 处理：表格内用 " / " 分隔，否则转换为真换行（后处理时会展开）
        if is_table_row:
            line = re.sub(r'<br\s*/?>', ' / ', line)
        else:
            line = re.sub(r'<br\s*/?>', '\n', line)

        # 剥离 <font ...>...</font>，保留内文
        line = re.sub(r'<font[^>]*>(.*?)</font>', r'\1', line, flags=re.DOTALL)

        # 剥离 <u>...</u>，保留内文
        line = re.sub(r'<u>(.*?)</u>', r'\1', line, flags=re.DOTALL)

        # 清理因去掉 font 标签后产生的空强调符：__ ** 等
        line = re.sub(r'\*{2}\s*\*{2}', '', line)
        line = re.sub(r'_{2}\s*_{2}', '', line)
        # 清理 _`_..._`_ 这类语雀混排斜体/代码嵌套 font 后的残留
        # 例：_<font>text</font>_`_<font>code</font>_`_ → _text_`code`
        # 先合并相邻的斜体标记：_text__more_ → _text more_（简单情况）
        line = re.sub(r'_\s*_', '', line)

        cleaned.append(line)

    return "\n".join(cleaned)

# ── KAG 上传辅助函数 ──────────────────────────────────────────────────────────

def _upload_markdown_to_kag(md_content: str, title: str, project_id: str, settings) -> dict:
    """将 Markdown 内容上传到 KAG 知识库。

    流程：写临时文件 → 上传文件拿 fileUrl → 提交构建任务。
    返回 {'job_id': ..., 'file_url': ...}。
    """
    import json as _json
    import requests as _requests

    host_addr = settings.kag_api_base
    filename = f"{title}.md"

    # 将 Markdown 内容写入临时文件
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", encoding="utf-8", delete=False
    ) as tmp:
        tmp_path = tmp.name
        tmp.write(f"# {title}\n\n{md_content}")

    try:
        session = _requests.Session()

        # ── Step 0: 登录，获取 session cookies ──────────────────────────────
        login_resp = session.post(
            f"{host_addr}/v1/accounts/login",
            json={"account": settings.kag_username, "password": settings.kag_password},
            timeout=30,
        )
        login_resp.raise_for_status()
        logger.debug(f"KAG 登录结果：{login_resp.json()}")

        # ── Step 1: 上传文件，拿到 fileUrl ───────────────────────────────────
        with open(tmp_path, "rb") as f:
            upload_resp = session.post(
                f"{host_addr}/public/v1/reasoner/dialog/uploadFile",
                files={"file": (filename, f, "text/markdown")},
                data={"projectId": project_id},
                timeout=60,
            )
        upload_resp.raise_for_status()
        upload_result = upload_resp.json()
        logger.debug(f"KAG 文件上传结果：{upload_result}")

        if not upload_result.get("success"):
            raise RuntimeError(f"KAG 文件上传失败：{upload_result}")
        file_url = upload_result["result"]

        # ── Step 2: 提交构建任务 ──────────────────────────────────────────────
        llm_config = _json.dumps(
            {
                "type": settings.kag_openie_llm_type,
                "base_url": settings.kag_openie_llm_base_url,
                "api_key": settings.kag_openie_llm_api_key,
                "model": settings.kag_openie_llm_model,
                "enable_check": False,
            },
            ensure_ascii=False,
        )
        extension = _json.dumps(
            {
                "dataSourceConfig": {
                    "columns": [],
                    "type": "UPLOAD",
                    "fileName": filename,
                    "fileUrl": file_url,
                    "ignoreHeader": True,
                    "structure": False,
                },
                "splitConfig": {
                    "splitLength": 500,
                    "semanticSplit": False,
                    "retrievals": [1],
                },
                "extractConfig": {
                    "llm": llm_config,
                    "llmPrompt": "",
                    "autoSchema": True,
                    "autoWrite": True,
                },
            },
            ensure_ascii=False,
        )
        submit_url = f"{host_addr}/public/v1/builder/job/submit?ctoken=bigfish_ctoken_1a6j98h155"

        submit_payload = {
            "action": "UPSERT",
            "computingConf": "",
            "createUser": settings.kag_username,
            "cron": "0 0 0 * * ?",
            "dataSourceType": "MD",
            "dependence": "INDEPENDENT",
            "extension": extension,
            "fileUrl": file_url,
            "jobName": title,
            "lifeCycle": "ONCE",
            "projectId": int(project_id),
            "retrievals": "[1]",
            "type": "FILE_EXTRACT",
        }
        build_resp = session.post(submit_url, json=submit_payload, timeout=30)
        build_resp.raise_for_status()
        build_result = build_resp.json()
        logger.debug(f"KAG 构建任务提交结果：{build_result}")

        job_id = build_result.get("data") or build_result.get("result")
        return {"job_id": job_id, "file_url": file_url}
    finally:
        Path(tmp_path).unlink(missing_ok=True)
