import streamlit as st
import skrf as rf
import pandas as pd
import numpy as np
import io
import os
import logging
from datetime import datetime
import tempfile
import streamlit.components.v1 as components
import json 

# ロギング設定
logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')

# --- Sパラメータ処理関数 ---
def process_s2p_files(uploaded_files, param_to_extract='S21', display_mode='対数振幅 (dB)'):
    param_indices = {
        'S11': (0, 0), 'S12': (0, 1), 'S21': (1, 0), 'S22': (1, 1)
    }
    if param_to_extract not in param_indices:
        st.error(f"無効なSパラメータ指定: {param_to_extract}")
        return None
    idx_row, idx_col = param_indices[param_to_extract]

    all_data = {}
    frequencies = None
    first_file_name = None
    error_occurred = False
    data_suffix = ""

    if not uploaded_files:
        st.warning("ファイルがアップロードされていません。")
        return None

    progress_bar = st.progress(0)
    status_text = st.empty()
    total_files = len(uploaded_files)
    temp_file_paths = []

    try:
        for i, uploaded_file in enumerate(uploaded_files):
            filename = uploaded_file.name
            progress_percentage = (i + 1) / total_files
            status_text.text(f"処理中: {filename} ({i+1}/{total_files})")
            logging.info(f"処理中のファイル: {filename}")
            temp_file_path = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".s2p") as temp_file:
                    temp_file.write(uploaded_file.getvalue())
                    temp_file_path = temp_file.name
                    temp_file_paths.append(temp_file_path)

                network = rf.Network(temp_file_path)

                if display_mode == '対数振幅 (dB)':
                    if hasattr(network, 's_def') and network.s_def == 'DB':
                        s_param_data = network.s_db[:, idx_row, idx_col]
                    else:
                        s_param_complex = network.s[:, idx_row, idx_col]
                        magnitude = np.abs(s_param_complex)
                        magnitude = np.maximum(magnitude, 1e-15)
                        s_param_data = 20 * np.log10(magnitude)
                    data_suffix = "_dB" # 関数内のdata_suffixは列名生成にのみ使用
                elif display_mode == '位相 (deg)':
                    s_param_complex = network.s[:, idx_row, idx_col]
                    s_param_data = np.angle(s_param_complex, deg=True)
                    data_suffix = "_deg" # 関数内のdata_suffixは列名生成にのみ使用
                else:
                    st.error(f"内部エラー: 無効な表示モードです - {display_mode}")
                    error_occurred = True
                    continue

                current_frequencies = network.f
                if frequencies is None:
                    frequencies = current_frequencies
                    first_file_name = filename
                elif not np.array_equal(frequencies, current_frequencies):
                    st.warning(f"ファイル '{filename}' の周波数が最初のファイル ('{first_file_name}') と異なります。")

                column_name = f"{os.path.splitext(filename)[0]}_{param_to_extract}{data_suffix}"
                all_data[column_name] = s_param_data
            except ValueError as ve:
                 st.error(f"ファイル '{filename}' の読み込みエラー: {ve}。形式を確認してください。")
                 error_occurred = True
            except Exception as e:
                st.error(f"ファイル '{filename}' の処理中にエラーが発生しました: {e}")
                error_occurred = True

        status_text.text("データ抽出完了。Excelデータを作成中...")

        if not all_data or frequencies is None:
            st.error("有効なデータをどのファイルからも抽出できませんでした。")
            progress_bar.empty(); status_text.empty()
            return None

        df_data = {'Frequency (Hz)': frequencies}
        processed_data = {}
        valid_freq_len = len(frequencies)
        excluded_files = []
        for key, value in all_data.items():
            if len(value) == valid_freq_len:
                processed_data[key] = value
            else:
                original_filename = key.replace(f"_{param_to_extract}{data_suffix}", "") + ".s2p"
                excluded_files.append(original_filename)
        if excluded_files:
            st.warning(f"以下のファイルは周波数点数が異なるためExcel/グラフから除外されました: {', '.join(excluded_files)}")
        if not processed_data:
            st.error("周波数点数が基準と一致する有効なデータがありませんでした。")
            progress_bar.empty(); status_text.empty()
            return None

        df_data.update(processed_data)
        df = pd.DataFrame(df_data)
        logging.info("DataFrame作成完了。")

        progress_bar.empty()
        status_text.empty()
        if error_occurred:
            st.warning("一部のファイルの処理中にエラーが発生しましたが、処理可能なファイルで結果を作成しました。")

        return df

    finally:
        status_text.text("一時ファイルをクリーンアップ中...")
        for path in temp_file_paths:
            try:
                if os.path.exists(path): os.remove(path); logging.info(f"一時ファイル削除: {path}")
            except Exception as e: logging.error(f"一時ファイル削除エラー ({path}): {e}")
        status_text.empty()

