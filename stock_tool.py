def goodinfo_stock_price(stock: int):
    import requests
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import pandas as pd
    import time

    stock_list = {}

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
    time.sleep(4)

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
    stock_info = driver.find_element(By.XPATH, '//table[2]//h2/a').text.split(' ')
    stock_number = stock_info[0]
    stock_name = stock_info[1]

    # 取得本益比 PER
    PER = driver.find_element(By.XPATH, '//td[@title="PER=成交價/近四季合計EPS"]').text

    # 取得數據更新時間
    update_time = driver.find_element(By.XPATH, '//table[2]//nobr[5]').text.split(' ')

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
                #print(f"最新一期股利發放年度({int(year)+1}) = {new_dividend}")
            else:
                new_dividend = float(df.iloc[i, 7])
                #print(f"最新一期股利發放年度({int(year)}年) = {new_dividend}")
            # #print(year)
            # 去年平均股價
            last_year_avg_price = float(df.iloc[i, 15])
            if PER != "N/A":
            # 去年 PER=成交價/近四季合計EPS
                last_year_PER = (float(last_year_avg_price)/float(df.iloc[i, 20]))
                # 去年盈餘分配率
                last_year_Dividend_Payout_Ratio = float(df.iloc[i, 21])
                last_year_Dividend_Payout_Ratio = float(last_year_Dividend_Payout_Ratio)/100
                # #print("last_year_Dividend_Payout_Ratio",last_year_Dividend_Payout_Ratio)
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
            #     #print(f"今年已發放次數{dividend_counts}")
            if str(df.iloc[i, 0]) == str(int(year_Dividend_Payout_Ratio)-1):
                dividend_row_star = i
                dividend_bol = True
                # #print(f"去年總發放次數：{dividend_all_counts}")
            if dividend_bol == True and str(df.iloc[i, 0]) == str(int(year_Dividend_Payout_Ratio)-2):
                dividend_all_counts  = i-dividend_row_star-1
                #print(f"{str(int(year_Dividend_Payout_Ratio)-1)}全年共發放 {dividend_all_counts} 次股息，預估今年也配相同次數(請注意!今年配息次數參考過去配息次數，實際配息次數與金額請依公司公告為準)")
                break;
    # 盈餘分配率
    Dividend_Payout_Ratio = df.iloc[0, 21]
    # 預估股利公式 = (股價/per)(盈餘分配率)
    if Dividend_Payout_Ratio != "-":
        Dividend_Payout_Ratio = float(Dividend_Payout_Ratio)/100
        # #print("Dividend_Payout_Ratio",Dividend_Payout_Ratio)
        reasonable_price_formula = (float(price) / float(PER)) * Dividend_Payout_Ratio
        # #print(f"今年預估股利：({price} / {PER}) * {Dividend_Payout_Ratio} = {round(reasonable_price_formula,2)}")
    elif last_year_Dividend_Payout_Ratio != "-":
        #因為未到今年配息日故用去年配息來計算
        reasonable_price_formula = (float(price) / float(PER)) * last_year_Dividend_Payout_Ratio
        # #print(f"今年預估股利：({price} / {PER}) * {last_year_Dividend_Payout_Ratio}  = {round(reasonable_price_formula,2)}")
        # #print("**因為未到今年配息日故用去年配息來計算**")
    else:
        reasonable_price_formula = f"很抱歉{stock_number}可能為ETF或缺少盈餘分配率故無法以此公式計算"


    # 關閉 Selenium 瀏覽器
    driver.quit()

    # 打印爬取到的數據
    #print("=============當前其他數據==============")
    # #print("股價淨值比(PBR)：", PBR)
    # stock_list["PBR"] = [f"股價淨值比(PBR)：{PBR}"]
    # #print("本益成長比(PEG)：", PEG)
    # stock_list["PEG"] = [f"本益成長比(PEG)：{PEG}"]
    #print("股票號碼：", stock_number)
    stock_list["stock_number"] = [f"股票號碼：{stock_number}"]
    #print("股票名稱：", stock_name)
    stock_list["stock_name"] = [f"股票名稱：{stock_name}"]
    #print("連漲連跌：", Continuous_rise_and_fall)
    stock_list["Continuous_rise_and_fall"] = [f"連漲連跌：{Continuous_rise_and_fall}"]
    #print("現在股價：", price)
    stock_list["price"] = [f"現在股價：{price}元台幣"]
    # #print("本益比(PER)：", PER)
    # stock_list["PER"] = [f"本益比(PER)：{PER}"]
    #print("數據更新日期：", f"{update_time[1]}")
    stock_list["update_time"] = [f"數據更新日期：{update_time[1]}"]
    
    # ... 其餘的數據處理及計算可以按需繼續添加

    #print(f"--------------------------------------\n去年數值({year})\n ")
    #print(year,"年平均股價：",last_year_avg_price)
    if PER != "N/A":
        print(year,"年本益比(PER)：",round(last_year_PER,3))
        print(year,"年盈餘分配率：",last_year_Dividend_Payout_Ratio)
        print(f"{year}年公式數值：({last_year_avg_price} / {last_year_PER}) * {last_year_Dividend_Payout_Ratio} =",round(last_year_reasonable_price_formula,2))
    else:
        print(f"{year}年公式數值：",(last_year_reasonable_price_formula))
        print(year,"年本益比(PER)：",(last_year_PER))
        print(year,"年盈餘分配率：",last_year_Dividend_Payout_Ratio)

    if Dividend_Payout_Ratio != "-" or last_year_Dividend_Payout_Ratio != "-":
        reasonable_price_formula = round(reasonable_price_formula,3)
        # 前一年最低價
        last_year_low_price = float(df.iloc[i, 14])
        #print(f"前一年({year})最低價:{last_year_low_price}")
        # 前一年最高價
        last_year_hig_price = float(df.iloc[i, 13])
        #print(f"前一年({year})最高價:{last_year_hig_price}")
        #前一年的股利(現金+股票)
        dividend = float(df.iloc[i, 7])
        #print(f"前一年({year})股利(現金+股票):{dividend}")

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
        print(f"預估便宜價 = 預估股利 × 15  \n預估便宜價: {round(reasonable_price_formula,2)}*15 = {round(reasonable_price_formula*15,2)}")
        # suggestion_1 += (f"預估便宜價 = 預估股利 × 15  \n預估便宜價: {round(reasonable_price_formula,2)}*15 = {round(reasonable_price_formula,2)*15}\n")
        # print(f"便宜價 = 當期股利 × 15  \n便宜價: {round(new_dividend,2)}*15 = {round(new_dividend,2)*15}\n")

        # 合理價 = 當期股利 × 20
        print(f"預估合理價 = 預估股利 × 20  \n預估合理價: {round(reasonable_price_formula,2)}*20 = {round(reasonable_price_formula*20,2)}")
        # suggestion_1 += (f"預估合理價 = 預估股利 × 20  \n預估合理價: {round(reasonable_price_formula,2)}*20 = {round(reasonable_price_formula,2)*20}\n")
        # print(f"合理價 = 當期股利 × 20  \n合理價: {round(new_dividend,2)}*20 = {round(new_dividend,2)*20}\n")

        # 昂貴價 = 當期股利 × 30
        print(f"預估昂貴價 = 預估股利 × 30  \n預估昂貴價: {round(reasonable_price_formula,2)}*30 = {round(reasonable_price_formula*30,2)}")
        # suggestion_1 += (f"預估昂貴價 = 預估股利 × 30  \n預估昂貴價: {round(reasonable_price_formula,2)}*30 = {round(reasonable_price_formula,2)*30}\n")
        # print(f"昂貴價 = 當期股利 × 30  \n昂貴價: {round(new_dividend,2)}*30 = {round(new_dividend,2)*30}\n")

        # if float(price) < float(new_dividend) *15:print(f"當前價位({price})與當前股利({new_dividend})屬於便宜價，建議買入")
        # elif float(price) >= float(new_dividend) *15 and float(price) < float(new_dividend)*20:print(f"當前價位({price})與當前股利({new_dividend})屬於便宜價與合理價之間，建議買入")
        # elif float(price) >= float(new_dividend) *20 and float(price) < float(new_dividend)*30:print(f"當前價位({price})與當前股利({new_dividend})屬於合理價與昂貴價之間，建議謹慎考慮再買入")
        # elif float(price) >= float(new_dividend) *30:print(f"當前價位({price})與當前股利({new_dividend})屬於昂貴價，建議不再買入")
        # else:print("數據異常!不再判斷區間無法判斷")

        if float(price) < float(reasonable_price_formula)*15:print(f"預估價位({price})與預估股利({round(reasonable_price_formula,2)})屬於便宜價{round(reasonable_price_formula,2)*15}，建議買入");suggestion_1 += (f"根據指標1分析： 屬於便宜價(現價低於{round(reasonable_price_formula*15,2)}元)，建議大量買入")
        elif float(price) >= float(reasonable_price_formula) *15 and float(price) < float(reasonable_price_formula)*20:print(f"預估價位({price})與預估股利({round(reasonable_price_formula,2)})屬於便宜價{round(reasonable_price_formula*15,2)}與合理價{round(reasonable_price_formula*20,2)}之間，建議買入");suggestion_1 += (f"根據指標1分析： 屬於合理價(現價位於便宜價{round(reasonable_price_formula*15,2)}元與合理價{round(reasonable_price_formula*20,2)}元之間)，建議買入")
        elif float(price) >= float(reasonable_price_formula) *20 and float(price) < float(reasonable_price_formula)*30:print(f"預估價位({price})與預估股利({round(reasonable_price_formula,2)})屬於合理價{round(reasonable_price_formula*20,2)}與昂貴價{round(reasonable_price_formula*30,2)}之間，建議謹慎考慮再買入");suggestion_1 += (f"根據指標1分析： 屬於合理偏高價(現價位於合理價{round(reasonable_price_formula*20,2)}元與昂貴價{round(reasonable_price_formula*30,2)}元之間，建議謹慎考慮再買入")
        elif float(price) >= float(reasonable_price_formula) *30:print(f"預估價位({price})與預估股利({round(reasonable_price_formula,2)})屬於昂貴價{round(reasonable_price_formula,2)*30}，建議不再買入");suggestion_1 += (f"建議： 屬於昂貴價(現價高於{round(reasonable_price_formula*30,2)}元)，建議不再買入")
        else:print("預估數據異常!不再判斷區間無法判斷");suggestion_1 += (f"指標1：\n 預估數據異常!不再判斷區間無法判斷")

        ##12/04 指標一暫時取消分析 **
        # stock_list["suggestion_1"] = suggestion_1


        # print("\n___方案2：以老師提供的公式推估價位___\n")
        print("\n___方案2：波動性股利估價法___\n")
        
        suggestion_2 =""

        if Dividend_Payout_Ratio != "-":print(f"預估股利公式 = (股價/per)(盈餘分配率)  \n今年預估股利：({price} / {PER}) * {round(Dividend_Payout_Ratio,2)} = {round(reasonable_price_formula,2)}");suggestion_2 += (f"指標2：預估股利公式 預估股利公式 = (股價/per)(盈餘分配率)  今年預估股利：({price} / {PER}) * {Dividend_Payout_Ratio} = {round(reasonable_price_formula,2)}")
        elif last_year_Dividend_Payout_Ratio != "-":print(f"預估股利公式 = (股價/per)(盈餘分配率)  \n今年預估股利：({price} / {PER}) * {round(last_year_Dividend_Payout_Ratio,2)}  = {round(reasonable_price_formula,2)}\n  **因為未到今年配息日故用去年({int(year)-1})配息來計算**\n");suggestion_2 += (f"指標2：預估股利公式 預估股利公式 = (股價/per)(盈餘分配率)   今年預估股利：({price} / {PER}) * {round(last_year_Dividend_Payout_Ratio,2)}  = {round(reasonable_price_formula,2)}  (因為未到今年配息日故用去年({int(year)-1})配息來計算)")
        stock_list["suggestion_2"] = suggestion_2

        #便宜價公式：(目前預估的股利/前一年的股利)(前一年最低價+0.3(前一年最高價-前一年最低價))
        estimated_cheap_price = round(((reasonable_price_formula/dividend)*(last_year_low_price+0.3*(last_year_hig_price-last_year_low_price))),2)
        suggestion_3 = ""
        suggestion_3 += (f"指標3：預估便宜價公式")
        print("便宜價公式：(目前預估的股利/前一年的股利)(前一年最低價+0.3(前一年最高價-前一年最低價))")
        # suggestion_3 += (f"便宜價公式：(目前預估的股利/前一年的股利)(前一年最低價+0.3(前一年最高價-前一年最低價))\n")
 
        print(f"預估便宜價：({reasonable_price_formula}/{dividend})*({last_year_low_price}+0.3*({last_year_hig_price}-{last_year_low_price})) = {estimated_cheap_price}")
        # suggestion_3 += (f"預估便宜價：({reasonable_price_formula}/{dividend})*({last_year_low_price}+0.3*({last_year_hig_price}-{last_year_low_price})) = {estimated_cheap_price}\n")
        #合理價公式：(目前預估的股利/前一年的股利)(前一年最低價+0.5(前一年最高價-前一年最低價))
        estimated_reasonable_price = round(((reasonable_price_formula/dividend)*(last_year_low_price+0.5*(last_year_hig_price-last_year_low_price))),2)
        print("合理價公式：(目前預估的股利/前一年的股利)(前一年最低價+0.5(前一年最高價-前一年最低價))")
        # suggestion_3 += (f"合理價公式：(目前預估的股利/前一年的股利)(前一年最低價+0.5(前一年最高價-前一年最低價))\n")
        print(f"預估合理價：({reasonable_price_formula}/{dividend})*({last_year_low_price}+0.5*({last_year_hig_price}-{last_year_low_price})) = {estimated_reasonable_price}\n")
        # suggestion_3 += (f"預估合理價：({reasonable_price_formula}/{dividend})*({last_year_low_price}+0.5*({last_year_hig_price}-{last_year_low_price})) = {estimated_reasonable_price}\n")
        #昂貴價公式：(目前預估的股利/前一年的股利)(前一年最低價+0.7(前一年最高價-前一年最低價))
        estimated_expensive_price = round(((reasonable_price_formula/dividend)*(last_year_low_price+0.7*(last_year_hig_price-last_year_low_price))),2)
        print("昂貴價公式：(目前預估的股利/前一年的股利)(前一年最低價+0.7(前一年最高價-前一年最低價))")
        # suggestion_3 += (f"昂貴價公式：(目前預估的股利/前一年的股利)(前一年最低價+0.7(前一年最高價-前一年最低價))\n")
        print(f"預估昂貴價:({reasonable_price_formula}/{dividend})*({last_year_low_price}+0.7*({last_year_hig_price}-{last_year_low_price})) = {estimated_expensive_price}\n")
        # suggestion_3 += (f"預估昂貴價:({reasonable_price_formula}/{dividend})*({last_year_low_price}+0.7*({last_year_hig_price}-{last_year_low_price})) = {estimated_expensive_price}\n")
    else:
        print(f"很抱歉! {stock_number}({stock_name}) 可能為ETF或缺少盈餘分配率故無法給出價位建議")
        suggestion_3 += (f"指標3：很抱歉! {stock_number}({stock_name}) 可能為ETF或缺少盈餘分配率故無法給出價位建議")



    if float(price) < float(estimated_cheap_price):
        print(f"指標3：屬於便宜價(現價低於{round(estimated_cheap_price,2)})，建議大量買入")
        suggestion_3 += (f"指標3：屬於便宜價(現價低於{round(estimated_cheap_price,2)}元台幣)，建議大量買入")
    elif float(price) >= float(estimated_cheap_price) and float(price) < float(estimated_reasonable_price):
        print(f"指標3：屬於合理價(現價位於便宜價{round(estimated_cheap_price,2)}元與合理價{round(estimated_reasonable_price,2)}元之間)，建議買入")
        suggestion_3 += (f"指標3：屬於合理價(現價位於便宜價{round(estimated_cheap_price,2)}元與合理價{round(estimated_reasonable_price,2)}元之間)，建議買入")
    elif float(price) >= float(estimated_reasonable_price) and float(price) < float(estimated_expensive_price):
        print(f"指標3：屬於合理偏高價(現價位於合理價{round(estimated_reasonable_price,2)}元與昂貴價{round(estimated_expensive_price,2)}元之間)，建議謹慎考慮再買入")
        suggestion_3 += (f"指標3：屬於合理偏高價(現價位於合理價{round(estimated_reasonable_price,2)}元與昂貴價{round(estimated_expensive_price,2)}元之間)，建議謹慎考慮再買入")
    elif float(price) >= float(estimated_expensive_price) :
        print(f"指標3：屬於昂貴價(現價高於{round(estimated_expensive_price,2)}元)，建議不再買入")
        suggestion_3 += (f"指標3：屬於昂貴價(現價高於{round(estimated_expensive_price,2)}元)，建議不再買入")
    else:print("預估數據異常!不再判斷區間無法判斷");suggestion_1 += (f"指標1：\n 預估數據異常!不再判斷區間無法判斷")
    stock_list["suggestion_3"] = suggestion_3
    stock_list["currency"] = "新台幣"
    stock_list["data_url"] = f"資料來源：{url}"
    print(url)
    print("\n''''''''''''''--輸出陣列--''''''''''''''''\n")
    print(stock_list)


    return str(stock_list)



