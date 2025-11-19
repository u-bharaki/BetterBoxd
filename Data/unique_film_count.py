import pandas as pd
import os
import glob

# Script klasörü
base_dir = os.path.dirname(os.path.abspath(__file__))
excel_dir = os.path.join(base_dir, "raw_excels")

if not os.path.exists(excel_dir):
    raise FileNotFoundError("'raw_excels' klasörü bulunamadı.")

# Excel dosyalarını listele
excel_files = glob.glob(os.path.join(excel_dir, "*.xls*"))

if not excel_files:
    raise FileNotFoundError("raw_excels içinde Excel dosyası bulunamadı.")

# En güncel Excel dosyasını bul (modified time'a göre)
latest_file = max(excel_files, key=os.path.getmtime)

print("Okunan en güncel dosya:", os.path.basename(latest_file))

# Excel dosyasını oku
df = pd.read_excel(latest_file)

# Kolonları göster (debug amaçlı)
print("Kolonlar:", df.columns.tolist())

# Title kolonu var mı?
if "Title" not in df.columns:
    raise KeyError("'Title' adlı bir sütun bulunamadı.")

# Unique değer sayısı
unique_count = df["Title"].nunique()

print(f"'{os.path.basename(latest_file)}' dosyasındaki 'Title' sütununda {unique_count} farklı değer var.")
