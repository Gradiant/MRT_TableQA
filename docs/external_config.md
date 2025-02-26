# External configuration

According to the [section about configuration](https://12factor.net/config) of the 12-factor app standard, _an app’s config is everything that is likely to vary between deploys (staging, production, developer environments, etc)_, and it should be strictly separated from the code. This often includes things like storage URLs and ports, hostnames, external service credentials, logging stuff...
This kind of configuration is not committed to version control, but rather populated at runtime through minimalistic, agnostic and standard **environment variables**.

The way in which these environment variables are **parsed** and **loaded** into the app will depend on the code itself, and the way in which they are **set** will depend on the particular development or deployment environment.

## Loading environment variables

### Defining configuration objects
This template uses [Pydantic Settings](https://docs.pydantic.dev/latest/usage/pydantic_settings/) to handle its external configuration.

Config objects inherit from pydantic's `BaseSettings`, and look like this:

```python
class ExampleLoggingConfig(BaseSettings):
    level: Literal["DEBUG", "INFO", "WARNING"]  # 1
    color: bool = True

    model_config = SettingsConfigDict(  # 2
        env_prefix="LOG_"  # 3
        env_file=".env",   # 4
    )
```
1. Pydantic performs validation through type hinting, providing a handy way of enforcing types, rules and defaults. Read about [Fields](https://docs.pydantic.dev/latest/usage/fields/) to find out more.
2. `model_config` is the official way of configuring Pydantic classes in Pydantic 2.
3. This specifies a prefix that Pydantic will use to look for the env variables that will be used to populate this model. In this case, the fields `level` and `color` will be filled with the values of env variables `LOG_LEVEL` and `LOG_COLOR` (envs are usually case insensitive).
4. And yes, you can specify an env file. Remember that proper environment variables will always take priority, so if your `.env` says `LOG_LEVEL=INFO` but there's already an env variable called `LOG_LEVEL` with value `DEBUG`, your `ExampleLoggingConfig` will load with the `level` attribute set to `DEBUG`. Pydantic won't export anything into the environment.

### Using configuration objects
To use one of these Pydantic config classes in your code, just import it and instantiate it. It will be populated using the env vars and env files **that exist at instantiation time**.
```python
# tqa/myapp/code.py
import os
from tqa.common.configuration.config import ExampleLoggingConfig

os.getenv("LOG_LEVEL")  # DEBUG

logging_config = ExampleLoggingConfig()
logging_config.level  # DEBUG

os.environ["LOG_LEVEL"] = "WARNING"

logging_config.level  # DEBUG

newly_spawned_logging_config = ExampleLoggingConfig()
newly_spawned_logging_config.level  # WARNING
```

### Testing with configuration objects
When you're not testing the config itself (but rather a different part of the system that depends on the config), you don't really want to be thinking about the state of your environment.

To build a test-friendly config object, just provide your desired values while instantiating it (and then inject it or mock it in the piece of code under test):
```python
test_logging_config = ExampleLoggingConfig(level="INFO", color=False)
```

## Setting environment variables

### In a local development environment
Open your favorite terminal and run the command `env`. You'll be welcomed by a long list of environment variables belonging to a variety of parts of your system: some familiar ones like `OS` and `PATH`, and some OS and app-specific ones like `DISPLAY`, `GNOME_SHELL_SESSION_MODE` or `CHROME_DESKTOP`.
This is the same pool of variables that gets accessed when you run your app locally and it tries to look for `IMPORTANT_CUSTOM_VARIABLE`.

To actually define the values of these variables, you could manually set them according to your OS specifications (e.g. by running `export IMPORTANT_CUSTOM_VARIABLE=123` in a bash shell), or you could choose to enjoy the convenience of an **env file**.
Env files are just text files that contain the definitions of the environmental variables that your app needs to function. They look like this: 
```
IMPORTANT_CUSTOM_VARIABLE=123
ANOTHER_IMPORTANT_CUSTOM_VARIABLE=True
YET_ANOTHER_IMPORTANT_CUSTOM_VARIABLE=vandalay
```
At runtime, they get parsed (by your app itself or by your deployment system), and are used to:
- Either populate the local environment (i.e. would show up by running `env`)...
- ...or directly build your app's configuration objects (i.e. would not show up by running `env`).

By convention, many apps (including those built using this template) will try to load an env file called `.env` located directly in the root of the project.

While local env files are handy, keep in mind that:
- Actual environment variables must always take priority and overwrite values read from env files. 
- Your tests should probably not depend on the existence of local env files.

### Within a containerized production environment
Container-based deployment frameworks usually provide standardized ways to populate the environments of newly-spawned containers; both by specifying them directly, and by pointing to convenience env files.

Plain old `docker run`, for instance, has `--env` and `--env-file` command line arguments for that purpose.

Docker Compose files have `environment` and `env_file` attributes.

Kubernetes has `env` and -arguably more complicated- `envFrom` fields.