# OpenAI 响应格式转换代理

本项目是一个轻量级的Python代理服务器，用于拦截发往OpenAI兼容API的请求，修改其响应格式后，再返回给客户端。

## 功能

- **监听本地端口**：在 `http://127.0.0.1:5106` 上启动一个HTTP服务器。
- **转发API请求**：
  - 将 `/v1/chat/completions` (POST) 请求转发到 `https://api.gmi-serving.com/v1/chat/completions`。
  - 将 `/v1/models` (GET) 请求转发到 `https://api.gmi-serving.com/v1/models`。
- **修改响应体**：对于 `/v1/chat/completions` 的响应，脚本会将 `choices[0].delta.reasoning_content` 或 `choices[0].message.reasoning_content` 的值移动到 `content` 字段，并将 `reasoning_content` 字段设置为 `null`。
- **支持流式与非流式**：能够正确处理并修改这两种响应模式。
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

3.  现在，你的客户端就可以像直接请求OpenAI API一样，向本地代理发送请求了。代理服务器会自动完成转发、修改和返回响应的全过程。
