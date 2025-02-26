from tqa.coder.controllers.controller import CoderController
from tqa.common.domain.entities.Dataset import Dataset


def test_explain():
    controller = CoderController()
    steps = 5
    result = controller.explain(
        "Who is the older person?",
        [
            entry.get("name")
            for entry in get_example_column_description().get("columns")
        ],
        get_example_column_description(),
        steps,
    )
    print(result)
    # assert result
    # for i in range(1, steps + 1):
    #     assert str(i) in result


def get_example_column_description():
    return {
        "columns": [
            {
                "name": "rank",
                "type": "uint16",
                "missing_values": 0,
                "unique": 228,
                "flag_binary": False,
                "mean": 1302.91904047976,
                "std": 747.8077823761639,
                "freq_values": None,
                "description": {
                    "name": "rank",
                    "description": "The rank of the individual based on their net worth or other criteria.",
                },
            },
            {
                "name": "personName",
                "type": "category",
                "missing_values": 0,
                "unique": 2666,
                "flag_binary": False,
                "mean": 0.0,
                "std": 0.0,
                "freq_values": None,
                "description": {
                    "name": "personName",
                    "description": "The full name of the individual being described.",
                },
            },
            {
                "name": "age",
                "type": "float64",
                "missing_values": 86,
                "unique": 77,
                "flag_binary": False,
                "mean": 64.21068938807126,
                "std": 13.401258058138897,
                "freq_values": None,
                "description": {
                    "name": "age",
                    "description": "The current age of the individual.",
                },
            },
            {
                "name": "finalWorth",
                "type": "uint32",
                "missing_values": 0,
                "unique": 228,
                "flag_binary": False,
                "mean": 4762.350074962519,
                "std": 10540.482258469303,
                "freq_values": None,
                "description": {
                    "name": "finalWorth",
                    "description": "The estimated net worth of the individual, typically expressed in thousands or millions.",
                },
            },
            {
                "name": "category",
                "type": "category",
                "missing_values": 0,
                "unique": 18,
                "flag_binary": False,
                "mean": 0.0,
                "std": 0.0,
                "freq_values": [
                    "Finance & Investments",
                    "Technology",
                    "Manufacturing",
                    "Fashion & Retail",
                    "Healthcare",
                ],
                "description": {
                    "name": "category",
                    "description": "The sector or industry in which the individual has made their fortune, such as Technology, Automotive, or Finance.",
                },
            },
            {
                "name": "source",
                "type": "category",
                "missing_values": 0,
                "unique": 914,
                "flag_binary": False,
                "mean": 0.0,
                "std": 0.0,
                "freq_values": [
                    "real estate",
                    "investments",
                    "pharmaceuticals",
                    "diversified",
                    "software",
                ],
                "description": {
                    "name": "source",
                    "description": "The primary company or business through which the individual gained their wealth.",
                },
            },
            {
                "name": "country",
                "type": "category",
                "missing_values": 13,
                "unique": 74,
                "flag_binary": False,
                "mean": 0.0,
                "std": 0.0,
                "freq_values": [
                    "United States",
                    "China",
                    "India",
                    "Germany",
                    "United Kingdom",
                ],
                "description": {
                    "name": "country",
                    "description": "The country in which the individual resides or is based.",
                },
            },
            {
                "name": "state",
                "type": "category",
                "missing_values": 1920,
                "unique": 43,
                "flag_binary": False,
                "mean": 0.0,
                "std": 0.0,
                "freq_values": [
                    "California",
                    "New York",
                    "Florida",
                    "Texas",
                    "Illinois",
                ],
                "description": {
                    "name": "state",
                    "description": "The state within the country where the individual lives or operates.",
                },
            },
            {
                "name": "city",
                "type": "category",
                "missing_values": 44,
                "unique": 750,
                "flag_binary": False,
                "mean": 0.0,
                "std": 0.0,
                "freq_values": [
                    "New York",
                    "Beijing",
                    "Hong Kong",
                    "London",
                    "Shanghai",
                ],
                "description": {
                    "name": "city",
                    "description": "The city where the individual resides or is primarily associated with.",
                },
            },
            {
                "name": "organization",
                "type": "category",
                "missing_values": 2316,
                "unique": 317,
                "flag_binary": False,
                "mean": 0.0,
                "std": 0.0,
                "freq_values": [
                    "Meta Platforms",
                    "Gap",
                    "Bill & Melinda Gates Foundation",
                    "Berkshire Hathaway",
                    "Alphabet",
                ],
                "description": {
                    "name": "organization",
                    "description": "The name of the organization or company that the individual is associated with, such as a business they founded or lead.",
                },
            },
            {
                "name": "selfMade",
                "type": "bool",
                "missing_values": 0,
                "unique": 2,
                "flag_binary": True,
                "mean": 0.7087706146926537,
                "std": 0.4544141572704145,
                "freq_values": None,
                "description": {
                    "name": "selfMade",
                    "description": "A boolean indicating whether the individual is self-made (True) or inherited their wealth (False).",
                },
            },
            {
                "name": "gender",
                "type": "category",
                "missing_values": 16,
                "unique": 3,
                "flag_binary": False,
                "mean": 0.0,
                "std": 0.0,
                "freq_values": ["M", "F"],
                "description": {
                    "name": "gender",
                    "description": "The gender of the individual, typically indicated as M for male and F for female.",
                },
            },
            {
                "name": "birthDate",
                "type": "datetime64[us, UTC]",
                "missing_values": 99,
                "unique": 2045,
                "flag_binary": False,
                "mean": 0.0,
                "std": 0.0,
                "freq_values": None,
                "description": {
                    "name": "birthDate",
                    "description": "The birth date of the individual, typically in a standard date format.",
                },
            },
            {
                "name": "title",
                "type": "category",
                "missing_values": 2267,
                "unique": 95,
                "flag_binary": False,
                "mean": 0.0,
                "std": 0.0,
                "freq_values": [
                    "Entrepreneur",
                    "Investor",
                    "Founder",
                    "CEO",
                    "Chairman",
                ],
                "description": {
                    "name": "title",
                    "description": "The professional title or position held by the individual within their organization.",
                },
            },
            {
                "name": "philanthropyScore",
                "type": "float64",
                "missing_values": 2272,
                "unique": 6,
                "flag_binary": False,
                "mean": 1.856060606060606,
                "std": 0.9714864697331448,
                "freq_values": None,
                "description": {
                    "name": "philanthropyScore",
                    "description": "A score reflecting the individual's philanthropic efforts or contributions to charitable causes.",
                },
            },
            {
                "name": "bio",
                "type": "object",
                "missing_values": 0,
                "unique": 2668,
                "flag_binary": False,
                "mean": 0.0,
                "std": 0.0,
                "freq_values": None,
                "description": {
                    "name": "bio",
                    "description": "A brief biography or summary of the individual's achievements and contributions.",
                },
            },
            {
                "name": "about",
                "type": "object",
                "missing_values": 1106,
                "unique": 1549,
                "flag_binary": False,
                "mean": 0.0,
                "std": 0.0,
                "freq_values": None,
                "description": {
                    "name": "about",
                    "description": "Additional information or personal anecdotes about the individual.",
                },
            },
        ]
    }


