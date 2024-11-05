from opencc import OpenCC
import ollama
import streamlit as st
import time
import os
from datetime import datetime
import asyncio
import subprocess
import re
cc = OpenCC('s2twp')

models = "qwen2.5"

# 工具調用功能------------

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd


def get_stock_price(stock: str) -> int:

    """
    Get the current stock price of "stock"
    """
    stock_list = {}
    # if not isinstance(stock, int):
    #     raise TypeError("Stock code must be a integer")

    # 初始化 Selenium 瀏覽器
    options = Options()
    options.add_argument('--headless')  # 無頭模式
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(), options=options)
    
    url = f'https://goodinfo.tw/tw/StockDividendPolicy.asp?STOCK_ID={stock}&SHOW_ROTC=F'
    driver.get(url)

    # 等待 3 秒後再進行爬取
    time.sleep(1)

    # 取得股價淨值比 PBR
    PBR = driver.find_element(By.XPATH, '//td[@title="PBR=成交價/最近一季BPS"]').text


    # 取得本益成長比 PEG
    PEG = driver.find_element(By.XPATH, '//td[@title="PEG=PER/近四季合計稅後淨利年成長率"]').text

    

    # 取得連漲連跌資訊
    Continuous_rise_and_fall = "-"
    for color in ['red', 'green', 'black']:
        try:
            Continuous_rise_and_fall = driver.find_element(By.XPATH, f'//font[@style="color:{color}"]').text
            break
        except:
            continue
    Continuous_rise_and_fall = Continuous_rise_and_fall.replace('\xa0', "")

    # 取得股價
    price = None
    for color in ['red', 'green', 'black']:
        try:
            price = driver.find_element(By.XPATH, f'//td[@style="font-weight:bold;color:{color}"]').text
            break
        except:
            continue

    # 取得股票名稱和編號
    stock_info = driver.find_element(By.XPATH, '/html/body/table[2]/tbody/tr[2]/td[3]/main/table/tbody/tr/td[1]/section/table/tbody/tr[1]/th/nobr[1]/h2/a').text.split(' ')
    stock_number = stock_info[0]
    stock_name = stock_info[1]


    # 取得本益比 PER
    PER = driver.find_element(By.XPATH, '//td[@title="PER=成交價/近四季合計EPS"]').text

    # 取得數據更新時間
    update_time = driver.find_element(By.XPATH, '/html/body/table[2]/tbody/tr[2]/td[3]/main/table/tbody/tr/td[1]/section/table/tbody/tr[1]/th/nobr[5]').text.split(' ')

    # 取得股利發放表格資料
    table = driver.find_element(By.ID, 'tblDetail')
    dfs = pd.read_html(table.get_attribute('outerHTML'))
    df = dfs[0]
    df.columns = df.columns.get_level_values(0)



    # 其他
    
    # 取得今年(最新年度)
    year_Dividend_Payout_Ratio = df.iloc[0, 0]

    for i in range(len(df)):
    # print(df.iloc[i, 0])
        year = str(df.iloc[i, 0])
        if year == str(int(year_Dividend_Payout_Ratio)):
            new_dividend = df.iloc[i, 7]
        if year == str(int(year_Dividend_Payout_Ratio)-1):
            if new_dividend != "-":
                new_dividend = float(new_dividend)
                print(f"最新一期股利發放年度({int(year)+1}) = {new_dividend}")
            else:
                new_dividend = float(df.iloc[i, 7])
                print(f"最新一期股利發放年度({int(year)}年) = {new_dividend}")
            # print(year)
            # 去年平均股價
            last_year_avg_price = float(df.iloc[i, 15])
            if PER != "N/A":
            # 去年 PER=成交價/近四季合計EPS
                last_year_PER = (float(last_year_avg_price)/float(df.iloc[i, 20]))
                # 去年盈餘分配率
                last_year_Dividend_Payout_Ratio = float(df.iloc[i, 21])
                last_year_Dividend_Payout_Ratio = float(last_year_Dividend_Payout_Ratio)/100
                # print("last_year_Dividend_Payout_Ratio",last_year_Dividend_Payout_Ratio)
                # 去年公式計算出的合理價  (股價/per)(盈餘分配率)
                last_year_reasonable_price_formula = (float(last_year_avg_price) / float(last_year_PER)) * (float(last_year_Dividend_Payout_Ratio))
                
            else:
                last_year_reasonable_price_formula = f"很抱歉{stock_number}可能為ETF或缺少EPS數據故無法以此公式計算"
                last_year_PER = f"很抱歉{stock_number}可能為ETF或缺少EPS數據故無法以此公式計算"
                last_year_Dividend_Payout_Ratio = f"很抱歉{stock_number}可能為ETF或缺少EPS數據故無法以此公式計算"
            break;
    
    # 計算配息次數(過去)
    ##註：目前尚未加上計算今年已配息次數的功能
    dividend_bol = False
    for i in range(len(df)):
        is_value = str(df.iloc[i, 1])
        if is_value:
            # if str(int(year_Dividend_Payout_Ratio)-1) < str(df.iloc[i, 0]) <= str(int(year_Dividend_Payout_Ratio)):
            #     dividend_counts += 1
            #     print(f"今年已發放次數{dividend_counts}")
            if str(df.iloc[i, 0]) == str(int(year_Dividend_Payout_Ratio)-1):
                dividend_row_star = i
                dividend_bol = True
                # print(f"去年總發放次數：{dividend_all_counts}")
            if dividend_bol == True and str(df.iloc[i, 0]) == str(int(year_Dividend_Payout_Ratio)-2):
                dividend_all_counts  = i-dividend_row_star-1
                print(f"{str(int(year_Dividend_Payout_Ratio)-1)}全年共發放 {dividend_all_counts} 次股息，預估今年也配相同次數(請注意!今年配息次數參考過去配息次數，實際配息次數與金額請依公司公告為準)")
                break;
    # 盈餘分配率
    Dividend_Payout_Ratio = df.iloc[0, 21]
    # 預估股利公式 = (股價/per)(盈餘分配率)
    if Dividend_Payout_Ratio != "-":
        Dividend_Payout_Ratio = float(Dividend_Payout_Ratio)/100
        # print("Dividend_Payout_Ratio",Dividend_Payout_Ratio)
        reasonable_price_formula = (float(price) / float(PER)) * Dividend_Payout_Ratio
        # print(f"今年預估股利：({price} / {PER}) * {Dividend_Payout_Ratio} = {round(reasonable_price_formula,4)}")
    elif last_year_Dividend_Payout_Ratio != "-":
        #因為未到今年配息日故用去年配息來計算
        reasonable_price_formula = (float(price) / float(PER)) * last_year_Dividend_Payout_Ratio
        # print(f"今年預估股利：({price} / {PER}) * {last_year_Dividend_Payout_Ratio}  = {round(reasonable_price_formula,4)}")
        # print("**因為未到今年配息日故用去年配息來計算**")
    else:
        reasonable_price_formula = f"很抱歉{stock_number}可能為ETF或缺少盈餘分配率故無法以此公式計算"


    # 關閉 Selenium 瀏覽器
    driver.quit()

    # 打印爬取到的數據
    print("=============當前其他數據==============")
    # print("股價淨值比(PBR)：", PBR)
    # stock_list["PBR"] = [f"股價淨值比(PBR)：{PBR}"]
    # print("本益成長比(PEG)：", PEG)
    # stock_list["PEG"] = [f"本益成長比(PEG)：{PEG}"]
    print("股票號碼：", stock_number)
    stock_list["stock_number"] = [f"股票號碼：{stock_number}"]
    print("股票名稱：", stock_name)
    stock_list["stock_name"] = [f"股票名稱：{stock_name}"]
    print("連漲連跌：", Continuous_rise_and_fall)
    stock_list["Continuous_rise_and_fall"] = [f"連漲連跌：{Continuous_rise_and_fall}"]
    print("現在股價：", price)
    stock_list["price"] = [f"現在股價：{price}元台幣"]
    # print("本益比(PER)：", PER)
    # stock_list["PER"] = [f"本益比(PER)：{PER}"]
    print("數據更新日期：", f"{update_time[1]}")
    stock_list["update_time"] = [f"數據更新日期：{update_time[1]}"]
    
    # ... 其餘的數據處理及計算可以按需繼續添加

    print(f"--------------------------------------\n去年數值({year})\n ")
    print(year,"年平均股價：",last_year_avg_price)
    if PER != "N/A":
        print(year,"年本益比(PER)：",round(last_year_PER,3))
        print(year,"年盈餘分配率：",last_year_Dividend_Payout_Ratio)
        print(f"{year}年公式數值：({last_year_avg_price} / {last_year_PER}) * {last_year_Dividend_Payout_Ratio} =",round(last_year_reasonable_price_formula,4))
    else:
        print(f"{year}年公式數值：",(last_year_reasonable_price_formula))
        print(year,"年本益比(PER)：",(last_year_PER))
        print(year,"年盈餘分配率：",last_year_Dividend_Payout_Ratio)

    if Dividend_Payout_Ratio != "-" or last_year_Dividend_Payout_Ratio != "-":
        reasonable_price_formula = round(reasonable_price_formula,3)
        # 前一年最低價
        last_year_low_price = float(df.iloc[i, 14])
        print(f"前一年({year})最低價:{last_year_low_price}")
        # 前一年最高價
        last_year_hig_price = float(df.iloc[i, 13])
        print(f"前一年({year})最高價:{last_year_hig_price}")
        #前一年的股利(現金+股票)
        dividend = float(df.iloc[i, 7])
        print(f"前一年({year})股利(現金+股票):{dividend}")

        #註：目前公式的目標標的主要為穩定配息且為高股息的股票，若為如台積電等一眾高成長帶動溢價型股票或如台塑等產業週期型股票則可能不適用於以下公式!
        #此工具的目標族群為年紀較長且選擇存股作為投資方案的用戶，以對話方式提供用戶所擁有的股票估值、近一年大致可獲得的股利、所選股票是否建議買入和獲利了結價位
    

    # 
        print("\n-*-*-*-計算合理價公式*-*-*-\n")
        print("現在股價：",price)
        suggestion_1 = ""

        print("\n___方案1：股利倍率估價法___\n")


        # print("\n___方案1：以15、20、30倍股利推估價位___\n")
        suggestion_1 += "指標1：以15、20、30倍股利推估價位"
        #因過去股利已成過去式，並不足以作為未來推估股利之依據，故取消將其作為判斷當其股利之依據
        # 便宜價 = 當期股利 × 15
        print(f"預估便宜價 = 預估股利 × 15  \n預估便宜價: {round(reasonable_price_formula,4)}*15 = {round(reasonable_price_formula,4)*15}")
        # suggestion_1 += (f"預估便宜價 = 預估股利 × 15  \n預估便宜價: {round(reasonable_price_formula,4)}*15 = {round(reasonable_price_formula,4)*15}\n")
        # print(f"便宜價 = 當期股利 × 15  \n便宜價: {round(new_dividend,4)}*15 = {round(new_dividend,4)*15}\n")

        # 合理價 = 當期股利 × 20
        print(f"預估合理價 = 預估股利 × 20  \n預估合理價: {round(reasonable_price_formula,4)}*20 = {round(reasonable_price_formula,4)*20}")
        # suggestion_1 += (f"預估合理價 = 預估股利 × 20  \n預估合理價: {round(reasonable_price_formula,4)}*20 = {round(reasonable_price_formula,4)*20}\n")
        # print(f"合理價 = 當期股利 × 20  \n合理價: {round(new_dividend,4)}*20 = {round(new_dividend,4)*20}\n")

        # 昂貴價 = 當期股利 × 30
        print(f"預估昂貴價 = 預估股利 × 30  \n預估昂貴價: {round(reasonable_price_formula,4)}*30 = {round(reasonable_price_formula,4)*30}")
        # suggestion_1 += (f"預估昂貴價 = 預估股利 × 30  \n預估昂貴價: {round(reasonable_price_formula,4)}*30 = {round(reasonable_price_formula,4)*30}\n")
        # print(f"昂貴價 = 當期股利 × 30  \n昂貴價: {round(new_dividend,4)}*30 = {round(new_dividend,4)*30}\n")

        # if float(price) < float(new_dividend) *15:print(f"當前價位({price})與當前股利({new_dividend})屬於便宜價，建議買入")
        # elif float(price) >= float(new_dividend) *15 and float(price) < float(new_dividend)*20:print(f"當前價位({price})與當前股利({new_dividend})屬於便宜價與合理價之間，建議買入")
        # elif float(price) >= float(new_dividend) *20 and float(price) < float(new_dividend)*30:print(f"當前價位({price})與當前股利({new_dividend})屬於合理價與昂貴價之間，建議謹慎考慮再買入")
        # elif float(price) >= float(new_dividend) *30:print(f"當前價位({price})與當前股利({new_dividend})屬於昂貴價，建議不再買入")
        # else:print("數據異常!不再判斷區間無法判斷")

        if float(price) < float(reasonable_price_formula)*15:print(f"預估價位({price})與預估股利({reasonable_price_formula})屬於便宜價{round(reasonable_price_formula,4)*15}，建議買入");suggestion_1 += (f"根據指標1分析： 屬於便宜價(現價低於{round(reasonable_price_formula,4)*15}元)，建議大量買入")
        elif float(price) >= float(reasonable_price_formula) *15 and float(price) < float(reasonable_price_formula)*20:print(f"預估價位({price})與預估股利({reasonable_price_formula})屬於便宜價{round(reasonable_price_formula,4)*15}與合理價{round(reasonable_price_formula,4)*20}之間，建議買入");suggestion_1 += (f"根據指標1分析： 屬於合理價(現價位於便宜價{round(reasonable_price_formula,4)*15}元與合理價{round(reasonable_price_formula,4)*20}元之間)，建議買入")
        elif float(price) >= float(reasonable_price_formula) *20 and float(price) < float(reasonable_price_formula)*30:print(f"預估價位({price})與預估股利({reasonable_price_formula})屬於合理價{round(reasonable_price_formula,4)*20}與昂貴價{round(reasonable_price_formula,4)*30}之間，建議謹慎考慮再買入");suggestion_1 += (f"根據指標1分析： 屬於合理偏高價(現價位於合理價{round(reasonable_price_formula,4)*20}元與昂貴價{round(reasonable_price_formula,4)*30}元之間，建議謹慎考慮再買入")
        elif float(price) >= float(reasonable_price_formula) *30:print(f"預估價位({price})與預估股利({reasonable_price_formula})屬於昂貴價{round(reasonable_price_formula,4)*30}，建議不再買入");suggestion_1 += (f"建議： 屬於昂貴價(現價高於{round(reasonable_price_formula,4)*30}元)，建議不再買入")
        else:print("預估數據異常!不再判斷區間無法判斷");suggestion_1 += (f"指標1：\n 預估數據異常!不再判斷區間無法判斷")
        stock_list["suggestion_1"] = suggestion_1
        # print("\n___方案2：以老師提供的公式推估價位___\n")
        print("\n___方案2：波動性股利估價法___\n")
        
        suggestion_2 =""

        if Dividend_Payout_Ratio != "-":print(f"預估股利公式 = (股價/per)(盈餘分配率)  \n今年預估股利：({price} / {PER}) * {Dividend_Payout_Ratio} = {round(reasonable_price_formula,4)}");suggestion_2 += (f"指標2：預估股利公式 預估股利公式 = (股價/per)(盈餘分配率)  今年預估股利：({price} / {PER}) * {Dividend_Payout_Ratio} = {round(reasonable_price_formula,4)}")
        elif last_year_Dividend_Payout_Ratio != "-":print(f"預估股利公式 = (股價/per)(盈餘分配率)  \n今年預估股利：({price} / {PER}) * {round(last_year_Dividend_Payout_Ratio,3)}  = {round(reasonable_price_formula,4)}\n  **因為未到今年配息日故用去年({int(year)-1})配息來計算**\n");suggestion_2 += (f"指標2：預估股利公式 預估股利公式 = (股價/per)(盈餘分配率)   今年預估股利：({price} / {PER}) * {round(last_year_Dividend_Payout_Ratio,3)}  = {round(reasonable_price_formula,4)}  (因為未到今年配息日故用去年({int(year)-1})配息來計算)")
        stock_list["suggestion_2"] = suggestion_2

        #便宜價公式：(目前預估的股利/前一年的股利)(前一年最低價+0.3(前一年最高價-前一年最低價))
        estimated_cheap_price = round(((reasonable_price_formula/dividend)*(last_year_low_price+0.3*(last_year_hig_price-last_year_low_price))),4)
        suggestion_3 = ""
        suggestion_3 += (f"指標3：預估便宜價公式")
        print("便宜價公式：(目前預估的股利/前一年的股利)(前一年最低價+0.3(前一年最高價-前一年最低價))")
        # suggestion_3 += (f"便宜價公式：(目前預估的股利/前一年的股利)(前一年最低價+0.3(前一年最高價-前一年最低價))\n")
 
        print(f"預估便宜價：({reasonable_price_formula}/{dividend})*({last_year_low_price}+0.3*({last_year_hig_price}-{last_year_low_price})) = {estimated_cheap_price}")
        # suggestion_3 += (f"預估便宜價：({reasonable_price_formula}/{dividend})*({last_year_low_price}+0.3*({last_year_hig_price}-{last_year_low_price})) = {estimated_cheap_price}\n")
        #合理價公式：(目前預估的股利/前一年的股利)(前一年最低價+0.5(前一年最高價-前一年最低價))
        estimated_reasonable_price = round(((reasonable_price_formula/dividend)*(last_year_low_price+0.5*(last_year_hig_price-last_year_low_price))),4)
        print("合理價公式：(目前預估的股利/前一年的股利)(前一年最低價+0.5(前一年最高價-前一年最低價))")
        # suggestion_3 += (f"合理價公式：(目前預估的股利/前一年的股利)(前一年最低價+0.5(前一年最高價-前一年最低價))\n")
        print(f"預估合理價：({reasonable_price_formula}/{dividend})*({last_year_low_price}+0.5*({last_year_hig_price}-{last_year_low_price})) = {estimated_reasonable_price}\n")
        # suggestion_3 += (f"預估合理價：({reasonable_price_formula}/{dividend})*({last_year_low_price}+0.5*({last_year_hig_price}-{last_year_low_price})) = {estimated_reasonable_price}\n")
        #昂貴價公式：(目前預估的股利/前一年的股利)(前一年最低價+0.7(前一年最高價-前一年最低價))
        estimated_expensive_price = round(((reasonable_price_formula/dividend)*(last_year_low_price+0.7*(last_year_hig_price-last_year_low_price))),4)
        print("昂貴價公式：(目前預估的股利/前一年的股利)(前一年最低價+0.7(前一年最高價-前一年最低價))")
        # suggestion_3 += (f"昂貴價公式：(目前預估的股利/前一年的股利)(前一年最低價+0.7(前一年最高價-前一年最低價))\n")
        print(f"預估昂貴價:({reasonable_price_formula}/{dividend})*({last_year_low_price}+0.7*({last_year_hig_price}-{last_year_low_price})) = {estimated_expensive_price}\n")
        # suggestion_3 += (f"預估昂貴價:({reasonable_price_formula}/{dividend})*({last_year_low_price}+0.7*({last_year_hig_price}-{last_year_low_price})) = {estimated_expensive_price}\n")
    else:
        print(f"很抱歉! {stock_number}({stock_name}) 可能為ETF或缺少盈餘分配率故無法給出價位建議")
        suggestion_3 += (f"指標3：很抱歉! {stock_number}({stock_name}) 可能為ETF或缺少盈餘分配率故無法給出價位建議")



    if float(price) < float(estimated_cheap_price):
        print(f"指標3：屬於便宜價(現價低於{round(estimated_cheap_price,4)})，建議大量買入")
        suggestion_3 += (f"指標3：屬於便宜價(現價低於{round(estimated_cheap_price,4)}元台幣)，建議大量買入")
    elif float(price) >= float(estimated_cheap_price) and float(price) < float(estimated_reasonable_price):
        print(f"指標3：屬於合理價(現價位於便宜價{round(estimated_cheap_price,4)}元與合理價{round(estimated_reasonable_price,4)}元之間)，建議買入")
        suggestion_3 += (f"指標3：屬於合理價(現價位於便宜價{round(estimated_cheap_price,4)}元與合理價{round(estimated_reasonable_price,4)}元之間)，建議買入")
    elif float(price) >= float(estimated_reasonable_price) and float(price) < float(estimated_expensive_price):
        print(f"指標3：屬於合理偏高價(現價位於合理價{round(estimated_reasonable_price,4)}元與昂貴價{round(estimated_expensive_price,4)}元之間)，建議謹慎考慮再買入")
        suggestion_3 += (f"指標3：屬於合理偏高價(現價位於合理價{round(estimated_reasonable_price,4)}元與昂貴價{round(estimated_expensive_price,4)}元之間)，建議謹慎考慮再買入")
    elif float(price) >= float(estimated_expensive_price) :
        print(f"指標3：屬於昂貴價(現價高於{round(estimated_expensive_price,4)}元)，建議不再買入")
        suggestion_3 += (f"指標3：屬於昂貴價(現價高於{round(estimated_expensive_price,4)}元)，建議不再買入")
    else:print("預估數據異常!不再判斷區間無法判斷");suggestion_1 += (f"指標1：\n 預估數據異常!不再判斷區間無法判斷")
    stock_list["suggestion_3"] = suggestion_3
    stock_list["currency"] = "新台幣"
    stock_list["data_url"] = f"資料來源：{url}"
    print(url)
    print("\n''''''''''''''--輸出陣列--''''''''''''''''\n")

    return str(stock_list)

