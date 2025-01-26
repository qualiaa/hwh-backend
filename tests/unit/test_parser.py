import pytest
from packaging.version import Version

from hwh_backend.parser import PyProject


def test_parse_basic_metadata(tmp_path, sample_pyproject):
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    pyproject_path = project_dir / "pyproject.toml"
    pyproject_path.write_text(sample_pyproject)

    parser = PyProject(project_dir)
    assert parser.package_name == "test_pkg"
    assert parser.package_version == Version("0.1.0")


def test_missing_pyproject(tmp_path):
    with pytest.raises(FileNotFoundError):
        PyProject(tmp_path)


def test_parse_dependencies(tmp_path, sample_pyproject):
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    pyproject_path = project_dir / "pyproject.toml"
    pyproject_path.write_text(sample_pyproject)

    parser = PyProject(project_dir)
    deps = parser.dependencies
    assert any(d.name == "Cython" for d in deps)


def test_hwh_config(tmp_path, sample_pyproject):
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    pyproject_path = project_dir / "pyproject.toml"
    pyproject_path.write_text(sample_pyproject)

    parser = PyProject(project_dir)
    config = parser.get_hwh_config()
    assert config.cython.language == "c"
    assert config.cython.compiler_directives.language_level == "3"
