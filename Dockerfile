FROM python:3.10-slim
# install system tools
RUN apt-get update && apt-get install -y \
    git wget curl vim \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

# install llm tools
RUN pip install torch torchvision torchaudio \
          	transformers sentencepiece langchain langchain-community langgraph huggingface_hub\
		faiss-cpu ray[default]
# install data processing tools
RUN pip install datasets scikit-learn pandas numpy netcat

# setting workplace
WORKDIR /app
COPY . /app
# run python
CMD ["/bin/sh","-c","bash"]
