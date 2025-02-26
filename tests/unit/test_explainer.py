import json

from tests import utils
from tqa.coder.domain.services.service import ExplainerService
from tqa.common.domain.services.InferenceService import InferenceService
from tqa.common.domain.entities.ExeContext import exeContext

def test_template_basic_format():
    service = ExplainerService()
    prompt = service.get_prompt(
        "¿Cuál es la edad máxima?",
        ["edad", "nombre", "apellidos", "ciudad", "trabajo"],
        column_descriptions=None,
        max_steps=5,
    )
    assert (
        prompt
        == "You are an AI assistant tasked with solving questions using a table.\nYou have the following columns available: ['edad', 'nombre', 'apellidos', 'ciudad', 'trabajo']\nYour task is to break down the steps required to answer the following question: ¿Cuál es la edad máxima?\nPlease list a maximum of 5 steps required to manipulate the data to answer the question, but if you can use less, it's better: keep it simple.\nThe last step should induce to give a answer type according to the type the question implicitly requires (for example a number, boolean (True/False), a string, a list, etc.)\nBe very specific and clear in describing how each step manipulates the table. Separate the instructions in sentences separated by a \".\" symbol. Don't use enumerations, don't enumerate the steps, don't write a header or introduction, don't give code examples. Use complete column names to refer to the columns. Just write down the instructions. Pay attention as many columns have missing data or data that must be casted or preprocessed to avoid throwing exceptions.\nInstructions:\n"
    )


def test_template_format_with_columdesc():
    column_descriptions = get_example_column_description()
    service = ExplainerService()
    prompt = service.get_prompt(
        "¿Cuál es la edad máxima?",
        ["edad", "nombre", "apellidos", "ciudad", "trabajo"],
        column_descriptions,
        5,
        max_categories_for_describe=4,
        table_name="Empleados",
    )
    assert (
        prompt
        == "You are an AI assistant tasked with solving questions using a table.\nThe name of the table is: Empleados.\nYou have the following columns available: \n- \"edad\": Age of the person. Type: uint16. The range of values goes from 2 (min) to 24 (max).\n- \"nombre\": name of the person. Type: str.\n- \"apellidos\": surnames of the person. Type: str.\n- \"ciudad\": city where he/she lives. Type: category. Options are: Madrid, Barcelona.\n- \"trabajo\": job the person has. Type: str.\nYour task is to break down the steps required to answer the following question: ¿Cuál es la edad máxima?\nPlease list a maximum of 5 steps required to manipulate the data to answer the question, but if you can use less, it's better: keep it simple.\nThe last step should induce to give a answer type according to the type the question implicitly requires (for example a number, boolean (True/False), a string, a list, etc.)\nBe very specific and clear in describing how each step manipulates the table. Separate the instructions in sentences separated by a \".\" symbol. Don't use enumerations, don't enumerate the steps, don't write a header or introduction, don't give code examples. Use complete column names to refer to the columns. Just write down the instructions. Pay attention as many columns have missing data or data that must be casted or preprocessed to avoid throwing exceptions.\nInstructions:\n"
    )

def test_template_correct_instructions():
    column_descriptions = get_example_column_description()
    service = ExplainerService()
    instructions = [
        "Filter the rows where Edad is bigger than 20",
        "Select the maximum value of height",
    ]
    prompt = service.get_prompt_correction(
        instructions,
        "¿Cuál es la edad máxima?",
        ["edad", "nombre", "apellidos", "ciudad", "trabajo"],
        column_descriptions,
        max_categories_for_describe=4,
        table_name="Empleados",
    )
    print(prompt)


def test_inference():
    service = ExplainerService()
    inferer = InferenceService()

    prompt = service.get_prompt(
        "¿Cuál es la edad máxima?",
        ["edad", "nombre", "apellidos", "ciudad", "trabajo"],
        max_steps=5,
    )
    llm_answer = inferer.inference("qwen_25", prompt)
    print(llm_answer)


# def test_llama1b_inference():
#     from huggingface_hub import login
#     login()
#     # Solicitar acceso aqui (me lo aceptaron en solo unos minutos)
#     inferer = InferenceService(use_model="llama_1b")
#     prompt = "Say hello: "  # for test a very short inference
#     llm_answer = inferer.inference(prompt)
#     print(llm_answer)


def test_parse_instructions():
    llm_answer_example = "Filter the rows where Edad is bigger than 20. Select the maximum value of height."
    service = ExplainerService()
    instructions = service.parse_llm_answer(llm_answer_example)
    assert instructions == [
        "Filter the rows where Edad is bigger than 20",
        "Select the maximum value of height",
    ]


