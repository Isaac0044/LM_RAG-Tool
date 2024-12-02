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


def get_stock_price(stock: str) -> int:

    """
    Get the current stock price of "stock"
    """
    stock_list = {}
    # if not isinstance(stock, int):
    #     raise TypeError("Stock code must be a integer")

    if not isinstance(stock, int):
        raise TypeError("Stock code must be a integer")
    import requests
    import pandas as pd
    from bs4 import BeautifulSoup
    import requests
    from concurrent.futures import ThreadPoolExecutor

    headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36'}

    # data = soup.select_one('M(0) P(0) List(n)')
    # dfs = pd.read_html(data.prettify())


    # df = dfs[0]
    # df.columns = df.columns.get_level_values(0)


    url = f'https://tw.stock.yahoo.com/quote/{stock}/dividend'    # 台積電 Yahoo 股市網址
    res = requests.get(url, headers = headers)                          # 取得網頁內容
    res.encoding = 'utf-8'
    soup = BeautifulSoup(res.text, "html.parser")    # 轉換內容
    # title = soup.find('h1')             # 找到 h1 的內容
    price = soup.select('.Fz\(32px\)')[0]     # 找到第一個 class 為 Fz(32px) 的內容，如果出現錯誤，可以使用 .Fz\(32px\) 轉義
    b = soup.select('.Fz\(20px\)')[0]     # 找到第一個 class 為 Fz(20px) 的內容，如果出現錯誤，可以使用 .Fz\(20px\) 轉義
    s = ''

    try:
        # 如果 main-0-QuoteHeader-Proxy id 的 div 裡有 C($c-trend-down) 的 class
        # 表示狀態為下跌
        quote_header = soup.select('#main-0-QuoteHeader-Proxy')
        if quote_header and quote_header[0].select('[class*="c-trend-down"]'):
            s = '-'
    except (IndexError, AttributeError) as e:
        print(f"First check error: {e}")
        try:
            # 如果 main-0-QuoteHeader-Proxy id 的 div 裡有 C($c-trend-up) 的 class
            # 表示狀態為上漲
            if quote_header and quote_header[0].select('[class*="c-trend-up"]'):
                s = '+'
        except (IndexError, AttributeError) as e:
            print(f"Second check error: {e}")
            # 如果都沒有包含，表示平盤
            s = ''



    price = price.get_text()
    stock_name = soup.select('.Fz\(24px\)')[0]
    stock_name = stock_name.get_text()
    
# 連漲連跌
    Continuous_rise_and_fall = soup.select('.Fz\(16px\)')[2]

# 更新日期
    update_time = soup.select('.Fz\(12px\)')[1]
    update_time = update_time.get_text()

    # print(f"**************************************\n目前數據(更新日：{year_Dividend_Payout_Ratio}/{update_time[1]})\n ")

    print(f"**************************************\n數據更新日期：({update_time})\n ")
    stock_list["update_time"] = [f"數據更新日期：{update_time}"]
    print("股票號碼：",stock)
    stock_list["stock_number"] = [f"股票號碼：{stock}"]
    print("股票名稱：",stock_name)
    stock_list["stock_name"] = [f"股票名稱：{stock_name}"]
    print("現在股價：",price)
    stock_list["price"] = [f"現在股價：{price}元台幣"]
# 上漲下跌
    print(f"上漲下跌：{s}{b.get_text()}")
    stock_list["Quote_change"] = [f"上漲下跌：{s}{b.get_text()}"]
# 連漲連跌
    print("連漲連跌：",Continuous_rise_and_fall.get_text())
    stock_list["Continuous_rise_and_fall"] = [f"連漲連跌：{Continuous_rise_and_fall.get_text()}"]
    # PER=成交價/近四季合計EPS
    # print("本益比(PER)：",PER)
    # stock_list["PER"] = [f"本益比(PER)：{PER}"]
    eps_url = f'https://tw.stock.yahoo.com/quote/{stock}.TW/eps'    # 台積電 Yahoo 股市網址
    eps_res = requests.get(eps_url, headers = headers)                          # 取得網頁內容
    eps_res.encoding = 'utf-8'
    eps_soup = BeautifulSoup(eps_res.text, "html.parser")    # 轉換內容
