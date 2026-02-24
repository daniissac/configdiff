<p align="center">
  <h1 align="center">ConfigDiff</h1>
  <p align="center">
    <strong>Structure-aware configuration comparison for humans and machines.</strong>
  </p>
  <p align="center">
    <a href="https://pypi.org/project/configdiff/"><img src="https://img.shields.io/pypi/v/configdiff?color=blue" alt="PyPI version"></a>
    <a href="https://pypi.org/project/configdiff/"><img src="https://img.shields.io/pypi/pyversions/configdiff" alt="Python versions"></a>
    <a href="https://github.com/daniissac/configdiff/blob/main/LICENSE"><img src="https://img.shields.io/github/license/daniissac/configdiff" alt="License"></a>
    <a href="https://github.com/daniissac/configdiff/actions"><img src="https://img.shields.io/github/actions/workflow/status/daniissac/configdiff/ci.yml?label=tests" alt="CI"></a>
    <a href="https://codecov.io/gh/daniissac/configdiff"><img src="https://img.shields.io/codecov/c/github/daniissac/configdiff" alt="Coverage"></a>
  </p>
</p>

ConfigDiff compares structured config files **semantically** -- parsing JSON, YAML, TOML, and INI into normalised trees and performing recursive deep comparison. It detects added, removed, modified, and type-changed values at any depth, then produces clean human-readable output for terminal review or machine-readable JSON/YAML for CI/CD pipelines.

```
$ configdiff before.yaml after.yaml

Found 11 change(s): 2 added, 9 modified

  ~ bgp.neighbors[0].remote_as:
      65001 → 65010
  ~ domain:
      'lab.example.com' → 'prod.example.com'
  ~ interfaces.GigabitEthernet0/1.enabled:
      True → False
  + interfaces.GigabitEthernet0/2: {'ip': '172.16.0.1', ...}
  ~ logging.level:
      'info' → 'warning'
```

---

## The Problem with `diff`

Traditional `diff` operates on **lines of text**. It has no understanding of structure, so it:

- **Conflates formatting with real changes** -- reindenting a YAML block produces dozens of "changes" that aren't
- **Cannot detect type changes** -- `port: "8080"` vs `port: 8080` looks identical to `diff`
- **Breaks on reordered lists** -- moving a DNS server from position 0 to position 1 shows as two changes instead of zero
- **Produces no machine-readable output** -- downstream automation has to scrape unified-diff syntax

For anyone managing router configs, Kubernetes manifests, Terraform variables, or application settings at scale, line-based diff creates noise that obscures the signal.

**ConfigDiff** parses each file into a normalised tree, performs a recursive deep comparison, and reports only the values that actually changed -- with dot-notation paths like `bgp.neighbors[0].remote_as`, proper type awareness, and structured output that CI/CD pipelines can consume directly.

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Structure-aware diff** | Recursive deep comparison of dicts, lists, and scalars -- not lines of text |
| **4 formats out of the box** | JSON, YAML, TOML, INI with auto-detection from file extension |
| **Change classification** | Every change is categorised: `added`, `removed`, `modified`, `type_changed` |
| **Dot-notation paths** | Changes reported as `bgp.neighbors[0].remote_as` for precise identification |
| **List order control** | `--ignore-order` to treat `[a, b]` and `[b, a]` as equivalent |
| **Multiple output formats** | Human-readable text (with colour), machine-readable JSON, machine-readable YAML |
| **CI/CD exit codes** | `0` = no changes, `1` = changes detected, `2` = error |
| **Plugin architecture** | Extensible parsers and formatters -- add new formats without touching core code |
| **Docker support** | Slim, non-root container image for pipeline use |
| **Minimal dependencies** | Single runtime dependency (`pyyaml`); everything else is Python stdlib |

---

## Quick Start

### Install

```bash
pip install configdiff
```

Requires Python 3.11+.

### Compare two configs

```bash
configdiff before.yaml after.yaml
```

```
Found 11 change(s): 2 added, 9 modified

  ~ bgp.neighbors[0].description:
      'Peer ISP-A' → 'Peer ISP-A (migrated)'
  ~ bgp.neighbors[0].remote_as:
      65001 → 65010
  ~ dns.servers[0]:
      '8.8.8.8' → '1.1.1.1'
  ~ dns.servers[1]:
      '8.8.4.4' → '8.8.8.8'
  ~ domain:
      'lab.example.com' → 'prod.example.com'
  ~ interfaces.GigabitEthernet0/1.description:
      'LAN segment' → 'LAN segment - maintenance'
  ~ interfaces.GigabitEthernet0/1.enabled:
      True → False
  + interfaces.GigabitEthernet0/2: {'ip': '172.16.0.1', 'mask': '255.255.255.0', 'enabled': True, 'description': 'New DMZ segment'}
  ~ logging.level:
      'info' → 'warning'
  ~ ntp.servers[0]:
      'pool.ntp.org' → 'time.google.com'
  + ntp.servers[1]: 'pool.ntp.org'
```

