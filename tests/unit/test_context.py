from tqa.common.domain.entities.ExeContext import exeContext
from tqa.common.errors.application_exception import ContextException


def test_different_executions():
    exe1 = exeContext().new(answer="1", question="1", table_name="1")
    exe2 = exeContext().new(answer="2", question="2", table_name="2")
    assert exe1 != exe2


def test_same_executions():
    exe1 = exeContext().new(answer="1", question="1", table_name="1")
    exe2 = exeContext().get(answer="1", question="1", table_name="1")
    assert exe1 == exe2


def test_get_or_new_executions():
    exe1 = exeContext().new(answer="1", question="1", table_name="1")
    exe2 = exeContext().get_or_new(answer="3", question="1", table_name="1")
    assert exe1 != exe2


def test_add_new_parameter():
    exe1 = exeContext().new(answer="1", question="1", table_name="1")
    exe2 = exeContext().add(use_model="run")

    assert exe1 == exe2, "exe1 and exe2 are not the same"
    assert hasattr(exe1, "use_model"), "No attribtue use_model in exe1"
    assert exe1.use_model == "run", "use_model has not been updated"


def test_exception():
    try:
        a = ContextException("Mensaje")
        raise a
    except ContextException as e:
        assert e.get_error_description() == "Mensaje"


def test_context_empty_init():
    context = exeContext()
    assert context
    assert context.exe_id != 0


def test_context():
    context = exeContext().new(question="question", table_name="table")
    context2 = exeContext().current_execution

    assert context == context2, "Singleton structure is not working"
    assert context2.question == "question", "Bad inicialization"