# 每股盈餘
    EPS_4 = 0
    for i in range(4):
      EPS = eps_soup.select('li.List\(n\) div.Fxg\(1\)')[4*i].get_text()
      print(f'前{i+1}季度：',EPS)
      EPS_4 += float(EPS)
    print("近四季合計EPS：",EPS_4)
# 現金股利
    # cash_dividend = float(soup.select('li.List\(n\) div.Fxg\(1\)')[1].get_text())
    try:
      cash_dividend = float(soup.select('li.List\(n\) div.Fxg\(1\)')[1].get_text())
    except:
      cash_dividend = soup.select('li.List\(n\) div.Fxg\(1\)')[1].get_text()
# 股票股利
    # stock_dividends = soup.select('li.List\(n\) div.Fxg\(1\)')[2].get_text()
    try:
      stock_dividends = float(soup.select('li.List\(n\) div.Fxg\(1\)')[2].get_text())
    except:
      stock_dividends = soup.select('li.List\(n\) div.Fxg\(1\)')[2].get_text()


    # D(f)
    print("現金股利：",cash_dividend)
    print("股票股利：",stock_dividends)

    # 公式為：（每股股利/每股盈餘）x100%=盈餘分配率
    Dividend_Payout_Ratio = cash_dividend / EPS_4
    print("盈餘分配率：",Dividend_Payout_Ratio)
    stock_list["Dividend_Payout_Ratio"] = [f"盈餘分配率：{Dividend_Payout_Ratio}"]

    # PER=成交價/近四季合計EPS
    PER = float(price.replace(',', '')) / EPS_4

    print("本益比(PER)：",PER)
    # 預估股利公式 = (股價/per)(盈餘分配率)
  #  Dividend_Payout_Ratio != "-":
  #  Dividend_Payout_Ratio = Dividend_Payout_Ratio/100
   # print("Dividend_Payout_Ratio",Dividend_Payout_Ratio)
    reasonable_price_formula = (float(price.replace(',', '')) / float(PER)) * Dividend_Payout_Ratio

    print(f"今年預估股利：({price} / {PER}) * {Dividend_Payout_Ratio} = {round(reasonable_price_formula,4)}")

    print("\n___方案2：以老師提供的公式推估價位___\n")
    suggestion_2 =""

    if Dividend_Payout_Ratio != "-":print(f"預估股利公式 = (股價/per)(盈餘分配率)  \n今年預估股利：({price} / {PER}) * {Dividend_Payout_Ratio} = {round(reasonable_price_formula,4)}");suggestion_2 += (f"指標2：預估股利公式 預估股利公式 = (股價/per)(盈餘分配率)  今年預估股利：({price} / {PER}) * {Dividend_Payout_Ratio} = {round(reasonable_price_formula,4)}元台幣")
    elif last_year_Dividend_Payout_Ratio != "-":print(f"預估股利公式 = (股價/per)(盈餘分配率)  \n今年預估股利：({price} / {PER}) * {round(last_year_Dividend_Payout_Ratio,3)}  = {round(reasonable_price_formula,4)}\n  **因為未到今年配息日故用去年({int(year)-1})配息來計算**\n");suggestion_2 += (f"指標2：預估股利公式 預估股利公式 = (股價/per)(盈餘分配率)  今年預估股利：({price} / {PER}) * {round(last_year_Dividend_Payout_Ratio,3)}  = {round(reasonable_price_formula,4)}元台幣  (因為未到今年配息日故用去年({int(year)-1})配息來計算)")
    stock_list["suggestion_2"] = suggestion_2


    print(f"full list -> {stock_list}")

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

