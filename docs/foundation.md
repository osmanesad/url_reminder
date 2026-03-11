# URL Reminder Foundation

## 1. Urun Tanimi

URL Reminder, kullanicinin daha sonra donmek istedigi baglantilari kaydettigi; bu baglantilardan metadata, ozet ve gorsel onizleme ureten; sonrasinda bunlari dogru zamanda tekrar gundeme getiren bir urundur.

Temel iddia:
Kaydedilen link yiginini "pasif arsiv" olmaktan cikarip "geri donulen bilgi havuzu" haline getirmek.

## 2. Cekirdek Problem

- Bookmark listeleri zamanla cop kutusuna donuyor.
- Kaydedilen icerigin neden kaydedildigi unutuluyor.
- Kullanici, linke tekrar bakmasi gereken dogru ani kendisi takip etmiyor.

## 3. Hedef Kullanici

- Surekli arastirma yapan bilgi calisanlari
- Icerik toplayan ogrenciler
- Sonra okumak icin cok sayida link biriktiren internet agir kullanicilari

## 4. MVP Siniri

MVP'ye dahil:

- Link ekleme
- Metadata extraction
- Kisa ozet
- Kategori/etiket
- Hatirlatma tarihi
- Bugun hatirlatilacaklar listesi
- Okundu, ertele, yeniden planla

MVP'ye dahil degil:

- Chrome extension
- Mobil uygulama
- Haftalik digest
- Benzer kayit onerisi
- Gelismis AI tabanli otomatik siniflandirma

Bu ayrim kritik; aksi halde urun erken asamada fazla dagilir.

## 5. MVP Kullanici Akisi

1. Kullanici linki ekler.
2. Sistem sayfadan baslik, aciklama, kapak gorseli ve domain bilgisini ceker.
3. Sistem kisa bir ozet uretir.
4. Kullanici isterse kategori, etiket ve "neden kaydettim" notu ekler.
5. Kayit okunacaklar havuzuna duser.
6. Hatirlatma zamani geldiginde in-app veya e-posta bildirimi gider.
7. Kullanici kaydi acar, okundu olarak isaretler, erteler veya yeniden planlar.

## 6. Veri Modeli V1

### `bookmarks`

- `id`
- `user_id`
- `url`
- `title`
- `description`
- `image_url`
- `source_domain`
- `user_note`
- `summary`
- `category_id`
- `status` (`unread`, `read`, `archived`)
- `created_at`
- `updated_at`
- `last_opened_at`

Not:
`is_read` ve `is_archived` yerine tek bir `status` alani daha temizdir.

### `reminder_rules`

- `id`
- `bookmark_id`
- `remind_at`
- `status` (`pending`, `sent`, `snoozed`, `cancelled`)
- `channel` (`email`, `in_app`)
- `snooze_count`
- `last_sent_at`
- `created_at`
- `updated_at`

### `tags`

- `id`
- `user_id`
- `name`
- `color`

### `bookmark_tags`

- `bookmark_id`
- `tag_id`

### `categories`

- `id`
- `user_id`
- `name`
- `icon`

## 7. Teknik Kararlar

### Onerilen stack

- App: Next.js monolith
- Styling: Tailwind
- Database/Auth: Supabase
- File/image cache: Supabase Storage
- Mail: Resend
- Background jobs: cron veya kuyruk tabanli worker

### Neden bu yon

- Tek deploy yuzeyi operasyonu azaltir.
- Supabase, auth + db + migrations tarafini hizlandirir.
- Hatirlatma sistemi icin basit cron ile baslanabilir.
- E-posta teslimati ilk surum icin push'tan daha gercekci.

## 8. Sistem Bilesenleri

### Link ingestion

- URL validation
- Domain extraction
- Metadata extraction (`title`, `description`, `og:image`, favicon)
- Gerekirse readability parser ile ana icerik cekme

### Summarization

- Ilk surumde kisa, tek paragraf ozet yeterli
- Ozet basarisizsa metadata tabanli fallback olmali

### Reminder engine

- `pending` kayitlari tarar
- `remind_at <= now` olanlari toplar
- Kanal bazli gonderir
- Gonderim sonucunu `last_sent_at` ve `status` ile isaretler

## 9. Urun Ilkeleri

- Kullaniciya link eklerken fazla form yuklenmemeli
- Hizli kayit, detayli duzenlemeden daha oncelikli olmali
- Erteleme aksiyonu tek tik olmali
- "Bu hafta tekrar hatirlat" gibi hazir secenekler olmali

## 10. Basari Metrikleri

- Kaydedilen link basina tekrar acilma orani
- Hatirlatma sonrasi tiklama orani
- Haftalik aktif kullanici
- Kayitlarin okunma orani
- Erteleme / arsivleme dengesi

## 11. Riskler

- Bazi siteler metadata veya icerik cekmeyi engelleyebilir
- Ozet kalitesi zayif olabilir
- Fazla bildirim urunu yorucu hale getirebilir
- MVP kapsam kaymasi gelistirmeyi yavaslatir

## 12. Gelistirme Sirasi

1. Veritabani semasi
2. Auth ve temel app iskeleti
3. Link kaydetme formu
4. Metadata extraction servisi
5. Listeleme ve filtreleme
6. Hatirlatma scheduler
7. E-posta gonderimi
8. Ozetleme ve otomatik etiketleme

## 13. Repo Icin Net Sonuc

Bu repo, mevcut haliyle urun yonunu tasimiyor. Dogru sonraki adim:

1. Flask prototipini referans kabul etmek
2. Yeni MVP iskeletini ayri bir uygulama olarak kurmak
3. Veri modelini migration tabanli hale getirmek
4. Hatirlatma sistemini tarayici `alert` mantigindan cikarmak
