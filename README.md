# Qwen3 Coder API 格式修正代理 (OpenAI 兼容)

本项目是一个轻量级的Python代理服务器，其核心目的是修正 **Qwen3 Coder** 模型API的非标准响应格式，使其完全兼容标准的OpenAI API格式。

许多客户端工具是为标准OpenAI API设计的，无法直接处理Qwen3 Coder API将内容输出在 `reasoning_content` 字段中的情况。本代理通过拦截并修改响应，解决了这个问题。

## 核心修正逻辑

- **监听本地端口**：在 `http://127.0.0.1:5106` 上启动一个HTTP服务器。
- **转发API请求**：
  - 将 `/v1/chat/completions` (POST) 请求转发到上游的Qwen3 Coder API服务 (`https://api.gmi-serving.com/v1/chat/completions`)。
  - 将 `/v1/models` (GET) 请求也进行转发。
- **修正响应格式**：对于 `/v1/chat/completions` 的响应（包括流式和非流式），本代理会：
  1.  将 `reasoning_content` 字段中的内容**移动**到标准的 `content` 字段。
  2.  将 `reasoning_content` 字段的值设置为 `null`。
- **生产级服务**：使用 `waitress` 作为WSGI服务器，稳定可靠。

## 安装

1.  克隆或下载本项目。
2.  安装所需的Python库：
    ```bash
    pip install -r requirements.txt
    ```

## 使用方法

1.  运行代理服务器：
    ```bash
    python openai_proxy.py
    ```
    服务器启动后，你将看到如下输出：
    ```
    OpenAI proxy server starting on http://127.0.0.1:5106
    Forwarding requests to: https://api.gmi-serving.com/v1/chat/completions
    ```

2.  **配置你的客户端**：
    将你的本地应用或API测试工具的 **API基地址 (Base URL)** 指向该代理服务器：
    
    **`http://127.0.0.1:5106`**

    **注意**：请确保使用 `http://` 而不是 `https://`。

3.  现在，你的客户端就可以无缝地与Qwen3 Coder API进行交互，如同它是一个标准的OpenAI服务。代理服务器会自动完成所有的格式修正工作。
