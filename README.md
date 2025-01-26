# Halfway House backend

[![Publish to PyPI](https://github.com/mkgessen/hwh-backend/actions/workflows/python-publish.yml/badge.svg)](https://github.com/mkgessen/hwh-backend/actions/workflows/python-publish.yml)

Provides [PEP-517](https://peps.python.org/pep-0517/) build hooks for building
Cython extensions with setuptools. Currently supports Cython 0.29.

Ideally similar functionality would be provided an actual setuptools backend.

## Requirements

- CI tests only for `Python 3.11` and `Cython` 0.29.xx at the moment
- your project should have `MANIFEST.in` file defining the `.pyx` files that
  should be included
- Currently doesn't support src builds

## Intended use

HWH is intended to be bolt on replacement for projects that build Cython
extensions with setuptools. You should be able to get rid of your `setup.py` and
you don't need to call `python -m setup.py` to build extensions.

### Scenarios that HWH tries to solve

1. Project that has `.pyx` files, but doesn't is not designed to be used by
   other projects. Doesn't contain `.pxd` files
2. Project that has `.pyx` and `.pxd` files and plain `.py` files
3. Project that has .`pyx` and `.pxd` files and depends on another project that
   looks like #2
   - dependency used in both Cython and Python

HWH backend is mainly configured through an additional section in
`pyproject.toml`. The section is entirely optional. The default behaviour is
described in [[tool.hwh.cython]] and [[tool.cython.modules]].

- You can use also use `python -m build --wheel --no-isolation` for wheel
  building and recompilation of extensions (editable install)
  - HWH currently provides 3 optinal arguments that can be used to control the
    build process
  - `python -m build --wheel --no-isolation configuration-setting annotate=true
  configuration-setting nthreads=10 configuration-setting force=true`
    - **annotate** (bool): build annotation .html files is set true
    - nthreads (int): number of threads allocated defaults to `os.cpu_count()`
      or 1 in case where cpu count in undefined
    - force (bool): force extensions to be rebuilt if set to true

HWH backend provides an additional **optional** section to `pyproject.toml`.
Valid options are shown in the example below. If `[tool.hwh]` is absent

### `[tool.hwh.cython]`

- `annotate`: Defines if Cython should build the annotation html files. Valid
  values are `true` and `false`. Defaults to `false`
- `language`: extension language (i.e. "c", "c++"). Will be detected from the
  source extensions if not provided. Option `objc` is not supported, since I
  can't test it.
- `nthreads`: Number of threads to build extensions. Defaults to
  `os.cpu_count()` or 1 in case where cpu count in undefined
- `force`: Force build. Valid values are `true` and `false`. Defaults to `false`

### `[tool.hwh.cython.modules]`

Configuration options for all Cython modules.

- `include_dirs`, `runtime_library_dirs` and `library_dirs` are passed to
  constructor of `Extension`
  - `include_dirs`: list of directories to search for C/C++ header files (in
    Unix form for portability)
  - `library_dirs`: list of directories to search for C/C++ libraries at link
    time. Gets extended by site-packages by default.
  - `runtime_library_dirs`: list of directories to search for C/C++ libraries at
    run time (for shared extensions, this is when the extension is loaded). Gets
    extended by site-packages by default.
  - `sources`: list of source filenames, relative to the distribution root. By
    default hwh searches for all *.pyx files in all directories within the
    distribution root. (=where `pyproject.toml` lives). Accepts wildcards like
    `foo/*.pyx`
  - `exclude_dirs` list of directories where *.pyx files shouldn't be searched
    from. Gets extended by <distribution_root>/build by default. Doesn't have
    impact when `sources` is present
  - `site_packages`: Defines which site-packages should be used. Allows options
    are:
    - **purelib** -> use `sysconfig.get_path("purelib")`
    - **user** -> use `site.getusersitepackages()`
    - **site** -> use `site.getsitepackages()`
    - **none** -> you want to explicitly use `library_dirs`, and `include_dirs`
      to define what to search for and where from

For more information, see
[Cython docs](https://cython.readthedocs.io/en/0.29.x/src/userguide/source_files_and_compilation.html)
and
[Setup tools extension docs](https://setuptools.pypa.io/en/latest/userguide/ext_modules.html)

### `[tool.hwh.cython.compiler_directives]`

HWH exposes the most of Cython's compiler directives. See
[compiler directives](https://cython.readthedocs.io/en/0.29.x/src/userguide/source_files_and_compilation.html#compiler-directives)
for more information. The `pyproject.toml` example below shows how to use the
compiler options

### Example `pyproject.toml`

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
site_packages = "purelib"

[tool.hwh.cython]
# language defaults to C
language="c"

# default = false
annotate=false

# default = os.cpu_count() or 1, if os.cpu_count() returns None
nthreads=1

# default = false
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
```
