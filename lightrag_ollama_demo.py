import os
import logging
from lightrag import LightRAG, QueryParam
from lightrag.llm import ollama_model_complete, ollama_embedding
from lightrag.utils import EmbeddingFunc


from opencc import OpenCC
import ollama
import streamlit as st
import time
import os
from datetime import datetime
import asyncio

cc = OpenCC('s2twp')

model = "qwen2.5:14b"


WORKING_DIR = "./dickens"

logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)

if not os.path.exists(WORKING_DIR):
    os.mkdir(WORKING_DIR)

rag = LightRAG(
    working_dir=WORKING_DIR,
    llm_model_func=ollama_model_complete,
    llm_model_name="qwen2.5:latest",
    llm_model_max_async=4,
    llm_model_max_token_size=32768,
    llm_model_kwargs={"host": "http://localhost:11434", "options": {"num_ctx": 32768}},
    embedding_func=EmbeddingFunc(
        embedding_dim=768,
        max_token_size=8192,
        func=lambda texts: ollama_embedding(
            texts, embed_model="nomic-embed-text", host="http://localhost:11434"
        ),
    ),
)

with open("./files/stock_output.txt", "r", encoding="utf-8") as stock_file, \
     open("./files/insurance_list_01.txt", "r", encoding="utf-8") as insurance_file:
    rag.insert(stock_file.read())
    rag.insert(insurance_file.read())





question = "我前陣子骨折了保險理賠嗎?"
# Perform naive search


print("---------------------------naive---------------------------")
naive = rag.query(question, param=QueryParam(mode="naive"))
print(naive)
api_message = f"你覺得此問題回答是否足夠完整且切合問題'是'的話請回傳True否則回傳False。(只能回傳True或False)     |    問題:{question}           |回答:{naive}"
response_1 = ''
i =0
while response_1 != 'True' or 'False':
    response_1 = ollama.chat(model=model, messages=[
                {
                    'role': 'user',
                    'content': api_message,
                }
            ])

    i += 1
    print(f"response_1  ({i}):",response_1)
print("---------------------------local---------------------------")

# Perform local search
local = rag.query(question, param=QueryParam(mode="local"))
print(local)
api_message = f"你覺得此問題回答是否足夠完整且切合問題'是'的話請回傳True否則回傳False。(只能回傳True或False)     |    問題:{question}           |回答:{local}"
response_2 = ''
i =0
while response_2 != 'True' or 'False':
    response_2 = ollama.chat(model=model, messages=[
                {
                    'role': 'user',
                    'content': api_message,
                }
            ])

    i += 1
    print(f"response_2  ({i}):",response_2)

print("---------------------------global---------------------------")

# Perform global search
global_sc =  rag.query(question, param=QueryParam(mode="global"))
print(global_sc)
api_message = f"你覺得此問題回答是否足夠完整且切合問題'是'的話請回傳True否則回傳False。(只能回傳True或False)     |    問題:{question}           |回答:{global_sc}"
response_3 = ''
i =0
while response_3 != 'True' or 'False':
    response_3 = ollama.chat(model=model, messages=[
                {
                    'role': 'user',
                    'content': api_message,
                }
            ])

    i += 1
    print(f"response_3  ({i}):",response_3)

print("---------------------------hybrid---------------------------")

# Perform hybrid search
hybrid = rag.query(question, param=QueryParam(mode="hybrid"))
print(hybrid)

api_message = f"你覺得此問題回答是否足夠完整且切合問題'是'的話請回傳True否則回傳False。(只能回傳True或False)     |    問題:{question}           |回答:{hybrid}"
response_3 = ''
i =0
while response_4 != 'True' or 'False':
    response_4 = ollama.chat(model=model, messages=[
                {
                    'role': 'user',
                    'content': api_message,
                }
            ])

    i += 1
    print(f"response_4  ({i}):",response_4)
