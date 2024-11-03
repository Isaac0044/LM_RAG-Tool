# LM_RAG-Tool
 financial-insurance

Tool Web
Run：
streamlit run simple.py

---------
upload data Web

BASE

cd C:\Research_Topics\DB_web

- conda activate DB_web_env

終端機：
DB_web_env\Scripts\activate
uvicorn main:app --reload

URL：
127.0.0.1:8000/form
127.0.0.1:8000/Insurance

streamlit run rag_l1.py

Naive RAG and tools used Web
cd combin 
streamlit run combin.py

---

cd Ollama-Chat
streamlit run simple.py
--------------------------------------------
#first create ENVIRONMENT#


cd D:\Research_Topics\LM_RAG-Tool

conda create -n DB_web_env python=3.11

conda activate DB_web_env

pip install fastapi "uvicorn[standard]" jinja2


開啟您的終端機，並在 HelloWorld 專案資料夾內，使用下列命令建立名為 venv 的虛擬環境：python3 -m venv .venv。

若要啟用虛擬環境，請輸入：source .venv/bin/activate。 如果運作正常，您應該會在命令提示字元前面看到 (.venv)。 您現在有一個就緒的獨立式環境，可供您撰寫程式碼及安裝套件。 當您完成虛擬環境時，請輸入下列命令將它停用：deactivate。