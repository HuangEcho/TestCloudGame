# 使用方法
## pytest
- 用例使用pytest执行
- 可在用例入口中用代码去执行
```python
import pytest
pytest.main(["-s", "test_service_rtc.py"])
```
- 或者直接在命令行中执行
```bash
pytest -s xxx.py
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
## 关于log
- 每次生成后都会覆盖
- 如果后续jenkins上想要保存日志，可以在执行结束后，cp到一个特定的文件夹中
```bash
cp -a pytest.log pytest_$(date +%Y%m%d_%H%M%S).log
``` 