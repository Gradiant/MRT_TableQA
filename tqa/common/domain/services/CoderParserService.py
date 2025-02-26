import re

from tqa.common.domain.services.Service import Service


def is_pure_code(message):
    return re.match(r"^\s*import\s+.*?\n(?:.*\n)*$", message.strip())


def extract_code_blocks(message):
    languages = ["bash", "css", "text"]
    language_pattern = "|".join(languages)
    code_block_pattern = rf"```python\n(.*?)```|```(?:{language_pattern})?\n(.*?)```"

    code_blocks = re.findall(code_block_pattern, message, re.DOTALL)
    code = [block[0] or block[1] for block in code_blocks if block[0] or block[1]]
    return [content.strip() for content in code]


def extract_inline_python_code(message):
    """
    Extrae líneas de código que se asemejan a la sintaxis de Python de texto libre.
    """
    code_lines = re.findall(
        r"^(import\s+.*|[a-zA-Z_]+\s*=.*|#.*|print\s*\(.*\)|if\s+.*:|for\s+.*:)",
        message,
        re.MULTILINE,
    )
    return [line.strip() for line in code_lines]


class CodeParserService(Service):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def code_parser(self, message):
        """
        Analiza el mensaje para extraer el código.
        """
        # Caso 1: Código sin texto adicional
        if is_pure_code(message):
            extracted_code = message.strip()
        else:
            # Caso 2: Extrae bloques de código
            code = extract_code_blocks(message)

            # Caso 3: Extrae líneas de código estilo Python en texto
            if not code:
                code = extract_inline_python_code(message)

            extracted_code = "\n".join(code) if code else ""
        return extracted_code
