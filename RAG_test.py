import os
import subprocess
import re

# 設定 PYTHONIOENCODING 環境變數為 utf-8
os.environ["PYTHONIOENCODING"] = "utf-8"

# 查詢文字變數
query_text = "資訊站放置地點"

# 執行命令並捕捉輸出
result = subprocess.run(
    [
        "python", "-m", "graphrag.query",
        "--root", "./ragtest",
        "--method", "global",
        query_text
    ],
    capture_output=True,
    text=True,
    encoding="utf-8"  # 強制以 UTF-8 解碼
)

# 檢查執行是否成功
if result.returncode == 0:
    # 搜尋 "SUCCESS: Global Search Response:" 後的內容
    response_match = re.search(r"SUCCESS: Global Search Response:\n(.+)", result.stdout, re.DOTALL)
    if response_match:
        # 提取並儲存到變數 response_text 中
        response_text = f"根據您的資料查詢結果：({response_match.group(1).strip()})"
        print("成功接收回應：")
        print(response_text)
    else:
        print("未找到成功回應的特定內容。")
else:
    print("執行失敗，錯誤訊息如下：")
    print(result.stderr)
