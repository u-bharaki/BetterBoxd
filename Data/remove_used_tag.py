file = "api_keys.txt"

with open(file, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("#used", "")

with open(file, "w", encoding="utf-8") as f:
    f.write(content)

print("Dosya başarıyla temizlendi.")