# --- Streamlit アプリ本体 ---
st.set_page_config(layout="wide", page_title="Sパラメータ解析ツール")
st.title('Sパラメータ (.s2p) 解析ツール')
st.markdown("アップロードしたSパラメータファイルから指定したパラメータを抽出し、グラフとExcelデータを作成します。")

# --- UI設定 ---
uploaded_files = st.file_uploader("1. .s2pファイルをアップロード", type='s2p', accept_multiple_files=True, help="...")
col1, col2 = st.columns(2)
with col1:
    param_options = ['S11', 'S12', 'S21', 'S22']
    selected_param = st.selectbox("2. Sパラメータを選択", param_options, index=2, help="...")
with col2:
    display_mode_options = ['対数振幅 (dB)', '位相 (deg)']
    selected_display_mode = st.selectbox("3. 表示モードを選択", display_mode_options, index=0, help="...")
run_button = st.button('4. 解析実行', disabled=(not uploaded_files), use_container_width=True)
st.divider()

# --- 解析実行と結果表示 ---
if run_button and uploaded_files:
    st.info(f"解析を開始します...")
    # process_s2p_files 関数を呼び出す
    df_result = process_s2p_files(uploaded_files, selected_param, selected_display_mode)

    if df_result is not None:
        st.success("解析が完了しました！")
        st.subheader("📊 解析結果グラフ (Chart.js)")

        # --- 修正箇所：HTMLテンプレート生成前に必要な変数を定義 ---
        if selected_display_mode == '対数振幅 (dB)':
            suffix_to_remove = f"_{selected_param}_dB" # 凡例ラベルから削除する接尾辞
            y_axis_unit = "dB"
        elif selected_display_mode == '位相 (deg)':
            suffix_to_remove = f"_{selected_param}_deg" # 凡例ラベルから削除する接尾辞
            y_axis_unit = "deg"
        else:
            suffix_to_remove = "" # Fallback
            y_axis_unit = ""

        # 軸ラベルを決定
        ylabel = f"{selected_param} ({y_axis_unit})" # Y軸ラベル
        max_freq = df_result['Frequency (Hz)'].max() if not df_result['Frequency (Hz)'].empty else 0
        if max_freq == 0: freq_unit, freq_divisor = 'Hz', 1
        elif max_freq >= 1e9: freq_unit, freq_divisor = 'GHz', 1e9
        elif max_freq >= 1e6: freq_unit, freq_divisor = 'MHz', 1e6
        elif max_freq >= 1e3: freq_unit, freq_divisor = 'kHz', 1e3
        else: freq_unit, freq_divisor = 'Hz', 1
        xlabel = f'周波数 ({freq_unit})' # X軸ラベル
        # ----------------------------------------------------------

        # DataFrameをChart.js用の辞書に変換
        chart_data_dict = df_result.to_dict(orient='split')
        # 色リスト
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd','#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf','#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5','#c49c94', '#f7b6d2', '#c7c7c7', '#dbdb8d', '#9edae5']

        # HTML/JavaScriptテンプレート
        # 上で定義したPython変数(suffix_to_remove, ylabel, xlabelなど)を埋め込む
        html_template = f"""
        <!DOCTYPE html><html><head>
            <meta charset="UTF-8"><title>S-Parameter Chart</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.2/dist/chart.umd.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-luxon@1.3.1/dist/chartjs-adapter-luxon.umd.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom@2.0.1/dist/chartjs-plugin-zoom.min.js"></script>
        </head><body>
            <div style="height: 550px; width: 100%;"> <canvas id="sParamChart"></canvas> </div>
            <script>
                const ctx = document.getElementById('sParamChart').getContext('2d');
                const chartDataDict = JSON.parse('{json.dumps(chart_data_dict)}');
                const colors = JSON.parse('{json.dumps(colors)}');
                const freqDivisor = {freq_divisor};
                const freqUnit = "{freq_unit}";
                const suffixToRemove = "{suffix_to_remove}"; // ★修正：Pythonから渡す
                const yLabel = "{ylabel}"; // ★修正：Pythonから渡す
                const xLabel = "{xlabel}"; // ★修正：Pythonから渡す

                const labels = chartDataDict.data.map(row => row[0] / freqDivisor);
                const datasets = [];
                for (let i = 1; i < chartDataDict.columns.length; i++) {{
                    datasets.push({{
                        label: chartDataDict.columns[i].replace(suffixToRemove, ''), // ★修正：JS変数を使う
                        data: chartDataDict.data.map(row => row[i]),
                        borderColor: colors[(i - 1) % colors.length],
                        backgroundColor: 'rgba(0,0,0,0)', borderWidth: 1.5, tension: 0.1,
                        pointRadius: 0, pointHitRadius: 5
                    }});
                }}

                const sParamChart = new Chart(ctx, {{
                    type: 'line', data: {{ labels: labels, datasets: datasets }},
                    options: {{
                        responsive: true, maintainAspectRatio: false,
                        interaction: {{ mode: 'index', intersect: false }},
                        scales: {{
                            x: {{ type: 'linear', title: {{ display: true, text: xLabel }}, // ★修正
                                ticks: {{ callback: function(v, i, vs) {{return v.toFixed(2);}} }} }},
                            y: {{ title: {{ display: true, text: yLabel }}, // ★修正
                                ticks: {{ callback: function(v, i, vs) {{return v.toFixed(1);}} }} }}
                        }},
                        plugins: {{
                            legend: {{ display: datasets.length <= 15, position: 'top' }},
                            tooltip: {{ callbacks: {{
                                title: function(tis) {{ return tis.length > 0 ? `${{tis[0].parsed.x.toFixed(2)}} ${{freqUnit}}` : ''; }},
                                label: function(c) {{ return `${{c.dataset.label || ''}}: ${{c.parsed.y !== null ? c.parsed.y.toFixed(2) : 'N/A'}}`; }}
                            }} }},
                            zoom: {{ pan: {{ enabled: true, mode: 'xy' }}, zoom: {{ wheel: {{ enabled: true }}, pinch: {{ enabled: true }}, mode: 'xy' }} }}
                        }}
                    }}
                }});
            </script>
        </body></html>
        """
        components.html(html_template, height=600, scrolling=False)

        # --- グラフ下の区切りとデータ表示 ---
        st.divider()
        st.subheader("📄 抽出データ")
        st.dataframe(df_result.style.format(precision=4), height=300)

        # --- Excelダウンロードボタン ---
        output_excel_bytes = io.BytesIO()
        try:
            with pd.ExcelWriter(output_excel_bytes, engine='openpyxl') as writer:
                df_result.to_excel(writer, index=False, sheet_name=selected_param)
            output_excel_bytes.seek(0)
            fn_excel = f"{selected_param}_{selected_display_mode.replace('(', '').replace(')', '').replace(' ', '_')}_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            st.download_button(label="📋 データをExcelでダウンロード (.xlsx)", data=output_excel_bytes, file_name=fn_excel, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        except ImportError: st.error("'openpyxl' がインストールされていません...")
        except Exception as excel_e: st.error(f"Excelデータ作成エラー: {excel_e}")

elif not uploaded_files:
    st.info("ファイルをアップロードしてください。")

st.divider()
st.caption("Made by HaruSato")