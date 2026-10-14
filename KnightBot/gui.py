import os
import shutil
import threading
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk

# Parçaladığımız modülleri projeye dahil ediyoruz
from bot_core import BotCore
from config_manager import (
    get_default_image_path,
    initialize_environment,
    load_bot_data,
    save_bot_data,
)


class KnightBotGUI:

  def __init__(self, root):
    self.root = root
    self.root.title(
        "Knight Online Python Bot - Modüler Konum & Tarama Paneli"
    )

    # Pencere Boyutları
    window_width = 880
    window_height = 720

    # Bilgisayar ekranının çözünürlüğünü al
    screen_width = self.root.winfo_screenwidth()
    screen_height = self.root.winfo_screenheight()

    # Ekranın tam ortasına gelecek X ve Y koordinatlarını hesapla
    center_x = int((screen_width / 2) - (window_width / 2))
    center_y = int((screen_height / 2) - (window_height / 2))

    # Pencere boyutunu ve merkez konumunu uygula (WxH+X+Y formatı)
    self.root.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
    self.root.resizable(False, False)

    # Ortam ve verileri hazırla
    initialize_environment()
    self.ignore_items = load_bot_data()

    # Bot Motorunu Tanımla
    self.bot_core = BotCore(log_callback=self.log_message)

    # Arayüz Bileşenlerini Oluştur
    self.create_widgets()

  def create_widgets(self):
    # --- ÜST KISIM: Durum ve Başlat/Durdur Butonları ---
    top_frame = ttk.LabelFrame(
        self.root, text=" Bot Kontrol & Durum ", padding=10
    )
    top_frame.pack(fill="x", padx=10, pady=10)

    self.status_label = ttk.Label(
        top_frame,
        text="Durum: Durduruldu",
        font=("Arial", 11, "bold"),
        foreground="red",
    )
    self.status_label.pack(side="left", padx=5)

    self.btn_stop = ttk.Button(
        top_frame,
        text="Durdur",
        command=self.stop_bot,
        state="disabled",
        width=12,
    )
    self.btn_stop.pack(side="right", padx=5)

    self.btn_start = ttk.Button(
        top_frame, text="Başlat", command=self.start_bot, width=12
    )
    self.btn_start.pack(side="right", padx=5)

    # --- ORTA KISIM: Genel Ayarlar ---
    settings_frame = ttk.LabelFrame(
        self.root, text=" Genel Ayarlar ", padding=10
    )
    settings_frame.pack(fill="x", padx=10, pady=5)

    self.collect_box_var = tk.BooleanVar(value=True)
    self.chk_collect_box = ttk.Checkbutton(
        settings_frame, text="Kasa (Kutu) Topla", variable=self.collect_box_var
    )
    self.chk_collect_box.pack(anchor="w", padx=5, pady=5)

    # Ana İçerik Alanı (Sol: Karalist, Sağ: Konsol/Log Paneli)
    content_frame = ttk.Frame(self.root)
    content_frame.pack(fill="both", expand=True, padx=10, pady=5)

    # --- SOL KISIM: Akıllı Karalist (2 Kolonlu Yapı) ---
    ignore_frame = ttk.LabelFrame(
        content_frame, text=" Eşya ve Çöp Filtresi ", padding=10
    )
    ignore_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

    list_container = ttk.Frame(ignore_frame)
    list_container.pack(fill="both", expand=True, padx=5, pady=5)

    self.canvas = tk.Canvas(list_container, height=200)
    self.scrollbar = ttk.Scrollbar(
        list_container, orient="vertical", command=self.canvas.yview
    )
    self.scrollable_frame = ttk.Frame(self.canvas)

    self.scrollable_frame.bind(
        "<Configure>",
        lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
    )
    self.canvas.create_window(
        (0, 0), window=self.scrollable_frame, anchor="nw"
    )
    self.canvas.configure(yscrollcommand=self.scrollbar.set)

    self.canvas.pack(side="left", fill="both", expand=True)
    self.scrollbar.pack(side="right", fill="y")

    self.item_vars = {}
    self.refresh_ignore_list()

    add_frame = ttk.Frame(ignore_frame)
    add_frame.pack(fill="x", padx=5, pady=5)

    btn_open_dialog = ttk.Button(
        add_frame,
        text="+ Yeni Eşya / Görsel Ekle",
        command=self.open_add_item_dialog,
    )
    btn_open_dialog.pack(side="left", padx=5)

    # --- SAĞ KISIM: Konum & Tarama Konsolu (Log Paneli) ---
    console_frame = ttk.LabelFrame(
        content_frame, text=" Konum & Tarama Konsolu ", padding=10
    )
    console_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))

    text_container = ttk.Frame(console_frame)
    text_container.pack(fill="both", expand=True)

    self.log_text = tk.Text(
        text_container,
        height=14,
        width=48,
        bg="#1e1e1e",
        fg="#00ff00",
        font=("Consolas", 9),
        state="disabled",
    )
    log_scrollbar = ttk.Scrollbar(
        text_container, orient="vertical", command=self.log_text.yview
    )
    self.log_text.configure(yscrollcommand=log_scrollbar.set)

    self.log_text.pack(side="left", fill="both", expand=True)
    log_scrollbar.pack(side="right", fill="y")

    btn_clear_log = ttk.Button(
        console_frame, text="Konsolu Temizle", command=self.clear_log
    )
    btn_clear_log.pack(anchor="e", pady=(5, 0))

  def log_message(self, message):
    self.log_text.config(state="normal")
    timestamp = datetime.now().strftime("[%H:%M:%S]")
    self.log_text.insert(tk.END, f"{timestamp} {message}\n")
    self.log_text.see(tk.END)
    self.log_text.config(state="disabled")

  def clear_log(self):
    self.log_text.config(state="normal")
    self.log_text.delete("1.0", tk.END)
    self.log_text.config(state="disabled")

  def refresh_ignore_list(self):
    for widget in self.scrollable_frame.winfo_children():
      widget.destroy()

    self.item_vars.clear()
    self.photo_references = []

    items = list(self.ignore_items.items())

    for index, (item_name, data) in enumerate(items):
      row = index // 2
      col = index % 2

      row_frame = ttk.Frame(self.scrollable_frame, padding=2)
      row_frame.grid(row=row, column=col, padx=8, pady=3, sticky="w")

      img_label = ttk.Label(
          row_frame,
          width=4,
          anchor="center",
          relief="solid",
          background="#e0e0e0",
      )
      img_path = data.get("image_path", "")

      if not img_path or not os.path.exists(img_path):
        img_path = get_default_image_path()

      try:
        pil_img = Image.open(img_path)
        pil_img = pil_img.resize((28, 28), Image.Resampling.LANCZOS)
        tk_img = ImageTk.PhotoImage(pil_img)
        self.photo_references.append(tk_img)
        img_label.config(image=tk_img, text="")
      except Exception:
        img_label.config(text="KO", font=("Arial", 9, "bold"))

      img_label.pack(side="left", padx=3)

      var = tk.BooleanVar(value=data["ignored"])
      self.item_vars[item_name] = var

      chk = ttk.Checkbutton(
          row_frame,
          text=item_name,
          variable=var,
          command=lambda name=item_name, v=var: self.on_ignore_toggle(name, v),
      )
      chk.pack(side="left", padx=3)

  def on_ignore_toggle(self, item_name, var):
    self.ignore_items[item_name]["ignored"] = var.get()
    save_bot_data(self.ignore_items)

    # Motor çalışıyorsa anlık filtreleri güncelle
    if hasattr(self, "bot_core"):
      self.bot_core.update_filters(self.ignore_items)

    status_text = "Çöp/Aktif" if var.get() else "Devre Dışı"
    self.log_message(f"Ayar değişti: '{item_name}' durumu -> {status_text}")

  def open_add_item_dialog(self):
    dialog = tk.Toplevel(self.root)
    dialog.title("Yeni Eşya Ekle")
    dialog.geometry("400x280")
    dialog.resizable(False, False)
    dialog.grab_set()

    ttk.Label(
        dialog, text="Eşya Adı:", font=("Arial", 10, "bold")
    ).pack(anchor="w", padx=20, pady=(15, 5))
    entry_name = ttk.Entry(dialog, width=38)
    entry_name.pack(anchor="w", padx=20)

    ttk.Label(
        dialog, text="Eşya Görseli (Opsiyonel):", font=("Arial", 10, "bold")
    ).pack(anchor="w", padx=20, pady=(15, 5))

    path_var = tk.StringVar(value="")
    path_frame = ttk.Frame(dialog)
    path_frame.pack(fill="x", padx=20)

    lbl_path = ttk.Label(
        path_frame, text="Varsayılan KO kullanılacak", foreground="gray", width=22
    )
    lbl_path.pack(side="left", padx=(0, 5))

    preview_label = ttk.Label(
        path_frame, width=6, anchor="center", relief="solid", background="#f0f0f0"
    )
    preview_label.pack(side="left", padx=5)

    dialog_photo_ref = []

    def update_preview(img_path):
      try:
        p_img = Image.open(img_path)
        p_img = p_img.resize((28, 28), Image.Resampling.LANCZOS)
        t_img = ImageTk.PhotoImage(p_img)
        dialog_photo_ref.append(t_img)
        preview_label.config(image=t_img, text="")
      except Exception:
        preview_label.config(text="KO", font=("Arial", 8))

    default_img_path = get_default_image_path()
    if os.path.exists(default_img_path):
      update_preview(default_img_path)

    def select_image():
      file_path = filedialog.askopenfilename(
          title="Eşya Resmi Seç",
          filetypes=[("Resim Dosyaları", "*.png *.jpg *.jpeg *.bmp")],
      )
      if file_path:
        path_var.set(file_path)
        lbl_path.config(text=os.path.basename(file_path), foreground="black")
        update_preview(file_path)

    btn_browse = ttk.Button(
        path_frame, text="Gözat...", command=select_image, width=8
    )
    btn_browse.pack(side="left")

    is_ignored_var = tk.BooleanVar(value=True)
    chk_trash = ttk.Checkbutton(
        dialog,
        text="Başlangıçta Çöp Olarak İşaretle",
        variable=is_ignored_var,
    )
    chk_trash.pack(anchor="w", padx=20, pady=15)

    def save_new_item():
      name = entry_name.get().strip()
      if not name:
        messagebox.showerror("Hata", "Eşya adı boş bırakılamaz!", parent=dialog)
        return

      if name in self.ignore_items:
        messagebox.showwarning(
            "Uyarı", "Bu eşya zaten listede var!", parent=dialog
        )
        return

      selected_path = path_var.get()
      if selected_path and os.path.exists(selected_path):
        ext = os.path.splitext(selected_path)[1]
        safe_name = "".join(
            c
            for c in name
            if c.isalnum() or c in (" ", "_", "-")
        ).strip()
        safe_name = safe_name.replace(" ", "_")
        dest_filename = f"{safe_name}{ext}"
        final_image_path = os.path.join("images", dest_filename)
        try:
          shutil.copy(selected_path, final_image_path)
        except Exception:
          final_image_path = default_img_path
      else:
        final_image_path = default_img_path

      self.ignore_items[name] = {
          "ignored": is_ignored_var.get(),
          "image_path": final_image_path,
      }
      save_bot_data(self.ignore_items)
      self.refresh_ignore_list()
      self.log_message(f"Sistem -> Yeni eşya eklendi: '{name}'")
      dialog.destroy()

    btn_save = ttk.Button(
        dialog, text="Listeye Ekle", command=save_new_item, width=15
    )
    btn_save.pack(pady=5)

  def start_bot(self):
    self.bot_core.start(self.ignore_items)
    self.status_label.config(text="Durum: Çalışıyor...", foreground="green")
    self.btn_start.config(state="disabled")
    self.btn_stop.config(state="normal")

    self.bot_thread = threading.Thread(
        target=self.bot_core.run_loop, daemon=True
    )
    self.bot_thread.start()

  def stop_bot(self):
    self.bot_core.stop()
    self.status_label.config(text="Durum: Durduruldu", foreground="red")
    self.btn_start.config(state="normal")
    self.btn_stop.config(state="disabled")


if __name__ == "__main__":
  root = tk.Tk()
  try:
    import PIL
  except ImportError:
    messagebox.showerror(
        "Eksik Kütüphane",
        "Lütfen terminale 'pip install Pillow' yazarak gerekli"
        " kütüphaneyi yükleyin!",
    )
  app = KnightBotGUI(root)
  root.mainloop()