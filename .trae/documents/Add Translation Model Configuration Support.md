## 实现步骤

### 1. 更新 .env 文件
- 在aiping API配置部分添加模型配置项 AIPING_MODEL，默认值为 "Qwen3-32B"
- 在硅基流动API配置部分添加模型配置项 SILICON_FLOW_MODEL，默认值为 "tencent/Hunyuan-MT-7B"

### 2. 更新 config.py 文件
- 在 Config 类中添加 AIPING_MODEL 配置项，从环境变量读取，默认为 "Qwen3-32B"
- 在 Config 类中添加 SILICON_FLOW_MODEL 配置项，从环境变量读取，默认为 "tencent/Hunyuan-MT-7B"

### 3. 更新 translation_service.py 文件
- 修改 get_translator 方法中创建 AipingTranslator 实例的代码，传递 config.AIPING_MODEL 作为 model 参数
- 修改 get_translator 方法中创建 SiliconFlowTranslator 实例的代码，传递 config.SILICON_FLOW_MODEL 作为 model 参数

### 4. 验证修改
- 确保默认值正确设置
- 确保环境变量配置生效
- 确保翻译功能正常工作

## 预期结果
- 用户可以在 .env 文件中配置aiping翻译模型，如 "Qwen3-32B"
- 用户可以在 .env 文件中配置硅基流动翻译模型，如 "tencent/Hunyuan-MT-7B"
- 当未配置时，使用各自的默认值
- 翻译服务正常使用配置的模型进行翻译