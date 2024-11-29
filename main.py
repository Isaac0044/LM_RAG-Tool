from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from starlette.responses import HTMLResponse
import json
import requests
import pandas as pd
import os

from opencc import OpenCC
import ollama
import streamlit as st
import time
import os
from datetime import datetime
import asyncio

cc = OpenCC('s2twp')

models = "qwen2.5"



app = FastAPI()

templates = Jinja2Templates(directory='templates/')

# 股票編號轉換為股票名稱
def get_stock_name(s_code):
    try:
        url = f'https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_{s_code}.tw'
        response = requests.get(url)
        data = response.json()
        if data['msgArray']:
            s_name = data['msgArray'][0]['n']
            return s_name
        else:
            return None
    except:
        return "None"

# 寫入excel
def write_data_to_excel(file_path, columns, all):
    if os.path.exists(file_path):
        df = pd.read_excel(file_path)
    else:
        df = pd.DataFrame(columns=[columns])

    new_data = pd.DataFrame([{columns: all}])
    df = pd.concat([df, new_data], ignore_index=True)
    df.to_excel(file_path, index=False)

    results = df.to_dict(orient='records')
    return json.dumps(results, ensure_ascii=False, indent=4)

# Route to display the form (GET request)
@app.get('/form', response_class=HTMLResponse)
async def get_form(request: Request):
    return templates.TemplateResponse('form.html', context={'request': request})

# Route to handle form submission (POST request)
@app.post('/form')
async def form_post(
    request: Request,
    s_code: int = Form(...),
    s_time: str = Form(...),
    s_fs: float = Form(...),
    s_price: float = Form(...)
):
    s_name = get_stock_name(s_code)

    s_all = f"股票代號:{s_code}\n股票名稱:{s_name}\n購買時間:{s_time}\n購買張數(1000股):{s_fs}\n購買金額(單價):{s_price}"
    s_columns = "股票資訊"
    file_path = 'files/stock.xlsx'
    result = write_data_to_excel(file_path, s_columns, s_all)

    # return templates.TemplateResponse('form.html', context={'request': request, 'result': result, 's_code': s_code, 's_fs': s_fs, 's_time': s_time, 's_price': s_price})
    return templates.TemplateResponse('form.html', context={'request': request, 's_code': s_code, 's_time': s_time})

