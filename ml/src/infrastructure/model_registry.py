"""Lightweight ML model registry and version/status tracking for NexteRaS."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from ml.src.common.config import REPO_ROOT, load_yaml_config, resolve_repo_path

LifecycleStatus = Literal[
    "PRETRAINED",
    "CONFIGURED",
    "DOWNLOADED",
    "INTEGRATED",
    "EVALUATED",
    "FINE_TUNED",
    "DEPLOYED",
    "PENDING",
]


class RegisteredModelSpec(BaseModel):
    key: str
    name: str
    model_id: str
    version: str
    model_type: str
    task: str
    input_schema: str
    output_schema: str
    embedding_dimension: int | None = None
    local_path: str | None = None
    fallback_model_id: str | None = None
    license: str
    owner: str
    fine_tuning_status: str
    evaluation_status: str
    lifecycle_status: LifecycleStatus
    approx_ram_mb: int
    approx_disk_mb: int
    known_limitations: list[str] = Field(default_factory=list)

    def resolve_active_identifier(self) -> tuple[str, bool]:
        """
        Return (active_model_path_or_hf_id, using_finetuned_checkpoint).
        If the fine-tuned local_path does not exist yet (e.g. Sanju's personal MiniLM),
        fall back safely to fallback_model_id or pretrained model_id without throwing.
        """
        if self.local_path:
            candidate = resolve_repo_path(self.local_path)
            if candidate.exists() and any(candidate.iterdir()):
                return str(candidate), True
        if self.fallback_model_id:
            return self.fallback_model_id, False
        return self.model_id, False


class ModelRegistry:
    """YAML-backed registry separating pretrained, configured, fine-tuned, and evaluated statuses."""

    def __init__(self, registry_path: str | Path = "ml/model_configs/ml_registry.yaml") -> None:
        raw = load_yaml_config(registry_path)
        self.registry_version = str(raw.get("registry_version", "1.0.0"))
        self.models: dict[str, RegisteredModelSpec] = {}
        for key, item in (raw.get("models") or {}).items():
            spec = RegisteredModelSpec.model_validate({"key": key, **item})
            self.models[key] = spec

    def get(self, key: str) -> RegisteredModelSpec:
        if key not in self.models:
            raise KeyError(f"Unknown model key '{key}'. Registered: {sorted(self.models)}")
        return self.models[key]

    def summary(self) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for spec in self.models.values():
            active_id, is_tuned = spec.resolve_active_identifier()
            rows.append(
                {
                    "key": spec.key,
                    "model_id": spec.model_id,
                    "version": spec.version,
                    "task": spec.task,
                    "embedding_dimension": spec.embedding_dimension,
                    "lifecycle_status": spec.lifecycle_status,
                    "fine_tuning_status": spec.fine_tuning_status,
                    "evaluation_status": spec.evaluation_status,
                    "active_identifier": active_id if not Path(active_id).is_absolute() else str(Path(active_id).relative_to(REPO_ROOT)),
                    "using_finetuned_checkpoint": is_tuned,
                    "approx_ram_mb": spec.approx_ram_mb,
                }
            )
        return rows
