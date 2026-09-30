import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os

# 後端 FastAPI 服務位址
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="PipelineIQ - Data Quality Platform",
    page_icon="📊",
    layout="wide"
)

st.title("📊 PipelineIQ - 資料品質檢測平台")
st.caption("無程式碼自動化資料健康度檢查與歷史稽核系統")

# 側邊欄選單
st.sidebar.title("功能導覽")
page = st.sidebar.radio("請選擇操作項目：", ["單檔與批次檢測 (Upload)", "歷史審計紀錄 (History)"])

# ==================== 分頁 1：單檔與批次檢測 ====================
if page == "單檔與批次檢測 (Upload)":
    st.header("📤 資料品質檢測 (支援單檔與批次檢測)")
    
    # accept_multiple_files=True 可同時支援單選與多選檔案
    uploaded_files = st.file_uploader(
        "請選擇要檢測的檔案 (.csv, .xlsx, .xls)，可一次選擇多個檔案：", 
        type=["csv", "xlsx", "xls"],
        accept_multiple_files=True
    )

    # ==================== Day 19 新增：預設公開範例資料集 (Preset Demo Datasets) ====================
    st.markdown("---")
    st.subheader("💡 或是直接選擇內建公開範例資料集 (Preset Public Demo Datasets)")
    st.caption("供招募官與評審免下載檔案、一鍵直接測試平台品質檢測能力")

    DEMO_DIR = "demo_datasets"
    preset_files = []
    if os.path.exists(DEMO_DIR):
        preset_files = [f for f in os.listdir(DEMO_DIR) if f.endswith(('.csv', '.xlsx', '.xls'))]

    if preset_files:
        selected_preset = st.selectbox("請選擇預載資料集：", ["-- 請選擇範例檔案 --"] + preset_files)
        
        if selected_preset != "-- 請選擇範例檔案 --":
            if st.button(f"🚀 載入並分析 [{selected_preset}]", type="secondary"):
                preset_path = os.path.join(DEMO_DIR, selected_preset)
                with st.spinner("正在讀取範例資料集並送往 Data Quality Engine 解析中..."):
                    try:
                        with open(preset_path, "rb") as f:
                            file_bytes = f.read()
                        
                        mime_type = "text/csv" if selected_preset.endswith(".csv") else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        files = {"file": (selected_preset, file_bytes, mime_type)}
                        
                        response = requests.post(f"{API_BASE_URL}/api/v1/upload", files=files)
                        if response.status_code == 200:
                            res_data = response.json()
                            st.success(f"🎉 範例資料集 [{selected_preset}] 解析完成！報告已成功儲存至雲端資料庫。")

                            # 1. 核心指標卡片
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

                            # 2. Plotly 視覺化圖表
                            st.subheader("📈 品質視覺化分析 (Quality Visualizations)")
                            chart_col1, chart_col2 = st.columns(2)
                            
                            # 圖表 1：Health Score 半圓形儀表盤
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
                                
                            # 圖表 2：各欄位缺失率柱狀圖
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
                            
                            # 3. 缺失值詳細表格
                            st.subheader("📋 缺失值統計 (Null Counts & Ratios)")
                            null_counts = res_data["quality_report"]["null_counts"]
                            
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
                        st.error(f"無法讀取預設範例檔案或連線後端: {str(e)}")
    else:
        st.info("提示：專案目錄下未發現 demo_datasets 資料夾，請先建立該資料夾並放入測試 CSV 檔案。")

    st.markdown("---")
    
    if uploaded_files:
        st.write(f"📁 已選擇 **{len(uploaded_files)}** 個檔案待檢測。")
        
        if st.button("🚀 開始執行品質檢測", type="primary"):
            # -------------------- 模式 A：單一檔案上傳 (呈現 Day 12 完整詳細視覺化) --------------------
            if len(uploaded_files) == 1:
                uploaded_file = uploaded_files[0]
                with st.spinner("正在將檔案送往 Data Quality Engine 解析中..."):
                    try:
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
                            
                            # Plotly 視覺化圖表
                            st.subheader("📈 品質視覺化分析 (Quality Visualizations)")
                            chart_col1, chart_col2 = st.columns(2)
                            
                            # 圖表 1：Health Score 半圓形儀表盤
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
                                
                            # 圖表 2：各欄位缺失率柱狀圖
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
                            
                            # 缺失值詳細表格
                            st.subheader("📋 缺失值統計 (Null Counts & Ratios)")
                            null_counts = res_data["quality_report"]["null_counts"]
                            
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

            # -------------------- 模式 B：多檔案批次上傳 (Day 16 新增批次摘要) --------------------
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()
                success_count = 0
                batch_summary = []
                
                for index, file_obj in enumerate(uploaded_files):
                    status_text.text(f"⏳ 正在分析第 ({index+1}/{len(uploaded_files)}) 個檔案: {file_obj.name}...")
                    try:
                        files = {"file": (file_obj.name, file_obj.getvalue(), file_obj.type)}
                        response = requests.post(f"{API_BASE_URL}/api/v1/upload", files=files)
                        
                        if response.status_code == 200:
                            res_data = response.json()
                            success_count += 1
                            batch_summary.append({
                                "檔案名稱": file_obj.name,
                                "Health Score": res_data["quality_report"]["health_score"],
                                "總列數": res_data["metadata"]["total_rows"],
                                "總欄數": res_data["metadata"]["total_columns"],
                                "重複列數": res_data["quality_report"]["duplicate_rows"],
                                "Audit ID": res_data["audit_id"]
                            })
                        else:
                            st.error(f"❌ 檔案 {file_obj.name} 檢測失敗 ({response.status_code}): {response.text}")
                    except Exception as e:
                        st.error(f"❌ 檔案 {file_obj.name} 連線失敗: {str(e)}")
                    
                    progress_bar.progress((index + 1) / len(uploaded_files))
                
                status_text.text("🎉 所有檔案批次檢測完成！")
                st.success(f"成功處理 {success_count} / {len(uploaded_files)} 個檔案，報告已儲存至雲端資料庫。")
                
                if batch_summary:
                    st.subheader("📋 本次批次檢測摘要 (Batch Summary)")
                    df_batch = pd.DataFrame(batch_summary)
                    st.dataframe(df_batch, use_container_width=True)

