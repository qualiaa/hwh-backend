import pytest

from hwh_backend.hwh_config import (
    CythonCompilerDirectives,
    CythonConfig,
    Language,
    SitePackages,
)


@pytest.fixture
def minimal_config():
    return {"language": "c", "compiler_directives": {}}


def test_basic_config(minimal_config):
    config = CythonConfig(**minimal_config)
    assert config.language == Language.C


def test_site_packages_config():
    config = CythonConfig(site_packages=SitePackages.PURELIB)
    assert config.site_packages == SitePackages.PURELIB


def test_invalid_language():
    with pytest.raises(ValueError):
        CythonConfig(language="invalid")


def test_compiler_directives_validation():
    with pytest.raises(TypeError):
        CythonCompilerDirectives(boundscheck="invalid")


def test_compiler_directives_types():
    with pytest.raises(TypeError):
        CythonCompilerDirectives(binding="not_a_bool")


def test_cython_compiler_directives_constant_language_level():
    """Test that language_level is constant and properly included in as_dict()."""
    directives = CythonCompilerDirectives()

    # Test that language_level is constant
    assert directives.language_level == "3"
    with pytest.raises(AttributeError):
        directives.language_level = "2"

    # Test that as_dict() includes language_level
    result = directives.as_dict()
    assert "language_level" in result
    assert result["language_level"] == "3"

    # Test that private fields are not included
    assert "_language_level" not in result

    # Test that all other fields work normally
    directives.binding = True
    result = directives.as_dict()
    assert result["binding"] is True
    assert result["language_level"] == "3"  # Still present and unchanged


def test_complete_config():
    config = CythonConfig(
        language=Language.CPP,
        sources=["src1.pyx", "src2.pyx"],
        exclude_dirs=["tests"],
        include_dirs=["/usr/include"],
        library_dirs=["/usr/lib"],
        runtime_library_dirs=["/usr/lib"],
        site_packages=SitePackages.SITE,
        compiler_directives=CythonCompilerDirectives(boundscheck=False),
    )
    assert config.language == Language.CPP
    assert len(config.sources) == 2
    assert not config.compiler_directives.boundscheck
