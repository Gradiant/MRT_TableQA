from tqa.coder.domain.services.service import FormatterSemevalService
from tqa.common.configuration.config import load_config
from tqa.common.domain.entities.ExeContext import exeContext


def test_interpreter_format_semeval_integers_eq5():
    formater = FormatterSemevalService()
    answer = [340, 340, 340, 340, 340]
    pred = formater.format(answer)
    print(pred)


def test_interpreter_format_semeval_integers():
    formater = FormatterSemevalService()
    answer = [3169, 2843]
    pred = formater.format(answer)

    print(pred)


def test_interpreter_format_semeval_integers_as_string():
    formater = FormatterSemevalService()
    answer = ["1", "2", "1"]
    pred = formater.format(answer)

    print(pred)


def test_interpreter_format_semeval():
    formater = FormatterSemevalService()
    answer = [
        1.0,
        0.6029751067034804,
        0.5666707687637932,
        0.5202348027491394,
        0.5110606617858531,
        0.5081183103684572,
    ]

    pred = formater.format(answer)

    print(pred)
