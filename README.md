# URL Reminder

Basit bir Flask uygulamasi. Amaç, "sonra bakarim" diye kaydedilen linkleri tarih vererek listelemek ve zamani geldiginde tekrar karsiya cikarmak.

## Mevcut Ozellikler

- Link ekleme
- Hatirlatma tarihi ve saati belirleme
- Linkten baslik, aciklama, domain ve ozet cekme denemesi
- Kategori, etiket ve kisa not ekleme
- Kayitlari `zamani gelen`, `siradaki` ve `tamamlanan` olarak listeleme
- `Okundu`, `24 saat ertele`, `arsivle`, `tekrar ac` aksiyonlari

## Kullanilan Teknolojiler

- Python
- Flask
- SQLite
- Requests
- BeautifulSoup

## Lokal Calistirma

1. Gerekli paketleri kur:

```bash
python -m pip install -r requirements.txt
```

2. Uygulamayi baslat:

```bash
python app.py
```

3. Tarayicida ac:

```text
http://127.0.0.1:5000
```

Not:
`templates/index.html` dosyasini tek basina acmayin. Bu dosya Flask template'i oldugu icin dogrudan tarayicida eksik veya bozuk gorunur.

## VS Code Icin

Repoda hazir debug ayari var:

- `Run and Debug`
- `Run URL Reminder`
- `F5`

## Proje Yapisi

- `app.py`: Flask uygulamasi ve temel is kurallari
- `templates/index.html`: sade arayuz
- `requirements.txt`: Python bagimliliklari
- `docs/foundation.md`: urun ve teknik temel notlari

## Su Anki Durum

Bu repo production hazir degil. Su anda lokal calisan bir MVP iskeleti var. Sonraki mantikli adimlar:

1. Mail hatirlatma altyapisini eklemek
2. Veri modelini migration tabanli hale getirmek
3. Flask prototipinden daha kalici bir yapıya gecmek
