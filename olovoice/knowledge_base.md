# Lale Bistro — Bilgi Tabanı

Bu belge, asistanın sabit gerçekler için kullanacağı referans bilgidir.
Değişken/anlık bilgi (belirli bir tarih ve saatte hangi masanın müsait
olduğu) burada **yer almaz** — o her zaman `check_availability` aracıyla
canlı olarak sorgulanır.

## Restoran

- **Ad:** Lale Bistro
- **Not:** Bu, bir teknik değerlendirme (case study) için kurgulanmış
  **demo bir restorandır**; gerçek bir işletme değildir.
- **Saat dilimi:** Europe/Istanbul

## Çalışma Saatleri

- Açık: her gün 12:00 – 23:00
- **Pazartesi günleri kapalı.**
- Son rezervasyon saati: 21:30 (bir rezervasyon masayı 90 dakika işgal
  ettiğinden, 21:30'da başlayan bir rezervasyon 23:00'te biter).

## Rezervasyon Süresi

Her rezervasyon, masayı **90 dakika** boyunca ayırır.

## Parti Büyüklüğü

- Çevrimiçi/telefon asistanı üzerinden alınabilecek **en fazla parti
  büyüklüğü 8 kişidir**.
- 8 kişiden büyük gruplar için asistan rezervasyon oluşturamaz; misafir bir
  insan çalışana yönlendirilmelidir.

## Rezervasyon ve İptal Politikası

- Rezervasyon oluşturmak için ad soyad, telefon numarası, tarih, saat ve
  kişi sayısı yeterlidir; ön ödeme veya kredi kartı istenmez.
- Başarılı bir rezervasyon, "LBL-" ile başlayan 4 karakterli bir onay kodu
  ile teyit edilir (örn. LBL-7K2Q).
- Bir rezervasyonu sorgulamak veya iptal etmek için **onay kodu ve
  rezervasyondaki telefon numarasının aynı anda eşleşmesi** gerekir.
- İptal edilen bir rezervasyon, ilgili masayı o zaman aralığı için tekrar
  müsait hale getirir.
- Rezervasyona gelinemeyecekse mümkün olduğunca önceden iptal edilmesi rica
  edilir.

## Menü

Aşağıdaki liste, sistemdeki menü verisiyle birebir aynı kalemleri (isim,
kategori, fiyat) içerir; asistan bunların dışında bir yemek veya fiyat
söylememelidir. Güncel/tam liste için yine de `search_menu` aracı
kullanılmalıdır.

The machine-readable counterpart of this table (and the vegetarian flags
below) is `menu_facts.json` in this same directory — that file, not this
prose, is what `tests/test_menu_facts.py` checks against the backend seed
data. Keep both in sync by hand when the menu changes.

| Yemek | Kategori | Fiyat (TL) |
|---|---|---|
| Mercimek Çorbası | Çorba | 120 |
| Ezogelin Çorbası | Çorba | 120 |
| Adana Kebap | Ana Yemek | 380 |
| Karışık Izgara | Ana Yemek | 520 |
| Etli Güveç | Ana Yemek | 340 |
| Mevsim Salata | Salata | 160 |
| Baklava | Tatlı | 220 |
| Künefe | Tatlı | 210 |
| Ayran | İçecek | 60 |
| Türk Kahvesi | İçecek | 90 |

## Vejetaryen ve Diyet Bilgisi

- **Vejetaryen seçenekler:** Mercimek Çorbası, Ezogelin Çorbası, Mevsim
  Salata, Baklava, Künefe, Ayran, Türk Kahvesi.
- Vegan, glutensiz veya diğer özel diyet ihtiyaçları için asistan kesin bir
  garanti veremez; misafir masaya geldiğinde personelle teyit etmelidir.

## Alerjen ve Çapraz Bulaşma Uyarısı

Mutfakta gluten, süt ürünleri, fındık/fıstık ve diğer yaygın alerjenler
kullanılmaktadır. Asistan hiçbir yemek için "alerjen içermez" veya
"güvenlidir" şeklinde kesin bir güvence veremez. Ciddi alerjisi olan
misafirler, siparişlerini vermeden önce mutlaka restoran personeliyle
doğrudan konuşmalıdır.

## İletişim ve İnsan Yönlendirmesi

- Asistanın çözemediği durumlarda (8+ kişilik gruplar, tekrarlayan sistem
  hatası, şikayetler, özel organizasyon talepleri) misafir bir insan
  çalışana yönlendirilmelidir.
- Bu, bir demo ortamı olduğundan gerçek bir telefon numarası veya e-posta
  adresi burada listelenmez; canlı ortamda bu bölüm restoranın gerçek
  iletişim bilgileriyle güncellenmelidir.
