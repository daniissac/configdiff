"""Machine-readable JSON formatter."""

from __future__ import annotations

import json

from configdiff.diff_engine.models import DiffResult
from configdiff.output.base import BaseFormatter


class JsonFormatter(BaseFormatter):
    format_name = "json"

    def format(self, result: DiffResult) -> str:
        payload = {
            "summary": result.summary,
            "total_changes": len(result.entries),
            "changes": [entry.to_dict() for entry in result.entries],
        }
        if result.metadata:
            payload["metadata"] = result.metadata
        return json.dumps(payload, indent=2, default=str)
