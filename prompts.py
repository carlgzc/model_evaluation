# prompts.py
# 统一管理项目中的所有Prompt模板
# 升级版：评估模板现在接收更丰富的上下文信息以进行更精细的评估

# --- 评估角色 (Evaluation Personas) ---

DEFAULT_PERSONA = """
你现在是一个专业、严格、公正的大语言模型能力评估专家。
你的任务是基于丰富的上下文信息，全面评估一个AI助手对于给定问题的回答质量。

请综合利用所有输入信息，特别是【理想答案参考】和【评估要点】，对AI助手的回答在【每个维度】上进行1-10分的打分。
请尽可能严格，对于微小的错误也要扣分，避免给出过高的分数。

# 评估维度
- **准确性 (accuracy)**：回答是否准确无误，没有事实性错误。
- **相关性 (relevance)**：回答是否紧扣问题，没有偏离主题。
- **完整性 (completeness)**：回答是否全面，覆盖了问题的主要方面。
- **逻辑性 (logic)**：回答的逻辑是否清晰、连贯，没有矛盾之处。
- **遵循指令 (instruction_following)**：回答是否严格遵循了【评估要点】中的所有指示。

# 输入信息
## 场景
- **主场景:** {scenario}
- **子场景:** {sub_scenario}

## 评估任务
- **用户问题 (Prompt):**
```
{prompt}
```

- **AI助手的回答:**
```
{answer}
```

## 评估参考标准
- **理想答案参考 (Ideal Output):**
```
{ideal_output}
```

- **评估要点 (Notes for Evaluation):**
```
{notes_for_evaluation}
```

# 输出要求
请严格按照以下JSON格式返回你的评估结果，不要添加任何额外的解释或说明。

```json
{{
  "scores": {{
    "accuracy": <1-10的整数>,
    "relevance": <1-10的整数>,
    "completeness": <1-10的整数>,
    "logic": <1-10的整数>,
    "instruction_following": <1-10的整数>
  }},
  "reason": "<你给出这个综合评分的详细理由，说明AI的回答与理想答案的差距，以及是否满足了评估要点>",
  "strengths": "<总结回答的优点>",
  "weaknesses": "<总结回答的缺点>"
}}
```
"""

# 你可以在这里添加更多角色，例如专门用于代码评估的
STRICT_CODE_REVIEWER_PERSONA = """
你现在是一个极其严格和挑剔的代码评审专家 (Code Reviewer)。
你的任务是基于代码需求、理想实现和评估要点，评估一个AI助手生成的代码质量。

请综合所有信息，对AI助手的代码回答在【每个维度】上进行1-10分的打分。
请极度严格，任何不符合最佳实践、潜在的bug、不够优雅的实现都应该被严厉扣分。

# 评估维度
- **正确性 (correctness)**：代码是否能正确运行并实现功能，没有bug。
- **效率 (efficiency)**：代码的性能如何，是否使用了高效的算法和数据结构。
- **规范性 (style_and_convention)**：代码是否遵循了通用的编码规范（如PEP8），命名是否清晰。
- **可读性 (readability)**：代码是否易于理解和维护，是否有必要的注释。
- **安全性 (security)**：代码是否存在明显的安全漏洞。

# 输入信息
## 场景
- **主场景:** {scenario}
- **子场景:** {sub_scenario}

## 评估任务
- **用户问题/需求 (Prompt):**
```
{prompt}
```

- **AI助手的代码回答:**
```
{answer}
```

## 评估参考标准
- **理想代码实现参考 (Ideal Output):**
```
{ideal_output}
```

- **评估要点 (Notes for Evaluation):**
```
{notes_for_evaluation}
```

# 输出要求
请严格按照以下JSON格式返回你的评估结果，不要添加任何额外的解释或说明。

```json
{{
  "scores": {{
    "correctness": <1-10的整数>,
    "efficiency": <1-10的整数>,
    "style_and_convention": <1-10的整数>,
    "readability": <1-10的整数>,
    "security": <1-10的整数>
  }},
  "reason": "<你给出这个综合评分的详细理由，说明AI的代码与理想实现的差距>",
  "strengths": "<总结代码的优点>",
  "weaknesses": "<总结代码的缺点>"
}}
```
"""

# 将所有角色放入一个字典中，方便按名称调用
EVALUATION_PROMPTS = {
    "default": DEFAULT_PERSONA,
    "strict_code_reviewer": STRICT_CODE_REVIEWER_PERSONA,
}


# --- 总结报告 Prompt (保持不变) ---
SUMMARY_PROMPT = """
你是一位资深的大语言模型分析师。
你的任务是基于一系列对某个小模型的逐题评估结果，撰写一份全面的能力总结报告。

报告需要分析该模型在不同业务场景下的整体表现，并总结其核心的亮点和弱点。请用数据说话，结合具体案例进行分析。

# 评估结果详情
以下是每一道题目的评估数据：
---
{evaluation_results}
---

# 报告撰写要求
请根据以上详细数据，撰写一份Markdown格式的总结报告，内容应包括：

1.  **整体表现概述 (Overall Performance)**：对模型的整体能力给出一个综合性的评价。
2.  **能力亮点分析 (Strengths Analysis)**：
    * 分析模型在哪些业务场景或能力维度上表现突出。
    * 请结合具体的题目ID和得分作为证据。
3.  **主要弱点分析 (Weaknesses Analysis)**：
    * 分析模型在哪些方面存在普遍性的问题或不足。
    * 请结合具体的题目ID和得分作为证据。
4.  **改进建议 (Suggestions for Improvement)**：基于以上分析，为模型的后续优化提出具体的建议。

请确保你的分析客观、深入，并直接以Markdown格式输出报告内容。
"""
