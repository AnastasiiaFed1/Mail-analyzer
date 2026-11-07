import glob
import os

import pandas as pd


def remove_invalid_csvs():
    csv_files = glob.glob("data/*.csv")
    deleted_count = 0

    for filepath in csv_files:
        try:
            df = pd.read_csv(filepath)
            # Перевіряємо, чи середня RAM дорівнює 0 або чи є нулі в колонці
            if (
                "working_set_ram_mb" in df.columns
                and df["working_set_ram_mb"].mean() == 0
            ):
                print(f"Видаляємо бітий файл (нулі в RAM): {filepath}")
                os.remove(filepath)
                deleted_count += 1
            else:
                print(f"Валідний файл що залишається: {filepath}")
        except Exception as e:
            print(f"Помилка зчитування {filepath}: {e}")

    print(f"\nГотово! Видалено {deleted_count} бітих файлів.")


if __name__ == "__main__":
    remove_invalid_csvs()