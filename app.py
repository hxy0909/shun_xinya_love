import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import random
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="我們的專屬小窩", layout="wide")

with st.sidebar:
    selected = option_menu(
        menu_title="功能選單",
        options=["首頁", "今天吃什麼", "記帳小管家", "旅遊地圖", "回憶相簿", "願望清單"],
        icons=["house", "egg-fried", "currency-dollar", "map", "images", "gift"],
        menu_icon="heart",
        default_index=0,
    )

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

    # 連線函式
    # --- 連接 Google Sheets 的函式 (簡單檔案版) ---
   # --- 連接 Google Sheets 的函式 (終極雙棲版) ---
    @st.cache_resource
    def get_google_sheet():
        scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
        
        creds = None
        
        # 1. 優先嘗試：從雲端保險箱讀取 (給 Streamlit Cloud 用)
        # 我們檢查保險箱裡有沒有剛剛設定的 "gcp"
        if "gcp" in st.secrets:
            try:
                # 這裡用 json.loads 把那串文字變回 Python 字典
                key_dict = json.loads(st.secrets["gcp"]["json_file"])
                creds = ServiceAccountCredentials.from_json_keyfile_dict(key_dict, scope)
            except Exception as e:
                st.error(f"保險箱讀取失敗: {e}")
        
        # 2. 備用方案：從電腦檔案讀取 (給 Localhost 用)
        if creds is None:
            # 只有當上面沒抓到時，才會來讀這個檔案
            creds = ServiceAccountCredentials.from_json_keyfile_name('secrets.json', scope)
            
        client = gspread.authorize(creds)
        sheet = client.open("OurLoveMoney").sheet1
        return sheet

    # 嘗試連線
    try:
        sheet = get_google_sheet()
        st.toast("✅ 雲端連線成功！") # 成功會跳出小通知
    except Exception as e:
        st.error(f"連線失敗！請檢查 secrets.json 或試算表名稱。錯誤訊息：{e}")
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
                
                # 寫入 Google Sheet
                st.info("資料上傳中...")
                sheet.append_row([date_str, item, price, payer])
                
                st.success("✅ 記帳成功！已儲存")
                # 清除快取以顯示最新資料
                st.cache_data.clear()
            else:
                st.warning("請輸入完整資料")

    # 顯示區
    st.divider()
    # 讀取資料
    records = sheet.get_all_records()
    
    if len(records) > 0:
        df = pd.DataFrame(records)
        st.dataframe(df, use_container_width=True)
        
        # 統計
        total = df["金額"].sum()
        st.metric("目前總花費", f"${total}")
    else:
        st.info("目前試算表是空的，快記下第一筆吧！")

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

# ... (前面的程式碼不用動) ...

elif selected == "願望清單":
    st.title("🎁 我們的願望清單")

    # 1. 連線到 "Wishlist" 分頁
    # 注意：這裡我們直接用原本的連線函式，只是改抓不同的工作表
    @st.cache_resource
    def get_wishlist_sheet():
        scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name('secrets.json', scope)
        client = gspread.authorize(creds)
        # 抓取名為 "Wishlist" 的分頁
        sheet = client.open("OurLoveMoney").worksheet("Wishlist")
        return sheet

    try:
        wish_sheet = get_wishlist_sheet()
    except Exception as e:
        st.error("找不到 'Wishlist' 分頁，請去 Google 試算表新增一個喔！")
        st.stop()

    # 2. 輸入區
    with st.expander("✨ 許下一個新願望", expanded=False):
        w_col1, w_col2 = st.columns([3, 1])
        with w_col1:
            wish_item = st.text_input("想要什麼？", placeholder="例如：Switch遊戲片、情侶鞋...")
        with w_col2:
            wisher = st.selectbox("許願者", ["我", "男朋友"], key="wisher") # key不能重複
        
        note = st.text_input("備註 (例如連結或價格)")

        if st.button("加入清單 ✨"):
            if wish_item:
                wish_sheet.append_row([wish_item, wisher, note])
                st.success(f"許願成功！希望 {wish_item} 早日入手！")
                st.cache_data.clear() # 清除快取以顯示最新資料
            else:
                st.warning("要寫想要什麼喔！")

    # 3. 清單顯示區 (這裡教你用 Checkbox 做成打勾清單！)
    st.subheader("待實現清單")
    
    # 讀取資料
    w_records = wish_sheet.get_all_records()
    
    if len(w_records) > 0:
        for i, row in enumerate(w_records):
            # 顯示格式： [誰的願望] 物品名稱 (備註)
            st.markdown(f"**{i+1}. [{row['誰許願的']}] {row['想買的東西']}**")
            if row['備註']:
                st.caption(f"   └ 備註：{row['備註']}")
            st.divider()
    else:
        st.info("目前沒有願望，是不是太知足了？😆")