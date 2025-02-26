import os
from typing import Dict, List

import pandas as pd

from tqa.common.domain.entities.ExeContext import exeContext
from tqa.common.domain.services.Service import Service
from tqa.common.utils import (
    PROJECT_PATH,
    ensure_path,
    eval_secure,
    get_str_date,
    read_json,
    read_jsonl,
    save_json,
    save_jsonl,
)


class Reporter(Service):
    name = "reporter"

    report_path: str

    trace_path: str
    trace_file_path: str
    trace_data: List[dict]

    trace_llm_path: str

    def __init__(self,result_path=None):
        super().__init__()
        self.report_path = ensure_path(self.get("report_name")) if not result_path else ensure_path(result_path)
        os.makedirs(self.report_path, exist_ok=True)
        self.trace_path = os.path.join(
            self.report_path, self.service_config.get("trace_folder_name")
        )
        os.makedirs(self.trace_path, exist_ok=True)
        trace_filename = "{}_{}.jsonl".format(
            self.service_config.get("trace_filename"), get_str_date()
        )
        self.trace_file_path = os.path.join(self.trace_path, trace_filename)
        self.trace_data = []
        self.trace_llm_path = os.path.join(
            self.report_path, self.service_config.get("trace_llm_folder_name")
        )
        os.makedirs(self.trace_llm_path, exist_ok=True)
        self.exe_supervisor_path = os.path.join(
            self.report_path, self.get("exe_supervisor")
        )

    def report_llm_out(
        self,
        module: str,
        table_name: str = None,
        question: str = None,
        llm_out: str = "",
        parsed_out: str = "",
        **kargs
    ):
        context = exeContext().current_execution
        file_path = os.path.join(self.trace_llm_path, "{}.jsonl".format(module))
        file_content = read_jsonl(file_path) if os.path.isfile(file_path) else []
        file_entry = {
            "module": module,
            "table_name": table_name if table_name else context.table_name,
            "question": question if question else context.question,
            "llm_out": llm_out,
            "parsed_out": parsed_out,
            "date": get_str_date(),
            "exe_id": context.exe_id,
            "answer": context.answer,
            "use_model": context.use_model,
        }
        file_entry = dict(file_entry, **kargs)
        # eval_answer = eval_secure(file_entry.get("answer"))
        # eval_result = eval_secure(file_entry.get("result"))
        # eval_result = eval_result if eval_result else file_entry.get("result")

        file_entry["match"] = (
            str(file_entry.get("result")).strip()
            == str(file_entry.get("answer")).strip()
        )
        file_content.append(file_entry)
        save_jsonl(file_path, file_content)
        return file_entry

    def _match_function(self, pred_value, true_value):
        if true_value:
            return str(eval_secure(pred_value)).strip() == str(eval_secure(true_value)).strip()
        else:
            return False

    def report_trace(
        self,
        module: str,
        table_name: str = None,
        question: str = None,
        use_model: str = None,
        **kargs
    ):
        context = exeContext().current_execution
        file_path = self.trace_file_path
        file_content = read_jsonl(file_path) if os.path.isfile(file_path) else []
        file_entry = {
            "module": module,
            "table_name": table_name if table_name else context.table_name,
            "question": question if question else context.question,
            "date": get_str_date(),
            "exe_id": context.exe_id,
            "answer": context.answer,
            "use_model": context.use_model if not use_model else use_model,
        }
        file_entry = dict(file_entry, **kargs)

        file_entry["match"] = self._match_function(
            file_entry.get("result"), file_entry.get("answer")
        )
        file_content.append(file_entry)
        save_jsonl(file_path, file_content)
        return file_entry

    def get_sheet_content(self, sheet_name: str) -> List[dict]:
        match sheet_name:
            case "traces":
                return self.get_traces_sheet()
            case "general":
                return self.get_general_sheet()
            case _:
                return []

    def get_traces_sheet(self):
        traces = []
        for file in os.listdir(self.trace_path):
            filepath = os.path.join(self.trace_path, file)
            data = read_jsonl(filepath)
            trace_id = "_".join(file.replace(".json", "").split("_")[1::])
            data = [dict(entry, **{"trace_id": trace_id}) for entry in data]
            traces.extend(data)
        return traces

    def _get_exceptions(self, traces, table, modules):
        return {
            "exception_{}".format(module): len(
                [
                    True
                    for entry in traces
                    if entry.get("table_name") == table
                    and entry.get("module") == module
                    and "Exception" in str(entry.get("state"))
                ]
            )
            for module in modules
        }

    def _get_table_traces(self, traces, table):
        return [
            entry
            for entry in traces
            if table == entry.get("table_name")
            and "interpreter" == entry.get("module")
            and entry["persist_count"]
            == max(
                [
                    e["persist_count"]
                    for e in traces
                    if table == e.get("table_name")
                    and "interpreter" == e.get("module")
                    and e.get("question") == entry.get("question")
                ]
            )
        ]

    def _get_persistence_by_question(self, traces, questions):
        return [
            max(
                [
                    entry.get("persist_count")
                    for entry in traces
                    if entry.get("question") == q and entry.get("state") is True
                ]
            )
            for q in questions
        ]

    def get_general_sheet(
        self,
        traces,
    ):
        general_trace = []
        tables = list(set([entry.get("table_name") for entry in traces]))

        for table in tables:
            modules = list(set(entry.get("module") for entry in traces))

            exceptions = self._get_exceptions(traces, table, modules)
            questions = list(set([entry.get("question") for entry in traces]))
            persistence_by_question = self._get_persistence_by_question(
                traces, questions
            )
            table_traces = self._get_table_traces(traces, table)
            execution_fixed = len(
                [True for persistence in persistence_by_question if persistence > 0]
            )

            execution = len(table_traces)
            matches = [entry.get("match") for entry in table_traces]
            correct = matches.count(True)
            incorrect = matches.count(False)
            acc = (
                correct / (correct + incorrect) * 100 if correct + incorrect > 0 else 0
            )
            correct_no_errors = len(
                [
                    True
                    for entry in table_traces
                    if entry.get("match") is True
                    and entry.get("state") is not False
                    and "Exception" not in str(entry.get("state"))
                ]
            )
            incorrect_no_errors = len(
                [
                    True
                    for entry in table_traces
                    if entry.get("match") is False
                    and entry.get("state") is not False
                    and "Exception" not in str(entry.get("state"))
                ]
            )
            total_no_errors = incorrect_no_errors + correct_no_errors
            acc_no_erros = (
                correct_no_errors / total_no_errors * 100 if total_no_errors > 0 else 0
            )

            errors = len(
                [True for entry in table_traces if entry.get("state") is False]
            )

            anwer_types = list(
                set(
                    [
                        type(eval_secure(entry.get("answer"))).__name__
                        if eval_secure(entry.get("answer"))
                        else type(entry.get("answer", "")).__name__
                        if entry.get("answer") != ""
                        else "empty"
                        for entry in table_traces
                    ]
                )
            )
            models = list(set([entry.get("use_model") for entry in table_traces]))

            general_trace.append(
                dict(
                    {
                        "table": table,
                        "executions": execution,
                        "correct": correct,
                        "incorrect": incorrect,
                        "acc": acc,
                        "correct_no_errors": correct_no_errors,
                        "incorrect_no_errors": incorrect_no_errors,
                        "acc_no_errors": acc_no_erros,
                        "errors": errors,
                        "answer_types": anwer_types,
                        "models": models,
                        "execution_fixed": execution_fixed,
                    },
                    **exceptions
                )
            )
        return general_trace

    def get_llm_sheets(self):
        llm_trace = {}
        for file in os.listdir(self.trace_llm_path):
            filepath = os.path.join(self.trace_llm_path, file)
            data = read_jsonl(filepath)
            module = file.split(".")[0]
            llm_trace[module] = [] if module not in llm_trace else llm_trace[module]
            llm_trace[module].extend(data)
        return llm_trace

    def make_excel(self):

        traces = self.get_traces_sheet()
        llm_trace = self.get_llm_sheets()
        general_trace = self.get_general_sheet(traces)

        out_path = ensure_path(os.path.join(self.report_path, "report.xlsx"))

        with pd.ExcelWriter(out_path, engine="openpyxl") as writer:

            pd.DataFrame.from_records(traces).to_excel(
                writer, sheet_name="Traces", index=False
            )
            pd.DataFrame.from_records(general_trace).to_excel(
                writer, sheet_name="General", index=False
            )

            for key, items in llm_trace.items():
                pd.DataFrame.from_records(items).to_excel(
                    writer, sheet_name=key, index=False
                )

    def _resume_supervisor(self, df_sup: pd.DataFrame) -> pd.DataFrame:
        df_sup["match"] = df_sup.apply(
            lambda row: self._match_function(row["pred"], row["true"]if "true" in row else None), axis=1
        )
        out = []
        for table_name in df_sup["table"].unique():
            df_table = df_sup.loc[df_sup["table"] == table_name]
            exe = len(df_table)
            trues = len(df_table[df_table["match"] == True])
            falses = len(df_table[df_table["match"] == False])
            acc = (trues / (trues + falses)) * 100
            exceptions = len(
                df_table[(df_table["pred"].astype(str).str.contains("Exception") == True) | df_table["pred"].isna()]
            )
            out.append(
                {
                    "table": table_name,
                    "executions": exe,
                    "trues": trues,
                    "falses": falses,
                    "acc": acc,
                    "exceptions": exceptions,
                }
            )

        return pd.DataFrame.from_records(out)

    def _resume_all_supervisor(self, dict_with_tables: Dict[str, pd.DataFrame]):
        out = []
        for table_name, df_table in dict_with_tables.items():
            df_table["match"] = df_table.apply(
                lambda row: self._match_function(row["pred"], row["true"] if "true" in row else None), axis=1
            )
            exe = len(df_table)
            tables = len(df_table["table"].unique())
            trues = len(df_table[df_table["match"] == True])
            falses = len(df_table[df_table["match"] == False])
            acc = (trues / (trues + falses)) * 100
            exceptions = len(
                df_table[(df_table["pred"].astype(str).str.contains("Exception") == True) | (df_table["pred"].isna())]
            )
            out.append(
                {
                    "table": table_name,
                    "num_tables": tables,
                    "executions": exe,
                    "trues": trues,
                    "falses": falses,
                    "acc": acc,
                    "exceptions": exceptions,
                }
            )
        return pd.DataFrame.from_records(out)

    def save_supervisors(self, files: List[tuple[str, str]]):
        out_path = ensure_path(
            os.path.join(PROJECT_PATH, "supervisor_{}.xlsx".format(get_str_date()))
        )
        with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
            data = {}
            for name, path in files:
                csv = pd.read_csv(ensure_path(path))
                if "pred" not in csv.columns:
                    csv["pred"]=csv["formatter"]
                if "answer" in csv.columns:
                    if not name.startswith("test_"):
                        csv["true"]=csv["answer"]
                data[name] = csv 
                data[name]["match"] = data[name].apply(
                    lambda row: self._match_function(row["pred"], row["true"] if "true" in row else None), axis=1
                )
                
                self._resume_supervisor(data[name]).to_excel(
                    writer, sheet_name="{}_resume".format(name), index=False
                )

            #criteria == best
            splits=list(set([name.split("_")[0] for name in data]))
            for split in splits:
                name="best_results_{}".format(split)
                split_data={n:d for n,d in data.items() if n.startswith(split)}
                if len(split_data.keys())>1:
                    data[name]=self._get_best_results(split_data,"best")
                    self._resume_supervisor(data[name]).to_excel(
                        writer, sheet_name="{}_resume".format(name), index=False
                    )
                    
            
            splits=list(set([name.split("_")[0] for name in data if not name.startswith("best_")]))
            for split in splits:
                name="democracy_results_{}".format(split)
                split_data={n:d for n,d in data.items() if n.startswith(split)}
                if len(split_data.keys())>1:
                    data[name]=self._get_best_results(split_data,"democracy")
                    self._resume_supervisor(data[name]).to_excel(
                        writer, sheet_name="{}_resume".format(name), index=False
                    )
            
            self._resume_all_supervisor(data).to_excel(
                writer, sheet_name="general_resume", index=False
            )
            
            for name in data:
                data[name].to_excel(writer, sheet_name=name, index=False)
            
        return self._resume_all_supervisor(data)
            


    def _choose_best_answer(self,answers,criteria="best"):

        
        match criteria:
            case "best":
                for model,answer in answers.items():
                    if self._match_function(answer.get("pred"),answer.get("true",None)):
                        return dict(answer,**{"model":model})
                    else:
                        return self._choose_best_answer(answers,criteria="democracy")
            case "democracy":
                all_answers=[answer.get("pred") for model,answer in answers.items()]
                if len(all_answers)==len(list(set(all_answers))):
                    return self._choose_best_answer(answers,"no_exception")
                else:
                    best_answers={all_answers.count(answer): answer for answer in all_answers}
                    best_index=max(list(best_answers.keys()))
                    for model,answer in answers.items():
                        if answer.get("pred")==best_answers.get(best_index):
                            return dict(answer,**{"model":model})
                    return dict(answer,**{"model":"Error"})
            case "no_exception":
                all_answers=[answer.get("pred") for model,answer in answers.items() if "Exception" not in str(answer.get("pred"))]
                if all_answers:
                    answer_correct=all_answers[0]
                    for model,answer in answers.items():
                        if answer.get("pred")==answer_correct:
                            return dict(answer,**{"model":model})
                    return dict(answer,**{"model":"Error"})
                else:
                    return dict(answers[0],**{"model":"all"})
                
                
                
        
    def _get_best_results(self, data:dict,criteria="best"):

        # priority=["phi-qwen14","phi-qwen7","phi","meta","qwen"]
        table_names=list(set([t for n,d in data.items() for t in d["table"].unique()]))
        
        out=[]
        for table_name in table_names:
            questions=list(set([t for n,d in data.items() for t in d[d["table"]==table_name]["question"].unique()]))
            for question in questions:
                answers={}
                for n,d in data.items():
                    model=n.split("_")[1]
                    answer = d[(d["table"] == table_name) & (d["question"]==question)]
                    if len(answer)>0:
                        answers[model]=answer.to_dict("records")[0]
                
                out.append(self._choose_best_answer(answers,criteria=criteria))

        try:
            result= pd.DataFrame.from_records(out)             
        except:
            pass

        return result