import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import random
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from datetime import date # 新增這一行

st.set_page_config(page_title="我們的專屬小窩", page_icon="☀️", layout="wide")

# 👇 請記得把這裡換成妳 Google Drive 的資料夾 ID (那串亂碼)
FOLDER_ID = "1sr5pM4dii95MR3n4NIObXiz6pPInUee9?usp=sharing"

# 👇 【請修改這裡】 2. 設定你們的交往紀念日 (格式：年, 月, 日)
LOVE_START_DATE = date(2025, 9, 17)

# --- 側邊欄 ---
with st.sidebar:
    selected = option_menu(
        menu_title="功能選單",
        options=["首頁", "今天吃什麼", "記帳小管家", "旅遊地圖", "回憶相簿"],
        icons=["house", "egg-fried", "currency-dollar", "map", "images"],
        menu_icon="heart",
        default_index=0,
    )

# --- 共用連線函式 (這裡是關鍵！必須要有 get_creds) ---
@st.cache_resource
def get_creds():
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    creds = None
    
    # 1. 雲端保險箱
    if "gcp" in st.secrets:
        try:
            key_dict = json.loads(st.secrets["gcp"]["json_file"])
            creds = ServiceAccountCredentials.from_json_keyfile_dict(key_dict, scope)
        except Exception as e:
            st.error(f"保險箱讀取錯誤: {e}")
    
    # 2. 本地檔案
    if creds is None:
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name('secrets.json', scope)
        except:
            st.error("找不到鑰匙！請確認 secrets.json 或雲端 Secrets 設定正確。")
            st.stop()
            
    return creds

# --- 上傳檔案到 Google Drive 的函式 ---
def upload_image_to_drive(file_obj, filename, folder_id, creds):
    try:
        service = build('drive', 'v3', credentials=creds)
        
        file_metadata = {
            'name': filename,
            'parents': [folder_id]
        }
        
        media = MediaIoBaseUpload(file_obj, mimetype=file_obj.type)
        
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        service.permissions().create(
            fileId=file.get('id'),
            body={'role': 'reader', 'type': 'anyone'}
        ).execute()
        
        file_id = file.get('id')
        return f"https://drive.google.com/uc?export=view&id={file_id}"
        
    except Exception as e:
        st.error(f"上傳失敗: {e}")
        return None

def get_price_label(price_code):
    # 如果讀到的是文字，嘗試轉成數字，轉不過就回傳原文字
    try:
        code = int(price_code)
    except:
        return str(price_code)

    if code == 1:
        return "$0 - $100"
    elif code == 2:
        return "$101 - $300"
    elif code == 3:
        return "$301 以上"
    else:
        return str(code)

# --- 頁面內容 ---

if selected == "首頁":
    st.title("歡迎回家！☀️✨")
    
    # --- 計算天數邏輯 ---
    today = date.today()
    # 1. 在一起天數
    days_together = (today - LOVE_START_DATE).days
    
    # 2. 下次紀念日倒數
    this_year_anniversary = date(today.year, LOVE_START_DATE.month, LOVE_START_DATE.day)
    if this_year_anniversary < today:
        # 如果今年的紀念日已經過了，就算明年的
        next_anniversary = date(today.year + 1, LOVE_START_DATE.month, LOVE_START_DATE.day)
    else:
        next_anniversary = this_year_anniversary
        
    days_countdown = (next_anniversary - today).days

    # --- 顯示數據 (使用卡片樣式) ---
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="💕 我們已經在一起", value=f"{days_together} 天")
    with col2:
        st.metric(label="🎂 距離週年紀念日還有", value=f"{days_countdown} 天")

elif selected == "今天吃什麼":
    st.title("🍔 吃飯選擇困難救星")

    # 連線到 Restaurants 分頁
    creds = get_creds()
    client = gspread.authorize(creds)
    try:
        res_sheet = client.open("OurLoveMoney").worksheet("Restaurants")
    except:
        st.error("找不到 'Restaurants' 分頁，請去 Google 試算表新增一個！")
        st.stop()

    # --- 功能 1: 顯示目前的口袋名單 & 篩選 ---
    all_restaurants = res_sheet.get_all_records()
    
    if not all_restaurants:
        st.warning("目前口袋名單是空的，快用下面的功能新增第一家餐廳吧！")
    else:
        # 準備資料
        df_res = pd.DataFrame(all_restaurants)
        
        # 篩選器介面
        st.write("---")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("💰 預算區間？")
            price_options = [1, 2, 3]
            selected_prices = st.multiselect(
                "選擇價格", 
                options=price_options, 
                default=price_options,
                format_func=get_price_label # 使用新的價格顯示函式
            )
        with col2:
            st.subheader("🍜 想吃哪一類？")
            # 確保類型不重複
            all_types = sorted(list(set(str(r['類型']) for r in all_restaurants)))
            selected_types = st.multiselect("選擇類型", options=all_types, default=all_types)

        # 決定按鈕
        st.write("---")
        if st.button("幫我們決定！", type="primary", use_container_width=True):
            # 篩選邏輯
            candidates = [
                r for r in all_restaurants 
                if r['價位'] in selected_prices and str(r['類型']) in selected_types
            ]
            
            if candidates:
                final_choice = random.choice(candidates)
                st.balloons()
                st.header(f"✨ 今天就吃：{final_choice['餐廳名稱']} ✨")
                p_label = get_price_label(final_choice['價位'])
                st.success(f"類型：{final_choice['類型']} | 預算：{p_label}")
            else:
                st.warning("沒有符合條件的餐廳，請放寬標準！")

    # --- 功能 2: 手機快速新增餐廳 ---
    with st.expander("➕ 新增餐廳到口袋名單", expanded=False):
        st.write("輸入餐廳資訊，下次就能抽到它！")
        with st.form("add_res_form"):
            new_name = st.text_input("餐廳名稱")
            col_a, col_b = st.columns(2)
            with col_a:
                new_type = st.text_input("類型 (如: 拉麵, 火鍋)")
            with col_b:
                # 這裡的選項也改成顯示價格區間
                new_price = st.selectbox(
                    "預算區間", 
                    options=[1, 2, 3], 
                    format_func=get_price_label
                )
            
            submitted = st.form_submit_button("加入名單")
            if submitted:
                if new_name and new_type:
                    res_sheet.append_row([new_name, new_type, new_price])
                    st.success(f"已加入：{new_name}")
                    st.cache_data.clear() # 清除快取以更新名單
                    st.rerun()
                else:
                    st.warning("名稱和類型都要填喔！")


