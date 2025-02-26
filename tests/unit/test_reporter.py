import os

from tqa.common.domain.entities.ExeContext import exeContext
from tqa.common.domain.services.Reporter import Reporter
from tqa.common.errors.application_exception import ContextException
from tqa.common.utils import read_jsonl


def test_init_reporter():
    reporter = Reporter()
    assert reporter.get("report_name")
    assert reporter.get("trace_folder_name")
    assert reporter.get("trace_llm_folder_name")
    assert reporter.get("trace_filename")


def test_report_llm():
    reporter = Reporter()
    out_file = os.path.join(reporter.trace_llm_path, "{}.jsonl".format("test"))

    if os.path.isfile(out_file):
        os.remove(out_file)

    report = reporter.report_llm_out("test", "table_name", "question", "answer_llmm")

    assert os.path.isfile(out_file), "Module test not created"
    data = read_jsonl(out_file)
    assert report in data, "Test report is not in report file content"


def test_report_llm_with_kargs():
    reporter = Reporter()
    out_file = os.path.join(reporter.trace_llm_path, "{}.jsonl".format("test"))

    if os.path.isfile(out_file):
        os.remove(out_file)

    report = reporter.report_llm_out(
        "test", "table_name", "question", "answer_llmm", new_key="new_key"
    )

    assert os.path.isfile(out_file), "Module test not created"
    data = read_jsonl(out_file)
    assert report in data, "Test report is not in report file content"
    assert "new_key" in report


def test_report_trace():
    reporter = Reporter()
    out_file = reporter.trace_file_path

    if os.path.isfile(out_file):
        os.remove(out_file)

    exeContext("question", "table_name", "answer")
    report = reporter.report_trace("test")

    assert os.path.isfile(out_file), "Module test not created"
    data = read_jsonl(out_file)
    assert report in data, "Test report is not in report file content"
