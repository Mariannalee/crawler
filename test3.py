from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import pandas as pd

# ===== 使用者設定 =====
station_ids = [  # 改名為 station_ids
"72S200",
"72S590",
"72T250",
"72U480",
"82S580",
"B2U990",
"E2S960",
"E2S980",

]
item_id = "GloblRad"
start_date = "2024/01/01"
end_date = "2024/01/31"

# ===== 啟動瀏覽器設定 =====
options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
service = Service()
driver = webdriver.Chrome(service=service, options=options)

url = "https://agr.cwa.gov.tw/history/station_day"

# ===== 累積所有結果 =====
final_result = []

# ===== 開始跑每個測站 =====
for station_id in station_ids:
    try:
        driver.get(url)
        time.sleep(2)

        Select(driver.find_element(By.ID, "station_level")).select_by_value("新農業站")
        time.sleep(0.5)
        Select(driver.find_element(By.ID, "area_name")).select_by_visible_text("東部")
        time.sleep(0.5)

        # 嘗試選擇測站（若不存在就跳過）
        try:
            Select(driver.find_element(By.ID, "station_name")).select_by_value(station_id)
        except:
            print(f"⚠️ 測站 {station_id} 不存在於此區域，跳過。")
            continue
        time.sleep(0.5)

        # 檢查 item_id 是否存在
        item_select = Select(driver.find_element(By.ID, "item_multiple"))
        available_items = [opt.get_attribute("value") for opt in item_select.options]
        if item_id not in available_items:
            print(f"⚠️ 測站 {station_id} 無觀測項目 {item_id}，略過。")
            continue

        item_select.select_by_value(item_id)
        time.sleep(0.5)

        # ===== 填入日期 =====
        driver.find_element(By.ID, "start_time").clear()
        driver.find_element(By.ID, "start_time").send_keys(start_date)
        driver.find_element(By.ID, "end_time").clear()
        driver.find_element(By.ID, "end_time").send_keys(end_date)

        # ===== 按下預覽資料按鈕 =====
        driver.find_element(By.ID, "create_table").click()
        time.sleep(2)

        # ===== 解析資料表格 =====
        soup = BeautifulSoup(driver.page_source, "html.parser")
        tables = soup.select("div#form > table")
        if not tables:
            print(f"⚠️ 測站 {station_id} 無資料表格，跳過。")
            continue

        rows = tables[0].select("tr")
        for row in rows[1:]:
            th = row.find("th")
            if not th:
                continue
            day = th.text.strip()
            if not day.isdigit():
                continue

            cols = row.find_all("td")
            for month, col in enumerate(cols, start=1):
                val = col.text.strip()
                if val and val != "/":
                    final_result.append({
                        "year": int(start_date[:4]),
                        "month": month,
                        "day": day,
                        "place": station_id,
                        "item_id": item_id,
                        "最低氣溫": val
                    })

    except Exception as e:
        print(f"🚨 測站 {station_id} 發生錯誤：{e}")
        continue

# ===== 匯出 CSV =====
if final_result:
    df = pd.DataFrame(final_result)
    df.to_csv("東部累積日射量.csv", index=False, encoding="utf-8-sig")
    print("✅ 已成功儲存至 東部累積日射量.csv")
else:
    print("⚠️ 無資料可寫入 CSV。")

# ===== 關閉瀏覽器 =====
driver.quit()
