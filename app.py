import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import random
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- 暫時的密碼清洗工具 (開始) ---
try:
    # 讀取你的 secrets.json
    with open("secrets.json", "r") as f:
        data = json.load(f)
        # 把它壓縮成一行 (這樣就絕對不會有格式問題！)
        clean_json = json.dumps(data)
        
        st.error("👇 這是你的完美格式密碼，請直接複製這個框框裡的內容：")
        # 顯示正確的 TOML 格式
        st.code(f"[gcp]\njson_file = '{clean_json}'", language="toml")
        st.info("複製完去貼上後，記得回來把這段程式碼刪掉喔！")
        st.stop() # 讓網頁停在這裡
except FileNotFoundError:
    pass # 如果沒檔案就不執行
# --- 暫時的密碼清洗工具 (結束) ---
st.set_page_config(page_title="我們的專屬小窩", layout="wide")

with st.sidebar:
    selected = option_menu(
        menu_title="功能選單",
        options=["首頁", "今天吃什麼", "記帳小管家", "旅遊地圖", "回憶相簿"],
        icons=["house", "egg-fried", "currency-dollar", "map", "images"],
        menu_icon="heart",
        default_index=0,
    )

# --- 共用連線函式 (最終防崩潰版) ---
@st.cache_resource
def get_google_sheet_client():
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    creds = None
    
    # 1. 嘗試讀取雲端保險箱 (專門給 Streamlit Cloud 用)
    try:
        # 這裡加了 try-except，如果本地沒有設定保險箱，會直接跳過，不會報錯！
        if "gcp" in st.secrets:
            key_dict = json.loads(st.secrets["gcp"]["json_file"])
            creds = ServiceAccountCredentials.from_json_keyfile_dict(key_dict, scope)
    except Exception as e:
        pass # 如果保險箱失敗，就安靜地跳過

    # 2. 如果上面失敗了，嘗試讀取本地檔案 (給你的電腦用)
    if creds is None:
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name('secrets.json', scope)
        except Exception as e:
            st.error(f"找不到鑰匙！請確認 secrets.json 有在資料夾內。錯誤：{e}")
            st.stop()
            
    client = gspread.authorize(creds)
    return client

if selected == "首頁":
    st.title("歡迎回家！💑")
    st.success("這是我們一起開發的第一個網站！")

elif selected == "今天吃什麼":
    st.title("🍔 選擇困難救星")
    food_list = ["麥當勞", "火鍋", "義大利麵", "壽司", "鹹酥雞"]
    if st.button("幫我們決定！"):
        st.header(f"✨ {random.choice(food_list)} ✨")

# --- 這裡是重點修改區 ---
elif selected == "記帳小管家":
    st.title("💰 雲端記帳本")
    try:
        client = get_google_sheet_client()
        sheet = client.open("OurLoveMoney").sheet1 # 抓第一頁
        st.toast("連線成功")
    except Exception as e:
        st.error(f"連線失敗: {e}")
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
        
        if st.button("上傳雲端", key="add_money"):
            from datetime import datetime
            date_str = datetime.now().strftime("%Y-%m-%d")
            sheet.append_row([date_str, item, price, payer])
            st.success("記帳成功！")
            st.cache_data.clear()

    # 顯示區
    records = sheet.get_all_records()
    if records:
        st.dataframe(pd.DataFrame(records), use_container_width=True)

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
    st.title("📸 我們的甜蜜回憶")
    
    # 1. 建立分頁 (Tab)
    # 這樣可以把照片分類，不會全部擠在一起
    tab1, tab2, tab3 = st.tabs(["甜蜜合照", "旅遊風景", "黑歷史(誤)"])

    # --- 第一個分頁：上傳區 ---
    with tab1:
        st.header("上傳一張新照片看看！")
        
        # 檔案上傳元件
        uploaded_file = st.file_uploader("選擇一張照片...", type=['jpg', 'png', 'jpeg'])
        
        if uploaded_file is not None:
            # 顯示剛上傳的照片
            st.image(uploaded_file, caption="剛上傳的照片", use_container_width=True)
            st.balloons() # 放個氣球慶祝一下
            st.success("照片上傳成功！好看嗎？")
            st.info("⚠️ 小提醒：目前因為還沒連上雲端，重新整理網頁後這張照片會消失喔！")

    # --- 第二個分頁：固定照片展示 ---
    with tab2:
        st.header("去過的地方")
        col1, col2 = st.columns(2)
        with col1:
            # 這裡示範怎麼顯示網路上的圖片 (最簡單的方法)
            st.image("https://images.unsplash.com/photo-1526772662000-3f88f107f5d8", caption="未來要去迪士尼！")
        with col2:
            st.image("https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1", caption="想去瑞士看山")

    # --- 第三個分頁：趣味區 ---
    with tab3:
        st.header("專屬收藏")
        st.write("這裡可以放一些只有你們懂的梗圖或醜照 😂")
        # 示範按鈕互動
        if st.button("查看男朋友的秘密"):
            st.error("權限不足！只有女朋友可以看！(開玩笑的)")
