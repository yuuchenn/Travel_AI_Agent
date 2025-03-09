FROM python:3.10-slim
WORKDIR /app
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl 
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cpu
COPY . /app
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
CMD ["/bin/sh","-c","bash"]
