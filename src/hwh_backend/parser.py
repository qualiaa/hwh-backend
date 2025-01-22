import tomllib
from pathlib import Path
from typing import Any, Dict, Optional

from packaging.requirements import Requirement
from packaging.version import Version
from pyproject_metadata import StandardMetadata

from .hwh_config import HwhConfig


class PyProject:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.pyproject_path = project_dir / "pyproject.toml"
        self._data: Optional[Dict[str, Any]] = None

    @property
    def toml(self):
        if self._data:
            return self._data

        if not self.pyproject_path.exists():
            raise FileNotFoundError(f"No pyproject.toml found in {self.project_dir}")

        with open(self.pyproject_path, "rb") as f:
            self._data = tomllib.load(f)

        return self._data

    @property
    def metadata(self) -> StandardMetadata:
        return StandardMetadata.from_pyproject(self.toml)

    @property
    def dependencies(self) -> set[Requirement]:
        metadata = self.metadata

        # Combine runtime and build dependencies
        all_deps = set(metadata.dependencies)

        # Add build-system requires if present
        build_deps = self.toml.get("build-system", {}).get("requires", [])
        for dep in build_deps:
            try:
                req = Requirement(dep)
                if req not in all_deps:
                    all_deps.add(req)
            except ValueError:
                continue

        return all_deps

    @property
    def package_name(self) -> str:
        """Get the package name from pyproject.toml"""
        return self.metadata.name

    @property
    def package_version(self) -> Optional[Version]:
        return self.metadata.version

    def get_hwh_config(self) -> HwhConfig:
        return HwhConfig(self.toml)
