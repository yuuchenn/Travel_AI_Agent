# TravelAgent

## 1. 啟動ray server
ray start --head --port=6379

## 2. 將LLM模型部署到ray，讓docker 可以使用本機gpu運行模型
python gpu_worker.py

## 3. 透過docker，運行Agent主程式
### Docker dev
- Dockerfile : travel_agent
- Docker-compose.yml 

### Agent 主程式
Main.py



-----
參考資料：
- https://langchain-ai.github.io/langgraph/tutorials/customer-support/customer-support/
- https://github.com/langchain-ai/langgraph/blob/main/docs/docs/tutorials/multi_agent/multi-agent-collaboration.ipynb
