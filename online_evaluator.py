# online_evaluator.py
# 升级版：从config读取temperature，修复API调用错误

import os
import json
import traceback
from openai import OpenAI
from prompts import EVALUATION_PROMPTS, SUMMARY_PROMPT

class OnlineEvaluator:
    def __init__(self, config, persona='default'):
        provider = config.get('provider', 'bytedance')
        provider_config = config.get(provider)

        if not provider_config:
            raise ValueError(f"评估服务商 '{provider}' 的配置不存在于 config.yaml 中。")
        
        print(f"Initializing evaluator with provider: {provider}")

        self.client = OpenAI(
            base_url=provider_config.get('base_url'),
            api_key=os.environ.get(provider_config['api_key_env']),
            timeout=120.0
        )
        self.model = provider_config['model_name']
        
        # --- MODIFIED: Read temperature from config ---
        self.evaluation_temperature = provider_config.get('evaluation_temperature', 0.0)
        self.summary_temperature = provider_config.get('summary_temperature', 0.5)
        print(f"Using temperature {self.evaluation_temperature} for evaluation and {self.summary_temperature} for summary.")
        # ---------------------------------------------
        
        if persona not in EVALUATION_PROMPTS:
            raise ValueError(f"评估角色 '{persona}' 不存在于 prompts.py 中。")
        self.evaluation_prompt_template = EVALUATION_PROMPTS[persona]
        
        self.summary_prompt_template = SUMMARY_PROMPT

    def _parse_evaluation_response(self, response_text):
        try:
            if '```json' in response_text:
                json_str = response_text.split('```json')[1].split('```')[0].strip()
            else:
                json_str = response_text
            data = json.loads(json_str)
            if not isinstance(data, dict):
                raise json.JSONDecodeError("Data is not a dictionary", json_str, 0)
            
            if 'scores' not in data or not isinstance(data['scores'], dict):
                 raise ValueError("解析JSON失败：缺少 'scores' 字典或格式不正确。")

            return {
                'scores': data.get('scores', {}),
                'reason': data.get('reason', 'No reason provided.'),
                'strengths': data.get('strengths', 'No strengths provided.'),
                'weaknesses': data.get('weaknesses', 'No weaknesses provided.')
            }
        except (json.JSONDecodeError, ValueError, IndexError) as e:
            print(f"解析评估JSON失败: {e}")
            return None
        except Exception as e:
            print(f"在解析过程中发生未知错误: {e}")
            return None

    def evaluate_single(self, task_item):
        """
        评估单个任务，并打印输入输出日志。
        """
        try:
            prompt_payload = {
                "scenario": task_item.get("scenario", ""),
                "sub_scenario": task_item.get("sub_scenario", ""),
                "prompt": task_item.get("prompt", ""),
                "answer": task_item.get("answer", ""),
                "ideal_output": task_item.get("ideal_output", ""),
                "notes_for_evaluation": task_item.get("notes_for_evaluation", "")
            }
            prompt = self.evaluation_prompt_template.format(**prompt_payload)
            
            print("\n" + "#"*20 + f" Evaluator Input (ID: {task_item.get('id')}) " + "#"*20)
            print(f"Model: {self.model}")
            print(f"Full Prompt:\n---\n{prompt}\n---")

            response = self.client.chat.completions.create(
                model=self.model, 
                messages=[{"role": "user", "content": prompt}], 
                # --- MODIFIED: Use temperature from config ---
                temperature=self.evaluation_temperature,
                # ---------------------------------------------
            )
            response_text = response.choices[0].message.content

            print("\n" + "#"*20 + f" Evaluator Output (ID: {task_item.get('id')}) " + "#"*20)
            print(f"Raw Response:\n---\n{response_text}\n---")
            print("#"*65 + "\n")

            return self._parse_evaluation_response(response_text)
        except Exception as e:
            print(f"\n[错误] 调用在线评估API时发生错误 (ID: {task_item.get('id')}): {e}")
            traceback.print_exc()
            return None

    def generate_summary(self, evaluation_results):
        results_str = ""
        # Dynamically find score columns from the first result if available
        if evaluation_results:
            score_columns = set(evaluation_results[0].keys()) - {'id', 'scenario', 'sub_scenario', 'prompt', 'ideal_output', 'notes_for_evaluation', 'answer', 'reason', 'strengths', 'weaknesses'}
        else:
            score_columns = set()

        for res in evaluation_results:
            scores_str = ", ".join([f"{key}: {res.get(key, 'N/A')}" for key in sorted(list(score_columns))])
            results_str += (f"题目ID: {res['id']}\n业务场景: {res['scenario']}/{res['sub_scenario']}\n问题: {res['prompt']}\n小模型回答: {res['answer']}\n得分详情: {scores_str}\n评分理由: {res.get('reason', 'N/A')}\n---\n")
        
        prompt = self.summary_prompt_template.format(evaluation_results=results_str)
        try:
            response = self.client.chat.completions.create(
                model=self.model, 
                messages=[{"role": "user", "content": prompt}], 
                # --- MODIFIED: Use temperature from config ---
                temperature=self.summary_temperature
                # ---------------------------------------------
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"生成总结报告时出错: {e}")
            return f"Error generating summary: {e}"