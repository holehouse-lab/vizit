# Development and testing tools

This directory contains optional helpers for development and testing that are
not part of the package itself. Continuous integration runs via GitHub Actions
(see `.github/workflows/ci.yml`); the conda files below are provided only as a
convenience for contributors who prefer a conda-based workflow.

## Manifest

### Conda environment

* `conda-envs/test_env.yaml`: a minimal environment with the base test
  dependencies. Channels are not pinned, so it respects your global conda
  configuration.

### Scripts

* `scripts/create_conda_env.py`: helper for creating a conda environment from a
  YAML file, with the Python version and environment name passed on the command
  line.

## How to contribute changes

- Fork or branch the repository: `git checkout -b my-feature`.
- Make your changes and add tests.
- Run the checks locally: `pytest`, `ruff check .`, `ruff format .`, `mypy vizit`.
- Push the branch and open a pull request on GitHub.

## Releasing

Versions are derived automatically from `git` tags by
[versioningit](https://versioningit.readthedocs.io) (PEP 440 compliant). To cut
a release, tag the commit and push the tag:

```bash
git tag -a X.Y.Z -m "vizit X.Y.Z"
git push --follow-tags
```

If a commit is exactly on a tag, the installed version is that tag (e.g.
`0.1.2`); otherwise versioningit appends the distance from the last tag and the
commit hash.
