import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import random
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from datetime import datetime, date
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import pydeck as pdk # 👈 新增這個強大的地圖工具！

st.set_page_config(page_title="我們的專屬小窩", page_icon="☀️", layout="wide")

# 👇 請記得把這裡換成妳 Google Drive 的資料夾 ID (那串亂碼)
FOLDER_ID = "1sr5pM4dii95MR3n4NIObXiz6pPInUee9"

# 👇 【請修改這裡】 2. 設定你們的交往紀念日 (格式：年, 月, 日)
LOVE_START_DATE = date(2025, 9, 17)

# 👇 【請修改這裡】 3. 貼上你們想聽的 YouTube 歌曲網址 (例如: Ed Sheeran - Perfect)
THEME_SONG_URL = "https://youtu.be/in8NNzwFa-s?si=GJlc9xHCFJxvPxF4" 


TAIWAN_DATA = {
    "基隆市": ["仁愛區", "信義區", "中正區", "中山區", "安樂區", "暖暖區", "七堵區"],
    "臺北市": ["中正區", "大同區", "中山區", "松山區", "大安區", "萬華區", "信義區", "士林區", "北投區", "內湖區", "南港區", "文山區"],
    "新北市": ["萬里區", "金山區", "板橋區", "汐止區", "深坑區", "石碇區", "瑞芳區", "平溪區", "雙溪區", "貢寮區", "新店區", "坪林區", "烏來區", "永和區", "中和區", "土城區", "三峽區", "樹林區", "鶯歌區", "三重區", "新莊區", "泰山區", "林口區", "蘆洲區", "五股區", "八里區", "淡水區", "三芝區", "石門區"],
    "桃園市": ["中壢區", "平鎮區", "龍潭區", "楊梅區", "新屋區", "觀音區", "桃園區", "龜山區", "八德區", "大溪區", "復興區", "大園區", "蘆竹區"],
    "新竹市": ["東區", "北區", "香山區"],
    "新竹縣": ["竹北市", "湖口鄉", "新豐鄉", "新埔鎮", "關西鎮", "芎林鄉", "寶山鄉", "竹東鎮", "五峰鄉", "橫山鄉", "尖石鄉", "北埔鄉", "峨眉鄉"],
    "苗栗縣": ["竹南鎮", "頭份市", "三灣鄉", "南庄鄉", "獅潭鄉", "後龍鎮", "通霄鎮", "苑裡鎮", "苗栗市", "造橋鄉", "頭屋鄉", "公館鄉", "大湖鄉", "泰安鄉", "銅鑼鄉", "三義鄉", "西湖鄉", "卓蘭鎮"],
    "臺中市": ["中區", "東區", "南區", "西區", "北區", "北屯區", "西屯區", "南屯區", "太平區", "大里區", "霧峰區", "烏日區", "豐原區", "后里區", "石岡區", "東勢區", "和平區", "新社區", "潭子區", "大雅區", "神岡區", "大肚區", "沙鹿區", "龍井區", "梧棲區", "清水區", "大甲區", "外埔區", "大安區"],
    "彰化縣": ["彰化市", "芬園鄉", "花壇鄉", "秀水鄉", "鹿港鎮", "福興鄉", "線西鄉", "和美鎮", "伸港鄉", "員林市", "社頭鄉", "永靖鄉", "埔心鄉", "溪湖鎮", "大村鄉", "埔鹽鄉", "田中鎮", "北斗鎮", "田尾鄉", "埤頭鄉", "溪州鄉", "竹塘鄉", "二林鎮", "大城鄉", "芳苑鄉", "二水鄉"],
    "南投縣": ["南投市", "中寮鄉", "草屯鎮", "國姓鄉", "埔里鎮", "仁愛鄉", "名間鄉", "集集鎮", "水里鄉", "魚池鄉", "信義鄉", "竹山鎮", "鹿谷鄉"],
    "雲林縣": ["斗南鎮", "大埤鄉", "虎尾鎮", "土庫鎮", "褒忠鄉", "東勢鄉", "臺西鄉", "崙背鄉", "麥寮鄉", "斗六市", "林內鄉", "古坑鄉", "莿桐鄉", "西螺鎮", "二崙鄉", "北港鎮", "水林鄉", "口湖鄉", "四湖鄉", "元長鄉"],
    "嘉義市": ["東區", "西區"],
    "嘉義縣": ["番路鄉", "梅山鄉", "竹崎鄉", "阿里山鄉", "中埔鄉", "大埔鄉", "水上鄉", "鹿草鄉", "太保市", "朴子市", "東石鄉", "六腳鄉", "新港鄉", "民雄鄉", "大林鎮", "溪口鄉", "義竹鄉", "布袋鎮"],
    "臺南市": ["中西區", "東區", "南區", "北區", "安平區", "安南區", "永康區", "歸仁區", "新化區", "左鎮區", "玉井區", "楠西區", "南化區", "仁德區", "關廟區", "龍崎區", "官田區", "麻豆區", "佳里區", "西港區", "七股區", "將軍區", "學甲區", "北門區", "新營區", "後壁區", "白河區", "東山區", "六甲區", "下營區", "柳營區", "鹽水區", "善化區", "大內區", "山上區", "新市區", "安定區"],
    "高雄市": ["新興區", "前金區", "苓雅區", "鹽埕區", "鼓山區", "旗津區", "前鎮區", "三民區", "楠梓區", "小港區", "左營區", "仁武區", "大社區", "東沙群島", "南沙群島", "岡山區", "路竹區", "阿蓮區", "田寮區", "燕巢區", "橋頭區", "梓官區", "彌陀區", "永安區", "湖內區", "鳳山區", "大寮區", "林園區", "鳥松區", "大樹區", "旗山區", "美濃區", "六龜區", "內門區", "杉林區", "甲仙區", "桃源區", "那瑪夏區", "茂林區", "茄萣區"],
    "屏東縣": ["屏東市", "三地門鄉", "霧臺鄉", "瑪家鄉", "九如鄉", "里港鄉", "高樹鄉", "鹽埔鄉", "長治鄉", "麟洛鄉", "竹田鄉", "內埔鄉", "萬丹鄉", "潮州鎮", "泰武鄉", "來義鄉", "萬巒鄉", "崁頂鄉", "新埤鄉", "南州鄉", "林邊鄉", "東港鎮", "琉球鄉", "佳冬鄉", "新園鄉", "枋寮鄉", "枋山鄉", "春日鄉", "獅子鄉", "車城鄉", "牡丹鄉", "恆春鎮", "滿州鄉"],
    "宜蘭縣": ["宜蘭市", "頭城鎮", "礁溪鄉", "壯圍鄉", "員山鄉", "羅東鎮", "三星鄉", "大同鄉", "五結鄉", "冬山鄉", "蘇澳鎮", "南澳鄉"],
    "花蓮縣": ["花蓮市", "新城鄉", "秀林鄉", "吉安鄉", "壽豐鄉", "鳳林鎮", "光復鄉", "豐濱鄉", "瑞穗鄉", "萬榮鄉", "玉里鎮", "卓溪鄉", "富里鄉"],
    "臺東縣": ["臺東市", "綠島鄉", "蘭嶼鄉", "延平鄉", "卑南鄉", "鹿野鄉", "關山鎮", "海端鄉", "池上鄉", "東河鄉", "成功鎮", "長濱鄉", "太麻里鄉", "金峰鄉", "大武鄉", "達仁鄉"],
    "澎湖縣": ["馬公市", "西嶼鄉", "望安鄉", "七美鄉", "白沙鄉", "湖西鄉"],
    "金門縣": ["金沙鎮", "金湖鎮", "金寧鄉", "金城鎮", "烈嶼鄉", "烏坵鄉"],
    "連江縣": ["南竿鄉", "北竿鄉", "莒光鄉", "東引鄉"]
}

