"""Crawl keyword management API."""

import asyncio
import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.services import crawl_keyword_service as kws
from app.services.llm_service import _call_llm

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/crawl-keywords", tags=["crawl-keywords"])


class KeywordItem(BaseModel):
    id: str
    keyword: str
    enabled: bool

    model_config = {"from_attributes": True}


class KeywordListResponse(BaseModel):
    items: list[KeywordItem]


class ExpandRequest(BaseModel):
    topic: str


class ExpandResponse(BaseModel):
    keywords: list[str]


class BatchAddRequest(BaseModel):
    keywords: list[str]


class ToggleRequest(BaseModel):
    enabled: bool


@router.get("", response_model=KeywordListResponse)
async def list_keywords(db: AsyncSession = Depends(get_db)):
    kws_list = await kws.get_all_keywords(db)
    return KeywordListResponse(
        items=[KeywordItem(id=k.id, keyword=k.keyword, enabled=k.enabled) for k in kws_list]
    )


@router.post("/expand", response_model=ExpandResponse)
async def expand_keywords(body: ExpandRequest):
    """Use LLM to expand a broad topic into specific crawl keywords."""
    prompt = (
        f"Given the research direction \"{body.topic}\", "
        f"list 10-15 specific technical keywords or sub-topics that would be useful "
        f"for filtering academic papers and GitHub repositories. "
        f"Return ONLY a JSON array of lowercase strings, no explanation. "
        f"Example format: [\"keyword1\", \"keyword2\", \"keyword3\"]"
    )

    result = await _call_llm(prompt)
    if not result:
        raise HTTPException(status_code=500, detail="LLM expansion failed")

    # Parse JSON from LLM response (may contain markdown wrapping)
    try:
        # Strip markdown code blocks if present
        text = result.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        keywords = json.loads(text)
        if not isinstance(keywords, list):
            raise ValueError("Not a list")
        keywords = [str(k).strip().lower() for k in keywords if str(k).strip()]
        return ExpandResponse(keywords=keywords[:20])
    except (json.JSONDecodeError, ValueError) as e:
        # Try fallback: split by newlines and extract quoted strings
        import re
        matches = re.findall(r'"([^"]+)"', result)
        if matches:
            return ExpandResponse(keywords=list(dict.fromkeys(m.strip().lower() for m in matches))[:20])
        raise HTTPException(status_code=500, detail=f"Failed to parse LLM response: {str(e)[:100]}")


@router.post("/batch", response_model=KeywordListResponse)
async def batch_add_keywords(body: BatchAddRequest, db: AsyncSession = Depends(get_db)):
    await kws.add_keywords(db, body.keywords)
    await db.commit()
    kws_list = await kws.get_all_keywords(db)
    return KeywordListResponse(
        items=[KeywordItem(id=k.id, keyword=k.keyword, enabled=k.enabled) for k in kws_list]
    )


@router.put("/{kw_id}", response_model=KeywordItem)
async def toggle_keyword(kw_id: str, body: ToggleRequest, db: AsyncSession = Depends(get_db)):
    kw = await kws.toggle_keyword(db, kw_id, body.enabled)
    if not kw:
        raise HTTPException(status_code=404, detail="Keyword not found")
    await db.commit()
    return KeywordItem(id=kw.id, keyword=kw.keyword, enabled=kw.enabled)


@router.delete("/{kw_id}")
async def delete_keyword(kw_id: str, db: AsyncSession = Depends(get_db)):
    ok = await kws.delete_keyword(db, kw_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Keyword not found")
    await db.commit()
    return {"ok": True}
