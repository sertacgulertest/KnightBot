import time
import pyautogui

print("Koordinat okuyucu başlatıldı. Çıkmak için terminalde Ctrl+C yapın.")
print("Fareyi öğrenmek istediğiniz yerin üzerine götürün...\n")

try:
  while True:
    # Mouse'un o anki X ve Y koordinatlarını al
    x, y = pyautogui.position()

    # Ekrandaki o pikslein RGB renk kodunu al
    pixel_color = pyautogui.pixel(x, y)

    # Ekrana yazdır (satırın üstüne yazması için \r kullanıyoruz ki spam olmasın)
    print(f"X: {x} | Y: {y} | Renk (RGB): {pixel_color}", end="\r")
    time.sleep(0.1)
except KeyboardInterrupt:
  print("\nKoordinat okuma durduruldu.")