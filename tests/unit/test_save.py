import os
import shutil
from time import sleep

from tqa.common.utils import ensure_path, read_jsonl
from tqa.common.utils_decorators import save

test_folder_path = "tests/assets/save"


@save(folder=test_folder_path)
def function_to_save(name):
    return {"key": name}


@save(folder=test_folder_path)
def function_multiple_attributes(name, surname):
    return [name, surname]


def remove_test_folder(function_name):
    input_filepath = os.path.join(
        ensure_path(test_folder_path), "{}_input.jsonl".format(function_name)
    )
    output_filepath = os.path.join(
        ensure_path(test_folder_path), "{}_output.jsonl".format(function_name)
    )

    if os.path.isfile(input_filepath):
        os.remove(input_filepath)
    if os.path.isfile(output_filepath):
        os.remove(output_filepath)
    if os.path.isdir(ensure_path(test_folder_path)):
        os.removedirs(ensure_path(test_folder_path))

    return input_filepath, output_filepath


def test_save_1():

    input_filepath, output_filepath = remove_test_folder("function_to_save")
    sleep(10)
    print("execution", function_to_save("Álvaro1"))

    assert os.path.isdir(ensure_path(test_folder_path))
    assert os.path.isfile(input_filepath)
    assert os.path.isfile(output_filepath)


def test_save_2():

    input_filepath, output_filepath = remove_test_folder("function_multiple_attributes")
    sleep(5)
    print("execution", function_multiple_attributes("Álvaro", "Bueno"))

    assert os.path.isdir(ensure_path(test_folder_path))
    assert os.path.isfile(input_filepath)
    assert os.path.isfile(output_filepath)


def test_save_3():

    input_filepath, output_filepath = remove_test_folder("function_multiple_attributes")
    sleep(5)
    print("execution", function_multiple_attributes("Álvaro", "Bueno"))
    print("execution", function_multiple_attributes("Álvaro", "Bueno"))
    assert os.path.isdir(ensure_path(test_folder_path))
    assert os.path.isfile(input_filepath)
    assert os.path.isfile(output_filepath)
    data = read_jsonl(output_filepath)
    assert len(data) == 2
