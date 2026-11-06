import os
import time
import pandas as pd
import psutil

# 1. Розширений словник процесів для виявлення в Windows
PROCESS_MAP = {
    "thunderbird": ["thunderbird.exe"],
    "proton_desktop": ["proton-mail.exe", "protonmail.exe"],
    "gmail_chrome": ["chrome.exe"],
    "outlook_new": [
        "olk.exe",
        "outlook.exe",
        "ms-outlook.exe",
        "hxmail.exe",
        "hxtsr.exe",
        "msedgewebview2.exe",  # Новий Outlook розгортається у WebView2
    ],
    "proton_web": ["chrome.exe", "msedge.exe"],
}


def monitor_app(app_key, scenario="idle", duration_sec=60, interval=1.0):
    """Збирає розширені метрики ОС для обраного поштового клієнта та сценарію."""
    target_names = PROCESS_MAP.get(app_key.lower(), [])
    if not target_names:
        print(f"[!] Невідомий поштовик: {app_key}")
        return None

    if not os.path.exists("data"):
        os.makedirs("data")

    print(
        f"\n[*] Моніторинг: '{app_key}' | Сценарій: '{scenario}' | Тривалість: {duration_sec}с..."
    )

    records = []
    start_time = time.time()
    last_ctx = psutil.cpu_stats().ctx_switches
    last_time = start_time

    while (time.time() - start_time) < duration_sec:
        current_time = time.time()
        dt = current_time - last_time

        cpu_times = psutil.cpu_times_percent(interval=None)
        curr_ctx = psutil.cpu_stats().ctx_switches

        ctx_switches_sec = (curr_ctx - last_ctx) / dt if dt > 0 else 0
        last_ctx = curr_ctx
        last_time = current_time

        total_ram_mb = 0.0
        total_page_faults = 0
        total_threads = 0
        process_count = 0

        for proc in psutil.process_iter(["name", "memory_info", "num_threads"]):
            try:
                proc_name = proc.info["name"].lower() if proc.info["name"] else ""
                if proc_name in target_names:
                    process_count += 1
                    mem_info = proc.memory_info()
                    total_ram_mb += mem_info.rss / (1024 * 1024)
                    total_threads += proc.info["num_threads"]

                    if hasattr(mem_info, "pagefaults"):
                        total_page_faults += mem_info.pagefaults
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if process_count == 0 and len(records) % 10 == 0:
            print(f"[ Попередження] Процеси для '{app_key}' не знайдені в системі! Перевірте: {target_names}")

        records.append({
            "rel_time_sec": round(current_time - start_time, 1),
            "app_key": app_key,
            "scenario": scenario,
            "process_count": process_count,
            "user_cpu_percent": cpu_times.user,
            "kernel_cpu_percent": cpu_times.system,
            "working_set_ram_mb": round(total_ram_mb, 2),
            "threads_count": total_threads,
            "ctx_switches_sec": round(ctx_switches_sec, 1),
            "page_faults_total": total_page_faults,
        })

        time.sleep(interval)

    df = pd.DataFrame(records)
    filename = f"data/metrics_{app_key}_{scenario}_{int(time.time())}.csv"
    df.to_csv(filename, index=False)
    print(f"[+] Збережено у файл: {filename}")
    return df


if __name__ == "__main__":
    print("=== Збір метрик ОС (system_monitor.py) ===")
    monitor_app("outlook_new", "heavy", 60)