import json
import shutil
import site
import sysconfig
from importlib.metadata import distributions
from pathlib import Path
from typing import List, Optional, Union

from Cython.Build import cythonize
from setuptools import find_packages
from setuptools.build_meta import (
    build_editable as _build_editable,
)
from setuptools.command.build_ext import build_ext
from setuptools.dist import Distribution
from setuptools.extension import Extension

from hwh_backend.hwh_config import SitePackages

from .parser import PyProject

# Global flag to prevent double builds
_EXTENSIONS_BUILT = False

# Global flag to pass --config-setting foo=bar values from python -m build
_CONFIG_OPTIONS: Optional[dict[str, int | bool]] = None


def debug_print(*args, **kwargs):
    print("[DEBUG]", *args, **kwargs)


def _is_editable_install():
    """Inspects package's site_packages/pkg_name/direct_url.json
    to dermine whether the installation is editable or not, see
    https://packaging.python.org/en/latest/specifications/direct-url-data-structure/"""
    project = PyProject(Path())
    pkg_name = project.package_name

    debug_print(f"===CHECKING EDITABLE=== for package {pkg_name}")
    # FIXME: using all site packages here might not be clever..
    site_packages = site.getsitepackages()
    debug_print(f"Used site packages: {site_packages}")
    for dist in distributions(name=pkg_name, path=site_packages):
        content = dist.read_text("direct_url.json")
        debug_print(f"Found content {content}")
        if content is not None:
            direct_url = json.loads(content)
            debug_print(f"Converting to json {direct_url}")
            if "dir_info" in direct_url:
                debug_print(f"[OK] Package {pkg_name} is editable install")
                return direct_url["dir_info"].get("editable", False)

    debug_print(f"Package {pkg_name} is not editable install")
    return False


def get_sitepackages(option: SitePackages):
    # TODO: move to hwh config
    match option:
        case SitePackages.PURELIB:
            return [sysconfig.get_path("purelib")]
        case SitePackages.USER:
            return [site.getusersitepackages()]
        case SitePackages.SITE:
            return site.getsitepackages()
        case SitePackages.NONE:
            return []


def find_cython_files(
    source_dir: Path,
    sources: Optional[List[Union[str, Path]]] = None,
    exclude_dirs: Optional[List[str]] = None,
) -> List[Path]:
    """Find all Cython source files in the package directory."""
    debug_print(f"Searching for Cython files in: {source_dir}")
    debug_print(f"Explicit sources: {sources}")
    debug_print(f"Exclude dirs: {exclude_dirs}")

    if sources:
        # Convert all sources to Path objects relative to source_dir
        res = [
            source_dir / src if isinstance(src, str) else src
            for src in sources
            if str(src).endswith(".pyx")
        ]
        debug_print(f"Using explicit sources: {res}")
        return res

    all_pyx = list(source_dir.rglob("*.pyx"))
    debug_print(f"Found all .pyx files: {all_pyx}")

    # FIXME: something wrong with types here
    # Filter out all directories that are excluded
    exclude_dirs = set(exclude_dirs or [])
    if exclude_dirs:
        # Convert exclude_dirs to full paths relative to source_dir
        exclude_paths = {source_dir / excluded for excluded in exclude_dirs}
        debug_print(f"Exclude paths: {exclude_paths}")
        filtered = [
            pyx
            for pyx in all_pyx
            if not any(exclude_path in pyx.parents for exclude_path in exclude_paths)
        ]
        debug_print(f"After exclusion: {filtered}")
        return filtered

    return list(all_pyx)


