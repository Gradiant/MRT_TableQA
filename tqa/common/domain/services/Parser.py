from tqa.common.domain.services.Service import Service


class Parser(Service):
    name = "parser"

    def parse_coder(self, llm_answer):
        return llm_answer

    def parse_explaner(self, llm_answer):
        return llm_answer
