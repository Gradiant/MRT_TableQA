import os

import yaml

CONFIG_PATH = os.path.dirname(os.path.abspath(__file__))
PROJECT_PATH = os.sep.join(CONFIG_PATH.split(os.sep)[0:-3])


def load_config(filename: str = "config.yaml"):
    docker_config_path = os.path.join("/configuration/", filename)

    config_path = (
        os.path.join(CONFIG_PATH, filename)
        if not os.path.isfile(docker_config_path)
        else docker_config_path
    )

    with open(config_path, "r") as f_stream:
        config = yaml.load(f_stream, Loader=yaml.FullLoader)

    if "datasets" in os.listdir(CONFIG_PATH):
        for file in os.listdir(os.path.join(CONFIG_PATH, "datasets")):
            with open(os.path.join(CONFIG_PATH, "datasets", file), "r") as f_stream:
                dataset = yaml.load(f_stream, Loader=yaml.FullLoader)
                config["datasets"] = dict(config.get("datasets", {}), **dataset)

    # path parser
    for module, options in config.items():
        if isinstance(options, str):
            if module.endswith("_path"):
                if not module.startswith((".", os.sep)):
                    config[module] = os.path.join(PROJECT_PATH, options)
        elif isinstance(options, dict):
            for key, value in options.items():
                if key.endswith("_path"):
                    if isinstance(value, str):
                        if not value.startswith((".", os.sep)):
                            options[key] = os.path.join(PROJECT_PATH, value)

    return config