### Get machine-readable output

```bash
configdiff before.json after.json --format json
```

```json
{
  "summary": {
    "modified": 6,
    "added": 3
  },
  "total_changes": 9,
  "changes": [
    {
      "path": "app.debug",
      "type": "modified",
      "old": true,
      "new": false
    },
    {
      "path": "app.version",
      "type": "modified",
      "old": "2.3.1",
      "new": "2.4.0"
    },
    {
      "path": "app.workers",
      "type": "added",
      "new": 4
    },
    {
      "path": "database.pool_size",
      "type": "modified",
      "old": 5,
      "new": 20
    }
  ],
  "metadata": {
    "before": "examples/before.json",
    "after": "examples/after.json",
    "format": "json"
  }
}
```

### Write output to a file

```bash
configdiff before.yaml after.yaml --format json -o changes.json
```

---

## Real-World Use Cases

### Network Configuration Validation

Compare router configs before and after a change window to verify only intended changes were applied:

```bash
configdiff router-baseline.yaml router-current.yaml
```

ConfigDiff immediately shows that `bgp.neighbors[0].remote_as` changed from `65001` to `65010` and `interfaces.GigabitEthernet0/1.enabled` flipped to `false` -- no wading through whitespace noise.

### Kubernetes / YAML Review

Compare staging and production manifests to catch configuration drift:

```bash
configdiff k8s/staging/deployment.yaml k8s/prod/deployment.yaml --format json
```

The JSON output feeds directly into review tooling or Slack notifications. Exit code `1` means drift exists; `0` means they match.

### Config Drift Detection in CI

Gate deployments on configuration consistency:

```yaml
# .github/workflows/config-check.yml
jobs:
  config-drift:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install configdiff
      - name: Detect drift
        run: configdiff config/prod.yaml config/staging.yaml --format json -o drift.json
      - name: Fail on drift
        if: ${{ failure() || steps.detect-drift.outcome == 'failure' }}
        run: |
          echo "Configuration drift detected:"
          cat drift.json
          exit 1
```

### Application Deployment Auditing

Compare the config deployed to production against the expected baseline:

```bash
configdiff expected.toml deployed.toml --format yaml -o audit.yaml
```

Machine-readable output flows into observability pipelines, ticketing systems, or compliance dashboards.

---

## CLI Reference

```
usage: configdiff [-h] [-f {text,json,yaml}] [--ignore-order]
                  [-o FILE] [-v] [-V]
                  BEFORE AFTER
```

| Argument / Flag | Description |
|-----------------|-------------|
| `BEFORE` | Path to the original (before) config file |
| `AFTER` | Path to the updated (after) config file |
| `-f, --format` | Output format: `text` (default), `json`, `yaml` |
| `--ignore-order` | Treat lists as unordered (ignore element position) |
| `-o, --output-file` | Write output to a file instead of stdout |
| `-v, --verbose` | Enable debug logging to stderr |
| `-V, --version` | Show version and exit |

### Exit Codes

| Code | Meaning | CI interpretation |
|------|---------|-------------------|
| `0` | No differences found | Configs match -- pass |
| `1` | Differences detected | Drift or changes present -- review/fail |
| `2` | Error | Bad input, missing file, parse failure |

### Supported Formats

| Format | Extension(s) | Parser |
|--------|-------------|--------|
| JSON | `.json` | `json` (stdlib) |
| YAML | `.yaml`, `.yml` | `pyyaml` |
| TOML | `.toml` | `tomllib` (stdlib, 3.11+) |
| INI | `.ini`, `.cfg`, `.conf` | `configparser` (stdlib) |

Both files must use the same format. Format is auto-detected from the file extension.

---

## Architecture

```
                    ┌──────────────────┐
                    │   CLI (argparse) │
                    │   cli/app.py     │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
     ┌────────────┐  ┌─────────────┐  ┌──────────┐
     │  Parsers   │  │ Diff Engine │  │  Output  │
     │  (plugin)  │  │  (core)     │  │ (plugin) │
     └────────────┘  └─────────────┘  └──────────┘
      BaseParser       compare()      BaseFormatter
      Registry         DiffEntry      TextFormatter
      JSON/YAML/       DiffResult     JsonFormatter
      TOML/INI         ChangeType     YamlFormatter
```

**Data flow:** The CLI resolves the file format via extension, dispatches to the appropriate parser to produce a normalised `dict`, passes both dicts to the diff engine which returns a `DiffResult` containing a list of `DiffEntry` dataclasses, and finally hands the result to the selected formatter for rendering.

### Design Principles

