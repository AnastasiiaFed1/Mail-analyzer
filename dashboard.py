import os
import glob
import pandas as pd
import streamlit as st
import plotly.express as px

# 1. Конфігурація сторінки Streamlit
st.set_page_config(
    page_title="Mail Analyzer Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# 2. Функція завантаження та кешування даних з CSV
@st.cache_data(ttl=30)
def load_all_metrics(data_dir="data"):
    """Завантажує всі CSV файли з директорії data/ та об'єднує їх."""
    if not os.path.exists(data_dir):
        return pd.DataFrame()

    csv_files = glob.glob(os.path.join(data_dir, "*.csv"))
    if not csv_files:
        return pd.DataFrame()

    df_list = []
    for filepath in csv_files:
        try:
            temp_df = pd.read_csv(filepath)
            # Додаємо джерело файлу для контексту, якщо потрібно
            temp_df["source_file"] = os.path.basename(filepath)
            df_list.append(temp_df)
        except Exception as e:
            st.warning(f"Не вдалося прочитати файл {filepath}: {e}")

    if df_list:
        return pd.concat(df_list, ignore_ignore_index=False if False else True)
    return pd.DataFrame()


# 3. Головна панель та заголовок
st.title("📊 Mail Analyzer — Інтерактивний дашборд метрик ОС")
st.markdown(
    """
    Даний дашборд дозволяє аналізувати системне навантаження (RAM, CPU, системні потоки та перемикання контексту) 
    під час виконання різних сценаріїв випробувань поштових клієнтів.
    """
)

# Завантажуємо дані
df = load_all_metrics()

# Перевірка наявності даних
if df.empty:
    st.error("⚠️ У папці `data/` не знайдено жодного CSV-файлу з метриками!")
    st.info(
        """
        **Як виправити:**
        1. Запустіть `test_runner.py` або `system_monitor.py`.
        2. Проведіть хоча б один тест для будь-якого поштового клієнта.
        3. Натисніть кнопку **Оновити дані** нижче.
        """
    )
    if st.button("🔄 Оновити дані"):
        st.rerun()
    st.stop()


# 4. Бічна панель (Sidebar) з фільтрами
st.sidebar.header("⚙️ Фільтри аналізу")

# Фільтр поштових клієнтів
available_apps = sorted(df["app_key"].unique().tolist())
selected_apps = st.sidebar.multiselect(
    "Обрати поштові клієнти:",
    options=available_apps,
    default=available_apps
)

# Фільтр сценаріїв
available_scenarios = sorted(df["scenario"].unique().tolist())
selected_scenarios = st.sidebar.multiselect(
    "Обрати сценарії тестування:",
    options=available_scenarios,
    default=available_scenarios
)

# Кнопка ручного оновлення
if st.sidebar.button("🔄 Оновити дані з `data/`"):
    st.cache_data.clear()
    st.rerun()

# Фільтрація даних
filtered_df = df[
    (df["app_key"].isin(selected_apps)) & 
    (df["scenario"].isin(selected_scenarios))
]

if filtered_df.empty:
    st.warning("⚠️ Немає даних, що відповідають обраним фільтрам. Змініть налаштування у бічному меню.")
    st.stop()


# 5. Ключові показники (KPI Cards)
st.subheader("📌 Загальні показники за обраними фільтрами")
col1, col2, col3, col4 = st.columns(4)

with col1:
    avg_ram = filtered_df["working_set_ram_mb"].mean()
    max_ram = filtered_df["working_set_ram_mb"].max()
    st.metric(
        label="🧠 RAM (Working Set)",
        value=f"{avg_ram:.1f} МБ",
        delta=f"Макс: {max_ram:.1f} МБ"
    )

with col2:
    avg_cpu = filtered_df["user_cpu_percent"].mean()
    max_cpu = filtered_df["user_cpu_percent"].max()
    st.metric(
        label="⚡ CPU User Usage",
        value=f"{avg_cpu:.1f} %",
        delta=f"Макс: {max_cpu:.1f} %"
    )

with col3:
    avg_threads = filtered_df["threads_count"].mean()
    max_threads = filtered_df["threads_count"].max()
    st.metric(
        label="🧵 Кількість потоків",
        value=f"{avg_threads:.0f}",
        delta=f"Макс: {max_threads:.0f}"
    )

with col4:
    avg_ctx = filtered_df["ctx_switches_sec"].mean()
    max_ctx = filtered_df["ctx_switches_sec"].max()
    st.metric(
        label="🔄 Context Switches / sec",
        value=f"{avg_ctx:.1f}",
        delta=f"Макс: {max_ctx:.1f}"
    )

st.markdown("---")


# 6. Вкладки з графіками та таблицями
tab_charts, tab_timeline, tab_summary, tab_raw = st.tabs(
    ["📊 Порівняльні діаграми", "📈 Динаміка у часі", "📋 Зводна таблиця", "📑 Сирі дані (CSV)"]
)

# --- Вкладка 1: Порівняльні діаграми ---
with tab_charts:
    st.subheader("Порівняльний аналіз метрик між поштовиками")
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        # Графік RAM
        fig_ram = px.bar(
            filtered_df.groupby(["app_key", "scenario"], as_index=False)["working_set_ram_mb"].mean(),
            x="app_key",
            y="working_set_ram_mb",
            color="scenario",
            barmode="group",
            title="Середнє використання RAM (МБ)",
            labels={"working_set_ram_mb": "RAM (МБ)", "app_key": "Поштовий клієнт", "scenario": "Сценарій"},
            text_auto=".1f"
        )
        st.plotly_chart(fig_ram, use_container_width=True)

        # Графік Threads
        fig_threads = px.bar(
            filtered_df.groupby(["app_key", "scenario"], as_index=False)["threads_count"].mean(),
            x="app_key",
            y="threads_count",
            color="scenario",
            barmode="group",
            title="Середня кількість активних потоків (Threads)",
            labels={"threads_count": "Потоки", "app_key": "Поштовий клієнт", "scenario": "Сценарій"},
            text_auto=".0f"
        )
        st.plotly_chart(fig_threads, use_container_width=True)

    with col_right:
        # Графік CPU
        fig_cpu = px.bar(
            filtered_df.groupby(["app_key", "scenario"], as_index=False)["user_cpu_percent"].mean(),
            x="app_key",
            y="user_cpu_percent",
            color="scenario",
            barmode="group",
            title="Середнє навантаження CPU User (%)",
            labels={"user_cpu_percent": "CPU (%)", "app_key": "Поштовий клієнт", "scenario": "Сценарій"},
            text_auto=".1f"
        )
        st.plotly_chart(fig_cpu, use_container_width=True)

        # Графік Context Switches
        fig_ctx = px.bar(
            filtered_df.groupby(["app_key", "scenario"], as_index=False)["ctx_switches_sec"].mean(),
            x="app_key",
            y="ctx_switches_sec",
            color="scenario",
            barmode="group",
            title="Інтенсивність перемикання контексту (Context Switches/sec)",
            labels={"ctx_switches_sec": "Перемикання/сек", "app_key": "Поштовий клієнт", "scenario": "Сценарій"},
            text_auto=".1f"
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
            ("threads_count", "Кількість потоків")
        ],
        format_func=lambda x: x[1]
    )
    
    selected_metric_col = metric_choice[0]
    selected_metric_label = metric_choice[1]

    # Графік зміщення метрики у часі
    fig_line = px.line(
        filtered_df,
        x="rel_time_sec",
        y=selected_metric_col,
        color="app_key",
        line_dash="scenario",
        title=f"Динаміка: {selected_metric_label}",
        labels={
            "rel_time_sec": "Час тесту (секунди)",
            selected_metric_col: selected_metric_label,
            "app_key": "Клієнт",
            "scenario": "Сценарій"
        }
    )
    st.plotly_chart(fig_line, use_container_width=True)


# --- Вкладка 3: Зводна таблиця ---
with tab_summary:
    st.subheader("📋 Зводна статистика метрик за клієнтами та сценаріями")
    
    summary_df = filtered_df.groupby(["app_key", "scenario"]).agg(
        RAM_Mean_MB=("working_set_ram_mb", "mean"),
        RAM_Max_MB=("working_set_ram_mb", "max"),
        CPU_User_Mean_Pct=("user_cpu_percent", "mean"),
        CPU_User_Max_Pct=("user_cpu_percent", "max"),
        Threads_Mean=("threads_count", "mean"),
        Ctx_Switches_Mean=("ctx_switches_sec", "mean"),
        Page_Faults_Max=("page_faults_total", "max")
    ).round(2).reset_index()

    st.dataframe(summary_df, use_container_width=True)

    # Скачування таблиці у CSV
    csv_data = summary_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Завантажити зводну таблицю (CSV)",
        data=csv_data,
        file_name="summary_metrics_report.csv",
        mime="text/csv"
    )


# --- Вкладка 4: Сирі дані ---
with tab_raw:
    st.subheader("📑 Усі виміряні записи з файлів")
    st.dataframe(filtered_df, use_container_width=True)