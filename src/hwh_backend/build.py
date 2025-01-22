import os
import shutil
from pathlib import Path
from typing import List, Optional, Union

from Cython.Build import cythonize
from setuptools.build_meta import (
    build_editable as _build_editable,
)
from setuptools.build_meta import (
    get_requires_for_build_editable as _get_requires_for_build_editable,
)
from setuptools.build_meta import (
    get_requires_for_build_wheel as _get_requires_for_build_wheel,
)
from setuptools.build_meta import (
    prepare_metadata_for_build_wheel as _prepare_metadata_for_build_wheel,
)
from setuptools.command.build_ext import build_ext
from setuptools.dist import Distribution
from setuptools.extension import Extension

from .parser import PyProject

# Global flag to prevent double builds
_EXTENSIONS_BUILT = False


def list_files_walk(start_path="."):
    for root, dirs, files in os.walk(start_path):
        for file in files:
            print(os.path.join(root, file))


def find_cython_files(
    source_dir: Path,
    sources: Optional[List[Union[str, Path]]] = None,
    exclude_dirs: Optional[List[str]] = None,
) -> List[Path]:
    if sources:
        # Convert all sources to Path objects relative to source_dir
        res = [
            source_dir / src if isinstance(src, str) else src
            for src in sources
            if str(src).endswith(".pyx")
        ]
        return res

    all_pyx = list(source_dir.rglob("*.pyx"))

    # Filter out all directories that are excluded
    exclude_dirs = set(exclude_dirs or [])
    if exclude_dirs:
        # Convert exclude_dirs to full paths relative to source_dir
        exclude_paths = {source_dir / excluded for excluded in exclude_dirs}
        return [
            pyx
            for pyx in all_pyx
            if not any(exclude_path in pyx.parents for exclude_path in exclude_paths)
        ]

    return list(all_pyx)


def _get_ext_modules(project: PyProject):
    """Get Cython extension modules configuration."""
    import site

    # Get site-packages directory
    site_packages = [site.getsitepackages()[0]]

    # Create directory lists for Extension ctor and cythonize()
    config = project.get_hwh_config().cython
    library_dirs = config.library_dirs + site_packages
    runtime_library_dirs = config.runtime_library_dirs + site_packages
    include_dirs = config.include_dirs + site_packages

    # Find all .pyx files in the package directory
    package_dir = Path(project.package_name)
    pyx_files = find_cython_files(
        package_dir, sources=config.sources, exclude_dirs=config.exclude_dirs
    )

    # Create Extensions
    ext_modules = []
    for pyx_file in pyx_files:
        module_path = (
            str(pyx_file).replace("/", ".").replace("\\", ".").replace(".pyx", "")
        )
        ext_modules.append(
            Extension(
                module_path,
                [str(pyx_file)],
                language=config.language,
                library_dirs=library_dirs,
                runtime_library_dirs=runtime_library_dirs,
            )
        )

    return cythonize(
        ext_modules,
        nthreads=config.nthreads,
        force=config.force,
        annotate=config.annotate,
        compiler_directives=config.compiler_directives.as_dict(),
        include_path=include_dirs,  # This helps find .pxd files
    )


def _build_extension():
    """Build the extension modules."""
    global _EXTENSIONS_BUILT

    if _EXTENSIONS_BUILT:
        return

    project = PyProject(Path())

    name = project.package_name

    dist = Distribution({"name": name, "ext_modules": _get_ext_modules(project)})

    dist.has_ext_modules = lambda: True

    cmd = build_ext(dist)
    cmd.ensure_finalized()
    cmd.run()

    # Copy built extensions to source directory
    built_files = cmd.get_outputs()
    for output in built_files:
        if os.path.exists(output):
            filename = os.path.basename(output)
            target_dir = Path(name)
            target_path = target_dir / filename
            print(f"Copying {output} to {target_path}")
            shutil.copy2(output, target_path)


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    """Build wheel."""
    _build_extension()

    project = PyProject(Path())
    name = project.package_name

    # Configure the distribution
    dist = Distribution(
        {
            "name": name,
            "version": str(project.package_version),
            "ext_modules": _get_ext_modules(project),
            "packages": [name],
            "package_data": {
                # TODO: Remove pyx files, we don't need them right?
                name: ["*.pxd", "*.so"],
            },
            "include_package_data": True,
        }
    )

    dist.script_name = "youcanapparentlyputanythinghere"
    dist.has_ext_modules = lambda: True

    from wheel.bdist_wheel import bdist_wheel as wheel_command

    class BdistWheelCommand(wheel_command):
        def finalize_options(self):
            super().finalize_options()
            self.root_is_pure = False

        def run(self):
            # TODO: check that this isn't required and remove
            self.run_command("build_ext")
            super().run()

    cmd = BdistWheelCommand(dist)
    cmd.dist_dir = wheel_directory

    cmd.ensure_finalized()
    cmd.run()

    # Find the built wheel in the wheel_directory
    wheel_path = next(Path(wheel_directory).glob("*.whl"))
    return wheel_path.name


def build_editable(wheel_directory, config_settings=None, metadata_directory=None):
    """Build editable wheel."""
    _build_extension()
    result = _build_editable(wheel_directory, config_settings, metadata_directory)
    return result


def get_requires_for_build_wheel(config_settings=None):
    """Get requirements for wheel build."""
    return _get_requires_for_build_wheel(config_settings)


def get_requires_for_build_editable(config_settings=None):
    """Get requirements for editable build."""
    return _get_requires_for_build_editable(config_settings)


def prepare_metadata_for_build_wheel(metadata_directory, config_settings=None):
    """Prepare wheel metadata."""
    return _prepare_metadata_for_build_wheel(metadata_directory, config_settings)


def prepare_metadata_for_build_editable(metadata_directory, config_settings=None):
    """Prepare editable wheel metadata."""
    return _prepare_metadata_for_build_wheel(metadata_directory, config_settings)


def build_sdist(sdist_directory, config_settings=None):
    """Build a source distribution."""
    from setuptools.build_meta import build_sdist as _build_sdist

    return _build_sdist(sdist_directory, config_settings)
