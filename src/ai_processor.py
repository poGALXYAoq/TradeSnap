import ollama
import base64
from src.ai_prompts import get_hk_stock_prompt, get_futures_prompt
from src.parsers import parse_ai_json

def process_image(image_bytes, mode='hk_stock'):
    """
    使用 Ollama 识别图片内容
    mode: 'hk_stock' 或 'futures'
    """
    # 将图片转为 base64
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    
    if mode == 'hk_stock':
        messages = get_hk_stock_prompt(base64_image)
    else:
        messages = get_futures_prompt(base64_image)
    
    try:
        # 调用 Ollama (模型使用 qwen3-vl:8b，根据 README)
        response = ollama.chat(
            model='qwen3-vl:8b', 
            messages=messages
        )
        json_str = response['message']['content']
        # 移除可能存在的 markdown 标记
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()
            
        return parse_ai_json(json_str)
    except Exception as e:
        print(f"AI Recognition Error: {e}")
        return []

