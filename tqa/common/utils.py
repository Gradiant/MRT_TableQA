import json
import os
import time
from datetime import datetime

import numpy as np
import pandas as pd
import yaml

CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))
MODULE_PATH = os.sep.join(CURRENT_PATH.split(os.sep)[0:-1])
PROJECT_PATH = os.sep.join(CURRENT_PATH.split(os.sep)[0:-2])



def config_file(filename="config.yml"):
    config_vars = read_yaml(os.path.join(CURRENT_PATH, filename))

    return config_vars

def save_yaml(path,data):
    with open(path, 'w') as outfile:
        yaml.dump(data, outfile, default_flow_style=False)
        
def read_yaml(_path):
    with open(_path, "r") as f_stream:
        config = yaml.load(f_stream, Loader=yaml.FullLoader)

    return config


def read_text(file_path: str):
    with open(file_path, "r") as input_text:
        return input_text.read()


def read_json(file_path: str):
    with open(file_path, "r", encoding="utf8") as json_in:
        return json.load(json_in)


def read_jsonl(file_path: str):
    with open(file_path, "r", encoding="utf8") as json_in:
        out = []

        for line in json_in:
            try:
                entry = json.loads(line)
                out.append(entry)
            except Exception:
                continue

        return out


def save_json(file_path: str, data: dict):
    with open(file_path, "w+", encoding="utf8") as json_out:
        json.dump(data, json_out, ensure_ascii=False)


def save_jsonl(file_path: str, data: list, option="w+"):
    with open(file_path, option, encoding="utf8") as json_out:
        for entry in data:
            json.dump(entry, json_out, ensure_ascii=False)
            json_out.write("\n")


def save_csv(file_path: str, data: pd.DataFrame):
    data.to_csv(ensure_path(file_path), index=False)


FILETYPES = {
    "JSON": (".json"),
    "JSONL": (".jsonl", ".ndjson"),
    "CSV": (".csv"),
    "EXCEL": (".xls", ".xlsx"),
}


def read_folder(path, *args, **kwargs):
    path = path if not path.startswith(os.sep) else os.path.join(CURRENT_PATH, path)
    for file in os.listdir(path):
        if not file.startswith("."):
            file_path = os.path.join(os.path.join(CURRENT_PATH, path, file))
            if file.endswith(FILETYPES["EXCEL"]):
                yield (file, pd.read_excel(file_path, engine="openpyxl"))
            elif file.endswith(FILETYPES["CSV"]):
                yield (file, pd.read_csv(file_path, **kwargs))
            elif file.endswith(FILETYPES["JSONL"]):
                yield (
                    file,
                    read_jsonl(os.path.join(CURRENT_PATH, path, file)),
                )
            elif file.endswith(FILETYPES["JSON"]):
                yield (file, read_json(os.path.join(CURRENT_PATH, path, file)))


def read_excel(file_path, **kargs):
    return pd.read_excel(pd.ExcelFile(file_path), None)


def read_csv(file_path, **kargs):
    return pd.read_csv(file_path).to_dict("records")


def measure(function, *args,**kargs):
    init = time.time()
    result = function(*args,**kargs)
    return result, time.time() - init


def read_jsonl_as_df(path):
    return pd.read_json(path, lines=True)


def ensure_path(path: str, reference=PROJECT_PATH):
    if not path.startswith("./") and not path.startswith("/"):
        return os.path.abspath(os.path.join(reference, path))
    else:
        return os.path.abspath(path)


def get_file_info(path, makedir=False):
    path = ensure_path(path)
    path_steps = [step for step in path.split(os.sep) if step != ""]

    last_step = path_steps[-1]

    if "." in last_step:
        folder = os.sep + os.sep.join(path_steps[0:-1])
        file_name = last_step
        extension = last_step.split(".")[-1]
    else:
        folder = path
        file_name = None
        extension = False

    os.makedirs(folder, exist_ok=True) if makedir else None

    return folder, file_name, extension


def get_str_date(format_str="%Y%m%d_%H%M%S"):
    return datetime.now().strftime(format_str)


def list_to_dim_1(lista: list):
    out = []
    if isinstance(lista, list):
        for element in lista:
            if (
                isinstance(element, str)
                or isinstance(element, bool)
                or isinstance(element, dict)
            ):
                out.append(element)
            elif isinstance(element, list):
                out.extend(list_to_dim_1(element))
        return out
    else:
        return False


def get_exp_difference(value1, value2):
    diff = abs(np.floor(np.log10(np.abs(value1 - value2))))
    if value1 > value2:
        return diff
    else:
        return -diff


def eval_secure(expresion_to_eval, error_result=None):
    try:
        result = eval(expresion_to_eval)
        return result
    except Exception:
        return error_result