elif selected == "記帳小管家":
    st.title("💰 雲端記帳本")
    creds = get_creds()
    client = gspread.authorize(creds)
    try:
        sheet = client.open("OurLoveMoney").sheet1
    except Exception as e:
        st.error(f"連線失敗，請檢查 Google 試算表名稱是否為 OurLoveMoney。錯誤：{e}")
        st.stop()

    with st.container(border=True):
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            item = st.text_input("消費項目")
        with col2:
            price = st.number_input("金額", min_value=0, step=10)
        with col3:
            payer = st.selectbox("誰付的？", ["寶寶", "白白"])
        
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
    st.title("🌍 我們的足跡地圖")
    
    # 記得要在最上面 import pandas (如果你之前的程式碼已經有 import pandas as pd 則不用重複寫)
    import pandas as pd 

    # 1. 初始化：如果沒有資料，先給兩個預設地點 (台北101、高雄駁二) 讓地圖不要空白
    if 'map_data' not in st.session_state:
        st.session_state.map_data = pd.DataFrame({
            'lat': [25.0339, 22.6204],  # 緯度
            'lon': [121.5644, 120.2816] # 經度
        })

    # 2. 顯示地圖 (這行指令最強大，直接畫出地圖！)
    st.map(st.session_state.map_data)

    # 3. 新增地點的功能
    st.divider()
    st.subheader("📍 標記新地點")
    
    with st.expander("教我怎麼找經緯度？"):
        st.write("1. 打開 Google Maps")
        st.write("2. 在你想去的地方按「滑鼠右鍵」")
        st.write("3. 第一個出現的數字串就是經緯度！(點一下就會複製)")
        st.write("4. 格式通常是：24.1234, 120.5678 (前面是緯度 lat，後面是經度 lon)")

    col1, col2 = st.columns(2)
    with col1:
        input_lat = st.number_input("緯度 (Latitude)", format="%.4f", value=24.1446)
    with col2:
        input_lon = st.number_input("經度 (Longitude)", format="%.4f", value=120.6839)

    if st.button("加入地圖"):
        # 建立新地點的資料
        new_point = pd.DataFrame({'lat': [input_lat], 'lon': [input_lon]})
        # 把新地點合併到原本的資料中
        st.session_state.map_data = pd.concat([st.session_state.map_data, new_point], ignore_index=True)
        st.success("成功標記！往上看地圖多了一個點！")
        st.rerun() # 重新整理網頁，讓地圖立刻更新

elif selected == "回憶相簿":
    st.title("📸 我們的精選回憶")
    
    creds = get_creds()
    client = gspread.authorize(creds)
    try:
        photo_sheet = client.open("OurLoveMoney").worksheet("Photos")
    except:
        st.error("找不到 'Photos' 分頁，請去試算表新增一個！")
        st.stop()

    # --- 手機上傳專區 ---
    with st.expander("➕ 新增照片 (手機上傳版)", expanded=True):
        st.write("直接從手機相簿選照片，機器人會自動幫你上傳到 Google Drive！")
        
        # 1. 輸入描述
        p_note = st.text_input("這張照片的故事...")
        
        # 2. 上傳按鈕
        uploaded_file = st.file_uploader("選擇一張照片...", type=['jpg', 'png', 'jpeg'])
        
        if uploaded_file is not None:
            if st.button("開始上傳 & 儲存", type="primary"):
                if p_note:
                    with st.spinner('正在把照片傳給機器人...請稍等...'):
                        # A. 上傳到 Google Drive
                        image_link = upload_image_to_drive(uploaded_file, uploaded_file.name, FOLDER_ID, creds)
                        
                        if image_link:
                            # B. 儲存連結到試算表
                            from datetime import datetime
                            date_str = datetime.now().strftime("%Y-%m-%d")
                            photo_sheet.append_row([date_str, p_note, image_link])
                            st.success("🎉 上傳成功！照片已永久保存！")
                            st.cache_data.clear()
                else:
                    st.warning("請先寫一點照片的故事喔！")

    st.divider()
    records = photo_sheet.get_all_records()
    if records:
        for row in reversed(records):
            if row['網址']:
                st.image(row['網址'], caption=f"{row['日期']} - {row['描述']}", use_container_width=True)
                st.markdown("---")