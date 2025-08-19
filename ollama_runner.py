# ollama_runner.py
# 负责与本地Ollama模型进行交互

import requests
import json

class OllamaRunner:
    def __init__(self, config):
        self.base_url = config.get('base_url', 'http://localhost:11434').strip()
        self.model = config['model_name']
        self.options = config.get('options', {})

    def generate(self, prompt):
        """
        向Ollama发送请求并获取模型的回答
        """
        # --- 新增日志 ---
        print("\n" + "="*20 + " Ollama Input " + "="*20)
        print(f"Model: {self.model}")
        print(f"Prompt:\n---\n{prompt}\n---")
        # ---------------

        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": self.options,
            "think": False
        }
        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            response_data = response.json()
            answer = response_data.get('response', '').strip()

            # --- 新增日志 ---
            print("\n" + "="*20 + " Ollama Output " + "="*20)
            print(f"Response:\n---\n{answer}\n---")
            print("="*55 + "\n")
            # ---------------

            return answer
        except requests.exceptions.RequestException as e:
            print(f"调用Ollama API时出错: {e}")
            return f"Error: Could not get response from Ollama. Details: {e}"
