# Halway House backend 

Provides [PEP-517](https://peps.python.org/pep-0517/) build hooks for building Cython extensions with setuptools.
Currently supports Cython 0.29. 

Ideally similar functionality would be provided an actual setuptools backend.

## Intended use

```toml pyproject.toml
[build-system]
requires = ["hwh-backend", "Cython<3.0.0"]
build-backend = "hwh_backend.build"

[project]
name = "mylib"
version = "1.0.0"

[tool.hwh.cython.modules]
include_dirs = ["first", "second"]
runtime_library_dirs = ["/usr/lib"]
library_dirs = ["/usr/lib", "/home/user/lib"]
sources = ["foo.pyx", "bar.pyx"]
exclude_dirs = ["this", "that"]

[tool.hwh.cython]
language="c"
annotate=false
nthreads=1
force=false

[tool.hwh.cython.compiler_directives]
# Cython compiler directives
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

# All cython modules go here
[tool.hwh_backend.cython.modules]
sources = [mylib/*.pyx]
```