def _get_ext_modules(project: PyProject, config_settings: Optional[dict] = None):
    """Get Cython extension modules configuration."""
    debug_print("\n=== Starting _get_ext_modules ===")
    debug_print(f"Project name: {project.package_name}")
    debug_print(f"Project version: {project.package_version}")
    debug_print(f"get ext Config settings: {config_settings}")

    # Parse build settings
    global _CONFIG_OPTIONS
    if not _CONFIG_OPTIONS:
        _CONFIG_OPTIONS = _parse_build_settings(config_settings)
    debug_print(f"Parsed build settings: {_CONFIG_OPTIONS}")

    # Create directory lists for Extension ctor and cythonize()
    config = project.get_hwh_config().cython
    site_packages = get_sitepackages(config.site_packages)
    debug_print(f"Site packages: {site_packages}")

    library_dirs = config.library_dirs + site_packages
    runtime_library_dirs = config.runtime_library_dirs
    include_dirs = config.include_dirs + site_packages

    debug_print(f"Library dirs: {library_dirs}")
    debug_print(f"Runtime library dirs: {runtime_library_dirs}")
    debug_print(f"Include dirs: {include_dirs}")

    # Find all .pyx files in the package directory
    # FIXME: Extension class' docstrings state that files are searched from the
    #  root downwards. Currently we only support <pkg_name>/<pkg_name>/<pyx files here>
    # kind of file tree
    # TODO: Add support for src/ structure
    package_dir = Path(project.package_name).parent
    debug_print(
        f"Looking for .pyx files in package dir: {package_dir.absolute().as_posix()}"
    )

    pyx_files = find_cython_files(
        package_dir,
        sources=config.sources,
        # NOTE: I'm going to hard code build dir to excluded dirs for now
        # use case being that python -m build gets called when build/
        # already exists. This would cause find_cython_files to find .pyx files
        # we want to exclude from the build
        exclude_dirs=config.exclude_dirs + [package_dir / "build"],
    )
    debug_print(f"Found .pyx files: {pyx_files}")

    # Create Extensions
    ext_modules = []
    for pyx_file in pyx_files:
        # Convert path to proper module path. Absolute paths are forbidden by pip
        rel_path = pyx_file.relative_to(package_dir)
        debug_print(f"\nProcessing: {pyx_file}")
        debug_print(f"Relative path: {rel_path}")

        # Construct full module path including package name
        module_parts = [project.package_name] + [
            part for part in rel_path.parent.parts if part != "."
        ]
        if rel_path.name != "__init__.pyx":
            module_parts.append(rel_path.stem)

        module_path = ".".join(module_parts).split(".", 1)[-1]
        debug_print(f"Constructed module path: {module_path}")

        ext = Extension(
            module_path,
            [str(pyx_file)],
            language=config.language,
            library_dirs=library_dirs,
            runtime_library_dirs=runtime_library_dirs,
        )
        debug_print(f"Created Extension object: {ext.name}")
        ext_modules.append(ext)

    debug_print(f"\nTotal extensions to build: {len(ext_modules)}")
    debug_print("=== Finished _get_ext_modules ===\n")

    # Override config values with build settings.
    if not _CONFIG_OPTIONS:
        _CONFIG_OPTIONS = {}
    nthreads = _CONFIG_OPTIONS.get("nthreads", config.nthreads)
    force = _CONFIG_OPTIONS.get("force", config.force)
    annotate = _CONFIG_OPTIONS.get("annotate", config.annotate)
    debug_print(f"\n=== FORCE = {force} ")
    debug_print(f"\n=== ANNOTATE = {annotate} ")
    debug_print(f"\n=== NTHREADS = {nthreads} ")

    cythonized = cythonize(
        ext_modules,
        nthreads=nthreads,
        force=force,
        annotate=annotate,
        compiler_directives=config.compiler_directives.as_dict(),
        include_path=include_dirs,  # This helps find .pxd files
    )

    return cythonized


class EditableBuildExt(build_ext):
    """Custom build_ext that handles editable installs properly."""

    def initialize_options(self):
        super().initialize_options()
        self._is_editable = False
        self._original_build_lib = None

    def finalize_options(self):
        """Finalize build options and set up editable install if needed."""
        super().finalize_options()
        self._is_editable = _is_editable_install()

        if self._is_editable:
            debug_print("Configuring for editable install")
            # Store original build_lib for later
            self._original_build_lib = self.build_lib
            # For editable install, build directly in source tree
            self.inplace = True
            self.build_lib = str(Path.cwd())
        else:
            debug_print("Configuring for regular install")

    def run(self):
        """Run the build process."""
        debug_print(f"Running build_ext (editable={self._is_editable})")
        debug_print(f"Build lib: {self.build_lib}")
        debug_print(f"Build temp: {self.build_temp}")

        # Run the actual build
        super().run()

        # if self._is_editable:
        # self._copy_extension_files()

    def _copy_extension_files(self):
        """Copy extension files to their final locations for editable installs."""
        if not self._original_build_lib:
            return

        build_lib_path = Path(self._original_build_lib)
        source_path = Path.cwd()

        debug_print(f"Copying extension files from {build_lib_path} to {source_path}")

        # Find all built extension files
        for ext in self.extensions:
            # Get the full path to the built extension
            ext_path = self.get_ext_fullpath(ext.name)
            rel_path = Path(ext_path).relative_to(build_lib_path)
            target_path = source_path / rel_path

            # Ensure target directory exists
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy the extension file
            if ext_path.exists():
                shutil.copy2(ext_path, target_path)
                debug_print(f"Copied {ext_path} to {target_path}")


