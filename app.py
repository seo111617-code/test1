import streamlit as st
import pandas as pd
import numpy as np

st.title("미세먼지 데이터 분석 대시보드")

BINS = [-0.1, 15, 35, 75, 1000]
LABELS = ["좋음", "보통", "나쁨", "매우나쁨"]

def make_sample():
    dates = pd.date_range("2026-09-01", periods=30)
    rows = []
    for region in ["수원", "서울", "부산"]:
        vals = np.random.randint(8, 90, size=30).astype(float)
        vals[[5, 12]] = np.nan  # 일부러 결측값 삽입
        rows += [(d, region, v) for d, v in zip(dates, vals)]
    return pd.DataFrame(rows, columns=["date", "region", "pm25"])

def clean(df):
    if not {"date", "region", "pm25"}.issubset(df.columns):
        raise ValueError("CSV에 date, region, pm25 열이 모두 있어야 합니다.")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["pm25"] = pd.to_numeric(df["pm25"], errors="coerce")
    df = df.dropna(subset=["date"])
    df = df[df["pm25"].isna() | df["pm25"].between(0, 1000)]
    df = df.sort_values(["region", "date"])
    df["pm25"] = df.groupby("region")["pm25"].transform(
        lambda s: s.interpolate().bfill().ffill())
    df = df.dropna(subset=["pm25"])
    if df.empty:
        raise ValueError("정제 후 남은 데이터가 없습니다.")
    df["등급"] = pd.cut(df["pm25"], bins=BINS, labels=LABELS)
    return df

file = st.file_uploader("CSV 파일 업로드", type="csv")
use_sample = st.checkbox("샘플 데이터 사용")

try:
    if file is not None:
        try:
            raw = pd.read_csv(file)
        except UnicodeDecodeError:
            file.seek(0)
            raw = pd.read_csv(file, encoding="cp949")
    elif use_sample:
        raw = make_sample()
    else:
        st.info("CSV를 업로드하거나 샘플 데이터를 선택하세요.")
        st.stop()

    df = clean(raw)
    region = st.selectbox("지역 선택", df["region"].unique())
    sub = df[df["region"] == region]

    c1, c2 = st.columns(2)
    c1.metric("평균 PM2.5", f"{sub['pm25'].mean():.1f} ㎍/㎥")
    c2.metric("최고 PM2.5", f"{sub['pm25'].max():.1f} ㎍/㎥")

    st.subheader("일별 추세")
    st.line_chart(sub.set_index("date")["pm25"])
    st.subheader("등급별 일수")
    st.bar_chart(sub["등급"].value_counts().reindex(LABELS))

except pd.errors.EmptyDataError:
    st.error("빈 파일입니다. 데이터가 있는 CSV를 올려주세요.")
except ValueError as e:
    st.error(f"데이터 오류: {e}")
except Exception as e:
    st.error(f"예상치 못한 오류가 발생했습니다: {e}")
