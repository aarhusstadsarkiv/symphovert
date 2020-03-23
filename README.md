[![Aarhus Stadsarkiv](https://raw.githubusercontent.com/aarhusstadsarkiv/py-template/master/img/logo.png)](https://stadsarkiv.aarhus.dk/)
# py-template
Template repository for Python projects at Aarhus Stadsarkiv.

## Instructions
This repository includes default configuration files. A few changes needs to be made in some of them, specifically regarding **module name** and **author information**.

#### pyproject.toml
In `pyproject.toml`, `name` and `authors` should be changed:
```toml
[tool.poetry]
name = "YOUR_MODULE_NAME"
version = "0.1.0"
description = ""
authors = ["YOUR NAME <YOUR@EMAIL>", 
    "Aarhus Stadsarkiv <stadsarkiv@aarhus.dk>"]
license = "GPL-3.0"
readme = "README.md"
homepage = "https://stadsarkiv.aarhus.dk/"
```
`name` refers to your module name. Remember to use underscores instead of dashes when naming your module!

#### mypy.ini
In `mypy.ini`, the per module options should be changed to reflect your module name:
```ini
# Per module options
[mypy-YOUR_MODULE_NAME.*]
disallow_untyped_defs = True

```

#### GitHub Actions
This repository includes a simple GitHub Actions workflow that sets up `poetry` with caching and checks linting using `flake8` and `black`. A slightly more complicated workflow can be found in [here](https://github.com/aarhusstadsarkiv/convertool/blob/master/.github/workflows/tests.yml).

#### And finally...
Remember to change this `README` to suit your repository! The logo link can be reused.