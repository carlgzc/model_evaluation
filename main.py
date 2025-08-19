# main.py
# 主程序入口，负责编排整个评估流程
# 升级版：支持循环评估在config.yaml中定义的多个本地模型

import os
import json
import yaml
import pandas as pd
import csv
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

from ollama_runner import OllamaRunner
from online_evaluator import OnlineEvaluator
from report_generator import ReportGenerator
from dotenv import load_dotenv
load_dotenv()

def load_config(config_path='config.yaml'):
    """加载配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def convert_csv_to_jsonl_if_needed(config):
    """检查题库文件，如果是CSV则自动转换为JSONL"""
    question_file = config['paths']['question_bank']
    if not question_file.endswith('.csv'):
        return question_file

    print(f"检测到输入文件为CSV: {question_file}")
    jsonl_path = question_file.replace('.csv', '.jsonl')
    
    try:
        with open(question_file, mode='r', encoding='utf-8') as csv_file, \
             open(jsonl_path, mode='w', encoding='utf-8') as jsonl_file:
            
            csv_reader = csv.DictReader(csv_file)
            required_columns = {'id', 'scenario', 'sub_scenario', 'prompt', 'ideal_output', 'notes_for_evaluation'}
            if not required_columns.issubset(csv_reader.fieldnames):
                raise ValueError(f"CSV文件缺少必要的列。需要: {required_columns}, 实际拥有: {csv_reader.fieldnames}")

            for row in csv_reader:
                json_record = json.dumps({key: row.get(key, "") for key in required_columns}, ensure_ascii=False)
                jsonl_file.write(json_record + '\n')
        
        print(f"成功将CSV转换为JSONL: {jsonl_path}")
        return jsonl_path
    except Exception as e:
        print(f"处理CSV文件时出错: {e}")
        exit(1)


def load_questions(file_path):
    """从jsonl文件加载题库"""
    questions = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            questions.append(json.loads(line))
    return questions

def sanitize_filename(name):
    """清理字符串，使其可以安全地作为文件名的一部分"""
    return re.sub(r'[^a-zA-Z0-9_-]', '_', name)

def evaluate_single_model(ollama_model_config, global_config):
    """
    对单个Ollama模型执行完整的评估流程。
    """
    task_name = sanitize_filename(global_config['evaluation'].get('task_name', 'default_task'))
    ollama_model_name = sanitize_filename(ollama_model_config['model_name'])
    evaluator_model_name = sanitize_filename(global_config['models']['online_evaluator'][global_config['models']['online_evaluator']['provider']]['model_name'])
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 文件夹名称现在包含被评估的小模型名称
    run_name = f"{task_name}_{ollama_model_name}_vs_{evaluator_model_name}_{timestamp}"
    output_dir = os.path.join(global_config['paths']['results_dir'], run_name)
    
    os.makedirs(output_dir, exist_ok=True)
    print(f"结果将保存在: {output_dir}")

    # 实例化运行器和评估器
    ollama_runner = OllamaRunner(ollama_model_config)
    online_evaluator = OnlineEvaluator(global_config['models']['online_evaluator'], global_config['evaluation']['prompt_persona'])
    report_generator = ReportGenerator(output_dir)

    question_jsonl_path = convert_csv_to_jsonl_if_needed(global_config)
    questions = load_questions(question_jsonl_path)
    print(f"成功加载 {len(questions)} 道题目。")

    print("\n--- 步骤 1: 本地小模型正在生成答案... ---")
    tasks_with_answers = []
    for q in tqdm(questions, desc=f"Ollama Generating ({ollama_model_name})"):
        answer = ollama_runner.generate(q['prompt'])
        q_copy = q.copy() # 复制一份以避免在循环中修改原始列表
        q_copy['answer'] = answer
        tasks_with_answers.append(q_copy)
    
    ollama_results_path = os.path.join(output_dir, "ollama_answers.jsonl")
    with open(ollama_results_path, 'w', encoding='utf-8') as f:
        for item in tasks_with_answers:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    print(f"小模型答案已保存至: {ollama_results_path}")

    print("\n--- 步骤 2: 在线大模型正在进行并发评估... ---")
    evaluation_results = []
    max_workers = global_config['evaluation']['max_workers']
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_task = {
            executor.submit(online_evaluator.evaluate_single, task_item): task_item 
            for task_item in tasks_with_answers
        }
        
        for future in tqdm(as_completed(future_to_task), total=len(tasks_with_answers), desc="Online Evaluating"):
            task_item = future_to_task[future]
            try:
                eval_result = future.result()
                if eval_result:
                    scores = eval_result.pop('scores', {})
                    task_item.update(eval_result)
                    task_item.update(scores)
                else:
                    task_item.update({'reason': 'Evaluation failed', 'strengths': 'N/A', 'weaknesses': 'N/A'})
                evaluation_results.append(task_item)
            except Exception as e:
                print(f"评估题目 {task_item['id']} 时主循环捕获到意外出错: {e}")
                task_item.update({'reason': str(e), 'strengths': 'Error', 'weaknesses': 'Error'})
                evaluation_results.append(task_item)

    try:
        evaluation_results.sort(key=lambda x: int(re.search(r'\d+', str(x.get('id', '0'))).group()))
    except (ValueError, AttributeError):
        print("警告：无法根据ID中的数字进行排序，将按原始顺序处理。")
    
    eval_results_path = os.path.join(output_dir, "evaluation_details.jsonl")
    with open(eval_results_path, 'w', encoding='utf-8') as f:
        for item in evaluation_results:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    print(f"详细评估结果已保存至: {eval_results_path}")

    print("\n--- 步骤 3: 在线大模型正在生成总结报告... ---")
    summary = online_evaluator.generate_summary(evaluation_results)
    
    print("\n--- 步骤 4: 正在生成Markdown报告... ---")
    # 创建一个临时config副本，用于报告中正确显示当前被评估的模型名称
    report_config = global_config.copy()
    report_config['models']['ollama'] = ollama_model_config
    report_generator.generate_markdown_report(evaluation_results, summary, report_config)
    print(f"Markdown评估报告已生成。")
    print(f"\n模型 {ollama_model_name} 的评估流程完成！")

def main():
    """主函数，加载配置并循环评估所有指定的模型"""
    config = load_config()
    
    ollama_models_to_test = config.get('models', {}).get('ollama_models', [])
    if not ollama_models_to_test:
        print("错误：在 config.yaml 中没有找到要评估的Ollama模型 (models.ollama_models)。")
        return

    print(f"检测到 {len(ollama_models_to_test)} 个本地模型待评估。")

    for model_config in ollama_models_to_test:
        print(f"\n{'='*25} 开始评估模型: {model_config['model_name']} {'='*25}\n")
        evaluate_single_model(model_config, config)

    print(f"\n{'='*30} 所有评估任务均已完成 {'='*30}")


if __name__ == "__main__":
    main()