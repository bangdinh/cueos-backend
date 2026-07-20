import sys

with open("main.py", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace('" đ"', '" VNĐ"')
content = content.replace("' đ'", "' VNĐ'")
content = content.replace("0 đ", "0 VNĐ")
content = content.replace("(đ)", "(VNĐ)")
content = content.replace("đ/h", "VNĐ/h")

with open("main.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Replaced all currencies")