def yahoo_get_stock(stock: int):

    """
    Get the current stock price of "stock"
    """
    stock_list = {}
    # if not isinstance(stock, int):
    #     raise TypeError("Stock code must be a integer")

    if not isinstance(stock, int):
        stock = int(stock)
        # raise TypeError("Stock code must be a integer")
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

    try:
        last_year_Dividend_Payout_Ratio = float(df.iloc[i, 21])
        last_year_Dividend_Payout_Ratio = float(last_year_Dividend_Payout_Ratio)/100
    except Exception as e:
        print(e)

    if Dividend_Payout_Ratio != "-":print(f"預估股利公式 = (股價/per)(盈餘分配率)  \n今年預估股利：({price} / {PER}) * {Dividend_Payout_Ratio} = {round(reasonable_price_formula,4)}");suggestion_2 += (f"指標2：預估股利公式 預估股利公式 = (股價/per)(盈餘分配率)  今年預估股利：({price} / {PER}) * {Dividend_Payout_Ratio} = {round(reasonable_price_formula,4)}元台幣")
    elif last_year_Dividend_Payout_Ratio != "-":print(f"預估股利公式 = (股價/per)(盈餘分配率)  \n今年預估股利：({price} / {PER}) * {round(last_year_Dividend_Payout_Ratio,3)}  = {round(reasonable_price_formula,4)}\n  **因為未到今年配息日故用去年({int(year)-1})配息來計算**\n");suggestion_2 += (f"指標2：預估股利公式 預估股利公式 = (股價/per)(盈餘分配率)  今年預估股利：({price} / {PER}) * {round(last_year_Dividend_Payout_Ratio,3)}  = {round(reasonable_price_formula,4)}元台幣  (因為未到今年配息日故用去年({int(year)-1})配息來計算)")
    stock_list["suggestion_2"] = suggestion_2

    stock_list["data_url"] = f"資料來源：{url}"


    print(f"full list -> {stock_list}")

    return str(stock_list)

