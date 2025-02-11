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
        """Discover packages using setuptools.packages.find configuration."""
        setuptools_config = self.setuptools_config

        # Check for packages.find
        packages_find = setuptools_config.get("packages", {}).get("find", {})
        if packages_find:
            # Get base directory for package search
            where = packages_find.get("where", ["."])
            if isinstance(where, str):
                where = [where]

            # Get include/exclude patterns. Default to include all.
            include = packages_find.get("include", ["*"])
            exclude = packages_find.get("exclude", [])

            # Convert paths relative to project root
            search_dirs = [self.project_dir / w for w in where]

            found_packages = []
            for search_dir in search_dirs:
                found = find_packages(
                    where=str(search_dir), include=include, exclude=exclude
                )
                found_packages.extend(found)

            if found_packages:
                return found_packages

        # Fallback to direct package list if specified
        packages = setuptools_config.get("packages", None)
        if isinstance(packages, list):
            return packages

        # Default to package name as last resort
        return [self.package_name]

    def get_package_path(self, package: str) -> Path:
        """Convert a package name to its directory path."""
        base = self.project_dir

        # Check for config, where setuptools.packages.find section defines "where"
        packages_find = self.setuptools_config.get("packages", {}).get("find", {})
        if where_paths := packages_find.get("where", []):
            if isinstance(where_paths, str):
                where_paths = [where_paths]
            # Use the first where path for now
            # TODO: figure out the cases where there are multiple "where"s.
            # havent' seen one yet?
            base = base / where_paths[0]

        return base / package.replace(".", "/")

    def get_all_package_paths(self) -> list[Path]:
        """Get paths for all configured packages."""
        # For src layout, we only want the root package path
        # added to stop duplicates
        if len(self.packages) > 0:
            root_pkg = self.packages[0].split(".")[0]
            return [self.get_package_path(root_pkg)]
        return []
