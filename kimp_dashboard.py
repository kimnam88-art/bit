import streamlit as st
import requests
import time
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go

st.set_page_config(page_title="김치프리미엄 대시보드", layout="wide", page_icon="₿")

st.title("₿ 비트코인 실시간 시세 & 김치 프리미엄 대시보드")
st.markdown("**Upbit • Bithumb vs CoinGecko** (10초 자동 갱신)")

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json'
}

# 이전 성공 데이터 저장 (오류 시 fallback)
if 'last_data' not in st.session_state:
    st.session_state.last_data = None

def fetch_data():
    for attempt in range(3):  # 3번 재시도
        try:
            # CoinGecko USD + KRW 동시에
            cg_resp = requests.get(
                "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd,krw",
                headers=headers, timeout=5
            )
            cg_resp.raise_for_status()
            cg = cg_resp.json()['bitcoin']
            global_usd = float(cg['usd'])
            global_krw = float(cg['krw'])

            # Upbit
            upbit_resp = requests.get("https://api.upbit.com/v1/ticker?markets=KRW-BTC", headers=headers, timeout=5)
            upbit_price = float(upbit_resp.json()[0]['trade_price'])

            # Bithumb
            bithumb_resp = requests.get("https://api.bithumb.com/public/ticker/BTC_KRW", headers=headers, timeout=5)
            bithumb_price = float(bithumb_resp.json()['data']['closing_price'])

            data = {
                "global_usd": round(global_usd, 2),
                "global_krw": int(global_krw),
                "upbit": int(upbit_price),
                "bithumb": int(bithumb_price),
                "time": datetime.now()
            }
            st.session_state.last_data = data
            return data
        except Exception as e:
            if attempt < 2:
                time.sleep(1)  # 재시도 전 잠시 대기
                continue
            # 3번 모두 실패 시 fallback
            st.error(f"임시 API 오류 (재시도 중...)")
            if st.session_state.last_data:
                st.warning("✅ 이전 데이터로 계속 표시합니다. (실시간은 잠시 후 복구)")
                return st.session_state.last_data
            return None

if 'price_history' not in st.session_state:
    st.session_state.price_history = []

data = fetch_data()

if data:
    global_usd = data["global_usd"]
    global_krw = data["global_krw"]
    upbit = data["upbit"]
    bithumb = data["bithumb"]
    
    premium_upbit = round((upbit / global_krw - 1) * 100, 2)
    premium_bithumb = round((bithumb / global_krw - 1) * 100, 2)

    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        st.metric(label="**CoinGecko (USD)**", value=f"${global_usd:,.0f}")
    with col2:
        delta = f"김프 {premium_upbit:+.1f}%"
        st.metric(label="**Upbit (KRW)**", value=f"₩{upbit:,.0f}", delta=delta)
    with col3:
        delta_b = f"김프 {premium_bithumb:+.1f}%"
        st.metric(label="**Bithumb (KRW)**", value=f"₩{bithumb:,.0f}", delta=delta_b)

    st.divider()
    pcol1, pcol2 = st.columns(2)
    with pcol1:
        color = "🔴" if premium_upbit > 0 else "🔵"
        st.subheader(f"{color} Upbit 김치 프리미엄: **{premium_upbit}%**")
    with pcol2:
        color = "🔴" if premium_bithumb > 0 else "🔵"
        st.subheader(f"{color} Bithumb 김치 프리미엄: **{premium_bithumb}%**")

    st.session_state.price_history.append({
        'time': data['time'].strftime('%H:%M:%S'),
        'upbit_p': premium_upbit,
        'bithumb_p': premium_bithumb
    })
    if len(st.session_state.price_history) > 120:
        st.session_state.price_history = st.session_state.price_history[-120:]

    df = pd.DataFrame(st.session_state.price_history)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['time'], y=df['upbit_p'], name='Upbit 김프', line=dict(color='#FF4B4B', width=3)))
    fig.add_trace(go.Scatter(x=df['time'], y=df['bithumb_p'], name='Bithumb 김프', line=dict(color='#FFA500', width=3)))
    fig.update_layout(title="김치 프리미엄 실시간 추이", xaxis_title="시간", yaxis_title="프리미엄 (%)", height=400, template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("최근 10회 기록")
    st.dataframe(df.tail(10)[['time', 'upbit_p', 'bithumb_p']].rename(columns={'upbit_p':'Upbit 김프(%)', 'bithumb_p':'Bithumb 김프(%)'}), use_container_width=True)

st.caption(f"마지막 업데이트: {datetime.now().strftime('%H:%M:%S')} | 자동 10초 갱신 중")

if st.button("🔄 지금 바로 새로고침"):
    st.rerun()

time.sleep(10)  # ← 여기서 10초로 변경 (중요!)
st.rerun()
