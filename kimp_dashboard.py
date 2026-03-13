import streamlit as st
import requests
import time
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go

st.set_page_config(page_title="김치프리미엄 대시보드", layout="wide", page_icon="₿")

st.title("₿ 비트코인 실시간 시세 & 김치 프리미엄 대시보드")
st.markdown("**Upbit • Bithumb vs Binance** 실시간 업데이트 (5초 자동 갱신)")

# --- 공통 헤더 (API 오류 방지 핵심!) ---
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# --- 데이터 가져오기 함수 (수정됨) ---
def fetch_data():
    try:
        # 1. Binance BTC/USDT
        binance_resp = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", headers=headers, timeout=10)
        binance_price = float(binance_resp.json()['price'])

        # 2. Upbit KRW-BTC
        upbit_resp = requests.get("https://api.upbit.com/v1/ticker?markets=KRW-BTC", headers=headers, timeout=10)
        upbit_price = float(upbit_resp.json()[0]['trade_price'])

        # 3. Bithumb BTC_KRW
        bithumb_resp = requests.get("https://api.bithumb.com/public/ticker/BTC_KRW", headers=headers, timeout=10)
        bithumb_price = float(bithumb_resp.json()['data']['closing_price'])

        # 4. Dunamu 환율
        rate_resp = requests.get("https://quotation-api-cdn.dunamu.com/v1/forex/recent?codes=FRX.KRWUSD", headers=headers, timeout=10)
        usd_krw = float(rate_resp.json()[0]['basePrice'])

        return {
            "binance": round(binance_price, 2),
            "upbit": int(upbit_price),
            "bithumb": int(bithumb_price),
            "usd_krw": round(usd_krw, 2),
            "time": datetime.now()
        }
    except Exception as e:
        st.error(f"API 오류: {str(e)[:80]}... (네트워크 지연일 수 있어요. 10초 후 다시 시도)")
        return None

# 나머지 코드는 그대로 (Session State, 메인 대시보드, 차트 등)
if 'price_history' not in st.session_state:
    st.session_state.price_history = []

data = fetch_data()

if data:
    binance = data["binance"]
    upbit = data["upbit"]
    bithumb = data["bithumb"]
    rate = data["usd_krw"]
    
    upbit_implied_usd = upbit / rate
    premium_upbit = round((upbit_implied_usd / binance - 1) * 100, 2)
    
    bithumb_implied_usd = bithumb / rate
    premium_bithumb = round((bithumb_implied_usd / binance - 1) * 100, 2)

    col1, col2, col3, col4 = st.columns([1,1,1,0.8])
    with col1:
        st.metric(label="**Binance (USD)**", value=f"${binance:,.0f}")
    with col2:
        delta = f"김프 {premium_upbit:+.1f}%"
        st.metric(label="**Upbit (KRW)**", value=f"₩{upbit:,.0f}", delta=delta)
    with col3:
        delta_b = f"김프 {premium_bithumb:+.1f}%"
        st.metric(label="**Bithumb (KRW)**", value=f"₩{bithumb:,.0f}", delta=delta_b)
    with col4:
        st.metric(label="**USD/KRW 환율**", value=f"{rate:,.0f}원")

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

st.caption(f"마지막 업데이트: {datetime.now().strftime('%H:%M:%S')} | 자동 5초 갱신 중")

if st.button("🔄 지금 바로 새로고침"):
    st.rerun()

time.sleep(5)
st.rerun()
