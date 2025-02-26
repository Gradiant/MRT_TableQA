# Annotations for developer


# use InferenceService 29/11/2024

Now InferenceService is  not a service. Is a Registry of InnerInferenceService which it do inherit from Service class (Singleto). So when a developer wants to load a model and make an inference the proper way to do it is: 
```
service = InferenceService()
answer = service.inference(
    "qwen_25_coder",
    "Definde the function parse_dataframe(df) where you get the maximun value of earnings of the users over 60. Both earnings and users are df columns.",
)
```
(Check test_inferencer out for more info)

That means that use_model is not more useful in config.yaml.


# loguru for logging
This proyect uses loguru. If you want to use the logging import:
```
from tqa.common.configuration.logger import get_logger
logger = get_logger("test")
```
And add that logger name "test" to the logger file if tqa/common/configuration/logger.yaml

# test service
All services should inherit from taq/common/domain/services/service.py which has the following features:
1. It is a Singleton. Therefore, if a model is loaded when the service is inizializated, the model won't be loaded again if you instance a new service. 
2. It has a attribute name which link automatically the attributes with its configuration in the configuration file. 
3. It has a function get which allows to acces the variables in the config easelly. Instead of:
```
    service.service_config.get("key", {}).get("subkey1",{}).get("subkey2",None)
```
The function get could be used:
```
    service.get("key","subkey1","subkey2")
```