def test_coder():
    controller = CoderController()

    columns = ["edad", "nombre", "apellidos", "ciudad", "trabajo"]
    steps = [
        "Step 1: Filter the table to only include the 'name' and 'age' columns** \nI will select only the 'name' and 'age' columns from the original table, ignoring the 'car' and 'id' columns. This will give me a new table with only two columns: ['name', 'age'].",
        "Step 2: Sort the table by 'age' in ascending order** \nI will sort the filtered table by the 'age' column in ascending order. This will arrange the table in a way that the person with the lowest age is at the top, and the person with the highest age is at the bottom."
        "Step 3: Identify the last row of the sorted table** \nSince I sorted the table by 'age' in ascending order, the last row will represent the person with the highest age. This row will contain the name and age of the older person."
        "*Step 4: Extract the 'name' value from the last row**\nI will extract the 'name' value from the last row of the sorted table, which corresponds to the older person."
        "**Step 5: Return the extracted 'name' value as the answer** \nThe final answer to the question 'Who is the older person?' is the extracted 'name' value, which represents the name of the person with the highest age in the original table.",
    ]

    result = controller.code(columns, steps)
    print(result)
    assert result


def test_process_table():
    controller = CoderController()

    dataset_service = Dataset()
    table_name = "007_Fifa"

    table_set = dataset_service.get_data(name=table_name)
    dataset_name = table_set["table_name"]
    question = table_set["questions"][0].get("question")
    answers = table_set["questions"][0].get("answer")
    df = dataset_service.get_tabular_df(dataset_name)
    print(dataset_name)
    print(question)
    print(answers)
    print(len(df))
    print(df.columns)
    result = controller.process_table(question, df, table_name=table_name)
    print("Result", result)
