import itertools
import json
import logging
import math
import os

import pandas as pd
import pytest
from datasets import load_dataset
from dotenv import load_dotenv
from pandas.api.types import is_numeric_dtype

from tqa.coder.domain.services.column_selector_service import ColumnSelectorService
from tqa.coder.usecases.column_selector_usecase import ColumnSelectorUseCase
from tqa.common.domain.services.InferenceService import InferenceService

from tqa.common.configuration.config import load_config
from tqa.common.configuration.logger import get_logger
from tqa.common.utils import ensure_path, read_json

load_dotenv()
logger = get_logger("tests")
config = load_config()


@pytest.fixture
def tables_descriptions():
    return read_json(ensure_path("tests/assets/table_result.json"))


def test_basic_selector_column():

    columns_descriptions = get_example_column_description()
    df = pd.DataFrame(
        {
            "edad": [10, 20, 30],
            "nombre": ["pedro", "paco", "pepe"],
            "apellidos": ["alonso", "fdez", "ruiz"],
            "ciudad": ["Barcelona", "Barcelona", "Madrid"],
            "trabajo": ["atleta", "profe", "conductor"],
        }
    )
    question = "Cuantas personas menores de 25 años viven en Barcelona?"
    usecase = ColumnSelectorUseCase(
        df, question, columns_descriptions, ColumnSelectorService(), InferenceService()
    )
    result = usecase.execute()
    used_columns = [
        col.get("name") for col in usecase.columns_descriptions.get("columns")
    ]
    print("Used columns:" + str(used_columns))
    print(result)


def test_filter_blacklist_columns():

    columns_descriptions = get_example_column_description()
    columns_descriptions["columns"][3]["name"] = "N_R__1"
    df = pd.DataFrame(
        {
            "edad": [10, 20, 30],
            "nombre": ["pedro", "paco", "pepe"],
            "apellidos": ["alonso", "fdez", "ruiz"],
            "N_R__1": ["Barcelona", "Barcelona", "Madrid"],
            "trabajo": ["atleta", "profe", "conductor"],
        }
    )
    question = "Cuantas personas menores de 25 años viven en Barcelona?"
    usecase = ColumnSelectorUseCase(
        df, question, columns_descriptions, ColumnSelectorService(), InferenceService()
    )
    result = usecase.execute()

    used_columns = [
        col.get("name") for col in usecase.columns_descriptions.get("columns")
    ]

    print("Used columns::" + str(used_columns))

    assert used_columns == ["edad"]


def test_filters():
    filtered = ColumnSelectorService().check_too_much_columns(columns_sample)
    assert len(filtered) < 40

def test_parser():
    text = "['Edad', 'Temperatura', 'Color']"
    parsed = ColumnSelectorService().parse_columnlist(text)
    print(parsed)
    assert parsed == ["Edad", "Temperatura", "Color"]


def test_parser_anomaly():
    text = "[name: Situación laboral recodificada]"
    parsed = ColumnSelectorService().parse_columnlist(text)
    print(parsed)
    assert parsed == ["Situación laboral recodificada"]

def test_parser_long():
    text = "[name: Dificultad de acceso al edificio, casa, urbanización, etc_, name: Viviendas en las que no hay nadie, name: Viviendas en las que se niegan a recibir ninguna explicación, name: Negativas de hombres a realizar la entrevista, name: Negativas de mujeres a realizar la entrevista]"
    parsed = ColumnSelectorService().parse_columnlist(text)
    print(parsed)
    assert parsed == ["Dificultad de acceso al edificio, casa, urbanización, etc_", "Viviendas en las que no hay nadie", "Viviendas en las que se niegan a recibir ninguna explicación", "Negativas de hombres a realizar la entrevista", "Negativas de mujeres a realizar la entrevista"]

def test_parser_quotes():
    text = "['Situación laboral '0' recodificada', 'Situación laboral '10' recodificada', 'ID']"
    parsed = ColumnSelectorService().parse_columnlist(text)
    print(parsed)
    assert parsed == ["Situación laboral '0' recodificada", "Situación laboral '10' recodificada", "ID"]
                     