# ------

import re

# 轉換台股名稱為代號
def convert_stock(stock):
    """
    將 stock 進行轉換：
    - 如果是數字格式，轉換為 int。
    - 如果是文字，根據字典進行轉換。
    :param stock: str - 股票代碼或文字描述
    :param stock_dict: dict - 股票對應字典
    :return: int 或 str - 轉換後的股票代碼
    """
    #讀取台股清單
    file_path = "tw_stock_list.md" 
    stock_dict = {}
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            # 使用正則表達式匹配 "key":"value" 的格式
            match = re.match(r'"([^"]+)"\s*:\s*"([^"]+)",?', line)
            if match:
                key, value = match.groups()
                stock_dict[key] = value

    # 轉換
    try:
        # 嘗試將 stock 轉換為數字
        return int(stock)
    except ValueError:
        # 如果是文字，嘗試在字典中查找
        if stock in stock_dict:
            try:
                return int(stock_dict[stock])
            except:
                return ''
        else:
            return ''





# # 轉換引用代碼
# file_path = "tw_stock_list.md" 
# stock_dict = load_stock_list(file_path)
# try:
#     stock = "大立光"
#     print(convert_stock(stock))  # 輸出: 大立光
#     print(type(convert_stock(stock)))  # 輸出: "3008"
# except ValueError as e:
#     print(e)


# stock = "2330"

# y = yahoo_get_stock(stock)
# g = goodinfo_stock_price(stock)

# print("------------Y------------------")
# print(y)

# print("------------G------------------")
# print(g)
