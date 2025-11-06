import pandas as pd
import os

# Aynı klasördeki Excel dosyasını bul (ilk .xlsx uzantılı dosya)
for file in os.listdir():
    if file.endswith(".xlsx"):
        excel_file = file
        break
else:
    raise FileNotFoundError("Klasörde herhangi bir .xlsx dosyası bulunamadı.")

# Excel dosyasını oku
df = pd.read_excel(excel_file)

# 'Title' kolonunun var olup olmadığını kontrol et
if 'Title' not in df.columns:
    raise KeyError("'Title' adlı bir sütun bulunamadı.")

# Unique değer sayısını hesapla
unique_count = df['Title'].nunique()

print(f"'{excel_file}' dosyasındaki 'Title' sütununda {unique_count} farklı değer var.")
