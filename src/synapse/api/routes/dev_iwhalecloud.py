from __future__ import annotations

import logging
import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from synapse.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()