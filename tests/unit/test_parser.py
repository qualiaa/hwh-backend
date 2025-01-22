import os

import pytest

from hwh_backend.hwh_config import CythonCompilerDirectives, CythonConfig
from hwh_backend.parser import PyProject


@pytest.fixture
def temp_project_dir(tmp_path, sample_pyproject):
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    toml_path = project_dir / "pyproject.toml"
    toml_path.write_text(sample_pyproject)

    readme_path = project_dir / "README.md"
    readme_path.write_text("lorem ipsum")
    return project_dir


def assert_cython_config(config: CythonConfig):
    assert config.language == "c"
    print(config.sources)
    print(config.include_dirs)
    assert config.nthreads == os.cpu_count()
    # assert all(src in config.sources for src in ["foo.pyx", "bar.pyx"])
    assert set(["foo.pyx", "bar.pyx"]) == set(config.sources)
    assert set(["first", "second"]) == set(config.include_dirs)
    assert set(["/usr/lib", "/home/user/lib"]) == set(config.library_dirs)
    assert set(["/usr/lib"]) == set(config.runtime_library_dirs)
    assert set(["this", "that"]) == set(config.exclude_dirs)
    assert_compiler_flags(config.compiler_directives)


def assert_compiler_flags(flags: CythonCompilerDirectives):
    assert flags.language_level == "3"
    assert flags.binding == False
    assert flags.boundscheck == False
    assert flags.wraparound == False
    assert flags.initializedcheck == False
    assert flags.nonecheck == False
    assert flags.overflowcheck == False
    assert flags.embedsignature == False
    assert flags.cdivision == False
    assert flags.cdivision_warnings == False
    assert flags.profile == False
    assert flags.linetrace == False
    assert flags.type_version_tag == True


def test_hwh(temp_project_dir):
    os.chdir(temp_project_dir)
    p = PyProject(temp_project_dir)
    assert_cython_config(p.get_hwh_config().cython)
