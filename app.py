import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import random
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

st.set_page_config(page_title="我們的專屬小窩", layout="wide")

# --- 側邊欄 (已移除願望清單) ---
with st.sidebar:
    selected = option_menu(
        menu_title="功能選單",
        # 這裡只保留 5 個功能
        options=["首頁", "今天吃什麼", "記帳小管家", "旅遊地圖", "回憶相簿"],
        icons=["house", "egg-fried", "currency-dollar", "map", "images"],
        menu_icon="heart",
        default_index=0,
    )

# --- 連線函式 (最穩定的雙棲版) ---
@st.cache_resource
def get_google_sheet_client():
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    creds = None
    
    # 1. 嘗試讀取雲端保險箱 (給 Streamlit Cloud 用)
    if "gcp" in st.secrets:
        try:
            key_dict = json.loads(st.secrets["gcp"]["json_file"])
            creds = ServiceAccountCredentials.from_json_keyfile_dict(key_dict, scope)
        except Exception as e:
            st.error(f"雲端保險箱讀取錯誤: {e}")
    
    # 2. 嘗試讀取本地檔案 (給電腦 Localhost 用)
    if creds is None:
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name('secrets.json', scope)
        except:
            pass
            
    # 如果兩邊都失敗，報錯
    if creds is None:
        st.error("找不到鑰匙！請確認 secrets.json 在資料夾內，或是雲端 Secrets 設定正確。")
        st.stop()
            
    client = gspread.authorize(creds)
    return client

# --- 頁面內容 ---

if selected == "首頁":
    st.title("歡迎回家！💑")
    st.success("這是我們一起開發的第一個網站！")
    st.balloons()

elif selected == "今天吃什麼":
    st.title("🍔 選擇困難救星")
    if st.button("幫我們決定！"):
        options = ['火鍋', '義大利麵', '壽司', '麥當勞', '牛排', '拉麵']
        st.header(f"✨ 今天就吃：{random.choice(options)} ✨")

elif selected == "記帳小管家":
    st.title("💰 雲端記帳本")
    
    # 連線
    try:
        client = get_google_sheet_client()
        sheet = client.open("OurLoveMoney").sheet1
    except Exception as e:
        st.error(f"連線失敗，請檢查 Google 試算表名稱是否為 OurLoveMoney。錯誤：{e}")
        st.stop()

    # 輸入區
    with st.container(border=True):
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            item = st.text_input("消費項目")
        with col2:
            price = st.number_input("金額", min_value=0, step=10)
        with col3:
            payer = st.selectbox("誰付的？", ["我", "男朋友"])
        
        if st.button("上傳雲端", use_container_width=True):
            if item and price > 0:
                from datetime import datetime
                date_str = datetime.now().strftime("%Y-%m-%d")
                sheet.append_row([date_str, item, price, payer])
                st.success("✅ 記帳成功！")
                st.cache_data.clear() # 清除快取以顯示最新資料
            else:
                st.warning("請輸入項目和金額喔！")

    # 顯示區
    st.divider()
    records = sheet.get_all_records()
    if records:
        df = pd.DataFrame(records)
        st.dataframe(df, use_container_width=True)
        st.metric("目前總花費", f"${df['金額'].sum()}")

elif selected == "旅遊地圖":
    st.title("🌍 我們的足跡")
    st.map(pd.DataFrame({'lat': [25.0339], 'lon': [121.5644]}))

elif selected == "回憶相簿":
    st.title("📸 相簿區")
    st.info("這裡可以放我們出去玩的照片...")