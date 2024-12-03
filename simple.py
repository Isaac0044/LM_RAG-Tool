from opencc import OpenCC
import ollama
import streamlit as st
import time
import os
from datetime import datetime
import asyncio

import os
import logging
from lightrag import LightRAG, QueryParam
from lightrag.llm import ollama_model_complete, ollama_embedding
from lightrag.utils import EmbeddingFunc

cc = OpenCC('s2twp')

models = "qwen2.5" 
rag_model = "jcai/breeze-7b-32k-instruct-v1_0:f16"
# rag_model = "ycchen/breeze-7b-instruct-v1_0:latest"
# 工具調用功能------------

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd


def query_naive(rag, message, mp):
    """執行 naive 模式查詢，回傳結果或空字串"""
    try:
        result = rag.query(message + mp, param=QueryParam(mode="naive"))
        return result
    except Exception:
        return ""

def query_local(rag, message, mp):
    """執行 local 模式查詢，回傳結果或空字串"""
    try:
        result = rag.query(message + mp, param=QueryParam(mode="local"))
        return result
    except Exception:
        return ""

def query_global(rag, message, mp):
    """執行 global 模式查詢，回傳結果或空字串"""
    try:
        result = rag.query(message + mp, param=QueryParam(mode="global"))
        return result
    except Exception:
        return ""

def query_hybrid(rag, message, mp):
    """執行 hybrid 模式查詢，回傳結果或空字串"""
    try:
        result = rag.query(message + mp, param=QueryParam(mode="hybrid"))
        return result
    except Exception:
        return ""

from stock_tool import yahoo_get_stock,goodinfo_stock_price,convert_stock
def get_stock_price(stock: str):
    try:
        stock = convert_stock(stock)
        print(convert_stock(stock))  # 輸出: 大立光
        print(type(convert_stock(stock)))  # 輸出: "3008"
    except ValueError as e:
        print(e)
        return f"爬取{stock}股票失敗請確認輸入的股票名稱或股票代號是否正確"
    
    stock_list = []
    try:
        stock_list = goodinfo_stock_price(stock)
        print("--採用goodinfo_stock_price方案--")
    except:
        stock_list = yahoo_get_stock(stock)
        print("--採用yahoo_get_stock方案--")


    return str(stock_list)

# ------------------------

import time

WORKING_DIR = "./dickens"

logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)

if not os.path.exists(WORKING_DIR):
    os.mkdir(WORKING_DIR)

