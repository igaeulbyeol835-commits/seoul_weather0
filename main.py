import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib as mpl
import urllib.request
import io

# ────────────────────────────────
# 페이지 설정
# ────────────────────────────────
st.set_page_config(
    page_title="서울 100년 기온 변화",
    page_icon="🌡️",
    layout="wide",
)

# ────────────────────────────────
# 한글 폰트 설정 (Streamlit Cloud 대응)
# ────────────────────────────────
@st.cache_resource
def set_korean_font():
    font_url = "https://github.com/googlefonts/nanum-gothic/raw/main/fonts/ttf/NanumGothic-Regular.ttf"
    font_path = "/tmp/NanumGothic-Regular.ttf"
    try:
        urllib.request.urlretrieve(font_url, font_path)
        fm.fontManager.addfont(font_path)
        font_name = fm.FontProperties(fname=font_path).get_name()
        mpl.rcParams["font.family"] = font_name
    except Exception:
        # 폰트 다운로드 실패 시 기본 폰트로 대체 (한글이 깨질 수 있음)
        pass
    mpl.rcParams["axes.unicode_minus"] = False

set_korean_font()

# ────────────────────────────────
# 데이터 불러오기
# ────────────────────────────────
DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv"

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL, encoding="utf-8-sig")
    df["날짜"] = pd.to_datetime(df["날짜"])
    df["연도"] = df["날짜"].dt.year
    return df

df = load_data()

# 연평균 기온 계산 (관측치가 충분한 해만 사용 — 관측 시작/끝 해는 데이터가 적어 왜곡될 수 있음)
yearly = df.groupby("연도").agg(
    평균기온=("평균기온", "mean"),
    최저기온=("최저기온", "mean"),
    최고기온=("최고기온", "mean"),
    관측일수=("평균기온", "count"),
).reset_index()

# 관측일수가 300일 이상인 해만 신뢰할 수 있는 연평균으로 간주
yearly_reliable = yearly[yearly["관측일수"] >= 300].copy()

# ────────────────────────────────
# 화면 구성
# ────────────────────────────────
st.title("🌡️ 서울, 100년의 기온 변화")
st.markdown(
    "서울(종로구, 지점번호 108)의 **1907년부터 이어져 온 기상 관측 자료**를 바탕으로, "
    "지난 100여 년간 연평균 기온이 어떻게 변해 왔는지 살펴봅니다."
)

start_year = int(yearly_reliable["연도"].min())
end_year = int(yearly_reliable["연도"].max())
total_change = (
    yearly_reliable.iloc[-1]["평균기온"] - yearly_reliable.iloc[0]["평균기온"]
)

col1, col2, col3 = st.columns(3)
col1.metric("관측 시작 연도", f"{start_year}년")
col2.metric("관측 최근 연도", f"{end_year}년")
col3.metric(
    f"{start_year}년 대비 {end_year}년 기온 변화",
    f"{total_change:+.1f}℃",
)

st.divider()

# ────────────────────────────────
# 메인 그래프: 연평균 기온 변화 추이
# ────────────────────────────────
st.subheader("연평균 기온 변화 추이")

show_trend = st.checkbox("추세선(선형 회귀) 표시", value=True)
show_minmax = st.checkbox("연평균 최저·최고 기온 함께 보기", value=False)

fig, ax = plt.subplots(figsize=(12, 6))

ax.plot(
    yearly_reliable["연도"],
    yearly_reliable["평균기온"],
    color="#1f77b4",
    linewidth=1.5,
    label="연평균 기온",
)

if show_minmax:
    ax.plot(
        yearly_reliable["연도"],
        yearly_reliable["최고기온"],
        color="#d62728",
        linewidth=1,
        alpha=0.6,
        label="연평균 최고기온",
    )
    ax.plot(
        yearly_reliable["연도"],
        yearly_reliable["최저기온"],
        color="#2ca02c",
        linewidth=1,
        alpha=0.6,
        label="연평균 최저기온",
    )

if show_trend:
    import numpy as np

    x = yearly_reliable["연도"].values
    y = yearly_reliable["평균기온"].values
    coeffs = np.polyfit(x, y, 1)
    trend = np.poly1d(coeffs)
    ax.plot(
        x, trend(x),
        color="black",
        linestyle="--",
        linewidth=1.5,
        label=f"추세선 (10년당 {coeffs[0]*10:+.2f}℃)",
    )

ax.set_xlabel("연도")
ax.set_ylabel("기온 (℃)")
ax.set_title("서울 연평균 기온 변화 (1908~현재)")
ax.legend(loc="upper left")
ax.grid(True, alpha=0.3)

st.pyplot(fig)

st.caption(
    "※ 관측 일수가 300일 미만인 연도(관측 시작·종료 해 등)는 통계 왜곡을 피하기 위해 제외했습니다."
)

st.divider()

# ────────────────────────────────
# 연대별 평균 기온 비교
# ────────────────────────────────
st.subheader("연대별 평균 기온 비교")

yearly_reliable["연대"] = (yearly_reliable["연도"] // 10) * 10
decade_avg = yearly_reliable.groupby("연대")["평균기온"].mean().reset_index()
decade_avg["연대"] = decade_avg["연대"].astype(str) + "년대"

fig2, ax2 = plt.subplots(figsize=(12, 5))
ax2.bar(decade_avg["연대"], decade_avg["평균기온"], color="#ff7f0e")
ax2.set_xlabel("연대")
ax2.set_ylabel("평균 기온 (℃)")
ax2.set_title("연대별 평균 기온")
plt.xticks(rotation=45)
ax2.grid(True, axis="y", alpha=0.3)

st.pyplot(fig2)

st.divider()

# ────────────────────────────────
# 원본 데이터 확인
# ────────────────────────────────
with st.expander("연도별 상세 데이터 보기"):
    st.dataframe(
        yearly_reliable[["연도", "평균기온", "최저기온", "최고기온", "관측일수"]]
        .sort_values("연도", ascending=False)
        .reset_index(drop=True)
    )

st.caption("데이터 출처: 기상청 서울(108) 관측소 일별 기온 자료")
