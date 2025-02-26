from time import sleep
from typing import Any, Dict

import torch
import transformers
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from llama_cpp import Llama
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

from tqa.common.configuration.config import load_config
from tqa.common.domain.entities.ExeContext import exeContext
from tqa.common.domain.services.Service import Service

load_dotenv()

# A ver no creo que hacer un model_registry entero sea la mejor idea
# Así que voy a mover InferenceService(old) a InnerInferenceService(new)
# Y Voy a crear un Wrapper con varios Inference Services
#
# InferenceService(old) --> InnerInferenceService
# InferenceService(new) = aprox = ModelRegistry
# Lo unico es que ahora hace falta poner un matching de args
# keys:
#   block_ref: model_ref
# p.e.
# keys:
#   coder: qwen_25
# Mirar config


class InferenceService:
    def __init__(self) -> None:
        self.model_registry: Dict[str, InnerInferenceService] = {}
        self.key_matching = {}
        self._load_key_matching_pairs()
        

    def _load_key_matching_pairs(self):
        config = load_config()
        self.key_matching = config.get("keys", {"default", "qwen_25"})

    def inference(
        self,
        inner_identifier: str,
        prompt: str,
        role: str = "user",
        prompt_system="",
        role_system="system",
    ):
        model_identifier = self.key_matching.get(inner_identifier, "default")
        InnerInferenceService("bypass").logger.info(inner_identifier, model_identifier)
        if model_identifier == "default":
            model_identifier = self.key_matching.get("default")

        model = self.model_registry.get(model_identifier, None)
        if model is None:
            
            
            if not load_config().get("llm_inference",{}).get("keep_models",False):
                models_registered = list(self.model_registry.keys())
                for model_registered in models_registered:
                    self._stop_model(model_registered)
                    
            self._start_model(model_identifier)
            model = self.model_registry.get(model_identifier, None)
            if model is None:
                raise Exception("Something went wrong with instantiation")

        return model.inference(prompt, role, prompt_system, role_system)

    def _start_model(self, model_identifier: str) -> None:
        self.model_registry[model_identifier] = InnerInferenceService(model_identifier)

    def _stop_model(self, model_identifier: str) -> None:
        # Esto si hace falta al final seguramente haya que mirarlo pq creo que si
        # hay interdependencias no funciona
        # si estamos en manolito se puede hacer algo mas conservador pq tentemos mucha ram-> self.model_registry[model_identifier].model.to("cpu")
        model = self.model_registry.pop(model_identifier)
        del model
        torch.cuda.empty_cache()


