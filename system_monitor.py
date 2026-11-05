import time
import pandas as pd
import psutil

# Словник процесів для дослідження
PROCESS_MAP = {
    "thunderbird": ["thunderbird.exe"],
    "proton_desktop": ["proton-mail.exe", "protonmail.exe"],
    "gmail_chrome": ["chrome.exe"],
    "outlook_new": ["ms-outlook.exe", "olk.exe"],
    "proton_web": ["chrome.exe", "msedge.exe"],
}


def monitor_app(app_key, duration_sec=60, interval=1.0):
    """Збирає розширені метрики ОС для обраного поштового клієнта."""
    target_names = PROCESS_MAP.get(app_key.lower(), [])
    if not target_names:
        print(f"[!] Невідомий поштовик: {app_key}")
        return

    print(
        f"[*] Розпочато моніторинг для '{app_key}' на {duration_sec} секунд (інтервал {interval}с)..."
    )

    records = []
    start_time = time.time()
    last_ctx = psutil.cpu_stats().ctx_switches
    last_time = start_time

    while (time.time() - start_time) < duration_sec:
        current_time = time.time()
        dt = current_time - last_time

        # 1. Загальні системні метрики (Лекції 3, 4 & Лаб №4)
        cpu_times = psutil.cpu_times_percent(interval=None)
        curr_ctx = psutil.cpu_stats().ctx_switches

        # Перемикання контексту на секунду (Context Switches/sec)
        ctx_switches_sec = (curr_ctx - last_ctx) / dt if dt > 0 else 0
        last_ctx = curr_ctx
        last_time = current_time

        # 2. Агрегація показників усіх процесів клієнта
        total_ram_mb = 0.0
        total_page_faults = 0
        total_threads = 0
        process_count = 0

        for proc in psutil.process_iter(
            ["name", "memory_info", "num_threads"]
        ):
            try:
                if proc.info["name"].lower() in target_names:
                    process_count += 1
                    mem_info = proc.memory_info()
                    total_ram_mb += mem_info.rss / (1024 * 1024)  # Working Set в МБ
                    total_threads += proc.info["num_threads"]

                    # Page faults (якщо підтримується ОС)
                    if hasattr(mem_info, "pagefaults"):
                        total_page_faults += mem_info.pagefaults
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Запис вибірки
        records.append({
            "rel_time_sec": round(current_time - start_time, 1),
            "app_key": app_key,
            "process_count": process_count,
            "user_cpu_percent": cpu_times.user,
            "kernel_cpu_percent": cpu_times.system,
            "working_set_ram_mb": round(total_ram_mb, 2),
            "threads_count": total_threads,
            "ctx_switches_sec": round(ctx_switches_sec, 1),
            "page_faults_total": total_page_faults,
        })

        time.sleep(interval)

    # Збереження у CSV
    df = pd.DataFrame(records)
    filename = f"data/metrics_{app_key}_{int(time.time())}.csv"
    df.to_csv(filename, index=False)
    print(f"[+] Моніторинг завершено! Дані збережено у файл: {filename}")
    return df


if __name__ == "__main__":
    # Тестовий запуск для Thunderbird на 30 секунд
    print("=== Тестовий запуск ===")
    monitor_app(app_key="thunderbird", duration_sec=30, interval=1.0)