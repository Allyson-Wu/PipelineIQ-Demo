import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 後端 FastAPI 服務位址
API_BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="PipelineIQ - Data Quality Platform",
    page_icon="📊",
    layout="wide"
)

st.title("📊 PipelineIQ - 資料品質檢測平台")
st.caption("無程式碼自動化資料健康度檢查與歷史稽核系統")

# 側邊欄選單
st.sidebar.title("功能導覽")
page = st.sidebar.radio("請選擇操作項目：", ["單檔檢測 (Upload)", "歷史審計紀錄 (History)"])

# ==================== 分頁 1：單檔檢測 ====================
if page == "單檔檢測 (Upload)":
    st.header("📤 單檔資料品質檢測")
    
    uploaded_file = st.file_uploader(
        "請選擇要檢測的檔案 (.csv, .xlsx, .xls)", 
        type=["csv", "xlsx", "xls"]
    )
    
    if uploaded_file is not None:
        if st.button("開始執行品質檢測", type="primary"):
            with st.spinner("正在將檔案送往 Data Quality Engine 解析中..."):
                try:
                    # 組裝發送給 FastAPI 的檔案 payload
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    response = requests.post(f"{API_BASE_URL}/api/v1/upload", files=files)
                    
                    if response.status_code == 200:
                        res_data = response.json()
                        st.success("檢測完成！報告已成功儲存至雲端資料庫。")
                        
                        # 顯示核心指標卡片
                        col1, col2, col3, col4 = st.columns(4)
                        
                        health_score = res_data["quality_report"]["health_score"]
                        duplicate_rows = res_data["quality_report"]["duplicate_rows"]
                        total_rows = res_data["metadata"]["total_rows"]
                        total_cols = res_data["metadata"]["total_columns"]
                        
                        col1.metric("Health Score (健康分數)", f"{health_score} / 100")
                        col2.metric("總列數 (Total Rows)", total_rows)
                        col3.metric("總欄數 (Total Columns)", total_cols)
                        col4.metric("重複列數 (Duplicates)", duplicate_rows)
                        
                        st.divider()
                        
                        # ==================== Day 12 新增：Plotly 視覺化圖表 ====================
                        st.subheader("📈 品質視覺化分析 (Quality Visualizations)")
                        chart_col1, chart_col2 = st.columns(2)
                        
                        # 圖表 1：Health Score 半圓形儀表盤 (Gauge Chart)
                        with chart_col1:
                            fig_gauge = go.Figure(go.Indicator(
                                mode="gauge+number",
                                value=health_score,
                                domain={'x': [0, 1], 'y': [0, 1]},
                                title={'text': "Data Health Score"},
                                gauge={
                                    'axis': {'range': [0, 100]},
                                    'bar': {'color': "#1f77b4"},
                                    'steps': [
                                        {'range': [0, 50], 'color': "#ff4b4b"},
                                        {'range': [50, 85], 'color': "#ffa800"},
                                        {'range': [85, 100], 'color': "#21c354"}
                                    ]
                                }
                            ))
                            fig_gauge.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
                            st.plotly_chart(fig_gauge, use_container_width=True)
                            
                        # 圖表 2：各欄位缺失率柱狀圖 (Bar Chart)
                        null_ratios = res_data["quality_report"]["null_ratios"]
                        with chart_col2:
                            df_null_chart = pd.DataFrame({
                                "Column": list(null_ratios.keys()),
                                "Null Ratio (%)": [r * 100 for r in null_ratios.values()]
                            })
                            fig_bar = px.bar(
                                df_null_chart, 
                                x="Column", 
                                y="Null Ratio (%)",
                                title="各欄位缺失率分布 (%)",
                                labels={"Column": "欄位名稱", "Null Ratio (%)": "缺失率 (%)"},
                                color="Null Ratio (%)",
                                color_continuous_scale="Reds"
                            )
                            fig_bar.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
                            st.plotly_chart(fig_bar, use_container_width=True)
                        
                        st.divider()
                        
                        # 顯示詳細資料表格
                        st.subheader("📋 缺失值統計 (Null Counts & Ratios)")
                        null_counts = res_data["quality_report"]["null_counts"]
                        
                        # 將 JSON 轉為 DataFrame 呈現
                        df_nulls = pd.DataFrame({
                            "欄位名稱": list(null_counts.keys()),
                            "缺失值筆數": list(null_counts.values()),
                            "缺失值比例": [f"{r*100:.2f}%" for r in null_ratios.values()]
                        })
                        st.dataframe(df_nulls, use_container_width=True)
                        
                        st.info(f"審計紀錄編號 (Audit ID): {res_data['audit_id']}")
                    else:
                        st.error(f"API 回傳錯誤 ({response.status_code}): {response.text}")
                except Exception as e:
                    st.error(f"無法連線至後端服務: {str(e)}")

# ==================== 分頁 2：歷史審計紀錄 ====================
elif page == "歷史審計紀錄 (History)":
    st.header("📜 歷史審計紀錄 (Audit History)")
    
    if st.button("重新整理歷史資料"):
        st.rerun()
        
    with st.spinner("正在載入歷史審計清單..."):
        try:
            response = requests.get(f"{API_BASE_URL}/api/v1/audits")
            if response.status_code == 200:
                res_data = response.json()
                audits = res_data.get("data", [])
                
                if audits:
                    st.write(f"目前資料庫共儲存 **{res_data.get('count', 0)}** 筆審計紀錄：")
                    df_audits = pd.DataFrame(audits)
                    
                    # 調整顯示欄位名稱
                    df_audits_display = df_audits.rename(columns={
                        "id": "Audit ID",
                        "file_name": "檔案名稱",
                        "total_rows": "總列數",
                        "total_columns": "總欄數",
                        "health_score": "健康分數",
                        "created_at": "檢測時間"
                    })
                    
                    st.dataframe(df_audits_display, use_container_width=True)
                else:
                    st.warning("目前資料庫中無任何審計紀錄。")
            else:
                st.error(f"無法取得歷史紀錄 ({response.status_code}): {response.text}")
        except Exception as e:
            st.error(f"無法連線至後端服務: {str(e)}")