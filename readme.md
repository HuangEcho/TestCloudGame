# pytest自动化用例
## 环境
使用python3来编写的，需要的依赖等：
- pytest
- allure
- requests
- logging
- yaml

## 代码结构
- dependent中放了一些依赖
- report用于allure最后生成报告使用
- 目前具体的用例在service_rtc_test/test_service_rtc.py文件中，后续如果有其他文件，再新增
  - 用例函数名需要以test开头，这个是pytest默认的，如果不想要这个开头，可以更改pytest用例收集规则。默认为：
    ```bash
    python_files = test*.py
    python_classes = Test*
    python_functions = test_*
    ```
  - service_rtc_test/script是用来执行用例前置操作的，为了测试方便，目前默认不执行。要执行的话需将service_rtc_test/test_service_rtc.py第46行打开，第47行注释,修改如下
    ```bash
        def driver(self, workspace):
        #def driver(self):
    ```
- temp是pytest结果存放地址
- pytest.log为日志文件
## pytest
- 用例使用pytest执行
- 可在用例入口中用代码去执行
```python
import pytest
pytest.main(["-s", "test_service_rtc.py"])
```
- 或者直接在命令行中执行,-s需要写具体的地址，如 service_core_test/test_resource_manage.py
```bash
pytest -s service_core_test/test_resource_manage.py --alluredir=service_core_test/temp
```
- 如果配置了pytest.ini文件，则可以把pytest的参数写在addopts中，命令行中只输入pytest即可
```bash
pytest
```
## allure
- pytest测试完毕后在命令行中输入
```bash
allure generate ./temp -o ./report --clean
```
- 建议还是每个service下放一个temp，把pytest的运行结果放在里面，这样运行allure的时候，只会有当前的项目的结果。不然会把所有的结果都展示出来
```bash
allure generate service_core_test/temp -o ./report --clean
```
## 关于log
- 每次生成后都会覆盖
- 如果后续jenkins上想要保存日志，可以在执行结束后，cp到一个特定的文件夹中
```bash
cp -a pytest.log pytest_$(date +%Y%m%d_%H%M%S).log
``` 