# Pre Commit Hooks

This project uses pre-commit hooks to check code quality and format before it's finally committed to the repository. To configure the pre-commit hooks to evaluate your code, follow these steps:

1. Install the pre-commit utility: `make install-dev`
2. Run the following command in the root directory: `pdm run pre-commit install`
3. Done.

After this setup, black and flake should run before each commit command.

```
git commit -m "example commit"
[INFO] Installing environment for https://github.com/psf/black.
[INFO] Once installed this environment will be reused.
[INFO] This may take a few minutes...
black....................................................................Passed
flake8...................................................................Passed
[master 12a838b] example commit
```

If you don't follow the style guide, these tools will show warning and they will abort your commit.

```
git commit -m "example commit"
black....................................................................Failed
- hook id: black
- files were modified by this hook

reformatted example_package/common/infrastructure/timescale_engine.py

All done! ✨ 🍰 ✨
1 file reformatted, 3 files left unchanged.

flake8...................................................................Failed
- hook id: flake8
- exit code: 1

example_package/cli.py:12:80: E501 line too long (88 > 79 characters)
example_package/common/infrastructure/timescale_engine.py:10:80: E501 line too long (88 > 79 characters)

```