- **Plugin-extensible parsers** -- Subclass `BaseParser`, register with `ParserRegistry`. New formats require zero changes to existing code.
- **Plugin-extensible formatters** -- Subclass `BaseFormatter`, add to the formatter map. Same `DiffResult` model regardless of input format.
- **Immutable data model** -- `DiffEntry` is a frozen dataclass. The diff engine produces data; formatters only read it.
- **Separation of concerns** -- Parsing, diffing, and formatting are fully independent modules. The CLI is a thin orchestration layer.

```
configdiff/
├── cli/
│   └── app.py               # argparse entry point, exit codes
├── parsers/
│   ├── base.py               # BaseParser ABC
│   ├── registry.py            # ParserRegistry (format/ext → parser)
│   ├── json_parser.py
│   ├── yaml_parser.py
│   ├── toml_parser.py
│   └── ini_parser.py
├── diff_engine/
│   ├── models.py              # DiffEntry, DiffResult, ChangeType
│   └── engine.py              # Recursive deep-diff, compare()
├── output/
│   ├── base.py                # BaseFormatter ABC
│   ├── text.py                # Coloured terminal output
│   ├── json_output.py         # Structured JSON
│   └── yaml_output.py         # Structured YAML
└── utils/
    ├── format_detection.py    # Extension-based format detection
    └── logging.py             # Logging configuration
```

---

## Docker

Docker is provided as an **optional** distribution channel for CI/CD and containerised environments. The primary interface is `pip install configdiff`.

```bash
# Build
docker build -t configdiff .

# Compare files mounted from the host
docker run --rm -v "$PWD:/data" configdiff before.yaml after.yaml

# JSON output
docker run --rm -v "$PWD:/data" configdiff before.json after.json -f json

# Write output to a file on the host
docker run --rm -v "$PWD:/data" configdiff before.yaml after.yaml -o changes.json
```

The image uses `python:3.12-slim`, runs as a non-root user (`UID 1000`), and uses a multi-stage build to keep the final image minimal.

---

## Extensibility

ConfigDiff is architected so that new capabilities can be added **without modifying core code**:

| Extension point | Mechanism | Future examples |
|----------------|-----------|-----------------|
| **New config formats** | Subclass `BaseParser`, register with `ParserRegistry` | XML, HCL/Terraform, Cisco IOS, JunOS |
| **New output formats** | Subclass `BaseFormatter`, add to formatter map | HTML report, Markdown, Slack blocks |
| **Diff plugins** | Future `DiffPlugin` base class with `pre_diff` / `post_diff` hooks | Network-aware semantics, risk scoring |
| **Policy gates** | Future `--policy` flag loading declarative rules | "No `debug: true` in production" |

Adding a new parser is three steps:

```python
from configdiff.parsers.base import BaseParser
from configdiff.parsers.registry import ParserRegistry

class XmlParser(BaseParser):
    format_name = "xml"
    extensions = [".xml"]

    def parse(self, path):
        ...  # parse and return a dict

ParserRegistry.register(XmlParser())
```

---

## Development

```bash
git clone https://github.com/daniissac/configdiff.git
cd configdiff
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

### Running Tests

```bash
# Full suite
pytest

# With coverage
pytest --cov=configdiff --cov-report=term-missing

# Single module
pytest tests/test_diff_engine.py -v
```

### Project Structure

```
tests/
├── test_parsers.py        # Parser unit tests (valid, malformed, edge cases)
├── test_diff_engine.py    # Diff engine tests (add/remove/modify/type/nested/lists)
├── test_output.py         # Formatter output verification
├── test_cli.py            # End-to-end CLI integration tests
├── conftest.py            # Shared fixtures
└── fixtures/              # Sample config files
examples/
├── before.yaml / after.yaml
└── before.json / after.json
```

---

## Roadmap

ConfigDiff is designed for incremental extension. Planned future work:

- **Network-aware diff plugins** -- Semantic understanding of IP addresses, subnets, ASNs, VLAN ranges, interface naming
- **Risk scoring engine** -- Annotate changes with risk levels (e.g. disabling an interface = high, changing a description = low)
- **CI/CD policy gates** -- Declarative policy files that fail pipelines on violations (e.g. "no `debug: true` in production")
- **GitHub Action** -- First-class Action for PR-based config review workflows
- **Additional formats** -- XML, HCL/Terraform, Cisco IOS, JunOS
- **Interactive TUI** -- Terminal UI for navigating large diffs with folding and search
- **AI-assisted explanations** -- LLM-powered plain-language summaries of complex config changes

---

## Contributing

Contributions are welcome. To get started:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Write tests for your changes
4. Ensure `pytest` passes with no regressions
5. Submit a pull request

Please keep PRs focused on a single change. For larger features, open an issue first to discuss the approach.

---

## License

MIT License. See [LICENSE](LICENSE) for details.
