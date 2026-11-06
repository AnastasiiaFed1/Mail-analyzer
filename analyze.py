import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def load_all_metrics(data_dir="data"):
    """Завантажує всі CSV файли з метриками з директорії data/ в єдиний DataFrame."""
    csv_files = glob.glob(os.path.join(data_dir, "metrics_*.csv"))

    if not csv_files:
        print(f"[!] CSV файлів у папці '{data_dir}/' не знайдено.")
        print("Спочатку запустіть 'monitor.py' та проведіть вимірювання.")
        return None

    df_list = []
    for filepath in csv_files:
        try:
            temp_df = pd.read_csv(filepath)
            df_list.append(temp_df)
        except Exception as e:
            print(f"[!] Помилка при зчитуванні файлу {filepath}: {e}")

    if not df_list:
        print("[!] Не вдалося зчитати жодного файлу даних.")
        return None

    combined_df = pd.concat(df_list, ignore_index=True)
    print(
        f"[+] Успішно завантажено {len(df_list)} файлів (всього записів: {len(combined_df)})."
    )
    return combined_df


def generate_summary_report(df):
    """Розраховує підсумкові статистичні показники (середні та максимальні)
    та зберігає їх у зводну таблицю summary_report.csv.
    """
    required_cols = [
        "working_set_ram_mb",
        "user_cpu_percent",
        "kernel_cpu_percent",
        "threads_count",
        "ctx_switches_sec",
    ]
    available_cols = [col for col in required_cols if col in df.columns]

    agg_dict = {col: ["mean", "max"] for col in available_cols}

    if "page_faults_total" in df.columns:
        agg_dict["page_faults_total"] = ["max"]

    summary = df.groupby(["app_key", "scenario"]).agg(agg_dict).round(2)

    print("\n=================== ЗВОДНИЙ ЗВІТ МЕТРИК ===================")
    print(summary)

    output_csv = "summary_report.csv"
    summary.to_csv(output_csv)
    print(f"\n[+] Зводний звіт збережено у файл: '{output_csv}'")
    return summary


def plot_graphs(df):
    """Будує порівняльні діаграми для метрик та зберігає їх у директорію plots/."""
    plots_dir = "plots"
    os.makedirs(plots_dir, exist_ok=True)

    # Налаштування стилю графіків
    sns.set_theme(style="whitegrid", palette="muted")
    plt.rcParams.update({"font.size": 11, "figure.autolayout": True})

    # 1. Використання оперативної пам'яті (RAM Working Set)
    if "working_set_ram_mb" in df.columns:
        plt.figure(figsize=(10, 6))
        ax = sns.barplot(
            data=df,
            x="app_key",
            y="working_set_ram_mb",
            hue="scenario",
            errorbar=None,
        )
        plt.title(
            "Порівняння використання оперативної пам'яті (RAM Working Set, МБ)",
            fontsize=14,
            pad=15,
        )
        plt.xlabel("Поштовий клієнт", fontsize=12)
        plt.ylabel("RAM (МБ)", fontsize=12)
        plt.legend(title="Сценарій навантаження")

        # Додаємо значення над стовпчиками
        for p in ax.patches:
            height = p.get_height()
            if height > 0:
                ax.annotate(
                    f"{height:.1f}",
                    (p.get_x() + p.get_width() / 2.0, height),
                    ha="center",
                    va="bottom",
                    fontsize=9,
                    xytext=(0, 3),
                    textcoords="offset points",
                )

        plt.savefig(os.path.join(plots_dir, "ram_comparison.png"), dpi=300)
        plt.close()

    # 2. Навантаження на процесор (CPU User %)
    if "user_cpu_percent" in df.columns:
        plt.figure(figsize=(10, 6))
        sns.barplot(
            data=df,
            x="app_key",
            y="user_cpu_percent",
            hue="scenario",
            errorbar=None,
        )
        plt.title(
            "Навантаження на процесор у режимі користувача (CPU User %)",
            fontsize=14,
            pad=15,
        )
        plt.xlabel("Поштовий клієнт", fontsize=12)
        plt.ylabel("CPU User (%)", fontsize=12)
        plt.legend(title="Сценарій навантаження")
        plt.savefig(
            os.path.join(plots_dir, "cpu_user_comparison.png"), dpi=300
        )
        plt.close()

    # 3. Кількість активних потоків (Threads Count)
    if "threads_count" in df.columns:
        plt.figure(figsize=(10, 6))
        sns.barplot(
            data=df,
            x="app_key",
            y="threads_count",
            hue="scenario",
            errorbar=None,
        )
        plt.title(
            "Порівняння кількості системних потоків (Threads)",
            fontsize=14,
            pad=15,
        )
        plt.xlabel("Поштовий клієнт", fontsize=12)
        plt.ylabel("Кількість потоків", fontsize=12)
        plt.legend(title="Сценарій навантаження")
        plt.savefig(
            os.path.join(plots_dir, "threads_comparison.png"), dpi=300
        )
        plt.close()

    # 4. Перемикання контексту (Context Switches/sec)
    if "ctx_switches_sec" in df.columns:
        plt.figure(figsize=(10, 6))
        sns.barplot(
            data=df,
            x="app_key",
            y="ctx_switches_sec",
            hue="scenario",
            errorbar=None,
        )
        plt.title(
            "Інтенсивність перемикання контексту (Context Switches / sec)",
            fontsize=14,
            pad=15,
        )
        plt.xlabel("Поштовий клієнт", fontsize=12)
        plt.ylabel("Перемикання/сек", fontsize=12)
        plt.legend(title="Сценарій навантаження")
        plt.savefig(
            os.path.join(plots_dir, "ctx_switches_comparison.png"), dpi=300
        )
        plt.close()

    print(
        f"[+] Графіки успішно побудовано та збережено в папку '{plots_dir}/'!"
    )


if __name__ == "__main__":
    print("=== Аналіз та візуалізація метрик поштових клієнтів ===")
    df_metrics = load_all_metrics()

    if df_metrics is not None:
        generate_summary_report(df_metrics)
        plot_graphs(df_metrics)
        print("\n[+] Обробка даних завершена успішно!")