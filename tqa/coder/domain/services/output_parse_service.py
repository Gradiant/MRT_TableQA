import locale
from typing import Any, List, Literal, Optional, Tuple, Union


class OutParserService:
    def try_parse_number(self, num_str: str) -> Union[float, None]:
        """
        Tries str -> num || returns either the number or None (not possible)
        """
        # Step 1: Try locale-based parsing for different number formats
        try:
            # Attempt to use comma as thousand separator and period as decimal point
            locale.setlocale(locale.LC_NUMERIC, "en_US.UTF-8")  # US format
            return locale.atof(num_str)
        except ValueError:
            pass

        try:
            # Da error
            # locale.setlocale(locale.LC_NUMERIC, 'eu')  # European format
            # return locale.atof(num_str)
            # los type ignore es pq no entiende que hay un try-catch
            num_str = float(num_str.replace(".", "").replace(",", "."))  # type: ignore
            return num_str  # type: ignore
        except ValueError:
            pass

        try:
            # normal float?
            num = float(num_str)
            return num
        except ValueError:
            pass

        return None

    def try_parse_bool(self, bool_str: str) -> Union[bool, None]:
        """
        Tries str -> bool || returns bool or None (not possible)

        bool str := {TRUE, True, true, FALSE, False, false}
        """
        if bool_str.lower() == "true":
            return True
        if bool_str.lower() == "false":
            return False
        return None

    def try_parse_list(self, list_str: str, separator: str) -> Union[List[Any], None]:
        """
        Tries str -> list
        """
        lista = list_str.split(separator)
        if len(lista) == 1:
            return None
        return lista

    def sub_parse_list(
        self, list_of_elements: List[str]
    ) -> Union[List[str], List[float], List[bool]]:
        """
        Triest
        list of str ["", "", ""] -> list of:
        - float [1,2,3]
        - bool [True, False, True]
        - str (stays the same)
        """
        _list_nums = []
        _list_bools = []
        flag_num, flag_bool = 1, 1

        for element in list_of_elements:
            if flag_num:
                num = self.try_parse_number(element)
                if num is None:
                    flag_num = 0
                else:
                    _list_nums.append(num)
                bool_el = self.try_parse_bool(element)
                if num is None:
                    flag_bool = 0
                else:
                    _list_bools.append(bool_el)

            if not flag_num and not flag_bool:
                break

        if flag_num:
            return _list_nums

        if flag_bool:
            return _list_bools

        return list_of_elements