rag = LightRAG(
    working_dir=WORKING_DIR,
    llm_model_func=ollama_model_complete,
    llm_model_name=rag_model,
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

with open("./files/stock/stock.txt", "r", encoding="utf-8") as stock_file, \
    open("./files/insurance_export.txt", "r", encoding="utf-8") as insurance_file:
    rag.insert(stock_file.read())
    print("stock_file ==>",stock_file.read())
    rag.insert(insurance_file.read())
    print("insurance_file ==>",insurance_file.read())


def response_generator(msg_content):
    if not msg_content:  # Check if msg_content is None or empty
        yield "No content provided.\n"
        return

    lines = msg_content.split('\n')  # Split the content into lines to preserve paragraph breaks.
    for line in lines:
        words = line.split()  # Split the line into words to introduce a delay for each word.
        for word in words:
            yield word + " "
            time.sleep(0.1)
        yield "\n"  # After finishing a line, yield a newline character to preserve paragraph breaks.

# def response_generator(msg_content):
#     lines = msg_content.split('\n')  # Split the content into lines to preserve paragraph breaks.
#     for line in lines:
#         words = line.split()  # Split the line into words to introduce a delay for each word.
#         for word in words:
#             yield word + " "
#             time.sleep(0.1)
#         yield "\n"  # After finishing a line, yield a newline character to preserve paragraph breaks.


# 顯示聊天訊息
def show_msgs():
    for msg in st.session_state.messages:
        if msg["role"] == "assistant":
            # For assistant messages, use the custom avatar
            with st.chat_message("assistant"):
                st.write(cc.convert(msg["content"]))
        else:
            # For user messages, display as usual
            with st.chat_message(msg["role"]):
                st.write(cc.convert(msg["content"]))
import logging
logging.basicConfig(level=logging.ERROR, filename="error_log.txt")



# 呼叫 ollama 模型進行回應
# test
# 呼叫 ollama 模型進行回應
def chat(message, model=models): ### CHANGE MODEL ID HERE 
    
    try:



        messages = [  {
        'role': 'system',
        'content': f"Your name is 穀寶, an AI assistant focused on insurance and stock planning and consulting. If you need more information to make a judgment, you can ask the user to provide more information, and you can use tools to help the user find it. Current stock prices, give suggestions and inquire about current stock status, and also check policy status. The current time is:{time.localtime}",
        },
        {'role': 'user', 
        'content': message 
        }]
        response = ollama.chat(model=model, messages=messages,
            tools=[
                {
                  'type': 'function',
                  'function': {
                      'name': 'get_stock_price',
                      'description': 'Query the real-time stock price of the specified stock code. The stock number is a four-digit number.',
                      'parameters': {
                          'type': 'object',
                          'properties': {
                              'stock': {'type': 'integer', 'description': 'The stock code you want to query, such as 2330 for TSMC'},
                          },
                          'required': ['stock_code'],
                      },
                  },
              },
            ],
        )
        # return response['message']['content']



        if not response['message'].get('tool_calls'):
            print("The model didn't use the function. Its response was:")
            print("-------------------無使用工具輸出---------------")
            print(response['message']['content'])
            response['message']['tool_calls']=""

            mp = "{請針對以下問題詳細回答並以清單來條列出來(如遇股票相關提問請回答股票名稱、代號、金額，其他參數依照問題附加；保單針對條文進行詳細回答，並敘述來文是來自哪個區段的)}"

            
            # print("---------------------------naive---------------------------")
            # naive = rag.query(message+mp, param=QueryParam(mode="naive"))
            # print(naive)

            print("---------------------------naive---------------------------")
            naive_result = query_naive(rag, message, mp)
        
            naive_result = f"回覆1:{naive_result}" if naive_result != '' else ""
            print(naive_result if naive_result else "Naive 模式回傳空值")

            print("---------------------------local---------------------------")
            # local_result = query_local(rag, message, mp)
            local_result = ''
            local_result = f"回覆2:{local_result}" if local_result != '' else ""
            print(local_result if local_result else "Local 模式回傳空值")


            print("---------------------------global---------------------------")
            global_result = query_global(rag, message, mp)
            global_result = f"回覆3:{global_result}" if global_result != '' else ""
            print(global_result if global_result else "Global 模式回傳空值")


            print("---------------------------hybrid---------------------------")
            hybrid_result = query_hybrid(rag, message, mp)
            hybrid_result = f"回覆4:{hybrid_result}" if hybrid_result != '' else ""
            print(hybrid_result if hybrid_result else "Hybrid 模式回傳空值")

            
            # print("---------------------------local---------------------------")
            # local = rag.query(message+mp, param=QueryParam(mode="local"))
            # print(local)
            # print("---------------------------global---------------------------")
            # global_sc =  rag.query(message+mp, param=QueryParam(mode="global"))
            # print(global_sc)
            # print("---------------------------hybrid---------------------------")
            # hybrid = rag.query(message+mp, param=QueryParam(mode="hybrid"))
            # print(hybrid)

            RAG_msg = f"請根據此問題挑選出各個回覆中切合問題的版本進行回覆，有可能會出現多則回覆，請在其中選擇最完整且契合問題的一個答案即可(僅選擇其中回答最好的版本，直接複製其回復，不須經過任何修改) :  問題:{message} \n {naive_result} \n {local_result} \n {global_result} \n {hybrid_result}"
            # RAG_msg = f"{naive}"



            RAG_response = ollama.chat(model='qwen2.5:14b', messages=[
                    {
                        'role': 'user',
                        'content': RAG_msg,
                    }
                ])

            print('RAG_response ->> ',RAG_response['message']['content'])

            return cc.convert(RAG_response['message']['content'])
            


        if response['message'].get('tool_calls'):
            print("-------------------詢問問題(tool_calls)---------------")
            print(response['message']['content'])

            available_functions = {
                'get_stock_price': get_stock_price,
            }

            print("function_response",response['message']['tool_calls'])

            for tool in response['message']['tool_calls']:
                print("調用工具 ==> ",tool['function']['name'])
                function_to_call = available_functions[tool['function']['name']]
                print("查找參數 ==> ",tool['function']['arguments']['stock_code'])
                function_response = function_to_call(tool['function']['arguments']['stock_code'])
                print("查找結果function_response ==> ",function_response)
                messages.append({'role': 'tool', 'content': function_response})

            # Second API call with the tool response

            print("--------------------------------------")
            print("final_response 前的messages",messages)
            print("--------------------------------------")

            final_response = ollama.chat(model=model, messages=messages)
            print("final_response",final_response['message']['content'])
            response['message']['tool_calls']=""
            return cc.convert(final_response['message']['content'])  
    except Exception as e:
        response['message']['tool_calls']=""
        error_message = str(e).lower()
        if "not found" in error_message:
            return f"Model '{model}' not found. Please refer to Doumentation at https://ollama.com/library."
        else:
        #     response = ollama.chat(model=model, messages=[
        #     {
        #         'role': 'user',
        #         'content': message,
        #     }
        # ])
            return f"{response['message']['content']}#_#"
            # return f"An unexpected error occurred with model '{model}': {str(e)}"

        
# 格式化訊息以供摘要使用
def format_messages_for_summary(messages):
    # Create a single string from all the chat messages
    return '\n'.join(f"{msg['role']}: {cc.convert(msg['content'])}" for msg in messages)

def summary(message, model=models):
    sysmessage = "summarize this conversation in 3 words. No symbols or punctuation:\n\n\n"
    api_message = sysmessage + message
    try:
        response = ollama.chat(model=model, messages=[
            {
                'role': 'user',
                'content': api_message,
            }
        ])
        return cc.convert(response['message']['content'])
    except Exception as e:
        error_message = str(e).lower()
        if "not found" in error_message:
            return f"Model '{model}' not found. Please refer to Documentation at https://ollama.com/library."
        else:
            return f"An unexpected error occurred with model '{model}': {str(e)}"

# 儲存聊天紀錄
def save_chat():
    if not os.path.exists('./Chats'):
        os.makedirs('./Chats')
    if st.session_state['messages']:
        formatted_messages = format_messages_for_summary(st.session_state['messages'])
        chat_summary = summary(formatted_messages)
        filename = f'./Chats/{chat_summary}.txt'
        with open(filename, 'w', encoding='UTF-8') as f:
            for message in st.session_state['messages']:
                # Replace actual newline characters with a placeholder
                encoded_content = cc.convert(message['content']).replace('\n', '\\n')
                f.write(f"{message['role']}: {encoded_content}\n")
        st.session_state['messages'].clear()
    else:
        st.warning("No chat messages to save.")

# 載入已保存的聊天紀錄
def load_saved_chats():
    chat_dir = './Chats'
    if os.path.exists(chat_dir):
        # Get all files in the directory
        files = os.listdir(chat_dir)
        # Sort files by modification time, most recent first
        files.sort(key=lambda x: os.path.getmtime(os.path.join(chat_dir, x)), reverse=True)
        for file_name in files:
            display_name = file_name[:-4] if file_name.endswith('.txt') else file_name  # Remove '.txt' from display
            if st.sidebar.button(display_name):
                st.session_state['show_chats'] = False  # Make sure this is a Boolean False, not string 'False'
                st.session_state['is_loaded'] = True
                load_chat(f"./Chats/{file_name}")
                # show_msgs()

def format_chatlog(chatlog):
    # Formats the chat log for downloading
    return "\n".join(f"{msg['role']}: {msg['content']}" for msg in chatlog)

# 讀取聊天紀錄檔案
def load_chat(file_path):
    # Clear the existing messages in the session state
    st.session_state['messages'].clear()  # Using clear() to explicitly empty the list
    show_msgs()
    # Read and process the file to extract messages and populate the session state
    with open(file_path, 'r', encoding='UTF-8') as file:
        for line in file.readlines():
            role, content = line.strip().split(': ', 1)
            # Decode the placeholder back to actual newline characters
            decoded_content = cc.convert(content.replace('\\n', '\n'))
            st.session_state['messages'].append({'role': role, 'content': decoded_content})


def main():
    st.title("穀寶")
    user_input = st.chat_input(":", key="1")

    if 'show' not in st.session_state:
        st.session_state['show'] = 'True'
    if 'show_chats' not in st.session_state:
        st.session_state['show_chats'] = 'False'
    if 'messages' not in st.session_state:
        st.session_state['messages'] = []
    show_msgs()
    if user_input:
        with st.chat_message("user"):
            st.write(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})
        messages = "\n".join(msg["content"] for msg in st.session_state.messages)


        if messages != '':
                
                model_sum = "qwen2.5" 
                re_msg_response = ollama.chat(model=model_sum, messages=[
            {
                'role': 'user',
                'content': "請總結重點問題和回答並回傳:"+messages,
            }
        ])
                print("re_msg_response == > ",re_msg_response['message']['content'])
                messages = re_msg_response['message']['content']


        # print(messages)
        response = chat(messages)
        st.session_state.messages.append({"role": "assistant", "content": response})

        with st.chat_message("assistant"):
            st.write_stream(response_generator(response))
    elif st.session_state['messages'] is None:
        st.info("Enter a prompt or load chat above to start the conversation")
    chatlog = format_chatlog(st.session_state['messages'])
    st.sidebar.download_button(
        label="下載對話紀錄檔",
        data=chatlog,
        file_name="chat_log.txt",
        mime="text/plain"
    )
    for i in range(5):
        st.sidebar.write("")
    if st.sidebar.button("儲存對話紀錄"):
        save_chat()

    
    # Show/Hide chats toggle
    if st.sidebar.checkbox("顯示/隱藏歷史對話紀錄", value=st.session_state['show_chats']):
        st.sidebar.title("對話紀錄")
        load_saved_chats()
        
    for i in range(3):
        st.sidebar.write(" ")
    

if __name__ == "__main__":
    main()

76