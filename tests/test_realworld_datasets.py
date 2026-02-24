"""Real-world dataset validation tests.

Validates ConfigDiff against representative configuration samples from
production-like scenarios: Kubernetes manifests, Terraform state, Ansible
inventories, Helm values, and network device configs.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from configdiff.cli.app import EXIT_CHANGES, EXIT_ERROR, EXIT_NO_CHANGES, run
from configdiff.diff_engine import ChangeType, compare
from configdiff.output.json_output import JsonFormatter
from configdiff.parsers.json_parser import JsonParser
from configdiff.parsers.yaml_parser import YamlParser

DATASETS = Path(__file__).parent / "datasets"


def _load_json(path: Path) -> dict:
    return JsonParser().parse(path)


def _load_yaml(path: Path) -> dict:
    return YamlParser().parse(path)


# ---------------------------------------------------------------------------
# Parametrized dataset-level integration tests (CLI)
# ---------------------------------------------------------------------------

_DATASET_PAIRS = [
    ("small", "before.json", "after.json"),
    ("small", "before.yaml", "after.yaml"),
    ("small", "before.toml", "after.toml"),
    ("small", "before.ini", "after.ini"),
    ("deeply_nested", "before.json", "after.json"),
    ("kubernetes", "before.yaml", "after.yaml"),
    ("terraform", "before.json", "after.json"),
    ("ansible", "before.yaml", "after.yaml"),
    ("helm", "before.yaml", "after.yaml"),
    ("network", "before.json", "after.json"),
    ("order_variant", "before.json", "after.json"),
    ("order_variant", "before.yaml", "after.yaml"),
]


@pytest.mark.parametrize(
    "category,before_name,after_name",
    _DATASET_PAIRS,
    ids=[f"{c}/{b}->{a}" for c, b, a in _DATASET_PAIRS],
)
class TestDatasetCLI:
    """Run ConfigDiff CLI against every real-world dataset pair."""

    def test_runs_without_error(
        self, category: str, before_name: str, after_name: str
    ) -> None:
        before = DATASETS / category / before_name
        after = DATASETS / category / after_name
        code = run([str(before), str(after), "--format", "json"])
        assert code in (EXIT_NO_CHANGES, EXIT_CHANGES)

    def test_json_output_is_valid(
        self,
        category: str,
        before_name: str,
        after_name: str,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        before = DATASETS / category / before_name
        after = DATASETS / category / after_name
        run([str(before), str(after), "--format", "json"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "summary" in data
        assert "changes" in data
        assert "total_changes" in data
        assert isinstance(data["changes"], list)
        assert data["total_changes"] == len(data["changes"])

    def test_output_to_file(
        self,
        category: str,
        before_name: str,
        after_name: str,
        tmp_path: Path,
    ) -> None:
        before = DATASETS / category / before_name
        after = DATASETS / category / after_name
        out = tmp_path / "result.json"
        code = run([
            str(before), str(after), "--format", "json", "-o", str(out)
        ])
        assert code in (EXIT_NO_CHANGES, EXIT_CHANGES)
        assert out.exists()
        data = json.loads(out.read_text(encoding="utf-8"))
        assert "changes" in data


# ---------------------------------------------------------------------------
# Semantic correctness on known datasets
# ---------------------------------------------------------------------------


class TestKubernetesDiff:
    """Validate semantics of a realistic K8s deployment diff."""

    @pytest.fixture()
    def k8s_result(self):
        before = _load_yaml(DATASETS / "kubernetes" / "before.yaml")
        after = _load_yaml(DATASETS / "kubernetes" / "after.yaml")
        return compare(before, after)

    def test_replica_change(self, k8s_result) -> None:
        paths = {e.path: e for e in k8s_result.entries}
        assert "spec.replicas" in paths
        entry = paths["spec.replicas"]
        assert entry.change_type is ChangeType.MODIFIED
        assert entry.old_value == 3
        assert entry.new_value == 5

    def test_image_tag_changed(self, k8s_result) -> None:
        image_entries = [
            e for e in k8s_result.entries if "image" in e.path and e.change_type is ChangeType.MODIFIED
        ]
        assert len(image_entries) >= 1

    def test_label_added(self, k8s_result) -> None:
        added = [
            e for e in k8s_result.entries
            if e.change_type is ChangeType.ADDED and "tier" in e.path
        ]
        assert len(added) >= 1

    def test_has_meaningful_changes(self, k8s_result) -> None:
        assert k8s_result.has_changes
        assert len(k8s_result.entries) >= 10


class TestTerraformDiff:
    """Validate diff on Terraform plan JSON output."""

    @pytest.fixture()
    def tf_result(self):
        before = _load_json(DATASETS / "terraform" / "before.json")
        after = _load_json(DATASETS / "terraform" / "after.json")
        return compare(before, after)

    def test_version_changed(self, tf_result) -> None:
        paths = {e.path: e for e in tf_result.entries}
        assert "terraform_version" in paths
        assert paths["terraform_version"].old_value == "1.6.0"
        assert paths["terraform_version"].new_value == "1.7.0"

    def test_detects_added_resource(self, tf_result) -> None:
        added = [e for e in tf_result.entries if e.change_type is ChangeType.ADDED]
        assert len(added) >= 1

    def test_has_changes(self, tf_result) -> None:
        assert tf_result.has_changes


class TestAnsibleDiff:
    """Validate diff on Ansible inventory."""

    @pytest.fixture()
    def ansible_result(self):
        before = _load_yaml(DATASETS / "ansible" / "before.yaml")
        after = _load_yaml(DATASETS / "ansible" / "after.yaml")
        return compare(before, after)

    def test_ntp_server_changed(self, ansible_result) -> None:
        paths = {e.path: e for e in ansible_result.entries}
        assert "all.vars.ntp_server" in paths

    def test_new_host_added(self, ansible_result) -> None:
        added = [
            e for e in ansible_result.entries
            if e.change_type is ChangeType.ADDED and "web03" in e.path
        ]
        assert len(added) >= 1

    def test_monitoring_group_added(self, ansible_result) -> None:
        added = [
            e for e in ansible_result.entries
            if e.change_type is ChangeType.ADDED and "monitoring" in e.path
        ]
        assert len(added) >= 1


class TestHelmDiff:
    """Validate diff on Helm chart values."""

    @pytest.fixture()
    def helm_result(self):
        before = _load_yaml(DATASETS / "helm" / "before.yaml")
        after = _load_yaml(DATASETS / "helm" / "after.yaml")
        return compare(before, after)

    def test_replica_count_changed(self, helm_result) -> None:
        paths = {e.path: e for e in helm_result.entries}
        assert "replicaCount" in paths
        assert paths["replicaCount"].old_value == 2
        assert paths["replicaCount"].new_value == 3

    def test_autoscaling_enabled(self, helm_result) -> None:
        paths = {e.path: e for e in helm_result.entries}
        assert "autoscaling.enabled" in paths
        assert paths["autoscaling.enabled"].new_value is True

    def test_ingress_enabled(self, helm_result) -> None:
        paths = {e.path: e for e in helm_result.entries}
        assert "ingress.enabled" in paths


class TestNetworkConfigDiff:
    """Validate diff on network device configuration."""

    @pytest.fixture()
    def net_result(self):
        before = _load_json(DATASETS / "network" / "before.json")
        after = _load_json(DATASETS / "network" / "after.json")
        return compare(before, after)

    def test_new_interface_added(self, net_result) -> None:
        added = [
            e for e in net_result.entries
            if e.change_type is ChangeType.ADDED
            and "GigabitEthernet0/2" in e.path
        ]
        assert len(added) >= 1

    def test_bgp_added(self, net_result) -> None:
        added = [
            e for e in net_result.entries
            if e.change_type is ChangeType.ADDED and "bgp" in e.path
        ]
        assert len(added) >= 1

    def test_interface_description_changed(self, net_result) -> None:
        mods = [
            e for e in net_result.entries
            if e.change_type is ChangeType.MODIFIED and "description" in e.path
        ]
        assert len(mods) >= 1