class InnerInferenceService(Service):
    name = "llm_inference"
    mandatory_keys = []

    def __init__(self, use_model: str) -> None:
        super().__init__()
        self.use_model = use_model
        self.logger.debug("Use model: {}".format(self.use_model))
        self.logger.info("MODELO: ", self.use_model)
        match self.use_model:
            case "bypass":
                self.model = None
            case "llama":
                self.model = None
                model_path = (
                    self.service_config.get("load_params")
                    .get("llama")
                    .get("model_path")
                )
                self.logger.info("Loading model in:{}".format(model_path))
                self.model = Llama(
                    model_path=model_path,
                    n_gpu_layers=-1,
                    verbose=True,
                )
            case "meta":
                self.model = None
                self.model = pipeline(
                    self.service_config.get("load_params").get("meta", {}).get("task"),
                    model=self.service_config.get("load_params")
                    .get("meta", {})
                    .get("model_path"),
                    torch_dtype=torch.float16,
                    device_map="cuda",
                )
            case "openai":
                self.model = ChatOpenAI(
                    model=self.service_config.get("load_params")
                    .get("openai", {})
                    .get("model")
                )
            case "llama_1b":
                self.model = None
                self.model = pipeline(
                    "text-generation",
                    model=self.service_config.get("load_params")
                    .get("llama_1b", {})
                    .get("model_path"),
                    torch_dtype=torch.float16,
                    device_map="auto",
                )
            case "qwen_25":
                self.model = None
                _args = self.service_config.get("load_params").get("qwen_25", {})
                _name = _args.get("model_path").replace(
                    "{tam}", _args.get("tam", str(7))
                )
                self.model = AutoModelForCausalLM.from_pretrained(
                    _name,
                    torch_dtype="auto",
                    device_map="auto",
                )
                self.tokenizer = AutoTokenizer.from_pretrained(_name)
            case "qwen_25_coder":
                self.model = None
                _args = self.service_config.get("load_params").get("qwen_25_coder", {})
                _name = _args.get("model_path").replace(
                    "{tam}", _args.get("tam", str(7))
                )
                self.model = AutoModelForCausalLM.from_pretrained(
                    _name,
                    torch_dtype="auto",
                    device_map="auto",
                )
                self.tokenizer = AutoTokenizer.from_pretrained(_name)
            case "gemma_9":
                self.model = None
                _args = self.service_config.get("load_params").get("gemma_9", {})
                _name = _args.get("model_path")
                self.model = AutoModelForCausalLM.from_pretrained(
                    _name,
                    torch_dtype=torch.bfloat16,
                    device_map="auto",
                )
                self.tokenizer = AutoTokenizer.from_pretrained(_name)
            case "gen5_gemma_9":
                self.model = None
                _args = self.service_config.get("load_params").get("gen5_gemma_9", {})
                _name = _args.get("model_path")
                self.model = AutoModelForCausalLM.from_pretrained(
                    _name,
                    torch_dtype=torch.bfloat16,
                    device_map="auto",
                )
                self.tokenizer = AutoTokenizer.from_pretrained(_name)
            case "zeus_gemma":
                self.model = None
                _args = self.service_config.get("load_params").get("zeus_gemma", {})
                _name = _args.get("model_path")
                self.model = AutoModelForCausalLM.from_pretrained(
                    _name,
                    torch_dtype=torch.bfloat16,
                    device_map="auto",
                )
                self.tokenizer = AutoTokenizer.from_pretrained(_name)
            case "phi_4":
                self.model = transformers.pipeline(
                    "text-generation",
                    model="microsoft/phi-4",
                    model_kwargs={"torch_dtype": "auto"},
                    device_map="auto",
                )
            case _:
                self.logger.error("No model type {}".format(self.use_model))
                self.model = None

    def hugginface_instruct_generate(
        self,
        hf_model,
        hf_tokenizer,
        hf_prompt: str,
        hf_sysprompt: str,
        config: Dict[str, Any] = {},
    ) -> str:
        messages = [
            {"role": "system", "content": hf_sysprompt},
            {"role": "user", "content": hf_prompt},
        ]
        try:
            text = hf_tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
        except Exception:
            text = hf_tokenizer.apply_chat_template(
                messages[1:], tokenize=False, add_generation_prompt=True  # no sysprompt
            )

        model_inputs = hf_tokenizer([text], return_tensors="pt").to(hf_model.device)

        generated_ids = hf_model.generate(**model_inputs, **config)

        generated_ids = [
            output_ids[len(input_ids) :]
            for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]
        response = hf_tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

        # devolver a la cpu para no generar basura
        # generated_ids = generated_ids.cpu()
        generated_ids[0] = generated_ids[0].to("cpu")
        model_inputs = model_inputs.to("cpu")
        # print(generated_ids, model_inputs)
        del generated_ids, model_inputs

        return response

    def inference(
        self, prompt: str, role: str = "user", prompt_system="", role_system="system"
    ) -> str:
        self.config = load_config()
        self.service_config = self.config.get(self.name, {})
        exeContext().add(use_model=self.use_model)
        match self.use_model:
            case "bypass":
                sleep(self.get("infer_params", "bypass", "time"))
                return self.get("infer_params", "bypass", "default_text")
            case "llama":
                model_output = self.model(
                    prompt,
                    **self.service_config.get("infer_params", {}).get("llama"),
                )
                return model_output["choices"][0]["text"].strip()
            case "qwen_25":

                if len(prompt_system) == 0:
                    _sysprompt = (
                        self.service_config.get("infer_params", {})
                        .get("qwen_25", {})
                        .get(
                            "sysprompt",
                            "You are a helpfull AI assistant. You answer clearly to what the user provides you. Do not hallucinate. Make sure to follow the isntructions clearly.",
                        )
                    )

                else:
                    _sysprompt = prompt_system

                _config = (
                    self.service_config.get("infer_params", {})
                    .get("qwen_25", {})
                    .get("config", {})
                )
                return self.hugginface_instruct_generate(
                    self.model, self.tokenizer, prompt, _sysprompt, _config
                )
            case "qwen_25_coder":
                _sysprompt = (
                    self.service_config.get("infer_params", {})
                    .get("qwen_25_coder", {})
                    .get(
                        "sysprompt",
                        "You are a helpfull AI assisntant. You answer clearly to what the user provides you. Do not hallucinate. Make sure to follow the isntructions clearly.",
                    )
                )
                _config = (
                    self.service_config.get("infer_params", {})
                    .get("qwen_25_coder", {})
                    .get("config", {})
                )
                return self.hugginface_instruct_generate(
                    self.model, self.tokenizer, prompt, _sysprompt, _config
                )
            case "zeus_gemma":
                _sysprompt = (
                    self.service_config.get("infer_params", {})
                    .get("zeus_gemma", {})
                    .get(
                        "sysprompt",
                        "You are a helpfull AI assisntant. You answer clearly to what the user provides you. Do not hallucinate. Make sure to follow the isntructions clearly.",
                    )
                )
                _config = (
                    self.service_config.get("infer_params", {})
                    .get("zeus_gemma", {})
                    .get("config", {})
                )
                return self.hugginface_instruct_generate(
                    self.model, self.tokenizer, prompt, _sysprompt, _config
                )
            case "gen5_gemma_9":
                _sysprompt = (
                    self.service_config.get("infer_params", {})
                    .get("gen5_gemma_9", {})
                    .get(
                        "sysprompt",
                        "You are a helpfull AI assisntant. You answer clearly to what the user provides you. Do not hallucinate. Make sure to follow the isntructions clearly.",
                    )
                )
                _config = (
                    self.service_config.get("infer_params", {})
                    .get("gen5_gemma_9", {})
                    .get("config", {})
                )
                return self.hugginface_instruct_generate(
                    self.model, self.tokenizer, prompt, _sysprompt, _config
                )
            case "gemma_9":
                _sysprompt = (
                    self.service_config.get("infer_params", {})
                    .get("gemma_9", {})
                    .get(
                        "sysprompt",
                        "You are a helpfull AI assisntant. You answer clearly to what the user provides you. Do not hallucinate. Make sure to follow the isntructions clearly.",
                    )
                )
                _config = (
                    self.service_config.get("infer_params", {})
                    .get("gemma_9", {})
                    .get("config", {})
                )
                return self.hugginface_instruct_generate(
                    self.model, self.tokenizer, prompt, _sysprompt, _config
                )
            case "phi_4":
                _sysprompt = (
                    self.service_config.get("infer_params", {})
                    .get("phi_4", {})
                    .get(
                        "sysprompt",
                        "You are a helpfull AI assisntant. You answer clearly to what the user provides you. Do not hallucinate. Make sure to follow the isntructions clearly.",
                    )
                )
                _config = (
                    self.service_config.get("infer_params", {})
                    .get("phi_4", {})
                    .get("config", {})
                )
                messages = [
                    {"role": "system", "content": _sysprompt},
                    {"role": "user", "content": prompt},
                ]
                outputs = self.model(messages, **_config)
                return outputs[0]["generated_text"][-1]["content"]
            case "llama_1b":
                model_output = self.model(
                    prompt,
                    **self.service_config.get("infer_params", {}).get("llama_1b"),
                )
                return model_output[0].get("generated_text").replace(prompt, "").strip()
            case "meta":
                terminators = [
                    self.model.tokenizer.eos_token_id,
                    self.model.tokenizer.convert_tokens_to_ids("<|eot_id|>"),
                ]

                if isinstance(prompt, str):
                    prompt = [{"role": role, "content": prompt}]

                outputs = self.model(
                    prompt,
                    eos_token_id=terminators,
                    **self.service_config.get("infer_params", {}).get("meta"),
                )
                return outputs[0]["generated_text"][-1].get("content")

            case "openai":
                if not prompt_system and not role_system:
                    prompt_template = ChatPromptTemplate.from_messages([(role, prompt)])
                else:
                    prompt_template = ChatPromptTemplate.from_messages(
                        [(role_system, prompt_system), (role, (prompt))]
                    )

                parser = StrOutputParser()

                chain = prompt_template | self.model | parser
                return chain.invoke({})

            case _:
                self.logger.error("no model type {}".format(self.use_model))
