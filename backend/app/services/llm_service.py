"""LLM-powered Chinese summary generation for papers and repos.

Uses any OpenAI-compatible API (Ollama, DeepSeek, OpenAI, etc.).
Failures are logged but never block the crawl pipeline.
"""

import asyncio
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_semaphore = asyncio.Semaphore(3)


async def _call_llm(prompt: str) -> str | None:
    """Call the LLM API with concurrency control and error handling."""
    if not settings.llm_api_base or not settings.llm_summary_enabled:
        return None

    async with _semaphore:
        try:
            headers = {"Content-Type": "application/json"}
            if settings.llm_api_key:
                headers["Authorization"] = f"Bearer {settings.llm_api_key}"

            # Detect Ollama vs OpenAI API format
            if "/v1" in settings.llm_api_base:
                url = f"{settings.llm_api_base}/chat/completions"
                body = {
                    "model": settings.llm_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": settings.llm_summary_max_tokens,
                    "temperature": 0.3,
                }
                resp_key = ["choices", 0, "message", "content"]
            else:
                url = f"{settings.llm_api_base}/api/chat"
                body = {
                    "model": settings.llm_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                }
                resp_key = ["message", "content"]

            async with httpx.AsyncClient(timeout=180) as client:
                resp = await client.post(url, headers=headers, json=body)
                if resp.status_code == 429:
                    logger.warning("LLM rate limited, retrying after 3s")
                    await asyncio.sleep(3)
                    return None
                resp.raise_for_status()
                data = resp.json()
                result = data
                for key in resp_key:
                    result = result[key]
                return result.strip()
        except Exception:
            logger.warning("LLM summary generation failed", exc_info=True)
            return None


async def generate_paper_summary_cn(title: str, abstract: str) -> str | None:
    """Generate a Chinese summary for a research paper."""
    text = abstract if abstract else title
    if not text or len(text) < 20:
        return None
    prompt = (
        f"请用中文简要总结以下研究论文的核心贡献与方法，控制在3-5句话内，突出创新点与实用价值：\n\n"
        f"标题: {title}\n\n摘要: {text[:3000]}"
    )
    return await _call_llm(prompt)


async def generate_paper_summary_en(title: str, abstract: str) -> str | None:
    """Generate an English summary for a research paper."""
    text = abstract if abstract else title
    if not text or len(text) < 20:
        return None
    prompt = (
        f"Summarize the following research paper in 2-4 sentences, highlighting its key contribution and approach:\n\n"
        f"Title: {title}\n\nAbstract: {text[:3000]}"
    )
    return await _call_llm(prompt)


# Keep old name as alias for backward compat
async def generate_paper_summary(title: str, abstract: str) -> str | None:
    return await generate_paper_summary_cn(title, abstract)


async def generate_repo_summary_cn(full_name: str, description: str, topics: list[str]) -> str | None:
    """Generate a Chinese summary for a GitHub repository."""
    desc = description or ""
    topic_str = ", ".join(topics) if topics else ""
    text = f"{desc} {topic_str}".strip()
    if not text or len(text) < 10:
        return None
    prompt = (
        f"请用中文简要总结以下GitHub开源项目的功能与用途，控制在2-4句话内，说明它解决了什么问题：\n\n"
        f"仓库名: {full_name}\n描述: {desc[:2000]}\n主题标签: {topic_str}"
    )
    return await _call_llm(prompt)


async def generate_repo_summary_en(full_name: str, description: str, topics: list[str]) -> str | None:
    """Generate an English summary for a GitHub repository."""
    desc = description or ""
    topic_str = ", ".join(topics) if topics else ""
    text = f"{desc} {topic_str}".strip()
    if not text or len(text) < 10:
        return None
    prompt = (
        f"Summarize the following GitHub project in 2-4 sentences, explaining what it does:\n\n"
        f"Repo: {full_name}\nDescription: {desc[:2000]}\nTopics: {topic_str}"
    )
    return await _call_llm(prompt)
