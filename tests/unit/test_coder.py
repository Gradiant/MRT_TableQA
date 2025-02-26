from tqa.coder.domain.services.service import CoderService
from tqa.common.domain.services.InferenceService import InferenceService


def test_template_format():
    service = CoderService()

    columns = ["edad", "nombre", "apellidos", "ciudad", "trabajo"]
    steps = [
        "Step 1: Filter the table to only include the 'name' and 'age' columns** \nI will select only the 'name' and 'age' columns from the original table, ignoring the 'car' and 'id' columns. This will give me a new table with only two columns: ['name', 'age'].",
        "Step 2: Sort the table by 'age' in ascending order** \nI will sort the filtered table by the 'age' column in ascending order. This will arrange the table in a way that the person with the lowest age is at the top, and the person with the highest age is at the bottom."
        "Step 3: Identify the last row of the sorted table** \nSince I sorted the table by 'age' in ascending order, the last row will represent the person with the highest age. This row will contain the name and age of the older person."
        "*Step 4: Extract the 'name' value from the last row**\nI will extract the 'name' value from the last row of the sorted table, which corresponds to the older person."
        "**Step 5: Return the extracted 'name' value as the answer** \nThe final answer to the question 'Who is the older person?' is the extracted 'name' value, which represents the name of the person with the highest age in the original table.",
    ]
    prompt = service.get_prompt(columns, steps)
    print(prompt)

    """ expected = f"You are an AI assistant tasked with generating pandas code. You will receive a series of steps describing how to manipulate a DataFrame to answer a question.
    The DataFrame has the following columns: {columns}.
    The steps to manipulate the data are: {"\n".join([str(i) + "." + " " + step for i, step in enumerate(steps, start=1)])}.
    Asume df is the name of the dataframe.
    Your task is to generate pandas code that executes these steps and returns the result as a Python string.
    Make sure you write only python code and nothing else.
    Make sure the code only returns a list with name 'result', no DataFrame or other types of objects.
    Make sure to not provide any examples on how to run the code.
    Make sure to try to work everything only on single function.
    In summary, complete the following function
    ```python
    def parse_dataframe(df: pd.DataFrame) -> str:
      ...
    ```
    """
    for column in prompt:
        assert column in prompt
    for step in steps:
        assert step in prompt


def test_inference():
    service = CoderService()
    inferer = InferenceService()

    columns = ["edad", "nombre", "apellidos", "ciudad", "trabajo"]
    steps = [
        "Step 1: Filter the table to only include the 'name' and 'age' columns** \nI will select only the 'name' and 'age' columns from the original table, ignoring the 'car' and 'id' columns. This will give me a new table with only two columns: ['name', 'age'].",
        "Step 2: Sort the table by 'age' in ascending order** \nI will sort the filtered table by the 'age' column in ascending order. This will arrange the table in a way that the person with the lowest age is at the top, and the person with the highest age is at the bottom."
        "Step 3: Identify the last row of the sorted table** \nSince I sorted the table by 'age' in ascending order, the last row will represent the person with the highest age. This row will contain the name and age of the older person."
        "*Step 4: Extract the 'name' value from the last row**\nI will extract the 'name' value from the last row of the sorted table, which corresponds to the older person."
        "**Step 5: Return the extracted 'name' value as the answer** \nThe final answer to the question 'Who is the older person?' is the extracted 'name' value, which represents the name of the person with the highest age in the original table.",
    ]
    prompt = service.get_prompt(columns, steps)
    llm_answer = inferer.inference("qwen_25", prompt)
    print(llm_answer)
    assert llm_answer


def test_checking():
    service = CoderService()

    codes = [
        (True, "import pandas as pd\ndef read_something():\n\treturn True"),
        (True, "def read_something():\n\treturn True\n# comentario\nread_something()"),
        (False, " import pandas as pd\ndef read_something():\n\treturn True"),
        (False, " hola"),
        (False, "Sure here is your code:\nimport something"),
    ]

    for result, code in codes:
        assert service.check_lsp(code) == result


def test_simple_correction():
    service = CoderService()

    text = "def function 'something'"
    expected = "def function(something)"

    corrected = service.correct_lsp(text)
    print(corrected)

    assert expected != corrected  # TODO 2to3


def test_correction_prompt():
    service = CoderService()

    code = "\ndef function('asdasd')\nreturn True"

    prompt = service.correction_prompt(code)
    # print(prompt)

    """ expected = f"You are an AI assintant tasked with helping other people Fix code. You will receive a code snippet that doesn't work syntactically and have the task to fix it.
    The code in question is the following: ```python {code}\n ```
    Do not change the name of the function, the name or type of the inputs nor the type of the outputs.
    Fix whathever semantic / syntactic problem the function has.
    Make sure you answer with only python code and nothing else.
    Do not provide example usage of the function.
    """

    assert code in prompt


def complex_correction():
    service = CoderService()
    inferer = InferenceService()

    code = """
    def function("asdasd")
    return True
    """
    prompt = service.correction_prompt(code)
    print(prompt)

    assert inferer.inference("qwen_25", prompt)


def answer_parser():

    elements = [
        (
            """Simulated LLM Output: You can check if a string is a palindrome (i.e., reads the same forward and backward) by comparing it to its reverse. Here's a Python function that does this:
```python
def is_palindrome(s):
    s = s.lower().replace(" ", "")
    return s == s[::-1]

print(is_palindrome("A man a plan a canal Panama"))  # Output: True
```

asdasdasdadad
""",
            """
def is_palindrome(s):
    s = s.lower().replace(" ", "")
    return s == s[::-1]
""",
        ),
        (
            """Simulated LLM Output: You can check if a string is a palindrome (i.e., reads the same forward and backward) by comparing it to its reverse. Here's a Python function that does this:
def is_palindrome(s):
    s = s.lower().replace(" ", "")
    return s == s[::-1]

print(is_palindrome("A man a plan a canal Panama"))  # Output: True
""",
            """
def is_palindrome(s):
    s = s.lower().replace(" ", "")
    return s == s[::-1]
""",
        ),
        (
            """Simulated LLM Output: You can check if a string is a palindrome (i.e., reads the same forward and backward) by comparing it to its reverse. Here's a Python function that does this:
```python
import pandas as pd

def is_palindrome(s):
    s = s.lower().replace(" ", "")
    return s == s[::-1]

print(is_palindrome("A man a plan a canal Panama"))  # Output: True
```

asdasdasdadad
""",
            """
import pandas as pd

def is_palindrome(s):
    s = s.lower().replace(" ", "")
    return s == s[::-1]
""",
        ),
        (
            """Simulated LLM Output: You can check if a string is a palindrome (i.e., reads the same forward and backward) by comparing it to its reverse. Here's a Python function that does this:
```python
def is_palindrome(s):
    s = s.lower().replace(" ", "")
    return s == s[::-1]

def other():
    return

print(is_palindrome("A man a plan a canal Panama"))  # Output: True
```

asdasdasdadad
""",
            """
def is_palindrome(s):
    s = s.lower().replace(" ", "")
    return s == s[::-1]

def other():
    return
""",
        ),
    ]

    service = CoderService()

    for llm, parsed in elements:
        assert parsed == service.parse_llm_answer(llm)
