from tqdm import tqdm

from tqa.coder.controllers.controller import CoderController
from tqa.common.domain.entities.Dataset import Dataset
from tqa.common.utils import measure, PROJECT_PATH, save_yaml,ensure_path
from tqa.common.configuration.config import load_config, CONFIG_PATH
import os
# nohup pytest tests/system/test_run_benchmark.py::test_process_all_tables &
def test_process_all_tables():
    controller = CoderController()
    controller.process_all_tables()
    controller.process_report("reports")

# ["descriptor","explainer","coder","runner","interpreter","formatter"]
def test_process_all_tables_batch():
    controller = CoderController()
    _ = controller.process_all_tables_batch(result_path="reports_test_meta_qwen14coder",mode="full")

   
def _set_models(module,model):
    config=load_config()
    config_path=os.path.join(CONFIG_PATH,"config.yaml")
    config["keys"][module]=model
    save_yaml(config_path,config)


def test_process_formater_module():
    controller = CoderController()
    _ = controller.process_all_tables_batch(result_path="reports_dev_meta_qwen14coder",mode="force",exe_steps=["interpreter","formatter"])
    files=[("dev_current_report", "reports/supervisor.csv")]
    df=controller.process_supervisors_files(files)
    print(df["acc"])


def test_report():
    controller = CoderController()
    controller.process_report("reports")
    

def test_supervisor():
    controller = CoderController()
    files = [("_".join(folder.split("_")[1::]), ensure_path(os.path.join(folder,"supervisor.csv"))) for folder in os.listdir(PROJECT_PATH) if "reports_" in folder and len(folder.split("_"))>1]
    df=controller.process_supervisors_files(files)
    print(df["acc"])


def test_one_table_one_question():
    test_table_name = "057_Spain"
    test_question = "List the top 3 most common ages among respondents"
    dataset_service = Dataset()
    controller = CoderController()

    df = dataset_service.get_tabular_df(test_table_name)
    
    result,time = measure(controller.process_table,test_question, df, table_name=test_table_name)
    
    print(">",result,time)
    # assert result is True





