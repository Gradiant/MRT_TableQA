import re

from tqa.coder.domain.services.service import InterpreterService
from tqa.coder.usecases.interpreter_usecase import InterpretUseCase
from tqa.common.domain.entities.ExeContext import exeContext
from tqa.common.domain.services.InferenceService import InferenceService
from tqa.common.domain.services.Reporter import Reporter
from tqa.common.utils import ensure_path
import pandas as pd
def test_interpreter_raw_boolean():
    question = "Are all reviews_per_month values greater than 5?"
    result = "['There are reviews_per_month values greater than 5']"
    prompt = "For the question: {} we have anwsered this: {}. Do you consider that is a good response? Response in a markdown with True if it is or False if it is not".format(
        question, result
    )
    exeContext().new(question=question, table_name="test", answer="result")
    service = InferenceService()
    llm_response = service.inference("default", prompt)
    print("LLM_response", llm_response)
    response = re.findall(r"```markdown(.*)```", llm_response, re.DOTALL)[0]
    print("FINAL RESPONSE", eval(response.strip("\n").strip(" ")))


def test_interpreter_change_out_boolean():
    question = "Are there any employees with more than 7 projects?"
    result = "No rows found with 'Number of Projects' greater than 7."
    prompt = "For the question: {} we have anwsered this: {}. The answer should be as a boolean (True or False), list (with results in brackets) or number (int). Response in a markdown.".format(
        question, result
    )
    exeContext().new(question=question, table_name="test", answer="result")
    service = InferenceService()
    llm_response = service.inference("default", prompt)
    print("LLM_response", llm_response)
    response = re.findall(r"```markdown(.*)```", llm_response, re.DOTALL)[0]
    print("FINAL RESPONSE", eval(response.strip("\n").strip(" ")))


def test_interpreter_change_out_number():
    question = "How many unique URLs are in the dataset?"
    result = "[62]"
    prompt = "For the question: {} we have anwsered this: {}. The answer should be as a boolean (True or False), list (with results in brackets) or number (int). Response in a markdown.".format(
        question, result
    )
    exeContext().new(question=question, table_name="test", answer="result")
    service = InferenceService()
    llm_response = service.inference("default", prompt)
    print("LLM_response", llm_response)
    response = re.findall(r"```markdown(.*)```", llm_response, re.DOTALL)[0]
    final_response = eval(response.strip("\n").strip(" "))
    print("FINAL RESPONSE", final_response)
    assert final_response == 62


def test_interpreter_change_out_int_from_str():
    question = "What is the maximum number of pregnancies recorded in the dataset?"
    result = "The maximum number of pregnancies in the dataset is: 17"
    prompt = "For the question: {} we have anwsered this: {}. The answer should be as a boolean (True or False), list (with results in brackets) or number (int). Response in a markdown with only the corected answer".format(
        question, result
    )
    exeContext().new(question=question, table_name="test", answer="result")
    service = InferenceService()
    llm_response = service.inference("default", prompt)
    print("LLM_response", llm_response)
    response = re.findall(r"```markdown(.*)```", llm_response, re.DOTALL)[0]
    final_response = eval(response.strip("\n").strip(" "))
    print("FINAL RESPONSE", final_response)
    assert final_response == 17


def test_interpreter_bad_output_1():
    question = "List the top 5 foods with the most calories."
    result = "['bacon', 'peanuts', 'chocolate bar', 'popcorn', 'cookie']"

    interperter = InterpreterService()
    inferencer = InferenceService()
    exeContext().new(question, "test", result)
    uc = InterpretUseCase(question, result, interperter, inferencer)
    uc.execute()
    print(uc._result)

    
def test_interpreter_bad_output_2():
    question = "Are there any Pokémon with a total stat greater than 700?"
    result = "True"

    interperter = InterpreterService()
    inferencer = InferenceService()
    exeContext().new(question, "test", result)
    uc = InterpretUseCase(question, result, interperter, inferencer)
    uc.execute()
    print(uc._result)

def test_interpreter_service():
    question = "What is the maximum number of pregnancies recorded in the dataset?"
    result = "The maximum number of pregnancies in the dataset is: 17"

    interpreter = InterpreterService()
    prompt = interpreter.get_prompt(question, result)

    exeContext().new(question=question, table_name="test", answer="result")
    service = InferenceService()
    llm_response = service.inference("default", prompt)

    final_response = interpreter.parse(llm_response)
    print("FINAL RESPONSE", final_response)
    assert final_response == 17


def test_interpreter_use_case():
    question = "What is the maximum number of pregnancies recorded in the dataset?"
    result = "The maximum number of pregnancies in the dataset is: 17"

    interperter = InterpreterService()
    inferencer = InferenceService()
    exeContext().new(question, "test", result)
    uc = InterpretUseCase(question, result, interperter, inferencer)
    uc.execute()
    assert uc._result == 17



            