def _parse_build_settings(config_settings: dict | None = None) -> dict[str, bool | int]:
    """Parse build settings from config_settings dict."""
    if not config_settings:
        return {}

    result = {}
    try:
        if annotate := config_settings.get("annotate"):
            result["annotate"] = annotate.lower() == "true"

        if nthreads := config_settings.get("nthreads"):
            try:
                result["nthreads"] = int(nthreads)
            except ValueError:
                print(f"Invalid nthreads value: {nthreads}")

        if force := config_settings.get("force"):
            result["force"] = force.lower() == "true"

    except Exception as e:
        print(f"Error parsing config settings: {e}")
        return {}

    return result


def _build_extension(inplace: bool = False, config_settings={}):
    """Build the extension modules with better editable install handling."""

    debug_print("\n=== Starting _build_extension ===")
    debug_print(f"\n with config {config_settings}")
    global _EXTENSIONS_BUILT

    if _EXTENSIONS_BUILT:
        debug_print("Extensions already built, skipping")
        return

    project = PyProject(Path())
    name = project.package_name

    dist = Distribution(
        {
            "name": name,
            "ext_modules": _get_ext_modules(project, config_settings=config_settings),
        }
    )
    dist.has_ext_modules = lambda: True

    cmd = EditableBuildExt(dist)
    cmd.inplace = inplace
    cmd.ensure_finalized()
    cmd.run()

    _EXTENSIONS_BUILT = True
    debug_print("=== Finished _build_extension ===\n")


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    """Build wheel with explicit editable install handling."""
    debug_print("\n=== Starting build_wheel ===")

    _build_extension(
        _is_editable_install(), config_settings=config_settings
    )  # No need to pass inplace flag anymore

    project = PyProject(Path())
    name = project.package_name

    # Find all subdirectories containing .pxd files
    package_dir = Path(name)
    pxd_dirs = set()
    for pxd_file in package_dir.rglob("*.pxd"):
        rel_path = pxd_file.relative_to(package_dir)
        pxd_dirs.add(
            str(rel_path.parent) + "/*.pxd" if rel_path.parent.parts else "*.pxd"
        )

    debug_print(f"Found .pxd patterns: {pxd_dirs}")
    dist = Distribution(
        {
            "name": name,
            "version": str(project.package_version),
            "ext_modules": _get_ext_modules(project),
            "packages": [name]
            + [f"{name}.{subpkg}" for subpkg in find_packages(str(package_dir))],
            "package_data": {name: ["*.pxd", "*.so"]},
            "include_package_data": True,
        }
    )

    # Use the custom build_ext command
    dist.cmdclass = {"build_ext": EditableBuildExt}
    dist.has_ext_modules = lambda: True
    from wheel.bdist_wheel import bdist_wheel as wheel_command

    class BdistWheelCommand(wheel_command):
        def finalize_options(self):
            super().finalize_options()
            self.root_is_pure = False
            self.user_options = config_settings

        def run(self):
            debug_print("Running custom bdist_wheel command")
            super().run()

    cmd = BdistWheelCommand(dist)
    cmd.dist_dir = wheel_directory
    cmd.distribution.script_name = "fubar"
    cmd.ensure_finalized()
    debug_print("Starting wheel build")
    cmd.run()
    debug_print("Finished wheel build")

    # Find the built wheel
    wheel_path = next(Path(wheel_directory).glob("*.whl"))
    debug_print(f"Built wheel: {wheel_path}")
    debug_print("=== Finished build_wheel ===\n")
    return wheel_path.name


def build_editable(wheel_directory, config_settings=None, metadata_directory=None):
    """Build editable wheel."""
    debug_print("\n=== Starting build_editable ===")
    debug_print(f"Wheel directory: {wheel_directory}")
    debug_print(f"Config settings: {config_settings}")
    debug_print(f"Metadata directory: {metadata_directory}")

    # Editable install=inplace
    debug_print(f"passing config {config_settings}")
    _build_extension(inplace=True, config_settings=config_settings)

    debug_print("Calling setuptools build_editable")
    result = _build_editable(wheel_directory, config_settings, metadata_directory)
    debug_print(f"Editable build result: {result}")
    debug_print("=== Finished build_editable ===\n")
    return result


def build_sdist(sdist_directory, config_settings=None):
    """Build source distribution. How is that meant to work with compiled code?"""
    from setuptools.build_meta import build_sdist as _build_sdist

    return _build_sdist(sdist_directory, config_settings)
