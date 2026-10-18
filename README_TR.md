# PhotoCraft NVIDIA DDS Exporter (DDS Dışa Aktarıcı) 🚀

> **PhotoCraft için Resmi NVIDIA NVTT 3.2.5 CUDA Donanım Hızlandırmalı, Normal Map ve Mipmap Üreticili DDS Eklentisi**

[PhotoCraft](https://github.com/storytold/photocraft) için geliştirilmiş, Adobe Photoshop'taki resmi **NVIDIA Texture Tools** eklentisiyle birebir aynı yeteneklere ve arayüze sahip açık kaynaklı DDS dışa aktarıcısıdır.

[![Platform](https://img.shields.io/badge/Platform-Windows%20x64-blue.svg)](#)
[![NVIDIA CUDA](https://img.shields.io/badge/NVIDIA-CUDA%20v3.2.5-76b900.svg)](#)
[![Lisans: MIT](https://img.shields.io/badge/Lisans-MIT-yellow.svg)](LICENSE)
[![PhotoCraft](https://img.shields.io/badge/PhotoCraft-v1.x-purple.svg)](#)

---

## ✨ Özellikler

- ⚡ **Resmi NVIDIA CUDA Donanım Hızlandırması:** 2K ve 4K dokuları NVIDIA CUDA çekirdekleri sayesinde saniyenin onda birinde (~0.15 - 0.25 sn) sıkıştırır.
- 🎨 **Tüm DDS Sıkıştırma Formatları:**
  - **BC7:** En yüksek kalite, modern oyun motorları, tam şeffaflık/alfa desteği.
  - **BC1 / DXT1:** Opak dokular, 1:8 sıkıştırma oranı.
  - **BC1a:** 1-bit keskin alfa (cutout).
  - **BC3 / DXT5:** Yumuşak geçişli alfa kanalları.
  - **BC5:** 2 kanallı (RG) özel Normal Harita (Normal Map) formatı.
  - **BC4:** Tek kanal yükseklik/pürüzlülük/grayscale.
  - **BC6H:** HDR / 16-bit float dokular.
  - **RGBA:** 32-bit sıkıştırmasız tam kalite.
- 🧭 **Gelişmiş Normal Map (Normal Haritası) Üreteci:**
  - **7 Yükseklik Kaynağı:** `Alpha Channel`, `Average RGB`, `Max RGB`, `Screen RGB`, `Red`, `Green`, `Blue`
  - **6 Filtre Tipi:** `4 Sample`, `3x3` (Sobel), `5x5`, `7x7`, `9x9`, `dUdV`
  - **Kusursuz Tekrar (Wrap / Tiling):** Doku sınırlarını kusursuz birleştiren wrap modu.
  - **DirectX / OpenGL Çevirme:** `Invert X` ve `Invert Y` (Unreal Engine, GTA V, FiveM, Unity için kritik yeşil kanal çevirme).
  - **Canlı Kaydırıcılar:** Kabartma şiddeti (`Scale`) ve `Min Z` derinlik ayarı.
  - **Vektör Normalizasyonu.**
- 📐 **Mipmap Filtreleme:**
  - Kaiser, Box, Triangle, Mitchell-Netravali, Min, Max filtreleri.
  - Minimum Mipmap boyutu belirleme.
- 🪄 **Canlı Görsel Efektleri:**
  - Negative, Lighter, Darker, Contrast More/Less, Smooth (Blur), Sharpen Soft/Medium, 2D Convolution.
- 👁️ **Kanal İzolasyonu ve Canlı Önizleme:**
  - Karanlık temalı önizleme ekranı.
  - Kanalları tek tek inceleme: `RGBA`, `RGB`, `Alpha`, `Red`, `Green`, `Blue`.
- ⌨️ **PhotoCraft Menü ve Kısayol Entegrasyonu:**
  - Doğrudan **`F10`** tuşuna atanmıştır.
  - Dosya menüsünde: **`File` › `Export` › `NVIDIA DDS…`** şeklinde görünür.
  - Tuvalinizi otomatik olarak kopyalayıp pencereye hazır getirir!

---

## 📦 Tek Tıkla Kolay Kurulum

### Gereksinimler
- Windows 10 veya 11 (64-bit)
- [Python 3.8+](https://www.python.org/downloads/) (Kurulum sırasında *"Add Python to PATH"* kutucuğunu işaretleyin).
- Bilgisayarınızda [PhotoCraft](https://github.com/storytold/photocraft) kurulu olmalıdır.

### Kurulum Adımları
1. Bu depoyu indirin veya klonlayın.
2. Klasördeki **`install.bat`** dosyasına çift tıklayın (veya terminalde `python installer/install.py` çalıştırın).
3. Yükleyici otomatik olarak:
   - Gerekli Python kütüphanelerini (`customtkinter`, `pillow`, `numpy`) yükler.
   - NVIDIA CUDA motorunu ve eklenti dosyalarını `%APPDATA%\Photocraft\` konumuna kopyalar.
   - `photocraft-dds://` sistem protokolünü Windows Kayıt Defteri'ne (Registry) ekler.
   - `photocraft.exe` dosyasını yedekleyerek menü bağlantısını günceller.
   - `F10` kısayolunu `preferences.json` dosyasına ekler.
4. PhotoCraft'ı açın ve kullanmaya başlayın!

---

## 🎮 Nasıl Kullanılır?

1. **PhotoCraft**'ı açın ve tasarımınızı/dokunuzu hazırlayın.
2. Klavyenizden **`F10`** tuşuna basın (veya menüden **`File` › `Export` › `NVIDIA DDS…`** seçin).
3. Exporter penceresi tuvalinizin görüntüsüyle birlikte açılacaktır.
4. **Image Type**, **Format** (örneğin BC7 veya Normal Map için BC5), **Mipmap** seçeneklerinizi belirleyin.
5. **`Save as DDS`** butonuna tıklayın. Açılan standart "Farklı Kaydet" penceresinde nereye kaydedeceğinizi ve dosya adını seçin.
6. CUDA donanım hızlandırmasıyla DDS dosyanız saniyenin onda birinde kaydedilecektir!

---

## 🔬 Teknik Mimari (Neden Güvenli ve Temiz?)

Geleneksel modlamalar uygulamanın kaynak kodunu yeniden derlemeyi (Rust/C++ derleyicileri, onlarca GB Visual Studio araçları) gerektirir. Bu projede **URL Protokol Köprüsü** mimarisi kullanılmıştır:

```
[ PhotoCraft Arayüzü (F10 / File > Export) ]
                      │
                      ▼
   links::COMMANDS tablosu (In-place yönlendirme)
                      │
                      ▼
   ShellExecute("photocraft-dds://export")
                      │
                      ▼
   HKCU\Software\Classes\photocraft-dds
                      │
                      ▼
   photocraft_dds_launcher.pyw
     ├── Tuvali panoya kopyalar (Ctrl+A -> Ctrl+Shift+C -> Ctrl+D)
     └── photocraft_dds_exporter.py uygulamasını önizleme yüklü açar
                      │
                      ▼
   NVIDIA NVTT 3.2.5 CUDA Motoru (nvcompress.exe)
```

- **Geri Alınabilir:** İlk kurulumda otomatik olarak `photocraft.exe.original` yedeği alınır.
- **Yönetici İzni Gerektirmez:** Kullanıcı alanında (`HKCU` ve `%APPDATA%`) çalışır.
- **Arka Planda Yük Oluşturmaz:** Arka planda çalışan dinleyici veya döngü yoktur; yalnızca siz F10'a veya menüye bastığınızda işletim sistemi protokolüyle tetiklenir.

---

## 🗑️ Kaldırma (Uninstall)

Klasördeki **`uninstall.bat`** dosyasına çift tıklayın (veya `python installer/uninstall.py` çalıştırın).  
Orijinal `photocraft.exe` yedeğini anında geri yükler, protokolü ve kısayolları temizler.

---

## 📄 Lisans

- **PhotoCraft NVIDIA DDS Exporter:** [MIT Lisansı](LICENSE) altında açık kaynak olarak sunulmuştur.
- **NVIDIA Texture Tools (NVTT):** Telif Hakkı © NVIDIA Corporation.
- **PhotoCraft:** Telif Hakkı © Storytold ve PhotoCraft katkıda bulunanları.