def get_example_column_description():
    return {
        "table": {"len": 45},
        "columns": [
            {
                "name": "edad",
                "type": "uint16",
                "min": 2,
                "max": 24,
                "description": {
                    "description": "Age of the person.",
                    "simple_name": "edad",
                },
            },
            {
                "name": "nombre",
                "type": "str",
                "description": {
                    "description": "name of the person.",
                    "simple_name": "nombre",
                },
            },
            {
                "name": "apellidos",
                "type": "str",
                "description": {
                    "description": "surnames of the person.",
                    "simple_name": "apellidos",
                },
            },
            {
                "name": "ciudad",
                "type": "category",
                "unique": 2,
                "description": {
                    "description": "city where he/she lives.",
                    "simple_name": "ciudad",
                },
                "freq_values": ["Madrid", "Barcelona"],
            },
            {
                "name": "trabajo",
                "type": "str",
                "description": {
                    "description": "job the person has.",
                    "simple_name": "work",
                },
            },
        ],
        "binary_subsets": [],
    }

columns_sample = [
        "CUEST_ID",
        "Estado",
        "La mala calidad de la enseñanza",
        "El desinterés de los políticos por los y las jóvenes",
        "Ningún problema",
        "Ns_Nc",
        "El paro_0",
        "La inseguridad y precariedad de los empleos_0",
        "Salarios bajos_0",
        "Dificultad para alquilar una casa_0",
        "Dificultad para comprar una casa_0",
        "La falta de ayudas públicas y becas_0",
        "La dificultad para emanciparse_0",
        "La falta de confianza en los_las jóvenes_0",
        "La falta de formación profesional_0",
        "La violencia de género_0",
        "La mala calidad de la enseñanza_0",
        "El desinterés de los políticos por los y las jóvenes_0",
        "Ningún problema_0",
        "Ns_Nc_0",
        "Y, sobre estos problemas mencionados antes y que te afectan más, ¿crees que, en general, mejorarán, empeorarán o seguirá",
        "¿Crees que dentro de un año la situación del país será mejor, igual o peor que ahora?",
        "Tener que depender económicamente de mi familia",
        "Tener que trabajar en lo que sea",
        "Estar en paro o con dificultad para encontrar trabajo",
        "Bajada salario o bajada de tu poder adquisitivo",
        "Recortar el gasto en hobbies, ocio y tiempo libre",
        "Tu trabajo o los estudios",
        "Tus relaciones familiares",
        "Tus relaciones de amistad",
        "Tus relaciones interpersonales (vecinos_as, compañeros_as, colegas, etc_)",
        "Tu situación económica",
        "Tu salud física o mental",
        "Tu interacción en las redes sociales",
        "Con tu familia",
        "Con tus estudios y_o trabajo",
        "Con tus amigos",
        "Con el tiempo libre de que dispones",
        "Con tus relaciones sexuales",
        "Con tu situación económica",
        "Con tus perspectivas de futuro",
        "Considerando todos los aspectos de tu vida, en general, ¿cómo valorarías tu grado de felicidad en el momento actual? Uti",
        "¿En qué medida se interesan otras personas (familiares, amigos_as, personas cercanas…) por lo que te pasa?",
        "¿En qué medida te resultaría fácil obtener ayuda de amigos_as en caso de necesidad? Ayuda para que te apoye, te aconseje",
        "Y, ¿te resultaría fácil obtener ayuda de tus familiares?",
        "Durante los últimos 12 meses, ¿en qué medida has sentido soledad o aislamiento social?",
        "Puedo ahorrar parte de mis ingresos mensuales (si tienes ingresos propios), o que en mi hogar se pueda ahorrar parte de",
        "Tener que depender económicamente de mi familia_0",
        "Tener que trabajar en lo que sea_0",
        "Estar en paro o con dificultad para encontrar trabajo_0",
        "Bajada salario o bajada de tu poder adquisitivo_0",
        "Recortar el gasto en hobbies, ocio y tiempo libre_0",
        "Recortar el gasto en cosas básicas (alimentación, etc_)_0",
        "Estar en peor estado anímico, ansiedad_0",
        "Puedo permitirme ir de vacaciones al menos una semana al año_0",
        "Puedo ahorrar parte de mis ingresos mensuales (si tienes ingresos propios), o que en mi hogar se pueda ahorrar parte de_0",
        "Estado de salud",
        "Problemas de salud mental",
        "Problemas de salud mental_0",
        "Sentimiento de soledad",
        "Sentimiento de soledad_0",
        "Ideación suicida",
        "Ideación suicida_0",
        "Ideación suicida_1",
        "Frecuencia de problemas P41",
        "Frecuencia de problemas P42",
        "Frecuencia de problemas P43",
        "Frecuencia de problemas P44",
        "Frecuencia de problemas P45",
        "Frecuencia de problemas P46",
        "Frecuencia de problemas P47",
        "Frecuencia de problemas P48",
        "Frecuencia de problemas P49",
        "Frecuencia de problemas P50",
    ]
    