from typing import Any, Callable, List, Literal, Tuple, Union

from tqa.coder.domain.services.output_parse_service import OutParserService
from tqa.common.usecases.base import BaseUseCase


class OutParserUseCase(BaseUseCase):
    """
    En teoría con el EXEC se conservan los tipos, es decir recuperará el tipo
    de dato que tuviera la columna,

    Entonces esto alomejor no hace falta, pero bueno queda aqui por si acaso ya que existe
    """

    def __init__(
        self,
        llm_output_string: str,
        out_parser: OutParserService,
    ) -> None:
        super.__init__()
        self.out_parser = out_parser
        self.llm_output_string = llm_output_string
        self._result = None

    @property
    def result(
        self,
    ) -> Union[str, float, bool, List[str], List[float], List[bool], Any]:
        return self._result

    # ! TODO si da problemas mirar algo para recuperar las categorias desde el explainer TODO
    def execute(self) -> None:
        """
        Does strict parsing (number, string, bool and lists)
        """
        self._result, _ = self._to_true_format(self.llm_output_string)

    def naive_execute(self) -> None:
        """
        Does naive typing, aka either string or List[string]
        """
        llm_output_string = self.llm_output_string
        # no lista
        # orden "inverso" por optimizacion
        separators = [
            ",",
            "|",
        ]  # "-" no puede ser separador pq se usa en strings de tipo rango
        flag = 0

        if llm_output_string.startswith("[") and llm_output_string.endswith("]"):
            flag = 1
        else:
            for character in llm_output_string:
                if character in separators:
                    flag = 2
                    break

        # no hay separadores = no hay lista
        if not flag:
            # es un string
            self._result, _ = llm_output_string, "no error"

        # lista con corchetes
        if flag == 1:
            # lista vacia
            if len(llm_output_string) == 2:
                self._result, _ = [""], "no error"
            # quitamos para tratar de la misma manera
            llm_output_string = llm_output_string[1:-1]

        # lista sin corchetes
        for separator in separators:
            list_of_elements = self.out_parser._try_parse_list(
                llm_output_string, separator
            )
            if list_of_elements is not None:
                self._result, _ = list_of_elements, "no error"

        # aqui no debería llegar nunca
        self._result, _ = llm_output_string, "error"

    # -------------------------------------------------------------------------
    # esperamos una entrada que sea texto (i.e texto del llm)
    # posibles entradas
    # string, numero, booleano
    # Pepe | 2.2 | True
    # listas de ... sin corchetes
    # Pepe, Pepe, Pepe ...
    # listas de ... con corchetes
    # [Pepe, Pepe, Pepe]

    def _to_true_format(
        self, llm_output_string: str
    ) -> Tuple[
        Union[
            str,
            float,
            bool,
            List[str],
            List[float],
            List[bool],
            Any,  # any para el type error
        ],
        Literal["error", "no error"],
    ]:
        """

        Returns:
            element + code (code == error | no error)
        """
        llm_output_string = llm_output_string
        # no lista
        # Digamos que es numero con coma (duro)
        num = self.out_parser.try_parse_number(llm_output_string)
        if num is not None:
            return num, "no error"

        # no lista
        # booleanos
        # orden "inverso" por optimizacion
        separators = [
            ",",
            "|",
        ]  # "-" no puede ser separador pq se usa en strings de tipo rango
        flag = 0

        if llm_output_string.startswith("[") and llm_output_string.endswith("]"):
            flag = 1
        else:
            for character in llm_output_string:
                if character in separators:
                    flag = 2
                    break

        # no hay separadores = no hay lista
        if not flag:
            # es un booleano
            bool = self.out_parser.try_parse_bool(llm_output_string)
            if bool is not None:
                return bool, "no error"

            # es un string
            return llm_output_string, "no error"

        # lista con corchetes
        if flag == 1:
            # lista vacia
            if len(llm_output_string) == 2:
                return [""], "no error"
            # quitamos para tratar de la misma manera
            llm_output_string = llm_output_string[1:-1]

        # lista sin corchetes
        for separator in separators:
            list_of_elements = self.out_parser.try_parse_list(
                llm_output_string, separator
            )
            if list_of_elements is not None:
                return self.out_parser.sub_parse_list(list_of_elements), "no error"

        # aqui llegamos si ha habido un problema o si habia una lista con corchetes de dos elementos
        if flag == 1:
            return [llm_output_string], "no error"

        # error (teoricamente)
        return llm_output_string, "error"