def test_split_parser():
    llm_answer_example = 'Check the total number of unique names by using the nunique() function on the "Name" column. .\nCompare the result of the nunique() function with the total number of rows in the DataFrame using the shape attribute.\nIf the two numbers are equal, every passenger\'s name is unique; otherwise, it is not. Induce a boolean value True for unique names, False for non-unique names.'
    service = ExplainerService()
    instructions = service.parse_llm_answer(llm_answer_example)
    print(instructions)

def test_with_dataset():
    # Forbes
    question = "Is the person with the highest net worth self-made?"
    id_table = 0
    template_test_with_dataset(question, id_table, table_name="001_Forbes")


def test_with_dataset_2():
    # Titanic
    question = "Is every passenger's name unique?"
    id_table = 1
    template_test_with_dataset(question, id_table, table_name="002_Titanic")


def test_with_dataset_3():
    # Titanic
    question = "Were there any female passengers in the 3rd class who survived?"
    id_table = 1
    template_test_with_dataset(question, id_table, table_name="002_Titanic")


def test_with_dataset_4():
    # Taxis
    question = "On which date did the first recorded trip occur?"
    id_table = 3
    template_test_with_dataset(question, id_table, table_name="004_Taxi")

def test_with_dataset_2_steps(): #check number of steps
    # Titanic
    question = "Were there any passengers who paid a fare of more than $500?"
    id_table = 1
    template_test_with_dataset(question, id_table, table_name="002_Titanic")

def test_with_dataset_average_Age(): #check number of steps
    # Love 
    question = "Is the average age of the respondents above 30?"
    id_table = 2
    template_test_with_dataset(question, id_table, table_name="003_Love")

def test_with_dataset_verify_identity(): #check number of steps
    # LOndon
    question = "Do all hosts verify their identity?"
    id_table = 5
    template_test_with_dataset(question, id_table, table_name="006_London")


################## TRAIN ############################################
"""
def test_correct_dataset_1():
    # Titanic
    question = "List the bottom 2 countries with the least number of billionaires."
    id_table = 0
    template_test_with_dataset_correction(question, id_table, table_name="001_Forbes")



def test_correct_dataset_3():
    # Titanic
    question = "Were there any female passengers in the 3rd class who survived?"
    id_table = 1
    template_test_with_dataset_correction(question, id_table, table_name="002_Titanic")


def test_correct_dataset_4():
    # Taxis
    question = "On which date did the first recorded trip occur?"
    id_table = 3
    template_test_with_dataset_correction(question, id_table, table_name="004_Taxi")

def test_correct_dataset_8():
    # Taxis
    question = "Which are the top 3 states with the most tornado-related injuries?"
    id_table = 7
    template_test_with_dataset_correction(question, id_table, table_name="008_Tornados")

def test_correct_dataset_5():
    # Taxis
    question = "Which neighbourhood has the most listings?"
    id_table = 5
    template_test_with_dataset_correction(question, id_table, table_name="006_London")



def test_correct_dataset_12():
    # Taxis
    question = "What is the status of the roller coaster with the highest G-force?"
    id_table = 12
    template_test_with_dataset_correction(question, id_table, table_name="013_Roller")

def test_correct_dataset_12_2():
    # Taxis
    question = "Did the oldest roller coaster in the dataset still operate?"
    id_table = 12
    template_test_with_dataset_correction(question, id_table, table_name="013_Roller")
"""

############ DEV
"""
def test_correct_dataset_dev_52():
    # 052_Professional
    question = "Name the bottom 2 professions in terms of Self-enhancement."
    question = "What are the highest 5 levels of Extraversion?"
    id_table = 52
    id_table -= 50
    template_test_with_dataset_correction(question, id_table, table_name="052_Professional")

def test_correct_dataset_dev_56():
    # 052_Professional
    question = "What is the average amount of total fat (in grams) across all foods?"
    id_table = 56
    template_test_with_dataset_correction(question, id_table -50, table_name="056_Emoji", id_columntable=id_table)


def test_correct_dataset_dev_54():
    # 052_Professional
    question = "What is the name of the user who is most often named in the dataset?"
    id_table = 54
    template_test_with_dataset_correction(question, id_table -50, table_name="054_Joe", id_columntable=id_table)

def test_correct_dataset_dev_55():
    # 052_Professional
    question = "What are the top 4 loan durations in the dataset?"
    question = "What are the top 3 jobs of borrowers with the highest loan amount?"
    id_table = 55
    template_test_with_dataset_correction(question, id_table -50, table_name="055_German", id_columntable=id_table)


def test_correct_dataset_dev_63():
    # 052_Professional
    question = "What are the bottom 2 entities in terms of page rank norm?"
    id_table = 63
    template_test_with_dataset_correction(question, id_table -50, table_name="063_Influencers", id_columntable=id_table)

def test_correct_dataset_dev_57():
    # 052_Professional
    question = "Identify the top 3 most common reasons for voting among respondents."
    id_table = 57
    template_test_with_dataset_correction(question, id_table -50, table_name="057_Spain", id_columntable=id_table)

def test_correct_dataset_dev_64():
    # 052_Professional
    question = "What is the class type of the animals with the most legs?"
    question = "Do all animals breathe?"
    id_table = 64
    template_test_with_dataset_correction(question, id_table -50, table_name="064_Clustering", id_columntable=id_table)

def test_correct_dataset_dev_58():
    # 052_Professional
    question = "Enumerate the 2 most common professions among the respondents. If two or more have the same number sort them out by alphabetical order."
    id_table = 58
    template_test_with_dataset_correction(question, id_table -50, table_name="058_US", id_columntable=id_table)

def test_correct_dataset_dev_50():
    # 052_Professional
    question = "Does the author with the longest name post mainly original content?"
    id_table = 50
    template_test_with_dataset_correction(question, id_table -50, table_name="050_ING", id_columntable=id_table)

"""



