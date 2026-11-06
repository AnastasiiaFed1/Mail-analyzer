import time
import threading
import pyautogui
import system_monitor

# Налаштування безпеки PyAutoGUI (якщо вести мишку у кут екрана — автоклік зупиниться)
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.3


def run_scenario_actions(scenario: str, duration_sec: int):
    """Виконує автоклікерні дії мишею та клавіатурою в залежності від сценарію."""
<<<<<<< HEAD
    print(f"Стартує емуляція сценарію: '{scenario}' на {duration_sec} секунд...")
=======
    print(f"[ PyAutoGUI] Стартує емуляція сценарію: '{scenario}' на {duration_sec} секунд...")
>>>>>>> 876dbbe0a345e2fcf75ce82d6779d853223ed71e
    
    # Очікуємо пару секунд, щоб користувач встиг активувати вікно поштовика
    time.sleep(2)
    start_time = time.time()

    while (time.time() - start_time) < duration_sec:
        if scenario == "idle":
            # Простій — нічого не робимо, просто чекаємо
            time.sleep(1)

        elif scenario == "medium":
            # Інтерактивний скролінг листа/списку листів
            pyautogui.scroll(-500)  # Скрол вниз
            time.sleep(1.5)
            pyautogui.scroll(500)   # Скрол вгору
            time.sleep(1.5)
            pyautogui.press("down") # Гортання клавішами
            time.sleep(0.5)
            pyautogui.press("up")
            time.sleep(1.5)

        elif scenario == "heavy":
            # Стрес-тест: Пошук, швидкий скролінг та переключення гарячими клавішами
            pyautogui.hotkey("ctrl", "f")  # Відкрити пошук (або Ctrl+E)
            time.sleep(0.5)
            pyautogui.typewrite("test report invoice urgent", interval=0.05)
            pyautogui.press("enter")
            time.sleep(1.0)
            
            # Агресивний скролінг
            for _ in range(5):
                pyautogui.scroll(-800)
                time.sleep(0.2)
            for _ in range(5):
                pyautogui.scroll(800)
                time.sleep(0.2)
                
            pyautogui.press("pagedown")
            time.sleep(0.5)
            pyautogui.press("pageup")
            time.sleep(0.5)
            pyautogui.press("esc")  # Скинути пошук
            time.sleep(1.0)

<<<<<<< HEAD
    print(f"Емуляцію сценарію '{scenario}' завершено.")
=======
    print(f"[ PyAutoGUI] Емуляцію сценарію '{scenario}' завершено.")
>>>>>>> 876dbbe0a345e2fcf75ce82d6779d853223ed71e


def start_test(app_key: str, scenario: str, duration_sec: int = 60):
    """Створює паралельні потоки для одночасного збору метрик ОС та виконання дій автоклікера."""
    
    # 1. Поток для збору метрик ОС (з файлу system_monitor.py)
    monitor_thread = threading.Thread(
        target=system_monitor.monitor_app,
        kwargs={
            "app_key": app_key,
            "scenario": scenario,
            "duration_sec": duration_sec,
            "interval": 1.0,
        },
        daemon=True
    )

    # 2. Поток для виконання автоклікерних дій
    action_thread = threading.Thread(
        target=run_scenario_actions,
        kwargs={
            "scenario": scenario,
            "duration_sec": duration_sec,
        },
        daemon=True
    )

    print("\n=======================================================")
<<<<<<< HEAD
    print(f" Старт тесту: {app_key.upper()} | Сценарій: {scenario.upper()}")
=======
    print(f"[ TEST RUNNER] Старт тесту: {app_key.upper()} | Сценарій: {scenario.upper()}")
>>>>>>> 876dbbe0a345e2fcf75ce82d6779d853223ed71e
    print("Увага! Переключіться на вікно поштового клієнта зараз!")
    print("Початок автокліків через 5 секунд...")
    print("=======================================================\n")
    
    for i in range(5, 0, -1):
        print(f"Старт через {i}...")
        time.sleep(1)

    # Одночасний запуск двох потоків
    monitor_thread.start()
    action_thread.start()

    # Очікуємо завершення обох процесів
    monitor_thread.join()
    action_thread.join()

<<<<<<< HEAD
    print("\nТестування успішно завершено! Дані збережено у папку 'data/'.")
=======
    print("\n Тестування успішно завершено! Дані збережено у папку 'data/'.")
>>>>>>> 876dbbe0a345e2fcf75ce82d6779d853223ed71e


if __name__ == "__main__":
    print("=== Автоматичний тест-раннер поштових клієнтів ===")
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
        print("\nОберіть сценарій навантаження:")
        print(" 1. Idle (Простій - без дій)")
        print(" 2. Medium (Інтерактивний скролінг)")
        print(" 3. Heavy (Стрес-тест / Пошук)")

        scen_choice = input("Введіть номер сценарію (1-3): ").strip()
        scen_dict = {"1": "idle", "2": "medium", "3": "heavy"}
        selected_scen = scen_dict.get(scen_choice, "idle")

        # Запуск тесту тривалістю 60 секунд
        start_test(app_key=selected_app, scenario=selected_scen, duration_sec=60)