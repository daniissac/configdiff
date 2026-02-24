"""Machine-readable YAML formatter."""

from __future__ import annotations

import yaml

from configdiff.diff_engine.models import DiffResult
from configdiff.output.base import BaseFormatter


class YamlFormatter(BaseFormatter):
    format_name = "yaml"

    def format(self, result: DiffResult) -> str:
        payload = {
            "summary": result.summary,
            "total_changes": len(result.entries),
            "changes": [entry.to_dict() for entry in result.entries],
        }
        if result.metadata:
            payload["metadata"] = result.metadata
        return yaml.dump(payload, default_flow_style=False, sort_keys=False)
