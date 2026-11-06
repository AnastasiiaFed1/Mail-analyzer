import os
import time
import pandas as pd
import psutil

# 1. Словник процесів для дослідження (список .exe файлів)
PROCESS_MAP = {
    "thunderbird": ["thunderbird.exe"],
    "proton_desktop": ["proton-mail.exe", "protonmail.exe", "proton mail.exe", "proton.exe"],
    "gmail_chrome": ["chrome.exe", "msedge.exe", "googlechrome.exe"],
    "outlook_new": ["ms-outlook.exe", "olk.exe"],
    "proton_web": ["chrome.exe", "msedge.exe"],
}


def monitor_app(app_key, scenario="idle", duration_sec=60, interval=1.0):
    """Збирає розширені метрики ОС для обраного поштового клієнта та сценарію."""
    target_names = PROCESS_MAP.get(app_key.lower(), [])
    if not target_names:
        print(f"[!] Невідомий поштовик: {app_key}")
        return None

    # Перевіряємо та створюємо папку data, якщо її немає
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

        # Метрики CPU та системного планивальника
        cpu_times = psutil.cpu_times_percent(interval=None)
        curr_ctx = psutil.cpu_stats().ctx_switches

        # Обчислення Context Switches/sec
        ctx_switches_sec = (curr_ctx - last_ctx) / dt if dt > 0 else 0
        last_ctx = curr_ctx
        last_time = current_time

        # Агрегація показників усіх процесів клієнта
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
                    # Working Set в МБ
                    total_ram_mb += mem_info.rss / (1024 * 1024)
                    total_threads += proc.info["num_threads"]

                    # Page Faults (якщо підтримується системою)
                    if hasattr(mem_info, "pagefaults"):
                        total_page_faults += mem_info.pagefaults
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Формування щосекундного запису
        records.append({
            "rel_time_sec": round(current_time - start_time, 1),
            "app_key": app_key,
            "scenario": scenario,  # Додано мітку сценарію (idle/medium/heavy)
            "process_count": process_count,
            "user_cpu_percent": cpu_times.user,
            "kernel_cpu_percent": cpu_times.system,
            "working_set_ram_mb": round(total_ram_mb, 2),
            "threads_count": total_threads,
            "ctx_switches_sec": round(ctx_switches_sec, 1),
            "page_faults_total": total_page_faults,
        })

        time.sleep(interval)

    # Збереження у CSV з деталізованою назвою
    df = pd.DataFrame(records)
    filename = f"data/metrics_{app_key}_{scenario}_{int(time.time())}.csv"
    df.to_csv(filename, index=False)
    print(f"[+] Збережено у файл: {filename}")
    return df


if __name__ == "__main__":
    print(" Збір метрик операційної системи для поштових клієнтів")
    print("Оберіть поштовий клієнт:")
    print(" 1. Thunderbird (Десктоп)")
    print(" 2. Proton Mail Desktop (Десктоп)")
    print(" 3. Outlook New (WebView2)")
    print(" 4. Proton Web (Браузер)")
    print(" 5. Gmail Web (Chrome - Спільний еталон)")

    choice = input("Введіть номер (1-5): ").strip()
    apps_dict = {
        "1": "thunderbird",
        "2": "proton_desktop",
        "3": "outlook_new",
        "4": "proton_web",
        "5": "gmail_chrome",
    }
    selected_app = apps_dict.get(choice)

    if not selected_app:
        print("[!] Невірний вибір. Вихід.")
    else:
        print("\nОберіть складність / сценарій тесту:")
        print(" 1. Idle (Простій - без дій)")
        print(" 2. Medium (Інтерактивний скролінг)")
        print(" 3. Heavy (Стрес-тест / Пошук)")

        scen_choice = input("Введіть номер сценарію (1-3): ").strip()
        scen_dict = {"1": "idle", "2": "medium", "3": "heavy"}
        selected_scen = scen_dict.get(scen_choice, "idle")

        print(
            f"\n[!] Переконайтеся, що програма '{selected_app}' ЗАПУЩЕНА в Windows!"
        )
        input(
            "Натисніть Enter для початку збору метрик (тривалість 60 секунд)..."
        )

        monitor_app(
            app_key=selected_app,
            scenario=selected_scen,
            duration_sec=60,
            interval=1.0,
        )