########################################################################3

def template_test_with_dataset(question, id_table, table_name):

    execution = exeContext().get_or_new(
        question=question, table_name=table_name
    )
    exeContext().set_current(exe_id=execution.exe_id)


    df = utils.get_table_from_dataset(id_table)
    service = ExplainerService()
    columns_description = get_column_description_from_table(id_table)
    prompt = service.get_prompt(question, df.columns, columns_description, 3)
    inferer = InferenceService()


    llm_answer = inferer.inference("meta", prompt)
    print("\n" + table_name)
    print(question)
    print(llm_answer+ "\n")
    instructions = service.parse_llm_answer(llm_answer)
    print(instructions)
    print("\nSize instructions: " + str(len(instructions)))
    print("\n----------------------------------------------\n")


def template_test_with_dataset_correction(question, id_table, table_name, id_columntable=None):

    if not id_columntable:
        id_columntable = id_table

    execution = exeContext().get_or_new(
        question=question, table_name=table_name
    )
    exeContext().set_current(exe_id=execution.exe_id)

    df = utils.get_table_from_dataset(id_table)
    service = ExplainerService()
    columns_description = get_column_description_from_table(id_columntable, table_name=table_name)
    prompt = service.get_prompt(question, df.columns, columns_description, 3)
    inferer = InferenceService()

    llm_answer = inferer.inference("meta", prompt)
    print("########################################################################\n" + table_name)
    print(question)
    print("  ##  LLM ANSWER:\n")# + llm_answer+ "\n")
    instructions = service.parse_llm_answer(llm_answer)
    for ins in instructions:
        print(ins)
    print("\nSize instructions: " + str(len(instructions)))

    instructions = service._correct_column_names(
        instructions, df.columns
    )
    
    if service.get("correct_prompt"):
        print("\n ## Correcting prompt")
            
        prompt_correction = service.get_prompt_correction(
            instructions,
            question,
            df.columns,
            columns_description,
            max_categories_for_describe=7,
            table_name=table_name,
        )
        #print("-------------")
        #print(prompt_correction)
        #print("-------------")

        llm_answer_corrected = inferer.inference("meta", prompt_correction)
        instructions_corrected =  service.parse_llm_answer_corrected(llm_answer_corrected, instructions)
        print("Corrected result: ")
        for ins in instructions_corrected:
            print(str(ins))
        #print("instructions_corrected: " + str(instructions_corrected))
    else:
        print("Not correcting prompt")
    print("\n----------------------------------------------\n")



def get_column_description_from_table(id_table, table_name=None):

    path_to_descriptions = "tests/assets/table_result.json"
    with open(path_to_descriptions, "r") as file:
        data = json.load(file)
    
    if table_name:
        for table in data:
            if table == table_name:
                return data[table]
    
    columns = data[list(data.keys())[id_table]]  # .get("columns")
    return columns


def get_example_column_description():
    return {
        "table": {"len": 45},
        "columns": [
            {
                "name": "edad",
                "type": "uint16",
                "min": 2,
                "max": 24,
                "description": {"description": "Age of the person."},
            },
            {
                "name": "nombre",
                "type": "str",
                "description": {"description": "name of the person."},
            },
            {
                "name": "apellidos",
                "type": "str",
                "description": {"description": "surnames of the person."},
            },
            {
                "name": "ciudad",
                "type": "category",
                "unique": 2,
                "description": {"description": "city where he/she lives."},
                "freq_values": ["Madrid", "Barcelona"],
            },
            {
                "name": "trabajo",
                "type": "str",
                "description": {"description": "job the person has."},
            },
        ],
        "binary_subsets": [],
    }

