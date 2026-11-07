import glob
import os
import pandas as pd
import plotly.express as px
import streamlit as st

# 1. Конфігурація сторінки Streamlit
st.set_page_config(
    page_title="Mail Analyzer Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)


# 2. Функція завантаження та кешування даних з CSV
@st.cache_data(ttl=30)
def load_all_metrics(data_dir="data"):
    """Завантажує всі CSV файли з директорії data/, відфільтровує біті записи
    та додає контекст про ПК-джерело.
    """
    if not os.path.exists(data_dir):
        return pd.DataFrame()

    csv_files = glob.glob(os.path.join(data_dir, "*.csv"))
    if not csv_files:
        return pd.DataFrame()

    df_list = []
    for filepath in csv_files:
        try:
            temp_df = pd.read_csv(filepath)

            # Перевірка та відсіювання бітих замірів (де RAM == 0)
            if (
                "working_set_ram_mb" in temp_df.columns
                and temp_df["working_set_ram_mb"].mean() > 0
            ):
                filename = os.path.basename(filepath)
                file_id = filename.split("_")[-1].replace(".csv", "")[-4:]

                # Визначаємо ПК за профілем навантаження потоків/процесів
                avg_th = temp_df["threads_count"].mean()
                pc_label = "ПК 2" if avg_th > 1500 else "ПК 1"

                temp_df["source_file"] = filename
                temp_df["run_id"] = f"#{file_id}"
                temp_df["pc_source"] = pc_label
                # Унікальний ярлик для відображення на графіках: "gmail_chrome (idle) [ПК 2 #1234]"
                temp_df["run_label"] = (
                    temp_df["app_key"]
                    + " ("
                    + temp_df["scenario"]
                    + ") ["
                    + pc_label
                    + " "
                    + temp_df["run_id"]
                    + "]"
                )

                df_list.append(temp_df)
        except Exception as e:
            st.warning(f"Не вдалося прочитати файл {filepath}: {e}")

    if df_list:
        return pd.concat(df_list, ignore_index=True)
    return pd.DataFrame()


# 3. Головна панель та заголовок
st.title("Mail Analyzer — Інтерактивний дашборд метрик ОС")
st.markdown(
    """
    Даний дашборд дозволяє аналізувати системне навантаження (RAM, CPU, системні потоки та перемикання контексту) 
    під час виконання різних сценаріїв випробувань поштових клієнтів на двох тестових ПК.
    """
)

# Завантажуємо дані
df = load_all_metrics()

# Перевірка наявності даних
if df.empty:
    st.error("У папці data/ не знайдено жодного валідного CSV-файлу з метриками!")
    st.info(
        """
        **Як виправити:**
        1. Переконайтеся, що в папці data/ є файли .csv.
        2. Запустіть test_runner.py для збору нових метрик.
        3. Перевірте, що процеси браузерів/поштовиків коректно знаходяться у PROCESS_MAP.
        """
    )
    if st.button("Оновити дані"):
        st.rerun()
    st.stop()


# 4. Бічна панель (Sidebar) з фільтрами
st.sidebar.header("Фільтри аналізу")

# Фільтр поштових клієнтів
available_apps = sorted(df["app_key"].unique().tolist())
selected_apps = st.sidebar.multiselect(
    "Обрати поштові клієнти:", default=available_apps, options=available_apps
)

# Фільтр сценаріїв
available_scenarios = sorted(df["scenario"].unique().tolist())
selected_scenarios = st.sidebar.multiselect(
    "Обрати сценарії тестування:",
    default=available_scenarios,
    options=available_scenarios,
)

# Фільтр по комп'ютерах (ПК 1 / ПК 2)
available_pcs = sorted(df["pc_source"].unique().tolist())
selected_pcs = st.sidebar.multiselect(
    "Обрати джерело (ПК):", default=available_pcs, options=available_pcs
)

# Кнопка ручного оновлення
if st.sidebar.button("Оновити дані з data/"):
    st.cache_data.clear()
    st.rerun()

# Фільтрація даних
filtered_df = df[
    (df["app_key"].isin(selected_apps))
    & (df["scenario"].isin(selected_scenarios))
    & (df["pc_source"].isin(selected_pcs))
]

if filtered_df.empty:
    st.warning(
        "Немає даних, що відповідають обраним фільтрам. Змініть налаштування у бічному меню."
    )
    st.stop()


# 5. Ключові показники (KPI Cards)
st.subheader("Загальні показники за обраними фільтрами")
col1, col2, col3, col4 = st.columns(4)

with col1:
    avg_ram = filtered_df["working_set_ram_mb"].mean()
    max_ram = filtered_df["working_set_ram_mb"].max()
    st.metric(
        label="RAM (Working Set)",
        value=f"{avg_ram:.1f} МБ",
        delta=f"Макс: {max_ram:.1f} МБ",
    )

with col2:
    avg_cpu = filtered_df["user_cpu_percent"].mean()
    max_cpu = filtered_df["user_cpu_percent"].max()
    st.metric(
        label="CPU User Usage",
        value=f"{avg_cpu:.1f} %",
        delta=f"Макс: {max_cpu:.1f} %",
    )

with col3:
    avg_threads = filtered_df["threads_count"].mean()
    max_threads = filtered_df["threads_count"].max()
    st.metric(
        label="Кількість потоків",
        value=f"{avg_threads:.0f}",
        delta=f"Макс: {max_threads:.0f}",
    )

with col4:
    avg_ctx = filtered_df["ctx_switches_sec"].mean()
    max_ctx = filtered_df["ctx_switches_sec"].max()
    st.metric(
        label="Context Switches / sec",
        value=f"{avg_ctx:.1f}",
        delta=f"Макс: {max_ctx:.1f}",
    )

st.markdown("---")


# 6. Вкладки з графіками та таблицями
tab_charts, tab_timeline, tab_summary, tab_raw = st.tabs(
    [
        "Порівняльні діаграми",
        "Динаміка у часі",
        "Зводна таблиця",
        "Сирі дані (CSV)",
    ]
)

# --- Вкладка 1: Порівняльні діаграми ---
with tab_charts:
    st.subheader("Порівняльний аналіз метрик між поштовиками")

    col_left, col_right = st.columns(2)

    with col_left:
        # Графік RAM
        ram_agg = filtered_df.groupby(["app_key", "scenario"], as_index=False)[
            "working_set_ram_mb"
        ].mean()
        fig_ram = px.bar(
            ram_agg,
            x="app_key",
            y="working_set_ram_mb",
            color="scenario",
            barmode="group",
            title="Середнє використання RAM (МБ)",
            labels={
                "working_set_ram_mb": "RAM (МБ)",
                "app_key": "Поштовий клієнт",
                "scenario": "Сценарій",
            },
            text_auto=".1f",
        )
        st.plotly_chart(fig_ram, use_container_width=True)

        # Графік Threads
        threads_agg = filtered_df.groupby(
            ["app_key", "scenario"], as_index=False
        )["threads_count"].mean()
        fig_threads = px.bar(
            threads_agg,
            x="app_key",
            y="threads_count",
            color="scenario",
            barmode="group",
            title="Середня кількість активних потоків (Threads)",
            labels={
                "threads_count": "Потоки",
                "app_key": "Поштовий клієнт",
                "scenario": "Сценарій",
            },
            text_auto=".0f",
        )
        st.plotly_chart(fig_threads, use_container_width=True)

    with col_right:
        # Графік CPU
        cpu_agg = filtered_df.groupby(["app_key", "scenario"], as_index=False)[
            "user_cpu_percent"
        ].mean()
        fig_cpu = px.bar(
            cpu_agg,
            x="app_key",
            y="user_cpu_percent",
            color="scenario",
            barmode="group",
            title="Середнє навантаження CPU User (%)",
            labels={
                "user_cpu_percent": "CPU (%)",
                "app_key": "Поштовий клієнт",
                "scenario": "Сценарій",
            },
            text_auto=".1f",
        )
        st.plotly_chart(fig_cpu, use_container_width=True)

        # Графік Context Switches
        ctx_agg = filtered_df.groupby(["app_key", "scenario"], as_index=False)[
            "ctx_switches_sec"
        ].mean()
        fig_ctx = px.bar(
            ctx_agg,
            x="app_key",
            y="ctx_switches_sec",
            color="scenario",
            barmode="group",
            title="Інтенсивність перемикання контексту (Context Switches/sec)",
            labels={
                "ctx_switches_sec": "Перемикання/сек",
                "app_key": "Поштовий клієнт",
                "scenario": "Сценарій",
            },
            text_auto=".1f",
        )
        st.plotly_chart(fig_ctx, use_container_width=True)


# --- Вкладка 2: Динаміка у часі ---
with tab_timeline:
    st.subheader("Зміна метрик упродовж тесту (60 секунд)")

    metric_choice = st.selectbox(
        "Оберіть метрику для часового ряду:",
        options=[
            ("working_set_ram_mb", "Використання RAM (МБ)"),
            ("user_cpu_percent", "Навантаження CPU (%)"),
            ("ctx_switches_sec", "Context Switches / sec"),
            ("threads_count", "Кількість потоків"),
        ],
        format_func=lambda x: x[1],
    )

    selected_metric_col = metric_choice[0]
    selected_metric_label = metric_choice[1]

    # Побудова лінійного графіка із захистом від накладання ліній через line_group
    fig_line = px.line(
        filtered_df,
        x="rel_time_sec",
        y=selected_metric_col,
        color="app_key",
        line_dash="scenario",
        line_group="source_file",  # Групування за файлом запобігає пересічанню дублікатів
        hover_data=["pc_source", "source_file"],
        title=f"Динаміка: {selected_metric_label}",
        labels={
            "rel_time_sec": "Час тесту (секунди)",
            selected_metric_col: selected_metric_label,
            "app_key": "Клієнт",
            "scenario": "Сценарій",
            "pc_source": "Комп'ютер",
        },
    )
    st.plotly_chart(fig_line, use_container_width=True)


# --- Вкладка 3: Зводна таблиця ---
with tab_summary:
    st.subheader("Зводна статистика метрик за клієнтами та сценаріями")

    summary_df = (
        filtered_df.groupby(["app_key", "scenario", "pc_source"])
        .agg(
            RAM_Mean_MB=("working_set_ram_mb", "mean"),
            RAM_Max_MB=("working_set_ram_mb", "max"),
            CPU_User_Mean_Pct=("user_cpu_percent", "mean"),
            CPU_User_Max_Pct=("user_cpu_percent", "max"),
            Threads_Mean=("threads_count", "mean"),
            Ctx_Switches_Mean=("ctx_switches_sec", "mean"),
            Page_Faults_Max=("page_faults_total", "max"),
        )
        .round(2)
        .reset_index()
    )

    st.dataframe(summary_df, use_container_width=True)

    # Скачування таблиці у CSV
    csv_data = summary_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Завантажити зводну таблицю (CSV)",
        data=csv_data,
        file_name="summary_metrics_report.csv",
        mime="text/csv",
    )


# --- Вкладка 4: Сирі дані ---
with tab_raw:
    st.subheader("Усі виміряні записи з файлів")
    st.dataframe(filtered_df, use_container_width=True)