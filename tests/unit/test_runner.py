from tqa.coder.domain.services.service import RunnerService
from tqa.coder.domain.services.coder_internal_functions import print_hola_mundo
from tqa.coder.domain.services import coder_internal_functions
import inspect

def test_runner_basic():
    runner = RunnerService()
    code = """def parse_dataframe() -> str:
                print('Hola Mundo desde test_runner_basic')
                return True """
    code = "import pandas as pd\n" + code + "\nresult = parse_dataframe()"

    result=runner.try_run(code,df=None)
    assert result

def test_runner_internal_function_directly():
    runner = RunnerService()
    code = """def parse_dataframe() -> str:
                print_hola_mundo()
                return True """
    code = "import pandas as pd\n" + code + "\nresult = parse_dataframe()"

    result = runner.try_run(code,df=None)
    assert result


