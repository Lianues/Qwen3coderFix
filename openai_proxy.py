import requests
import json
from flask import Flask, request, Response, stream_with_context

# --- 配置 ---
# 目标API的URL
TARGET_URL = "https://api.gmi-serving.com/v1/chat/completions"
# 本地代理服务器监听的端口
LISTEN_PORT = 5106
# ----------------

app = Flask(__name__)

def modify_chunk(chunk_data):
    """
    核心修改逻辑：将 'reasoning_content' 的值移动到 'content'。
    适用于流式和非流式响应。
    """
    if not isinstance(chunk_data, dict):
        return chunk_data

    if 'choices' in chunk_data and chunk_data['choices']:
        choice = chunk_data['choices'][0]
        
        # 处理流式响应块 (delta)
        if 'delta' in choice and choice.get('delta'):
            delta = choice['delta']
            if 'reasoning_content' in delta and delta['reasoning_content'] is not None:
                # 将 reasoning_content 的值赋给 content
                delta['content'] = delta['reasoning_content']
                # 将原来的键设置为 null
                delta['reasoning_content'] = None

        # 处理非流式响应 (message)
        if 'message' in choice and choice.get('message'):
            message = choice['message']
            if 'reasoning_content' in message and message['reasoning_content'] is not None:
                message['content'] = message['reasoning_content']
                message['reasoning_content'] = None
                
    return chunk_data

@app.route('/v1/chat/completions', methods=['POST'])
def proxy_request():
    """
    接收客户端请求，转发到目标URL，修改响应后返回。
    """
    print("\n--- [1] Request Received ---")
    # 获取客户端的请求体
    client_data = request.get_json()
    is_stream = client_data.get("stream", False)

    # 准备转发的请求头，主要是透传Authorization
    headers = {
        "Authorization": request.headers.get("Authorization"),
        "Content-Type": "application/json",
    }

    # 使用 stream=True 发送请求，以便处理流式响应
    try:
        print(f"--- [2] Forwarding request to {TARGET_URL} for model: {client_data.get('model')} ---")
        upstream_response = requests.post(
            TARGET_URL,
            headers=headers,
            json=client_data,
            stream=True  # 始终使用流式请求以便统一处理
        )
        upstream_response.raise_for_status()
        print("--- [3] Upstream response received successfully ---")
    except requests.exceptions.RequestException as e:
        print(f"--- [!] Error forwarding request: {e} ---")
        return Response(f"Error forwarding request: {e}", status=502)

    # 根据客户端请求的是否为流式，决定如何返回响应
    if is_stream:
        def generate_stream():
            """
            生成器函数，用于处理流式响应。
            """
            for line in upstream_response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        json_str = line_str[len('data: '):]
                        if json_str.strip() == '[DONE]':
                            yield line_str + '\n\n'
                            break
                        try:
                            chunk = json.loads(json_str)
                            modified_chunk = modify_chunk(chunk)
                            modified_line = f"data: {json.dumps(modified_chunk, ensure_ascii=False)}\n\n"
                            yield modified_line
                        except json.JSONDecodeError:
                            yield line_str + '\n\n' # 如果解析失败，返回原始行
                    else:
                        yield line_str + '\n\n'
        
        # 使用Flask的stream_with_context返回流式响应
        print("--- [4] Sending stream response to client ---")
        return Response(stream_with_context(generate_stream()), mimetype='text/event-stream')
    else:
        # 处理非流式响应
        try:
            response_data = upstream_response.json()
            modified_data = modify_chunk(response_data)
            print("--- [4] Sending non-stream response to client ---")
            return Response(json.dumps(modified_data, ensure_ascii=False),
                            status=upstream_response.status_code,
                            mimetype='application/json')
        except json.JSONDecodeError as e:
            return Response(f"Error decoding upstream JSON: {e}", status=502)


@app.route('/v1/models', methods=['GET'])
def proxy_models():
    """
    转发对 /v1/models 的GET请求。
    这个接口通常不需要修改响应体。
    """
    print("\n--- [MODELS] Request Received ---")
    headers = {
        "Authorization": request.headers.get("Authorization"),
    }
    try:
        print(f"--- [MODELS] Forwarding request to {TARGET_URL.replace('chat/completions', 'models')} ---")
        upstream_response = requests.get(
            TARGET_URL.replace('chat/completions', 'models'),
            headers=headers
        )
        upstream_response.raise_for_status()
        print("--- [MODELS] Upstream response received successfully ---")
        
        # 直接返回上游的响应
        return Response(upstream_response.content,
                        status=upstream_response.status_code,
                        mimetype=upstream_response.headers.get('Content-Type'))
                        
    except requests.exceptions.RequestException as e:
        print(f"--- [!] Error forwarding models request: {e} ---")
        return Response(f"Error forwarding models request: {e}", status=502)


if __name__ == '__main__':
    from waitress import serve
    print(f"OpenAI proxy server starting on http://127.0.0.1:{LISTEN_PORT}")
    print(f"Forwarding requests to: {TARGET_URL}")
    # 需要安装: pip install Flask requests waitress
    serve(app, host='127.0.0.1', port=LISTEN_PORT)