# ------------------------
def response_generator(msg_content):
    lines = msg_content.split('\n')  # Split the content into lines to preserve paragraph breaks.
    for line in lines:
        words = line.split()  # Split the line into words to introduce a delay for each word.
        for word in words:
            yield word + " "
            time.sleep(0.1)
        yield "\n"  # After finishing a line, yield a newline character to preserve paragraph breaks.


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
        # graph rag區域-----------------------------
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
            response_text = ""

        # ----------------

        messages = [  {
        'role': 'system',
        'content': f"Your name is 穀寶, an AI assistant focused on insurance and stock planning and consulting. If you need more information to make a judgment, you can ask the user to provide more information, and you can use tools to help the user find it. Current stock prices, give suggestions and inquire about current stock status, and also check policy status. The current time is:{time.localtime}",
        },
        {'role': 'user', 
        'content': message+response_text
        }]
        response = ollama.chat(model=model, messages=messages,
            tools=[
                {
                  'type': 'function',
                  'function': {
                      'name': 'get_stock_price',
                      'description': 'Query real-time stock prices for a given stock code',
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
            print("-------------------初始回應---------------")
            print(response['message']['content'])
            response['message']['tool_calls']=""

            return cc.convert(response['message']['content'])  

            

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
            final_response = ollama.chat(model=models, messages=messages)
            print("final_response",final_response['message']['content'])
            response['message']['tool_calls']=""
            return cc.convert(final_response['message']['content'])  
    except Exception as e:
        response['message']['tool_calls']=""
        error_message = str(e).lower()
        if "not found" in error_message:
            return f"Model '{model}' not found. Please refer to Doumentation at https://ollama.com/library."
        else:
            return f"An unexpected error occurred with model '{model}': {str(e)}"

        
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


