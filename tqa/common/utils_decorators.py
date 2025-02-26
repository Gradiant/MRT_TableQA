import os
from time import sleep

from tqa.common.utils import ensure_path, get_str_date, measure, save_jsonl


def save(folder):
    folder_path = ensure_path(folder)
    if not os.path.isdir(folder_path):
        os.makedirs(folder_path, exist_ok=True)
        sleep(1)

    def save_input_and_output(funct):
        function_name = funct.__name__
        input_filepath = os.path.join(
            folder_path, "{}_input.jsonl".format(function_name)
        )
        output_filepath = os.path.join(
            folder_path, "{}_output.jsonl".format(function_name)
        )

        def executer(*args, **kargs):
            input = dict({"kargs": kargs}, **{"args": list(args)})
            result, time = measure(funct, *args, **kargs)
            output = {"time": time, "date": get_str_date(), "out": result}
            save_jsonl(input_filepath, [input], option="a") if os.path.isfile(
                input_filepath
            ) else save_jsonl(input_filepath, [input], option="w")
            save_jsonl(output_filepath, [output], option="a") if os.path.isfile(
                output_filepath
            ) else save_jsonl(output_filepath, [output], option="w")

            return result

        return executer

    return save_input_and_output
