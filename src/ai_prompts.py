"""
此模块存放用于 Ollama 视觉模型的 System Prompts。
"""

# 通用视觉识别 Prompt 模板
OCR_SYSTEM_PROMPT = """
你是一个专业的金融数据录入员。你的任务是将交易软件的截图转换为结构化的 JSON 数据。
请严格遵守以下规则：

1. **专注数据**：忽略截图中的广告、时间栏、手机电量等无关信息，只提取表格中的交易记录。
2. **输出格式**：只输出纯 JSON 字符串，不要包含 Markdown 标记（如 ```json），不要包含任何解释性文字。
3. **字段定义**：
   - time: 成交时间 (字符串，格式 HH:MM:SS)
   - name: 证券名称
   - code: 证券代码 (如果是港股，通常是数字；如果是期货，如 HSI/NQ)
   - side: 交易方向 (严格映射为: "BUY" 或 "SELL"。如果图中有"买入/开仓"则为BUY，"卖出/平仓"则为SELL)
   - qty: 成交数量 (数字类型)
   - price: 成交价格 (数字类型)
   - fee: 手续费 (数字类型，如果没有则为 0)
4. **异常处理**：
   - 如果图片模糊无法识别，返回空列表 []。
   - 注意区分数字 '0' 和字母 'O'。
"""

def get_hk_stock_prompt(base64_image):
    """
    生成用于识别港股截图的消息体
    """
    user_content = "请分析这张港股证券订单流截图。提取每一行交易记录。注意：港股代码通常为5位数字，如 00700。如果有多行记录，请全部提取。"
    
    return [
        {'role': 'system', 'content': OCR_SYSTEM_PROMPT},
        {
            'role': 'user',
            'content': user_content,
            'images': [base64_image]
        }
    ]

def get_futures_prompt(base64_image):
    """
    生成用于识别期货截图的消息体
    """
    user_content = "请分析这张期货交易截图。提取每一行记录。注意：期货代码可能是英文（如 NQ, HSI, GC）。请特别注意区分'开仓'和'平仓'，并在 side 字段中反映（买入开仓/卖出平仓 -> BUY, 卖出开仓/买入平仓 -> SELL，或者根据具体的净方向判断）。"
    
    return [
        {'role': 'system', 'content': OCR_SYSTEM_PROMPT},
        {
            'role': 'user',
            'content': user_content,
            'images': [base64_image]
        }
    ]