# --- 側邊欄 ---
with st.sidebar:
    selected = option_menu(
        menu_title="功能選單",
        options=["首頁", "要吃什麼", "去哪裡玩", "旅遊計畫", "記帳管家", "旅遊地圖", "使用說明"],
        icons=["house", "egg-fried", "airplane-engines", "journal-bookmark", "currency-dollar", "map", "book"],
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

# --- 價格顯示轉換小工具 (吃飯用) ---
def get_price_label(price_code):
    # 如果讀到的是文字，嘗試轉成數字，轉不過就回傳原文字
    try:
        code = int(price_code)
    except:
        return str(price_code)

    if code == 1:
        return "0 - 200"
    elif code == 2:
        return "201 - 400"
    elif code == 3:
        return "401 以上"
    else:
        return str(code)

# --- 價格顯示轉換小工具 (旅遊用) ---
def get_play_price_label(price_code):
    try:
        code = int(price_code)
    except:
        return str(price_code)
    if code == 1: return "免費 / 銅板價"
    elif code == 2: return "百元 (門票/低消)"
    elif code == 3: return "千元 (樂園/住宿)"
    else: return str(code)

# --- 頁面內容 ---
if selected == "首頁":
    st.title("歡迎回家！💑")
    st.markdown("---")
    today = date.today()
    days_together = (today - LOVE_START_DATE).days
    this_year_anniversary = date(today.year, LOVE_START_DATE.month, LOVE_START_DATE.day)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            f"""
            <div style="text-align: center;">
                <h3 style="color: #666; margin-bottom: 10px;">💕 我們已經在一起</h3>
                <h1 style="color: #000000; font-size: 60px; margin-top: 0px;">{days_together} 天</h1>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    st.markdown("---")
    
    col_bgm1, col_bgm2, col_bgm3 = st.columns([1, 2, 1])
    with col_bgm2:
        st.markdown("<h3 style='text-align: center; color: #666;'>🎵 我們的專屬 BGM</h3>", unsafe_allow_html=True)
        st.link_button("▶️ 點擊播放我們的歌 (YouTube)", THEME_SONG_URL, use_container_width=True)
    
    st.success("這是我們一起開發的第一個網站！")

elif selected == "要吃什麼":
    st.title("🍔 吃飯選擇困難救星")
    creds = get_creds()
    client = gspread.authorize(creds)
    try:
        res_sheet = client.open("OurLoveMoney").worksheet("Restaurants")
    except:
        st.error("⚠️ 找不到 'Restaurants' 分頁！")
        st.stop()

    all_restaurants = res_sheet.get_all_records()
    st.write("---")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📍 縣市")
        existing_cities = list(TAIWAN_DATA.keys())
        selected_cities = st.multiselect("縣市", options=existing_cities)
    with c2:
        st.subheader("🏘️ 地區")
        available_districts = []
        if selected_cities:
            for city in selected_cities:
                if city in TAIWAN_DATA: available_districts.extend(TAIWAN_DATA[city])
        else:
            available_districts = sorted(list(set([str(r.get('地區', '')) for r in all_restaurants if r.get('地區')])))
        selected_districts = st.multiselect("地區", options=available_districts)

    c3, c4 = st.columns(2)
    with c3:
        st.subheader("💰 預算")
        price_options = [1, 2, 3]
        selected_prices = st.multiselect("價格", options=price_options, default=price_options, format_func=get_price_label)
    with c4:
        st.subheader("🍜 類型")
        all_types = sorted(list(set(str(r['類型']) for r in all_restaurants))) if all_restaurants else []
        selected_types = st.multiselect("類型", options=all_types, default=all_types)

    st.write("---")
    if st.button("幫我們決定！", type="primary", use_container_width=True):
        candidates = []
        for r in all_restaurants:
            if selected_cities and r.get('縣市') not in selected_cities: continue
            if selected_districts and r.get('地區') not in selected_districts: continue
            if r['價位'] not in selected_prices: continue
            if str(r['類型']) not in selected_types: continue
            candidates.append(r)
        
        if candidates:
            final_choice = random.choice(candidates)
            st.balloons()
            st.header(f"✨ 今天就吃：{final_choice['餐廳名稱']} ✨")
            p_label = get_price_label(final_choice['價位'])
            st.success(f"📍 {final_choice.get('縣市', '')}{final_choice.get('地區', '')} | {final_choice['類型']} | {p_label}")
        else:
            st.warning("🥺 沒找到餐廳... 試著放寬條件？")

    with st.expander("➕ 新增餐廳到口袋名單", expanded=False):
        st.info("👇 請先在這裡選擇地點")
        col_city, col_dist = st.columns(2)
        with col_city:
            new_city = st.selectbox("縣市", options=list(TAIWAN_DATA.keys()), index=list(TAIWAN_DATA.keys()).index("臺北市"))
        with col_dist:
            new_district = st.selectbox("地區", options=TAIWAN_DATA[new_city])
        with st.form("add_res_form"):
            new_name = st.text_input("餐廳名稱")
            col_a, col_b = st.columns(2)
            with col_a:
                new_type = st.text_input("類型 (如: 拉麵, 火鍋)")
            with col_b:
                new_price = st.selectbox("預算區間", options=[1, 2, 3], format_func=get_price_label)
            if st.form_submit_button("加入名單"):
                if new_name and new_type:
                    res_sheet.append_row([new_name, new_type, new_price, new_city, new_district])
                    st.success(f"✅ 已加入：{new_city}{new_district} 的 {new_name}")
                    st.cache_data.clear()
                    st.rerun()

elif selected == "去哪裡玩":
    st.title("🎢 出遊選擇困難救星")
    creds = get_creds()
    client = gspread.authorize(creds)
    try:
        # 記得新增 PlayList 分頁！
        play_sheet = client.open("OurLoveMoney").worksheet("PlayList")
    except:
        st.error("⚠️ 找不到 'PlayList' 分頁！請去試算表新增，標題：地點、縣市、類型、預算、備註")
        st.stop()

    all_places = play_sheet.get_all_records()
    
    st.write("---")
    if not all_places:
        st.info("目前還沒有景點名單，快來新增第一個想去的地方吧！👇")
    else:
        # --- 篩選器 ---
        c1, c2, c3 = st.columns(3)
        with c1:
            st.subheader("🚗 縣市")
            existing_cities = sorted(list(set([str(r.get('縣市', '')) for r in all_places if r.get('縣市')])))
            selected_cities = st.multiselect("選擇縣市", options=existing_cities)
        
        with c2:
            st.subheader("🎨 類型")
            all_types = sorted(list(set(str(r['類型']) for r in all_places)))
            selected_types = st.multiselect("選擇類型", options=all_types)

        with c3:
            st.subheader("💰 預算")
            price_options = [1, 2, 3]
            selected_prices = st.multiselect("選擇預算", options=price_options, default=price_options, format_func=get_play_price_label)

        st.write("---")
        if st.button("🎲 幫我們決定去哪玩！", type="primary", use_container_width=True):
            candidates = []
            for r in all_places:
                # 1. 篩選縣市
                if selected_cities and r.get('縣市') not in selected_cities:
                    continue
                # 2. 篩選類型
                if selected_types and r.get('類型') not in selected_types:
                    continue
                # 3. 篩選預算 (新功能)
                if selected_prices and r.get('預算') not in selected_prices:
                    continue
                candidates.append(r)
            
            if candidates:
                final_choice = random.choice(candidates)
                st.balloons()
                st.markdown(f"## 🎯 決定了！就去：**{final_choice['地點']}**")
                p_label = get_play_price_label(final_choice.get('預算', 1)) # 預設為1
                st.success(f"📍 {final_choice['縣市']} | {final_choice['類型']} | 💰 {p_label}")
                if final_choice.get('備註'):
                    st.info(f"💡 筆記：{final_choice['備註']}")
            else:
                st.warning("🥺 嗚嗚，這個條件下沒有景點... 試著放寬一點？")

    # --- 新增景點功能 ---
    st.divider()
    with st.expander("➕ 新增想去的口袋名單", expanded=False):
        with st.form("add_play_form"):
            new_place = st.text_input("景點名稱")
            
            c_city, c_type = st.columns(2)
            with c_city:
                new_city = st.selectbox("縣市", options=list(TAIWAN_DATA.keys()))
            with c_type:
                new_type = st.text_input("類型 (如: 戶外, 室內, 逛街, 樂園)")
            
            c_price, c_note = st.columns(2)
            with c_price:
                # 這裡增加預算選擇
                new_price = st.selectbox("預算", options=[1, 2, 3], format_func=get_play_price_label)
            with c_note:
                new_note = st.text_input("備註 (如: 門票價格, 營業時間)")
            
            if st.form_submit_button("加入願望清單"):
                if new_place and new_type:
                    play_sheet.append_row([new_place, new_city, new_type, new_price, new_note])
                    st.success(f"✅ 已加入願望：{new_city} 的 {new_place}")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.warning("景點名稱和類型都要填喔！")

elif selected == "旅遊計畫":
    st.title("✈️ 我們的出國計畫書")
    creds = get_creds()
    client = gspread.authorize(creds)
    try:
        plan_sheet = client.open("OurLoveMoney").worksheet("TravelPlans")
    except:
        st.error("⚠️ 找不到 'TravelPlans' 分頁！請去試算表新增，標題：旅遊名稱、日期、計畫書連結、備註")
        st.stop()

    # --- 1. 顯示現有的計畫書 ---
    all_plans = plan_sheet.get_all_records()
    if all_plans:
        st.write("這是我們未來的冒險！🌍")
        for plan in all_plans:
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.subheader(f"🛫 {plan['旅遊名稱']}")
                    st.caption(f"📅 日期：{plan['日期']}")
                    if plan.get('備註'):
                        st.info(f"💡 {plan['備註']}")
                with c2:
                    if plan.get('計畫書連結'):
                        st.link_button("📄 查看詳細行程", plan['計畫書連結'], use_container_width=True)
                    else:
                        st.warning("尚未上傳連結")
    else:
        st.info("目前還沒有旅遊計畫，快來建立第一個吧！👇")

    # --- 2. 新增計畫功能 ---
    st.divider()
    with st.expander("➕ 新增旅遊計畫", expanded=False):
        st.write("把 Notion、Google 文件或 PDF 的雲端連結貼在這裡，方便隨時查看！")
        with st.form("add_plan_form"):
            new_title = st.text_input("旅遊名稱")
            new_date = st.text_input("日期範圍")
            new_link = st.text_input("計畫書連結 (請貼上網址)")
            new_note = st.text_input("備註")
            
            if st.form_submit_button("建立計畫"):
                if new_title:
                    plan_sheet.append_row([new_title, new_date, new_link, new_note])
                    st.success(f"✅ 已建立計畫：{new_title}")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.warning("請至少輸入旅遊名稱喔！")

elif selected == "記帳管家":
    st.title("💰 雲端記帳管家")
    creds = get_creds()
    client = gspread.authorize(creds)
    try:
        sheet = client.open("OurLoveMoney").sheet1
    except:
        st.error("找不到試算表，請檢查名稱。")
        st.stop()

    # --- 1. 新增記帳區 ---
    with st.container(border=True):
        st.subheader("📝 新增一筆")
        col1, col2 = st.columns([2, 1])
        with col1:
            item = st.text_input("消費項目", placeholder="例如: 晚餐、電影")
        with col2:
            total_price = st.number_input("總金額", min_value=0, step=10)
            
        col3, col4 = st.columns(2)
        with col3:
            payer = st.selectbox("誰先付錢？", ["薪雅", "白白"])
        with col4:
            # 這裡就是妳要的「選擇彼此花了多少」
            split_mode = st.radio("怎麼分攤？", ["一人一半", "輸入各付多少"], horizontal=True)

        debt_amount = 0
        if split_mode == "一人一半":
            debt_amount = total_price / 2
        elif split_mode == "輸入各付多少":
            debt_amount = st.number_input(f"💸 {payer} 先付了 {total_price}，其中對方該付多少？", min_value=0.0, max_value=float(total_price))

        if st.button("上傳雲端", key="add_money", type="primary", use_container_width=True):
            if item and total_price > 0:
                date_str = datetime.now().strftime("%Y-%m-%d")
                # 欄位順序：日期, 項目, 總金額, 付款人, 對方應付, 狀態
                sheet.append_row([date_str, item, total_price, payer, debt_amount, "未結清"])
                st.success("✅ 記帳成功！")
                st.cache_data.clear()
                st.rerun()
            else:
                st.warning("項目金額要填喔！")

    # --- 2. 顯示與管理區 ---
    st.divider()
    
    # 讀取所有資料
    all_records = sheet.get_all_records()
    
    if all_records:
        df = pd.DataFrame(all_records)
        
        # 確保有 '狀態' 這個欄位 (避免舊資料報錯)
        if "狀態" not in df.columns:
            st.error("⚠️ 試算表缺少『狀態』欄位！請去 Google 試算表新增 F 欄標題為『狀態』")
            st.stop()

        # 分成「未結清」和「已結清」
        unsettled_df = df[df["狀態"] != "已結清"].reset_index() # reset_index 保留原始行號 (為了刪除用)
        settled_df = df[df["狀態"] == "已結清"]

        # 頁籤切換
        tab1, tab2 = st.tabs([f"🔥 未結清 ({len(unsettled_df)})", "✅ 歷史紀錄 (已結清)"])
        
        with tab1:
            if not unsettled_df.empty:
                # 顯示表格 (只顯示重要資訊)
                display_cols = ["日期", "項目", "總金額", "付款人", "對方應付"]
                st.dataframe(unsettled_df[display_cols], use_container_width=True)

                # --- 自動計算誰欠誰 ---
                my_debt = unsettled_df[unsettled_df["付款人"] == "白白"]["薪雅應付"].sum() # 白白付，薪雅欠他
                bf_debt = unsettled_df[unsettled_df["付款人"] == "薪雅"]["白白應付"].sum() # 薪雅付，白白欠我
                
                final_debt = bf_debt - my_debt
                
                st.info(f"💡 目前結算：薪雅欠白白 ${my_debt}，白白欠薪雅 ${bf_debt}")
                
                if final_debt > 0:
                    st.success(f"👉 **結論：白白要給薪雅 ${int(final_debt)}**")
                elif final_debt < 0:
                    st.error(f"👉 **結論：薪雅要給白白 ${int(abs(final_debt))}**")
                else:
                    st.success("👉 **結論：已結清！完美！**")

                # --- 管理功能 (刪除 / 結清) ---
                st.write("---")
                st.caption("🔧 管理選單：選一筆資料來操作")
                
                # 讓使用者選擇要操作哪一筆 (顯示: 日期-項目-金額)
                options = unsettled_df.apply(lambda x: f"{x['index']+2}. {x['日期']} - {x['項目']} (${x['總金額']})", axis=1)
                selected_item = st.selectbox("選擇項目", options)
                
                # 解析出行號 (Row Number)
                row_num = int(selected_item.split(".")[0])
                
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ 標記為已結清", use_container_width=True):
                        # 更新 Google Sheet 的 F 欄 (狀態)
                        sheet.update_cell(row_num, 6, "已結清") 
                        st.success("已結清！")
                        st.cache_data.clear()
                        st.rerun()
                with c2:
                    if st.button("🗑️ 刪除這筆資料", type="primary", use_container_width=True):
                        sheet.delete_rows(row_num)
                        st.success("已刪除！")
                        st.cache_data.clear()
                        st.rerun()

            else:
                st.info("目前沒有未結清的帳款，太棒了！")
        with tab2:
            st.dataframe(settled_df, use_container_width=True)
            st.caption("這些是已經結算過的歷史帳務。")

    else:
        st.info("目前還沒有任何記帳資料喔！")

elif selected == "旅遊地圖":
    st.title("🌍 我們的足跡")
    creds = get_creds()
    client = gspread.authorize(creds)
    try:
        map_sheet = client.open("OurLoveMoney").worksheet("TravelMap")
    except:
        st.error("⚠️ 找不到 'TravelMap' 分頁！")
        st.stop()

    # --- 1. 顯示地圖 ---
    map_records = map_sheet.get_all_records()
    if map_records:
        df_map = pd.DataFrame(map_records)
        if not df_map.empty and '緯度' in df_map.columns:
            
            center_lat = df_map['緯度'].mean() if not df_map.empty else 23.5
            center_lon = df_map['經度'].mean() if not df_map.empty else 121.0

            deck = pdk.Deck(
                map_style=None,
                initial_view_state=pdk.ViewState(
                    latitude=center_lat,
                    longitude=center_lon,
                    zoom=7,
                    pitch=0,
                ),
                layers=[
                    pdk.Layer(
                        'ScatterplotLayer',
                        data=df_map,
                        get_position='[經度, 緯度]',
                        get_color='[255, 75, 75, 200]',
                        get_radius=100,
                        pickable=True,
                        auto_highlight=True,
                    ),
                ],
                tooltip={
                    "html": "<b>{地點}</b><br/>📅 {日期}<br/>📝 {備註}",
                    "style": {
                        "backgroundColor": "steelblue",
                        "color": "white"
                    }
                }
            )
            st.pydeck_chart(deck)
    else:
        st.info("地圖上還是空的，快來標記第一個約會地點吧！👇")

    # --- 2. 新增地點區 ---
    st.divider()
    
    # === A. 自動搜尋 ===
    with st.container(border=True):
        st.subheader("📍 標記新地點 (自動搜尋)")
        place_name = st.text_input("地點名稱")
        visit_date = st.date_input("日期", date.today())
        note = st.text_input("備註")
        
        if st.button("🔍 搜尋並加入地圖", type="primary", use_container_width=True):
            if place_name:
                try:
                    geolocator = Nominatim(user_agent="our_love_map_app_v1")
                    location = geolocator.geocode(place_name)
                    
                    if location:
                        lat = location.latitude
                        lon = location.longitude
                        date_str = visit_date.strftime("%Y-%m-%d")
                        
                        map_sheet.append_row([place_name, lat, lon, date_str, note])
                        st.success(f"✅ 找到了！已加入：{place_name}")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("🥺 找不到這個地方... 試試看下面的手動輸入！")
                except Exception as e:
                    st.error(f"發生錯誤：{e}")
            else:
                st.warning("請輸入地點名稱喔！")
    
    # === B. 手動輸入 (新功能) ===
    st.write("")
    with st.expander("📍 找不到地點？手動輸入座標", expanded=False):
        st.info("💡 小撇步：在 Google Maps 上**長按**你想去的地方，搜尋列或下方就會出現一串數字（例如 `24.123, 120.456`），那就是座標！")
        
        col_lat, col_lon = st.columns(2)
        with col_lat:
            manual_lat = st.number_input("緯度 (Latitude)", value=24.0, format="%.5f")
        with col_lon:
            manual_lon = st.number_input("經度 (Longitude)", value=121.0, format="%.5f")
            
        manual_place = st.text_input("地點名稱(Place)")
        manual_date = st.date_input("日期(Date)", date.today(), key="manual_date")
        manual_note = st.text_input("備註(Remark)")
        
        if st.button("➕ 手動加入座標", type="primary"):
            if manual_place:
                date_str = manual_date.strftime("%Y-%m-%d")
                map_sheet.append_row([manual_place, manual_lat, manual_lon, date_str, manual_note])
                st.success(f"✅ 手動加入成功：{manual_place}")
                st.cache_data.clear()
                st.rerun()
            else:
                st.warning("請輸入地點名稱喔！")

elif selected == "使用說明":
    st.title("📖 網站使用說明書")
    st.write("歡迎使用我們的專屬小窩！這裡記錄了所有功能的操作方法：")
    
    with st.expander("🍔 要吃什麼 (美食抽籤)"):
        st.write("""
        1. 篩選：可以選擇「縣市」、「地區」、「預算」和「類型」。
        2. 抽籤：按下「幫我們決定！」按鈕，系統會從符合條件的口袋名單中隨機選出一家。
        3. 新增餐廳：
           - 點擊下方的「➕ 新增餐廳到口袋名單」。
           - **重要**：請先在選單上方選擇「縣市」和「地區」，選單會自動連動。
           - 填寫名稱、類型和預算，按下「加入名單」即可。
        """)
    
    with st.expander("🎢 去哪裡玩 (旅遊抽籤)"):
        st.write("""
        1. 功能：專治「不知道去哪玩」。
        2. 篩選：選擇想去的「縣市」、「類型」或「預算」。
        3. 新增：
           - 在下方輸入你想去的景點名稱。
           - 記得選好縣市、類型和預算，方便以後篩選喔！
        """)

    with st.expander("✈️ 旅遊計畫 (出遊行程)"):
        st.write("""
        1. **功能**：集中管理出遊行程表。
        2. **新增**：
           - 填寫旅遊名稱和日期。
           - **關鍵**：在「計畫書連結」欄位貼上妳的 Notion、Google Doc 或雲端硬碟連結。
        3. **使用**：點擊卡片右邊的按鈕，就能直接跳轉到你的詳細行程表！
        """)
        
    with st.expander("💰 記帳管家 (理財工具)"):
        st.write("""
        1. 記帳：
           - 輸入項目和總金額。
           - 選擇「誰先付錢」。
           - **分攤方式**：
             - **一人一半**：系統自動除以 2。
             - **自定義**：手動輸入「對方該付多少錢」（例如你吃 200，對方吃 500，他先付錢，你在這裡輸入 200）。
        2. 看債務：切換到「🔥 未結清」頁面，藍色框框會自動算出「誰要給誰多少錢」。
        3. 結帳/刪除：
           - 在下方的選單選擇要處理的項目。
           - 按 **「✅ 標記為已結清」**：該筆帳會移入歷史紀錄，不再計算債務。
           - 按 **「🗑️ 刪除」**：直接刪除該筆資料。
        """)
        
    with st.expander("🌍 旅遊地圖 (打卡紀錄)"):
        st.write("""
        1. 自動搜尋：輸入地名（例如：台北101），選擇日期，按下搜尋。系統會自動抓取座標並標記。
        2. 手動輸入：如果自動搜尋找不到（例如深山露營區）：
           - 打開手機 Google Maps。
           - **長按**地圖上的點。
           - 搜尋列或下方會出現一串數字（例如 `24.123, 120.456`）。
           - 點開網站上的「📍 找不到地點？手動輸入座標」，把數字填進去即可。
        3. 查看地圖：滑鼠移到地圖上的紅點，會顯示日期和備註喔！
        """)