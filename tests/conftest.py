import pytest


@pytest.fixture(scope="package")
def sample_pyproject():
    content = """
    [build-system]
    requires = [
        "hwh-backend",
        "Cython==0.29.*",
        "my_cython_library @ git+ssh://git@github.com/user/test-repo.git@1.0.0",
    ]
    build-backend = "hwh_backend"

    [project]
    name = "second_lib"
    description = "A second Cython library that depends on my_cython_library"
    requires-python = ">=3.11"
    dependencies = [
        "my_cython_library @ git+ssh://git@github.com/user/test-repo.git@v1.0.0",
    ]
    readme = "README.md"
    license = { text = "MIT" }
    version = "1.0.0"

    [project.optional-dependencies]
    test = ["pytest>=7.0", "pytest-cov>=4.0", "coverage>=7.0"]

    [tool.pytest.ini_options]
    testpaths = ["tests"]
    python_files = ["test_*.py"]
    addopts = "-v"

    [tool.hwh.cython.modules]
    include_dirs = ["first", "second"]
    runtime_library_dirs = ["/usr/lib"]
    library_dirs = ["/usr/lib", "/home/user/lib"]
    sources = ["foo.pyx", "bar.pyx"]
    exclude_dirs = ["this", "that"]

    [tool.hwh.cython]
    language="c"
    annotate=false

    [tool.hwh.cython.compiler_directives]
    # Cython compiler directives

    language_level = "3"  # Options: "2", "3", "3str"
    binding = false  # Generate Python wrapper functions
    boundscheck = false  # Array bounds checking
    wraparound = false  # Negative indexing
    initializedcheck = false  # Check if extension types are initialized
    nonecheck = false  # Generate checks for null Python references
    overflowcheck = false  # Check for C integer overflows
    embedsignature = false  # Include docstrings in the C code
    cdivision = false  # Division by zero checking
    cdivision_warnings = false  # Division by zero warning
    profile = false  # Enable profiling
    linetrace = false  # Enable line tracing
    type_version_tag = true  # Enable CPython's type attribute cache
    """

    return content


@pytest.fixture()
def temp_project_dir(tmp_path, sample_pyproject):
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    toml_path = project_dir / "pyproject.toml"
    toml_path.write_text(sample_pyproject)

    readme_path = project_dir / "README.md"
    readme_path.write_text("lorem ipsum")
    return project_dir