# ==================== 分頁 2：歷史審計紀錄 (Day 13 新增品質趨勢折線圖) ====================
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

                    # ==================== Day 13 新增：品質趨勢折線圖 ====================
                    st.subheader("📈 歷史 Health Score 變化趨勢 (Quality Trend)")
                    
                    # 確保 health_score 與時間欄位轉型正確，避開歷史空資料報錯
                    df_audits["health_score_num"] = pd.to_numeric(df_audits.get("health_score", 0), errors="coerce").fillna(0.0)
                    df_audits["created_at_dt"] = pd.to_datetime(df_audits.get("created_at"), errors="coerce")
                    
                    # 依時間升冪排序以繪製時間序列折線圖
                    df_audits_sorted = df_audits.sort_values(by="created_at_dt", ascending=True)

                    fig_trend = px.line(
                        df_audits_sorted,
                        x="created_at_dt",
                        y="health_score_num",
                        markers=True,
                        text="health_score_num",
                        title="歷次資料審計 Health Score 走勢圖",
                        labels={"created_at_dt": "審計時間 (Time)", "health_score_num": "健康分數 (Health Score)"},
                        hover_data=[c for c in ["file_name", "total_rows", "duplicate_rows"] if c in df_audits_sorted.columns]
                    )
                    
                    fig_trend.update_traces(
                        line=dict(width=3, color="#1f77b4"),
                        marker=dict(size=8, color="#0d47a1"),
                        textposition="top center"
                    )
                    fig_trend.update_layout(
                        yaxis=dict(range=[0, 105]),
                        height=380,
                        margin=dict(l=20, r=20, t=50, b=20)
                    )
                    
                    st.plotly_chart(fig_trend, use_container_width=True)

                    st.divider()

                    # 調整顯示欄位名稱
                    df_audits_display = df_audits.rename(columns={
                        "id": "Audit ID",
                        "file_name": "檔案名稱",
                        "total_rows": "總列數",
                        "total_columns": "總欄數",
                        "health_score": "健康分數",
                        "created_at": "檢測時間"
                    })
                    
                    # 排除內部繪圖用的臨時欄位再展示表格
                    display_cols = [c for c in df_audits_display.columns if c not in ["health_score_num", "created_at_dt"]]
                    st.dataframe(df_audits_display[display_cols], use_container_width=True)

                    # ==================== Day 18 新增：單筆歷史紀錄調閱與下載 ====================
                    st.divider()
                    st.subheader("🔍 單筆審計報告調閱與 JSON 匯出 (Report Export)")

                    # 建立選單選單選項列表 (格式: "檔案名稱 (Audit ID前8碼)")
                    audit_options = {
                        f"{record.get('file_name', 'Unkown')} ({str(record.get('id', ''))[:8]}...) - {record.get('created_at', '')[:10]}": record
                        for record in audits
                    }

                    selected_option = st.selectbox("請選擇要調閱與匯出的審計紀錄：", list(audit_options.keys()))

                    if selected_option:
                        selected_audit = audit_options[selected_option]

                        with st.expander("📋 檢視選定紀錄之完整 JSON 日誌 (JSON Log)", expanded=True):
                            st.json(selected_audit)

                        # 一鍵下載 JSON 按鈕
                        json_str = json.dumps(selected_audit, indent=2, ensure_ascii=False)
                        file_id_short = str(selected_audit.get("id", "audit"))[:8]
                        file_name_clean = str(selected_audit.get("file_name", "report")).replace(".", "_")

                        st.download_button(
                            label="📥 下載此筆 JSON 審計報告",
                            data=json_str,
                            file_name=f"audit_report_{file_name_clean}_{file_id_short}.json",
                            mime="application/json",
                            type="secondary"
                        )

                else:
                    st.warning("目前資料庫中無任何審計紀錄。")
            else:
                st.error(f"無法取得歷史紀錄 ({response.status_code}): {response.text}")
        except Exception as e:
            st.error(f"無法連線至後端服務: {str(e)}")