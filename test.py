import re


def get_stock_list():
    # 步驟1：讀取原始資料
    input_file = 'files/stock_list.txt'
    output_file = 'files/stcok.txt'

    with open(input_file, 'r') as file:
        data = file.read()

    # 步驟2：解析資料
    pattern = re.compile(
        r'股票代號：(.*?)\((.*?)\)\n'
        r'購買時間：(.*?)\n'
        r'購買股數\(張{1000股}\)：(\d+)\n'
        r'購買金額\(單價\)：(\d+\.\d+)\n'
        r'[-]{2,}'
    )

    matches = pattern.findall(data)

    # 使用字典來存儲股票信息
    stock_data = {}

    for match in matches:
        stock_code, stock_name, purchase_date, quantity, price = match
        quantity = int(quantity)
        price = float(price)
        
        if stock_code not in stock_data:
            stock_data[stock_code] = {
                'name': stock_name,
                'total_quantity': 0,
                'total_value': 0.0
            }
        
        stock_data[stock_code]['total_quantity'] += quantity
        stock_data[stock_code]['total_value'] += price * quantity

    # 步驟3：計算平均股價
    summary_data = []
    for stock_code, data in stock_data.items():
        average_price = data['total_value'] / data['total_quantity']
        summary_data.append(f"股票代號：{stock_code}({data['name']})\n"
                            f"擁有股數：{data['total_quantity']}\n"
                            f"平均股價：{average_price:.1f}\n")

    # 步驟4：寫入結果
    with open(output_file, 'w') as file:
        file.write("\n".join(summary_data))

    print(f"結果已寫入 {output_file}")


    get_stock_list()