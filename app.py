import streamlit as st
import pandas as pd
from src.parsers import parse_ashare_csv, parse_futures_csv
from src.ai_processor import process_image
from src.calculator import PortfolioCalculator
from src.models import Position
import io
from datetime import date

st.set_page_config(page_title="TradeSnap - 跨市场持仓与盈亏快照", layout="wide")

# 初始化 session state
if 'calculator' not in st.session_state:
    st.session_state.calculator = PortfolioCalculator()

st.title("📸 TradeSnap: 跨市场每日持仓与盈亏快照")

# 全局设置
with st.sidebar:
    st.header("⚙️ 全局设置")
    base_date = st.date_input("默认交易日期 (若文件中缺失)", date.today())
    
    if st.button("重置所有数据", type="primary"):
        st.session_state.calculator = PortfolioCalculator()
        st.rerun()
    
    st.divider()
    st.markdown("""
    ### 使用说明
    1. 在各子页面上传对应文件。
    2. 核对解析后的数据。
    3. 点击“确认导入”更新持仓。
    4. 在“持仓总览”查看结果。
    """)

# 子页面切换
tab1, tab2, tab3, tab4 = st.tabs(["📊 持仓总览", "🇨🇳 A股导入", "📈 期货导入", "🤖 AI 识别"])

# --- Tab 1: 持仓总览 ---
with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📅 当日持仓快照")
        snapshot = st.session_state.calculator.get_snapshot()
        if snapshot:
            st.dataframe(pd.DataFrame(snapshot), use_container_width=True, hide_index=True)
        else:
            st.info("暂无持仓数据，请先从其他页面导入交易记录。")

    with col2:
        st.subheader("💰 当日已实现盈亏")
        pnl_report = st.session_state.calculator.get_pnl_report()
        if pnl_report:
            df_pnl = pd.DataFrame(pnl_report)
            st.dataframe(df_pnl, use_container_width=True, hide_index=True)
            st.metric("今日总盈亏", f"{df_pnl['产生的盈亏'].sum():,.2f}")
        else:
            st.info("暂无盈亏数据。")

    if snapshot or pnl_report:
        st.divider()
        st.subheader("📥 导出报表")
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            if snapshot: pd.DataFrame(snapshot).to_excel(writer, sheet_name='持仓快照', index=False)
            if pnl_report: pd.DataFrame(pnl_report).to_excel(writer, sheet_name='盈亏明细', index=False)
        
        st.download_button(
            label="下载 Excel 报表",
            data=output.getvalue(),
            file_name=f"TradeSnap_{date.today().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# --- Tab 2: A股导入 ---
with tab2:
    st.subheader("导入 A股 CSV 成交明细")
    ashare_file = st.file_uploader("请拖入 A股 CSV 文件", type=["csv"], key="ashare_uploader")
    if ashare_file:
        try:
            content = ashare_file.getvalue().decode("gbk", errors="ignore")
            trades = parse_ashare_csv(content)
            if trades:
                st.write("🔍 预览解析到的数据:")
                df_trades = pd.DataFrame([vars(t) for t in trades])
                st.dataframe(df_trades, use_container_width=True)
                
                if st.button("确认导入 A股记录", key="btn_ashare"):
                    st.session_state.calculator.process_trades(trades, base_date=base_date)
                    st.success(f"成功导入 {len(trades)} 笔记录！")
            else:
                st.warning("未能解析到有效数据，请检查 CSV 格式。")
        except Exception as e:
            st.error(f"解析出错: {e}")

# --- Tab 3: 期货导入 ---
with tab3:
    st.subheader("导入中国期货 CSV 成交明细")
    futures_file = st.file_uploader("请拖入期货 CSV 文件", type=["csv"], key="futures_uploader")
    if futures_file:
        try:
            content = futures_file.getvalue().decode("gbk", errors="ignore")
            trades = parse_futures_csv(content)
            if trades:
                st.write("🔍 预览解析到的数据:")
                df_trades = pd.DataFrame([vars(t) for t in trades])
                st.dataframe(df_trades, use_container_width=True)
                
                if st.button("确认导入期货记录", key="btn_futures"):
                    st.session_state.calculator.process_trades(trades, base_date=base_date)
                    st.success(f"成功导入 {len(trades)} 笔记录！")
            else:
                st.warning("未能解析到有效数据，请检查 CSV 格式。")
        except Exception as e:
            st.error(f"解析出错: {e}")

# --- Tab 4: AI 识别 ---
with tab4:
    st.subheader("AI 截图识别 (港股 / 外盘期货)")
    img_mode = st.radio("截图类型", ["港股", "外盘期货"], horizontal=True)
    img_file = st.file_uploader("请上传或拖入截图", type=["png", "jpg", "jpeg"], key="img_uploader")
    
    if img_file:
        st.image(img_file, caption="待处理截图", width=400)
        if st.button("开始 AI 解析", key="btn_ai"):
            with st.spinner("AI 正在识别中，请稍候..."):
                mode = 'hk_stock' if img_mode == "港股" else 'futures'
                trades = process_image(img_file.getvalue(), mode=mode)
                if trades:
                    st.session_state.temp_ai_trades = trades
                    st.success(f"AI 提取到 {len(trades)} 笔记录！")
                else:
                    st.error("AI 识别失败，请检查图片清晰度。")
    
    if 'temp_ai_trades' in st.session_state:
        st.write("🔍 AI 提取结果预览:")
        st.dataframe(pd.DataFrame([vars(t) for t in st.session_state.temp_ai_trades]), use_container_width=True)
        if st.button("确认导入 AI 识别记录", key="btn_ai_confirm"):
            st.session_state.calculator.process_trades(st.session_state.temp_ai_trades, base_date=base_date)
            del st.session_state.temp_ai_trades
            st.success("导入成功！")
