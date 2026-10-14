import os
import time
import cv2
import numpy as np
from mss import mss


class BotCore:

  def __init__(self, log_callback):
    self.is_running = False
    self.log_callback = log_callback
    self.active_filters = {}

  def start(self, filters):
    self.active_filters = filters
    self.is_running = True
    self.log_callback(
        "Sistem -> Tarama motoru başlatıldı (Filtreler senkronize edildi)."
    )

  def update_filters(self, filters):
    self.active_filters = filters

  def stop(self):
    self.is_running = False
    self.log_callback("Sistem -> Tarama motoru durduruldu.")

  def analyze_inventory_slots(
      self, start_x=1418, start_y=548, cols=7, rows=4, width=39, height=38, step=49
  ):
    """Envanterdeki 4x7 (4 satır, 7 sütun) matris şeklindeki çanta slotlarını tarar

    ve her slotun dolu mu boş mu olduğunu piksel renk varyansı ile raporlar.
    """
    VARIANCE_THRESHOLD = 25.0
    slot_status = []

    with mss() as sct:
      monitor = sct.monitors[1]
      screenshot = sct.grab(monitor)
      img = np.array(screenshot)
      img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

      for row in range(rows):
        row_results = []
        for col in range(cols):
          x = start_x + (col * step)
          y = start_y + (row * step)

          # Slot alanını ekrandan kırp
          slot_crop = img_bgr[y : y + height, x : x + width]
          if slot_crop.size == 0:
            continue

          # Renk varyansını (Standart Sapma) hesapla
          gray_slot = cv2.cvtColor(slot_crop, cv2.COLOR_BGR2GRAY)
          _, std_dev = cv2.meanStdDev(gray_slot)
          variance = std_dev[0][0]

          # Dolu / Boş Durumu
          is_full = variance >= VARIANCE_THRESHOLD
          status = "DOLU" if is_full else "BOŞ"

          row_results.append(
              {
                  "slot": f"R{row+1}C{col+1}",
                  "status": status,
                  "variance": round(variance, 2),
              }
          )
        slot_status.append(row_results)

    return slot_status

  def run_loop(self):
    """MSS and OpenCV kullanarak aktif filtreye sahip ürünleri ve

    envanter slotlarını tarar
    """
    with mss() as sct:
      monitor = sct.monitors[1]
      counter = 0

      while self.is_running:
        try:
          scanned_any = False

          # 1. Önce normal eşyaları (Pot, Shard vb.) tara
          for item_name, data in self.active_filters.items():
            if not self.is_running:
              break

            if not data.get("ignored", True):
              continue

            img_path = data.get("image_path", "")
            if not img_path or not os.path.exists(img_path):
              continue

            template = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
            if template is None:
              continue

            if template.shape[2] == 4:
              template = cv2.cvtColor(template, cv2.COLOR_BGRA2BGR)

            t_h, t_w = template.shape[:2]

            screenshot = sct.grab(monitor)
            img_np = np.array(screenshot)
            screen_bgr = cv2.cvtColor(img_np, cv2.COLOR_BGRA2BGR)

            result = cv2.matchTemplate(
                screen_bgr, template, cv2.TM_CCOEFF_NORMED
            )
            _, max_val, _, max_loc = cv2.minMaxLoc(result)

            THRESHOLD = 0.80
            if max_val >= THRESHOLD:
              top_left_x, top_left_y = max_loc
              center_x = top_left_x + (t_w // 2)
              center_y = top_left_y + (t_h // 2)

              self.log_callback(f"{item_name} -> [{center_x}, {center_y}]")
              scanned_any = True
              time.sleep(1.0)

          # 2. Envanter Çanta Doluluk Kontrolü (4x7 = 28 Slot)
          counter += 1
          if counter >= 5:
            counter = 0
            inventory_status = self.analyze_inventory_slots()

            empty_slots = 0
            full_slots = 0
            detay_log = []

            for row in inventory_status:
              for slot in row:
                if slot["status"] == "BOŞ":
                  empty_slots += 1
                else:
                  full_slots += 1
                #detay_log.append(f"{slot['slot']}:{slot['status']}(v:{slot['variance']})")

            self.log_callback(
                f"Çanta Analizi -> Dolu: {full_slots} | Boş: {empty_slots}"
            )
            #self.log_callback(" | ".join(detay_log[:14]))
            #self.log_callback(" | ".join(detay_log[14:]))

          if not scanned_any:
            time.sleep(0.5)

        except Exception as e:
          self.log_callback(f"Tarama Hatası -> {str(e)}")
          time.sleep(1)