from __future__ import annotations

import asyncio
import json

from langgraph_core.graph import run_workflow


async def _demo() -> None:
    result = await run_workflow({"image": "yellow_tomato_leaf.jpg"}, user_id="demo-user")
    output = {
        "diagnosis": result.get("vision_result", {}).get("disease", "unknown"),
        "confidence": result.get("confidence", 0.0),
        "graph_paths": result.get("graph_paths", []),
        "answer_en": result.get("final_answer_en", ""),
        "answer_ar": result.get("final_answer_ar", ""),
        "sources": result.get("sources", []),
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(_demo())
