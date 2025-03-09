import os
import ray
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from huggingface_hub import login
#import ollama

#login()

# 初始化 Ray
ray.init(address="auto", namespace="default")

@ray.remote
class ModelWorker:
    def __init__(self):
        print("[GPU Worker] Initializing model on MPS...")
        self.tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2-0.5B")
        self.model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2-0.5B").to("mps")
        self.model.config.pad_token_id = self.tokenizer.eos_token_id
        print("[GPU Worker] Model initialized.")
        
    def generate(self, prompt):
        inputs = self.tokenizer(prompt, return_tensors="pt").to("mps")
        outputs = self.model.generate(**inputs)
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)

if __name__== "__main__":
    # 啟動 GPU Worker
    print("[GPU Worker] Starting Ray...")
    worker = ModelWorker.options(name="model_worker").remote()
    print("[GPU Worker] Ready for remote calls.")
    try:
        while True:
            pass
    except KeyboardInterrupt:
            print("Shutting down...")
