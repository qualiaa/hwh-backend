import os
import tomllib
from pathlib import Path
from typing import Any, Dict, Optional

from packaging.requirements import Requirement
from packaging.version import Version
from pyproject_metadata import StandardMetadata
from setuptools import find_packages

from .hwh_config import HwhConfig


class PyProject:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.pyproject_path = project_dir / "pyproject.toml"
        if not self.pyproject_path.exists():
            raise FileNotFoundError(
                f"Couldn't locate pyproject.toml from {str(self.project_dir)}"
            )
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
        """Get the package version from pyproject.toml"""
        return self.metadata.version

    def get_hwh_config(self) -> HwhConfig:
        # TODO: switch to property
        return HwhConfig(self.toml)

    @property
    def setuptools_config(self) -> dict:
        """Get setuptools configuration from pyproject.toml."""
        return self.toml.get("tool", {}).get("setuptools", {})

    @property
    def package_dir(self) -> dict:
        """Get package directory mapping from setuptools config."""
        return self.setuptools_config.get("package-dir", {})

    @property
    def packages(self) -> list[str]:
        """Get list of packages to include."""
        return self._discover_packages()

    def _discover_packages(self) -> list[str]:
        """Discover packages using setuptools configuration."""
        setuptools_config = self.setuptools_config

        # Direct package listing
        packages = setuptools_config.get("packages", None)
        print(f"direct packages {packages}")
        if isinstance(packages, list):
            return packages

        packages_config = setuptools_config.get("packages", {})
        if isinstance(packages_config, dict):
            find_config = packages_config.get("find", {})
            if find_config:
                print("finding config")
                where = ["."]
                if self.package_dir and "" in self.package_dir:
                    where = [self.package_dir[""]]
                search_dir = self.project_dir / where[0]

                include = find_config.get("include", ["*"])
                exclude = find_config.get("exclude", [])
                print(f"Includes {include}")
                print(f"Excludes {exclude}")
                print(f"Finding {where}")
                print(os.getcwd())
                found = find_packages(
                    where=str(search_dir), include=include, exclude=exclude
                )
                print(f"Found {found}")
                return found

        # Default to package name
        return [self.package_name]

    def get_package_path(self, package: str) -> Path:
        """Convert a package name to its directory path."""
        base = self.project_dir

        # Handle package-dir mapping
        for prefix, directory in self.package_dir.items():
            if prefix == "":  # Root package
                base = base / directory
                break
            if package.startswith(prefix):
                base = base / directory
                package = package[len(prefix) :].lstrip(".")
                break

        return base / package.replace(".", "/")

    def get_all_package_paths(self) -> list[Path]:
        """Get paths for all configured packages."""
        return [self.get_package_path(pkg) for pkg in self.packages]
