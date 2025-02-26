from tqa.common.configuration.config import load_config
from tqa.common.domain.entities.ExeContext import exeContext
from tqa.common.domain.services.InferenceService import InferenceService


def test_zeus_gemma():
    service = InferenceService()
    service._start_model("zeus_gemma")  # manual
    prompt = "Hola esto es una prueba de que funcionas bien. Devuelveme algo de demuestre que funcionas perfectamente."
    answer = service.inference("zeus_gemma", prompt)
    assert answer != prompt


def test_gen5_gemma_9():
    service = InferenceService()
    service._start_model("gen5_gemma_9")  # manual
    prompt = "Hola esto es una prueba de que funcionas bien. Devuelveme algo de demuestre que funcionas perfectamente."
    answer = service.inference("gen5_gemma_9", prompt)
    assert answer != prompt


def test_gemma_9():
    service = InferenceService()
    service._start_model("gemma_9")  # manual
    prompt = "Hola esto es una prueba de que funcionas bien. Devuelveme algo de demuestre que funcionas perfectamente."
    answer = service.inference("gemma_9", prompt)
    assert answer != prompt


def test_phi4():
    service = InferenceService()
    service._start_model("phi_4")  # manual
    prompt = "Hola esto es una prueba de que funcionas bien. Devuelveme algo de demuestre que funcionas perfectamente."
    answer = service.inference("phi_4", prompt)
    assert answer != prompt


def test_bypass():
    service = InferenceService()
    service._start_model("bypass")  # manual
    out = service.model_registry.get("bypass").get(
        "llm_inference",
        "infer_params",
        "bypass",
        "default_text",
        search_in=load_config(),
    )
    answer = service.inference("bypass", "Hola esto es una prueba")
    assert out == answer


def test_llama():
    service = InferenceService()
    service._start_model("llama")  # manual
    prompt = "Hola esto es una prueba de que funcionas bien. Devuelveme algo de demuestre que funcionas perfectamente."
    answer = service.inference("llama", prompt)
    assert answer != prompt


def test_meta():
    service = InferenceService()
    service._start_model("meta")  # manual
    answer = service.inference("meta", "Hola esto es una prueba de que funcionas bien")
    print(answer)
    assert answer


def test_normal_qwen():
    service = InferenceService()
    answer = service.inference(
        "qwen_25", "Imagine a generic DF, 2 columns, 3 rows. Describe it"
    )
    print(answer[:25])
    assert answer


def test_code_qwen():
    service = InferenceService()
    answer = service.inference(
        "qwen_25_coder",
        "Definde the function parse_dataframe(df) where you get the maximun value of earnings of the users over 60. Both earnings and users are df columns.",
    )
    print(answer[:25])
    assert answer
