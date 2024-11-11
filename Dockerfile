# 使用官方的 Python 映像
FROM python:3.11

# 設置工作目錄
WORKDIR /app
RUN pip install requests
# 將當前目錄的內容複製到容器的 /app 目錄
COPY kong-setup.py .

# 設置容器啟動時運行的命令
CMD ["python", "kong-setup.py"]