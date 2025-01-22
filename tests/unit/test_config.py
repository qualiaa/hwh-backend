import os
import tomllib
from textwrap import dedent

import pytest

from hwh_backend.hwh_config import (
    CythonCompilerDirectives,
    CythonConfig,
    HwhConfig,
    Language,
)
from hwh_backend.parser import PyProject


@pytest.fixture()
def toml_no_hwh(tmp_path, sample_pyproject):
    import tomli_w

    pyproj_content = tomllib.loads(sample_pyproject)
    assert isinstance(pyproj_content, dict)
    del pyproj_content["tool"]["hwh"]
    project_dir = tmp_path / "test_project2"
    project_dir.mkdir()
    toml_path = project_dir / "pyproject.toml"
    with open(toml_path, "wb") as f:
        tomli_w.dump(pyproj_content, f)

    readme_path = project_dir / "README.md"
    readme_path.write_text("lorem ipsum")
    return project_dir


def test_cython_config(temp_project_dir):
    os.chdir(temp_project_dir)
    p = PyProject(temp_project_dir)
    t = HwhConfig(p.toml)
    print(t.cython)
    assert str(t.cython.language) == "c"
    assert t.cython.nthreads == os.cpu_count()
    assert t.cython.force is False
    assert t.cython.annotate is False

    assert t.cython.sources == ["foo.pyx", "bar.pyx"]
    assert t.cython.exclude_dirs == ["this", "that"]
    # assert False


def test_cython_config_undefined(toml_no_hwh):
    os.chdir(toml_no_hwh)
    p = PyProject(toml_no_hwh)
    t = HwhConfig(p.toml)
    assert str(t.cython.language) == "c"
    assert t.cython.nthreads == os.cpu_count()
    assert t.cython.force is False
    assert t.cython.annotate is False

    assert t.cython.sources == []
    assert t.cython.exclude_dirs == []


def test_default_cython_config():
    conf = CythonConfig()
    assert conf.language == Language.C
    assert conf.compiler_directives.language_level == "3"
    assert conf.compiler_directives.binding is False
    assert conf.compiler_directives.boundscheck is True
    assert conf.compiler_directives.wraparound is True
    assert conf.compiler_directives.initializedcheck is False
    assert conf.compiler_directives.nonecheck is False
    assert conf.compiler_directives.overflowcheck is False
    assert conf.compiler_directives.embedsignature is False
    assert conf.compiler_directives.cdivision is False
    assert conf.compiler_directives.cdivision_warnings is False
    assert conf.compiler_directives.profile is False
    assert conf.compiler_directives.linetrace is False
    assert conf.compiler_directives.infer_types is None
    assert conf.compiler_directives.type_version_tag is True


def test_invalid_compiler_directives():
    invalid_cases = [
        # Invalid language_level
        """
        [tool.hwh.cython.compiler_directives]
        language_level = "invalid"
        """,
        """
        [tool.hwh.cython.compiler_directives]
        binding = "not_a_bool"
        """,
    ]

    with pytest.raises(ValueError):
        toml_str = invalid_cases[0]
        config = tomllib.loads(dedent(toml_str))
        CythonCompilerDirectives(
            **config["tool"]["hwh"]["cython"]["compiler_directives"]
        )

    with pytest.raises(TypeError):
        toml_str = invalid_cases[1]
        config = tomllib.loads(dedent(toml_str))
        CythonCompilerDirectives(
            **config["tool"]["hwh"]["cython"]["compiler_directives"]
        )


def test_invalid_directive_values():
    """Test handling of invalid values for specific directives."""
    invalid_cases = [
        # Invalid language_level
        """
        [tool.hwh.cython.compiler_directives]
        language_level = "invalid"
        """,
        """
        [tool.hwh.cython.compiler_directives]
        binding = "not_a_bool"
        """,
        """
        [tool.hwh.cython]
        language = "mymadeupprogramminglanguage"
        """,
    ]

    for toml_str in invalid_cases:
        with pytest.raises((ValueError, TypeError)):
            config = tomllib.loads(dedent(toml_str))
            conf_obj = CythonConfig(**config["tool"]["hwh"]["cython"])
