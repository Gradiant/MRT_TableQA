import os
import traceback
from time import time
from typing import List, Optional

import pandas as pd
from tqdm import tqdm

from tqa.coder.domain.services.column_descriptor_service import ColumnDescriptorService
from tqa.coder.domain.services.service import (
    CoderService,
    ExplainerService,
    InterpreterService,
    RunnerService,
    FormatterSemevalService
)
from tqa.coder.usecases.column_description_usecase import ColumnDescriptorUseCase
from tqa.coder.usecases.interpreter_usecase import InterpretUseCase
from tqa.coder.usecases.formatter_usecase import FormatterUseCase
from tqa.coder.usecases.qa_usecase import CoderUseCase, ExplainUseCase, RunnerUseCase
from tqa.common.configuration.logger import get_logger
from tqa.common.domain.entities.Dataset import Dataset
from tqa.common.domain.entities.ExeContext import exeContext
from tqa.common.domain.services.InferenceService import InferenceService
from tqa.common.domain.services.Reporter import Reporter
from tqa.common.errors.application_exception import InterpreterException
from tqa.common.usecases.base import BaseUseCase
from tqa.common.utils import ensure_path, get_str_date, read_csv, save_csv, save_json
from tqa.common.configuration.config import load_config
from tqa.coder.usecases.process_table_usecase import run_use_case
logger = get_logger("batch_usecase")


class ProcessAllTablesBatchUseCase(BaseUseCase):
    
    steps=["descriptor","explainer","coder","runner","interpreter","formatter"]
    
    def __init__(
        self,
        descripter: ColumnDescriptorService,
        explainer: ExplainerService,
        inferer: InferenceService,
        coder: CoderService,
        runner: RunnerService,
        interpreter: InterpreterService,
        formatter: FormatterSemevalService,
        max_steps: int = 5,
        exe_steps=["descriptor","explainer","coder","runner","interpreter","formatter"],
        mode= "full"
    ):
        self._descripter = descripter
        self._explainer = explainer
        self._inferer = inferer
        self._coder = coder
        self._runner = runner
        self._interpreter = interpreter
        self._formatter = formatter
        self._max_steps = max_steps
        self.exe_steps = exe_steps
        self.mode=mode
        

    def _run_module(self, module_name: str, prev_res=None,df=None,table_name=None,question=None, batch=None) -> tuple[List | dict, dict]:
        """_summary_

        Args:
            module_name (str): name of the module
            prev_res (_type_, optional): result of the revious module. Defaults to None.

        Returns:
            tuple[List|dict,dict]: returns the ouput of the function run_use_case
        """
        match module_name:
            case "descriptor":
                return run_use_case(
                    ColumnDescriptorUseCase,
                    df,
                    self._descripter,
                    self._inferer,
                    **{"table_name": table_name},
                )
            case "explainer":
                return run_use_case(
                    ExplainUseCase,
                    question,
                    df.columns,
                    prev_res,
                    self._max_steps,
                    self._explainer,
                    self._inferer,
                    self._reporter,
                    **{"table_name": table_name},
                )
            case "coder":
                return run_use_case(
                    CoderUseCase,
                    df.columns,
                    prev_res,
                    self._coder,
                    self._inferer,
                    self._reporter,
                    None,
                    None,
                )
            case "runner":
                max_persist=3

                for persist_count in range(0,max_persist+1):
                    try:
                        result = run_use_case(RunnerUseCase, df, prev_res, self._runner)

                    except Exception as e:

                        if persist_count==max_persist:
                            raise e
                        
                        old_code=prev_res
                        exception_lines=traceback.format_exc().splitlines()
                        separation_line=[line for line in exception_lines if "During handling" in line]
                        index = exception_lines.index(separation_line[0]) if separation_line else len(separation_line)
                        exception_lines=exception_lines[0:index]
                        old_exception = "{}".format("\n".join(exception_lines).strip())
                        
                            
                        prev_res = run_use_case(
                            CoderUseCase,
                            df.columns,
                            batch["explainer"],
                            self._coder,
                            self._inferer,
                            self._reporter,
                            old_code,
                            old_exception,
                        )[0]
                        if old_code==prev_res:
                            print("Same code")
                        else:
                            print("corrected!")
                        batch["coder"]=prev_res
                        continue
                    break
                
                return result
                        
            case "interpreter":
                return run_use_case(
                    InterpretUseCase,
                    question,
                    prev_res,
                    self._interpreter,
                    self._inferer,
                    self._reporter
                )
            case "formatter":
                return run_use_case(
                    FormatterUseCase,
                    prev_res,
                    self._formatter,
                    self._reporter
                )


    def _create_batch_supervisor(self,tables_info):
        return [
                dict({"table":table.get("table_name"),
                 "question":question.get("question"),
                 "exe_id":exeContext().get_or_new(table_name=table.get("table_name"),question=question.get("question")).exe_id,
                 "answer":question.get("answer",None),
                 },**dict({step:None for step in self.steps},**{"error":False,"exe":False}))
                for table in tables_info for question in table.get("questions")]

    
    def _mode_condition(self,batch,step):
        match self.mode:
            case "full":
                return not batch.get("exe") and not batch.get("error")
            case "errors":
                if "Exception" in str(batch.get(step)):
                    return True
                if batch.get(step,None)==None:
                    return True
                if isinstance(batch.get(step,[]),list) or isinstance(batch.get(step,[]),dict):
                    if not batch.get(step,[]):
                        return True
                else:
                    if pd.isna(batch.get(step,pd.NA)):
                        return True
                return False
            case "force":
                return True

        
        
    def execute(self, result_path=None):
        self._reporter= Reporter(result_path)
        dataset_service = Dataset()
        tables_set = dataset_service.get_data()
        tables_set = tables_set
        tables_info = dataset_service.format_data_for_batch_exec(tables_set)
        exe_supervisor_path = self._reporter.exe_supervisor_path
        save_json(os.path.join(self._reporter.report_path,"config.json"),load_config())
        batch_supervisor=self._create_batch_supervisor(tables_info) if not os.path.isfile(exe_supervisor_path) else read_csv(exe_supervisor_path)
        for batch in batch_supervisor:
            for key,item in batch.items():
                try:
                    batch[key]=eval(str(item))
                except:
                    pass


        current_table = ""
        
        for step in self.steps:

            prev_step= self.steps[self.steps.index(step)-1] if  self.steps.index(step)-1>=0 else ""
            for batch in tqdm(batch_supervisor,desc="Procesing step: {}".format(step)):
                exeContext().get_or_new(batch.get("table"),batch.get("question"))
                if step in self.exe_steps:
                    df = dataset_service.get_tabular_df(batch.get("table")) if current_table!=batch.get("table") else df
                    current_table=batch.get("table")
                    prev_res=batch.get(prev_step,None)
                    if self._mode_condition(batch,step):
                        try:
                            batch[step]=self._run_module(step,prev_res,df,batch.get("table"),batch.get("question"),batch)[0]

                        except Exception as e:
                            batch[step]="Exception: "+ str(e)
                            batch["error"]=True
                            pass
                        except InterpreterException as e:
                            batch[step]="Exception: "+ str(e)
                            batch["error"]=True
                            pass
                    save_csv(exe_supervisor_path,pd.DataFrame.from_records(batch_supervisor)) 
                    
                if step==self.steps[-1]:
                    batch["exe"]=True
        
                       
        save_csv(exe_supervisor_path,pd.DataFrame.from_records(batch_supervisor))     
        self._result = exe_supervisor_path
