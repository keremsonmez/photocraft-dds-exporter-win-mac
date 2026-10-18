# PhotoCraft DDS Exporter (Windows & macOS) 🚀

> **PhotoCraft için DirectDraw Surface (DDS) Doku Dışa Aktarıcısı, Normal Map ve Mipmap Üreticisi**
> **Windows'ta Resmi NVIDIA CUDA v3.2.5 Donanım Hızlandırması & macOS'ta Çoklu Motor (Apple Silicon & Intel)**

[PhotoCraft](https://github.com/storytold/photocraft) için geliştirilmiş, Adobe Photoshop'taki resmi **NVIDIA Texture Tools** eklentisiyle birebir aynı yeteneklere ve arayüze sahip açık kaynaklı DDS dışa aktarıcısıdır. Hem **Windows** hem de **macOS** işletim sistemlerinde tek bir paket olarak ortak çalışır.

[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS-blue.svg)](#)
[![NVIDIA CUDA](https://img.shields.io/badge/NVIDIA-CUDA%20v3.2.5-76b900.svg)](#)
[![Apple Silicon](https://img.shields.io/badge/Apple%20Silicon-M1%20%2F%20M2%20%2F%20M3%20%2F%20M4-black.svg?logo=apple)](#)
[![Lisans: MIT](https://img.shields.io/badge/Lisans-MIT-yellow.svg)](LICENSE)
[![PhotoCraft](https://img.shields.io/badge/PhotoCraft-v1.x-purple.svg)](#)

[🇺🇸 Click here for English Documentation (README.md)](README.md)

---

## ✨ Özellikler

- ⚡ **Yüksek Performanslı Doku Sıkıştırma Motorları:**
  - **Windows:** Resmi **NVIDIA NVTT 3.2.5 CUDA** çekirdekleri (~0.15 - 0.25 sn sürede 2K/4K sıkıştırma).
  - **macOS:** Yerel çoklu motor mimarisi (macOS için derlenmiş `nvcompress`, `texconv`, AMD `compressonator` veya yerleşik Python DDS motoru).
- 🎨 **Tüm DDS Sıkıştırma Formatları:**
  - **BC7:** En yüksek kalite, modern oyun motorları, tam şeffaflık/alfa desteği.
  - **BC1 / DXT1:** Opak dokular, 1:8 sıkıştırma oranı.
  - **BC1a:** 1-bit keskin alfa (cutout).
  - **BC3 / DXT5:** Yumuşak geçişli alfa kanalları.
  - **BC5:** 2 kanallı (RG) özel Normal Harita formatı.
  - **BC4:** Tek kanal yükseklik / pürüzlülük / grayscale.
  - **BC6H:** HDR / 16-bit float dokular.
  - **RGBA:** 32-bit sıkıştırmasız tam kalite.
- 🧭 **Eksiksiz Yükseklikten Normal Harita (Height-to-Normal Map) Üreticisi:**
  - **7 Yükseklik Kaynağı:** `Alpha Channel`, `Average RGB`, `Max RGB`, `Screen RGB`, `Red`, `Green`, `Blue`
  - **6 Filtreleme Türü:** `4 Sample`, `3x3` (Sobel), `5x5`, `7x7`, `9x9`, `dUdV`
  - **Sorunsuz Doku Tekrarı (Tiling):** Wrap modu (tekrar et veya sınırda kes)
  - **DirectX / OpenGL Çevirme:** `Invert X` ve `Invert Y` (Unreal Engine, GTA V, FiveM, Unity için kritik)
  - **Hassas Kaydırıcılar:** Canlı `Scale` (kabartma şiddeti), `Min Z` kontrolü ve vektör normalizasyonu
- 📐 **Mipmap Filtreleme:** Kaiser, Box, Triangle, Mitchell-Netravali, Min, Max filtreleri ve minimum boyut sınırı.
- 🪄 **Canlı 2D Efektler:** Negatif, Aydınlık, Karanlık, Kontrast Artır/Azalt, Yumuşat (Blur), Keskinleştir, 2D Konvolüsyon.
- 👁️ **Kanal İzolasyonu & Canlı Önizleme:** Koyu temalı tuval üzerinde `RGBA`, `RGB`, `Alpha`, `Red`, `Green`, `Blue` kanallarını anlık inceleme.
- ⌨️ **Kısayol Entegrasyonu:**
  - Doğrudan **`F10`** tuşuna atanır.
  - Aktif tuvali otomatik kopyalayarak dışa aktarıcıyı önceden yüklenmiş halde açar!

---

## 📦 Kurulum (Tek Tıkla)

Kullandığınız işletim sistemine göre aşağıdaki adımları takip edin:

### 🪟 Windows Kurulumu

#### Ön Koşullar
- Windows 10 / 11 (64-bit)
- [Python 3.8+](https://www.python.org/downloads/) (*"Add Python to PATH"* seçeneği işaretli kurulmalıdır).
- [PhotoCraft](https://github.com/storytold/photocraft) kurulu olmalıdır.

#### Kurulum Adımları
1. Klasördeki **`install.bat`** dosyasına çift tıklayın (veya terminalden `python installer/install.py` çalıştırın).
2. Yükleyici otomatik olarak:
   - Gerekli Python kütüphanelerini kurar (`customtkinter`, `pillow`, `numpy`).
   - NVIDIA CUDA ikililerini `%APPDATA%\Photocraft\` dizinine kopyalar.
   - `photocraft-dds://` sistem protokolünü Windows Kayıt Defteri'ne (`HKCU`) kaydeder.
   - `photocraft.exe` dosyasını orijinal yedeğini (`.original`) alarak yamalar.
   - `F10` kısayolunu ayarlar.
3. PhotoCraft'ı açın ve `F10`'a basın!

---

### 🍏 macOS Kurulumu

#### Ön Koşullar
- macOS 10.15 veya üstü (Apple Silicon M1/M2/M3/M4 veya Intel Mac).
- Python 3.8+ yüklü olmalıdır (`python3 --version`).
- [PhotoCraft](https://github.com/storytold/photocraft) uygulaması (`/Applications` veya `~/Applications` altında).

#### Kurulum Adımları
1. Proje klasöründe Terminal açın ve şu komutu girin:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```
   *(Veya: `python3 installer/install_mac.py`)*
2. Yükleyici otomatik olarak:
   - Gerekli Python kütüphanelerini kurar (`customtkinter`, `pillow`, `numpy`).
   - Çalışma dosyalarını `~/Library/Application Support/Photocraft/` altına yerleştirir.
   - `~/Applications/` içinde `PhotoCraft DDS Exporter.app` oluşturur ve `photocraft-dds://` protokolünü macOS LaunchServices'e kaydeder.
   - `PhotoCraft.app` binary dosyasının `.original` yedeğini alır ve yönlendirmeyi yapar.
   - macOS Gatekeeper uyarısı vermemesi için bundle'ı otomatik olarak imzalar (`codesign --force --deep --sign -`).
   - `F10` kısayolunu `preferences.json` içine işler.
3. PhotoCraft'ı açın ve `F10`'a basın!

---

## 🎮 Nasıl Kullanılır?

1. **PhotoCraft**'ı açın ve dokunuz üzerinde çalışın.
2. Klavyenizden **`F10`** tuşuna basın (veya uygulamalardan `PhotoCraft DDS Exporter`ı başlatın).
3. Dışa aktarıcı penceresi, PhotoCraft'taki aktif tuvalinizi otomatik yüklemiş olarak açılır.
4. İstediğiniz **Sıkıştırma Formatını** (ör. BC7, BC1 veya Normal Harita BC5), **Mipmap Filtresini** veya Normal Harita ayarlarını seçin.
5. **`Save as DDS`** butonuna tıklayın ve kayıt konumunu belirleyin.
6. Dosyanız saniyeler içinde sıkıştırılarak kaydedilir!

---

## 🔬 Teknik Mimari (Sıfır Yük & Güvenli)

Rust kodlarını yeniden derlemek yerine modern bir **URL Protokol Köprüsü** kullanılır:

```
[ PhotoCraft Arayüzü (F10 Tuşuna Basıldığında) ]
                         │
                         ▼
             photocraft-dds://export Açılır
                         │
             ┌───────────┴───────────┐
             ▼                       ▼
        [ Windows ]              [ macOS ]
      HKCU Registry         macOS LaunchServices
             │                       │
             ▼                       ▼
  photocraft_dds_launcher   PhotoCraft DDS Exporter.app
    ├── Windows user32        ├── AppleScript System Events
    │   (Ctrl+Shift+C)        │   (Cmd+Shift+C)
    └── ImageGrab             └── Pano / AppleScript yakalama
             │                       │
             └───────────┬───────────┘
                         ▼
             photocraft_dds_exporter.py
                         │
                         ▼
        Doku Sıkıştırma Motoru Seçimi
        ├── Windows: NVIDIA CUDA nvcompress 3.2.5
        └── macOS: nvcompress / texconv / Yerel DDS Motoru
```

- **Geri Döndürülebilir:** İlk çalıştırmada çalıştırılabilir dosyanın `.original` kopyası saklanır.
- **Yönetici / Root İzni İstemez:** Tamamen kullanıcı alanında (`AppData` / `Application Support`) çalışır.
- **Arka Planda CPU Tüketmez:** Sadece kısayola basıldığında çağrılır, arka planda servis veya dinleyici çalıştırmaz.

---

## 🛠️ İsteğe Bağlı: macOS'ta `nvcompress` Derleme

macOS sürümünde varsayılan olarak yerleşik Python DDS motoru tüm popüler formatlarda hazırdır. İsterseniz C++ hızındaki `nvcompress` motorunu Apple Clang ile derleyebilirsiniz:

```bash
chmod +x bin/build_nvcompress_mac.sh
./bin/build_nvcompress_mac.sh
```

---

## 🗑️ Kaldırma (Uninstall)

İşletim sisteminize uygun kaldırma betiğini çalıştırarak PhotoCraft'ı orijinal haline getirebilirsiniz:

### 🪟 Windows
Klasördeki **`uninstall.bat`** dosyasına çift tıklayın (veya `python installer/uninstall.py` çalıştırın).  
Orijinal `photocraft.exe` geri yüklenir, Kayıt Defteri protokolü silinir ve `preferences.json` temizlenir.

### 🍏 macOS
Terminalde çalıştırın:
```bash
chmod +x uninstall.sh
./uninstall.sh
```
*(Veya: `python3 installer/uninstall_mac.py`)*  
Orijinal `PhotoCraft.app` binary dosyasını geri yükler, `codesign` imzasını tazeler, protokolü ve `.app` dosyasını sistemden kaldırır.

---

## 📄 Lisans & Telif Hakları

- **PhotoCraft DDS Exporter:** [MIT Lisansı](LICENSE) ile sunulmaktadır.
- **NVIDIA Texture Tools (NVTT):** Copyright © NVIDIA Corporation.
- **PhotoCraft:** Copyright © Storytold & PhotoCraft katkıcıları.
