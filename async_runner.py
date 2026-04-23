from __future__ import annotations

import asyncio
from typing import Any

from langgraph_core.graph import run_workflow


async def run_many(inputs: list[Any]) -> list[dict]:
    tasks = [run_workflow(item, user_id=f"user-{idx}") for idx, item in enumerate(inputs, start=1)]
    return await asyncio.gather(*tasks)
