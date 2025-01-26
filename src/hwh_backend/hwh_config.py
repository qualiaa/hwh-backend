import os
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Union, get_args, get_origin


class Language(StrEnum):
    C = "c"
    CPP = "c++"


class SitePackages(StrEnum):
    PURELIB = "pure"  # use sysconfig.get_path('purelib')
    USER = "user"  # use site.getusersitepackages()
    SITE = "site"  # use site.getsitepackages()
    NONE = "none"  # don't add sitepackages at all


@dataclass
class CythonCompilerWarningDirectives:
    # TODO: Unused atm
    undeclared: bool = False
    unreachable: bool = True
    maybe_uninitialized: bool = False
    unused: bool = False
    unused_arg: bool = False
    unused_result: bool = False
    multiple_declarators: bool = True


@dataclass
class CythonCompilerDirectives:
    # see https://cython.readthedocs.io/en/0.29.x/src/userguide/source_files_and_compilation.html#compiler-directives
    # Defaults are documentation's defauls
    binding: bool = False
    boundscheck: bool = True
    wraparound: bool = True
    initializedcheck: bool = False
    nonecheck: bool = False
    overflowcheck: bool = False
    # TODO: overflowcheck.fold, need to alter the dict..
    # overflowcheck_fold: bool = True
    embedsignature: bool = False
    cdivision: bool = False
    cdivision_warnings: bool = False
    # TODO: always_allow_keywords: bool = ?
    profile: bool = False
    linetrace: bool = False
    infer_types: bool | None = None
    # TODO: c_string_type: ?? = ??
    # c_string_unicoding: ?? = ??
    type_version_tag: bool = True
    # TODO: unraisable_traceback: bool = ?
    # TODO: iterable_coroutine: bool = ?

    # TODO: add warning directives

    def as_dict(self) -> dict[str, str | bool]:
        """Convert directives to dictionary for cythonize()."""
        return {
            key: value
            for key, value in self.__dict__.items()
            if value is not None  # Skip None values
        }

    def __post_init__(self):
        """Validate types and values after initialization."""
        for field_name, field_value in self.__dict__.items():
            field_type = self.__annotations__[field_name]

            # Type validation
            if get_origin(field_type) is Union:
                allowed_types = get_args(field_type)
                if field_value is not None and not isinstance(
                    field_value, allowed_types[0]
                ):
                    raise TypeError(
                        f"Field {field_name} must be {allowed_types[0].__name__} or None, "
                        f"got {type(field_value).__name__}"
                    )
            else:
                if not isinstance(field_value, field_type):
                    raise TypeError(
                        f"Field {field_name} must be {field_type.__name__}, "
                        f"got {type(field_value).__name__}"
                    )


@dataclass
class CythonConfig:
    language: Language = field(default=Language.C)
    compiler_directives: CythonCompilerDirectives = field(
        default_factory=CythonCompilerDirectives
    )
    nthreads: int = field(default_factory=lambda: os.cpu_count() or 1)
    force: bool = False
    annotate: bool = False
    sources: list[str] = field(default_factory=list)
    exclude_dirs: list[str] = field(default_factory=list)
    include_dirs: list[str] = field(default_factory=list)
    library_dirs: list[str] = field(default_factory=list)
    runtime_library_dirs: list[str] = field(default_factory=list)
    site_packages: SitePackages = field(default=SitePackages.PURELIB)

    def __post_init__(self):
        if isinstance(self.compiler_directives, dict):
            self.compiler_directives = CythonCompilerDirectives(
                **self.compiler_directives
            )

        if isinstance(self.language, str):
            try:
                self.language = Language(self.language.lower())
            except ValueError as e:
                valid_options = [lang.value for lang in Language]
                raise ValueError(
                    f"Invalid language: {self.language}. Valid options {valid_options}"
                ) from e

    @classmethod
    def from_pyproject(cls, tool_config: dict) -> "CythonConfig":
        cython_config = tool_config.get("cython", {})

        modules = {}
        modules = cython_config.get("modules", {})
        sources = modules.get("sources", [])
        exclude_dirs = modules.get("exclude_dirs", [])
        include_dirs = modules.get("include_dirs", [])
        runtime_library_dirs = modules.get("runtime_library_dirs", [])
        library_dirs = modules.get("library_dirs", [])
        return cls(
            language=cython_config.get("language") or Language.C,
            compiler_directives=CythonCompilerDirectives(
                **cython_config.get("compiler_directives", {})
            ),
            nthreads=cython_config.get("nthreads", os.cpu_count() or 1),
            force=cython_config.get("force", False),
            annotate=cython_config.get("annotate", False),
            sources=sources,
            exclude_dirs=exclude_dirs,
            include_dirs=include_dirs,
            library_dirs=library_dirs,
            runtime_library_dirs=runtime_library_dirs,
            site_packages=cython_config.get("site_packages") or SitePackages.PURELIB,
        )


class HwhConfig:
    def __init__(self, pyproject_data: dict):
        all_tools = pyproject_data.get("tool")
        config = {}

        if all_tools:
            config = all_tools.get("hwh", {})
        self.cython = CythonConfig.from_pyproject(config)
