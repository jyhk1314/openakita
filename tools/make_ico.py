from PIL import Image

src = r"apps/setup-center/src-tauri/icons/icon.png"
dst = r"apps/setup-center/src-tauri/icons/icon.ico"

img = Image.open(src).convert("RGBA")
# 含 96：Windows 125%/150% 缩放常用；含 20/40：更多 DPI 档位
sizes = [(16, 16), (20, 20), (24, 24), (32, 32), (40, 40), (48, 48), (64, 64), (96, 96), (128, 128), (256, 256)]
img.save(dst, sizes=sizes)
print("written", dst)