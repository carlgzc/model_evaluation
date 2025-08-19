# report_generator.py
# 升级版：在报告中展示更丰富的上下文信息

import os
import json
import pandas as pd
from datetime import datetime

class ReportGenerator:
    def __init__(self, output_dir):
        self.output_dir = output_dir

    def _calculate_stats(self, df):
        """计算多维度统计数据"""
        stats = {'total_questions': len(df)}
        
        # 动态找出所有评分维度列
        score_columns = [col for col in df.columns if col not in ['id', 'scenario', 'sub_scenario', 'prompt', 'ideal_output', 'notes_for_evaluation', 'answer', 'reason', 'strengths', 'weaknesses']]
        
        if not score_columns:
            return stats # 如果没有评分列，直接返回

        for col in score_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        valid_df = df.dropna(subset=score_columns, how='all')
        stats['evaluated_questions'] = len(valid_df)

        if len(valid_df) == 0:
            return stats

        avg_scores = valid_df[score_columns].mean().to_dict()
        stats['avg_scores'] = avg_scores
        
        scenario_avg_scores = valid_df.groupby('scenario')[score_columns].mean().to_dict('index')
        stats['scenario_avg_scores'] = {k: {dim: round(score, 2) for dim, score in v.items()} for k, v in scenario_avg_scores.items()}

        return stats

    def generate_markdown_report(self, evaluation_results, summary, config):
        """生成包含多维度评分和丰富上下文的主评估报告"""
        df = pd.DataFrame(evaluation_results)
        stats = self._calculate_stats(df.copy())

        report_path = os.path.join(self.output_dir, "evaluation_report.md")
        summary_path = os.path.join(self.output_dir, "summary.md")

        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary)

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"# LLM评估报告\n\n")
            f.write(f"**评估时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**被评估模型:** `{config['models']['ollama']['model_name']}`\n")
            f.write(f"**评估角色:** `{config['evaluation']['prompt_persona']}`\n\n")
            
            f.write("## 1. 整体评估总结\n\n")
            f.write(summary)
            f.write("\n\n")

            f.write("## 2. 核心指标统计\n\n")
            if 'avg_scores' in stats:
                f.write("### 各维度平均分 (Overall)\n\n")
                f.write("| " + " | ".join(stats['avg_scores'].keys()) + " |\n")
                f.write("|" + ":---:|" * len(stats['avg_scores']) + "\n")
                f.write("| " + " | ".join([f"{score:.2f}" for score in stats['avg_scores'].values()]) + " |\n\n")

            if 'scenario_avg_scores' in stats:
                f.write("### 各场景 & 各维度平均分\n\n")
                scenarios = list(stats['scenario_avg_scores'].keys())
                dims = list(stats.get('avg_scores', {}).keys())
                if dims:
                    f.write("| 场景 | " + " | ".join(dims) + " |\n")
                    f.write("|:---|"+ ":---:|" * len(dims) + "\n")
                    for scenario in scenarios:
                        scores = [f"{stats['scenario_avg_scores'][scenario].get(dim, 0):.2f}" for dim in dims]
                        f.write(f"| {scenario} | " + " | ".join(scores) + " |\n")
                    f.write("\n")

            f.write("## 3. 逐题评估详情\n\n")
            score_columns = [col for col in df.columns if col not in ['id', 'scenario', 'sub_scenario', 'prompt', 'ideal_output', 'notes_for_evaluation', 'answer', 'reason', 'strengths', 'weaknesses']]
            for _, row in df.iterrows():
                scores_str = " | ".join([f"**{col.capitalize()}:** {row.get(col, 'N/A')}" for col in score_columns])
                f.write(f"### 题目 ID: {row['id']} | 场景: {row['scenario']} / {row['sub_scenario']}\n\n")
                f.write(f"**得分详情:** {scores_str}\n\n")
                f.write(f"**问题 (Prompt):**\n```\n{row.get('prompt', 'N/A')}\n```\n\n")
                f.write(f"**模型回答:**\n```\n{row.get('answer', 'N/A')}\n```\n\n")
                f.write(f"**理想答案参考:**\n```\n{row.get('ideal_output', 'N/A')}\n```\n\n")
                f.write(f"**评估要点:**\n```\n{row.get('notes_for_evaluation', 'N/A')}\n```\n\n")
                f.write(f"**评分理由:**\n{row.get('reason', 'N/A')}\n\n")
                f.write(f"**优点:**\n{row.get('strengths', 'N/A')}\n\n")
                f.write(f"**缺点:**\n{row.get('weaknesses', 'N/A')}\n\n")
                f.write("---\n\n")
