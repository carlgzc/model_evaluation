LLM-Auto-Evaluator：自动化大模型评估框架
LLM-Auto-Evaluator 是一个用于自动化评估本地大语言模型（LLMs）能力的框架。它通过一个更强大的在线“裁判”模型（例如 GPT-4o, Gemini 等），对本地模型（通过 Ollama 部署）的性能进行系统性、多维度、数据驱动的评估。

本框架专为模型开发者、研究人员和AI应用工程师设计，旨在提供一个标准化的流程来衡量模型的表现、追踪调优带来的改进，并最终生成详尽、易于解读的评估报告。

✨ 核心功能
多模型批量评估: 在一次运行中，可以按顺序对配置文件中定义的多个本地 LLM 进行评估，非常适合进行模型横向对比。

LLM-as-a-Judge (以模型为裁判): 利用强大的在线 LLM 进行精细化的自动评分，超越了传统基于固定指标评估的局限性。

可定制的评估角色 (Persona): 允许定义不同的评估“角色”（例如 default, strict_code_reviewer），每个角色都有独特的评估标准和评分维度，以适应不同的测试场景。

全面的评估报告: 自动生成详细的 Markdown 报告，内容包括整体性能指标、各场景下的得分明细，以及逐题的深度分析。

并发处理: 利用多线程技术加速评估阶段，通过并行调用裁判模型 API 来更快地获得结果。

灵活的数据输入: 同时支持 .csv 和 .jsonl 格式的题库文件，并能自动将 CSV 转换为 JSONL。

🚀 工作流程
整个评估流程被划分为三个核心阶段：

生成答案 (Answer Generation): OllamaRunner 模块会读取题库中的每一个问题，并将其发送给 config.yaml 中指定的本地模型，然后收集并保存模型生成的答案。

自动评估 (Automated Evaluation): OnlineEvaluator 模块将原始问题、本地模型的答案、理想参考答案以及评估要点打包，形成一个结构化的 Prompt 发送给“裁判”LLM。裁判模型会返回一个包含多维度评分和定性反馈（评分理由、优点、缺点）的 JSON 对象。

生成报告 (Report Generation): 最后，ReportGenerator 模块会汇总所有的评估数据，计算统计指标（例如，各维度和各场景的平均分），并生成最终的 Markdown 评估报告。

📂 项目结构
/
|-- main.py                 # 主程序入口，负责编排整个评估流程
|-- ollama_runner.py        # 与本地 Ollama 模型交互的模块
|-- online_evaluator.py     # 与在线“裁判”LLM 交互的模块
|-- report_generator.py     # 用于创建 Markdown 报告的模块
|-- prompts.py              # 存储所有用于裁判模型的 Prompt 模板
|-- config.yaml             # 项目的核心配置文件
|-- requirements.txt        # Python 依赖库
|-- .gitignore              # Git 忽略文件配置
|-- .env                    # (需自行创建) 用于存放 API 密钥
|-- data/
|   |-- questions.csv       # 示例题库文件
|-- results/
|   |-- <run_folder>/       # 每次运行的结果会存放在这里
|       |-- ollama_answers.jsonl
|       |-- evaluation_details.jsonl
|       |-- summary.md
|       |-- evaluation_report.md
|-- README.md               # 项目说明文档

🛠️ 快速开始
请遵循以下步骤来设置并运行您的第一次评估。

1. 环境准备
Python 3.8 或更高版本

Ollama 已安装、正在运行且网络可访问。

至少已通过 Ollama 拉取一个本地模型 (例如, ollama pull llama3)。

2. 安装
克隆代码库:

git clone <your-repo-url>
cd <repo-name>

安装所需的 Python 依赖包:

pip install -r requirements.txt

3. 配置
设置您的 API 密钥: 在项目的根目录下创建一个名为 .env 的文件。这个文件将用于存储您的私密 API 密钥。根据您在 config.yaml 中设置的服务商，添加相应的密钥：

# 如果使用 OpenAI
OPENAI_API_KEY="sk-..."

# 如果使用 ByteDance (豆包)
ARK_API_KEY="..."

编辑 config.yaml: 打开 config.yaml 文件，根据您的需求进行定制：

models.ollama_models: 添加或修改您希望评估的本地模型列表。您必须指定 model_name，也可以选择性地提供 base_url 和生成参数 options (如 temperature)。

models.online_evaluator: 配置“裁判”模型。设置 provider (例如 "openai")，然后填写其详细信息，如 model_name 和 api_key_env。

paths.question_bank: 提供您的题库文件的正确路径。

evaluation: 为您的运行设置一个 task_name，并根据您的 API 限速调整 max_workers（并发线程数）。您还可以在这里更改 prompt_persona（评估角色）。

4. 准备题库
您的题库文件 (例如 data/questions.csv) 是整个评估的核心。它必须包含以下列：

id: 每个问题的唯一标识符。

scenario: 问题的主要类别或领域 (例如, "通用知识", "代码生成")。

sub_scenario: 更具体的子类别 (例如, "历史", "Python")。

prompt: 发送给模型的实际问题或指令。

ideal_output: 一个标准的、理想的参考答案，用于指导裁判模型。

notes_for_evaluation: 给裁判模型的具体评估指示，例如需要关注的标准或需要检查的约束条件。

5. 运行评估
在您的终端中执行主程序脚本：

python main.py

脚本将启动评估流程，并在控制台打印每一步的进度。运行结束后，一个新的、带有唯一命名（包含任务名、模型名和时间戳）的文件夹将被创建在 results/ 目录下，其中包含了所有的输出文件。

🔧 进阶定制
本框架被设计为易于扩展。

添加新的评估角色 (Persona): 要创建一个新的评估角色，只需在 prompts.py 文件中定义一个新的 Prompt 模板，并将其添加到 EVALUATION_PROMPTS 字典中。然后您就可以在 config.yaml 中选择使用这个新角色。

支持更多的服务商: 您可以通过修改 online_evaluator.py 中的 OnlineEvaluator 类来添加对其他在线模型服务商（如 Google Gemini, Anthropic Claude）的支持，主要是处理它们特定的 API 客户端和认证方式。

更改评估维度: 评分维度（如准确性、相关性等）直接定义在 prompts.py 的模板中。您可以直接修改这些模板以适应您的评估需求，ReportGenerator 会动态地适应新的评分列。

📄 许可证
本项目采用 MIT 许可证。详情请参阅 LICENSE 文件。