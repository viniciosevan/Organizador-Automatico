from PIL import Image


img = Image.open("img/icone.png")  
img.save("icone.ico", format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
print("✅ Ícone gerado com sucesso: icone.ico")