import json
import os
from PIL import Image, ImageDraw

IMAGE_DIR = "images"
DATA_FILE = "bot_items.json"
DEFAULT_IMAGE_NAME = "default_ko.png"


def initialize_environment():
  """Gerekli klasör ve varsayılan dosyaların varlığını kontrol eder/oluşturur"""
  if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

  default_path = os.path.join(IMAGE_DIR, DEFAULT_IMAGE_NAME)
  if not os.path.exists(default_path):
    try:
      img = Image.new("RGB", (32, 32), color="#4A6984")
      d = ImageDraw.Draw(img)
      d.text((6, 9), "KO", fill="#FFFFFF")
      img.save(default_path)
    except Exception as e:
      print(f"Varsayılan resim oluşturulamadı: {e}")


def load_bot_data():
  """Kayıtlı eşya verilerini JSON dosyasından okur"""
  if os.path.exists(DATA_FILE):
    try:
      with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
    except Exception as e:
      print(f"Veri okunurken hata oluştu: {e}")
  return {}


def save_bot_data(data):
  """Mevcut eşya verilerini JSON dosyasına kaydeder"""
  try:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
      json.dump(data, f, ensure_ascii=False, indent=4)
  except Exception as e:
    print(f"Veri kaydedilirken hata oluştu: {e}")


def get_default_image_path():
  return os.path.join(IMAGE_DIR, DEFAULT_IMAGE_NAME)