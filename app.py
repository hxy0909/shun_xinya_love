import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import random
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

st.set_page_config(page_title="我們的專屬小窩", layout="wide")

FOLDER_ID = "1sr5pM4dii95MR3n4NIObXiz6pPInUee9?usp=sharing"

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

def upload_image_to_drive(file_obj, filename, folder_id, creds):
    try:
        # 建立 Drive 服務
        service = build('drive', 'v3', credentials=creds)
        
        file_metadata = {
            'name': filename,
            'parents': [folder_id]
        }
        
        media = MediaIoBaseUpload(file_obj, mimetype=file_obj.type)
        
        # 執行上傳
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        # 設定權限為公開 (這樣網頁才看得到)
        service.permissions().create(
            fileId=file.get('id'),
            body={'role': 'reader', 'type': 'anyone'}
        ).execute()
        
        # 產生圖片直接連結
        file_id = file.get('id')
        return f"https://drive.google.com/uc?export=view&id={file_id}"
        
    except Exception as e:
        st.error(f"上傳失敗: {e}")
        return None


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
    
    # --- Google Drive 連結翻譯機 ---
    def fix_google_drive_url(url):
        if "drive.google.com" in url:
            # 如果是 Google Drive 的連結，進行轉換
            file_id = url.split('/')[-2]
            if "id=" in url: # 另一種格式
                 file_id = url.split('id=')[-1].split('&')[0]
            # 變成可以直接顯示的圖片網址
            return f"https://drive.google.com/uc?export=view&id={file_id}"
        return url

    # 1. 連線到 Google Sheet
    try:
        client = get_google_sheet_client()
        photo_sheet = client.open("OurLoveMoney").worksheet("Photos")
    except:
        st.error("找不到 'Photos' 分頁，請去 Google 試算表新增一個喔！")
        st.stop()

    # 2. 新增照片區
    with st.expander("➕ 新增照片到回憶牆"):
        st.info("💡 小撇步：把照片上傳到 Google Drive，按右鍵「取得連結」(記得開權限：知道連結的人均可檢視)，然後把連結貼過來就好囉！")
        p_note = st.text_input("這張照片的故事...")
        p_url_input = st.text_input("照片網址 (支援 Google Drive 分享連結)")
        
        if st.button("永久收藏"):
            if p_note and p_url_input:
                # 在存入之前，先用翻譯機轉換一下
                final_url = fix_google_drive_url(p_url_input)
                
                from datetime import datetime
                date_str = datetime.now().strftime("%Y-%m-%d")
                photo_sheet.append_row([date_str, p_note, final_url])
                st.success("回憶已儲存！")
                st.cache_data.clear()
            else:
                st.warning("描述和網址都要填喔！")

    # 3. 顯示相簿牆
    st.divider()
    records = photo_sheet.get_all_records()
    
    if records:
        for row in reversed(records):
            if row['網址']:
                # 顯示圖片 (這裡不用再轉了，因為存進去的時候已經轉好了)
                st.image(row['網址'], caption=f"{row['日期']} - {row['描述']}", use_container_width=True)
                st.markdown("---")
    else:

        st.info("目前還沒有照片，快去貼上第一張精選回憶吧！")