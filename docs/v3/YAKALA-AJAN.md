# Yakala ajanı: aşamalı öneri

Bu seri #384'teki isteğe bağlı ajanı ayrı incelenebilir katmanlara ayırır.
Bakımcı özellik issue'sunda kapsamı kabul etmeden upstream'e gönderilmez.
Varsayılan ayar kapalıdır; mevcut Yakala yakalama/işleme yolu korunur.

## Yerel MCP köprüsü

Bu aşama bağımsız test edilen, kapalı altyapıdır. Henüz kullanıcı tarafından
ajan başlatma komutu veya istemci süreci yoktur. `_ajan-mcp` yalnız geçerli
bir çalışan işin süreli yetkisiyle açılır; uydurma iş kimliği yetki vermez.

Dört araç vardır: `read_note`, `search_notes`, `write_note`, `complete`.
Genel kabuk ve doğrudan dosya sistemi aracı yoktur. Ağ araçları bu aşamada
sunulmaz. Okumalar kaynak/çıktı kapsamına, gizlilik etiketlerine ve symlink
kontrollerine tabidir. Yazma yalnız Yakala çıktısında atomik, üzerine yazmayan
yayın akışından geçer. Gizli notları arama üzerinden dolaylı okumak da reddedilir.

Her araç çağrısı öncesinde ve sonrasında işin gerçek süreç kimliği, monotonic
süre sınırı ve tamamlanma durumu doğrulanır. Kalıcı bir PID tek başına yetki
sayılmaz. `complete` çağrısından sonra aynı MCP oturumu da yeni işlem yapamaz.

Bu dosya bir kurulum önerisidir; altyapının test edilmesi bir Windows canlı
ölçümü veya bütün ajan deneyiminin bu aşamada tamamlandığı iddiası değildir.

## Sınırlı ağ araçları

`fetch_source` ve `download` araçları iş oluşturulurken dondurulan kaynak URL'si
ve o kaynaktan doğrulanarak çıkarılan bağlantılarla sınırlıdır. `ag=acik`
yalnız açık kullanıcı tercihiyle başka genel İnternet URL'lerini açar.
Özel/yerel IP'ler, DNS yeniden bağlama, güvensiz yönlendirme ve HTTPS'ten HTTP'ye
düşürme kabul edilmez. Denetim araç listesinin yanında gerçek çağrı/yönlendirme
yollarında da yapılır. Süresi dolan iş ağ çağrısından sonra çıktı yayımlayamaz.

İş başına sekiz ağ çağrısı bütçesi kalıcıdır; köprünün yeniden başlatılması
bütçeyi sıfırlamaz. İndirme 50 MiB ile sınırlıdır, tür/uzantı kontrolünden geçer
ve yalnız staging alanına yazılır. Aynı adlı kullanıcı dosyasının üzerine yazılmaz.
Bu aşama da kullanıcıya ajan çalıştırma arayüzü eklemez.

## Başsız Claude worker

Bu aşamadan itibaren özellik açık CLI tercihiyle kullanılabilir:

```text
python beyin.py yakala ajan claude
python beyin.py yakala ajan-gonder <kart-id> --istek "Kaynağı özetle."
python beyin.py yakala ajan
python beyin.py yakala ajan kapali
```

Kalıcı ayar `state/yakala/ajan/config.json` içindedir; dosya yoksa kapalıdır.
İşler ayrı `jobs/<id>/` dizinlerinde tutulur. Tek worker OS kilidiyle sırayla
işler. Çökme sonrası yarım kalan iş otomatik tekrarlanmaz, onay bekler. Süre
aşımı ve kapatma sahip olunan süreç ağacını durdurur; kalıcı eski PID ile
başka bir sürece sinyal gönderilmez. İşin süreli MCP yetkisi de sona erer.

Claude başsız çalışır; yerleşik kabuk/dosya araçları kapalı, MCP yapılandırması
dar ve kesindir. İstemci sürümü/özellikleri çalıştırmadan önce doğrulanır.
JSON dışındaki son metin veya sıfır çıkış kodu başarı kanıtı sayılmaz. Sonuç
manifesti, çıktı dosyaları ve gerçek oturumla yazılan receipt doğrulandıktan
sonra kart tamamlanır. Sonuç özeti private notta kalır; Last-Session değiştirilmez.

Varsayılan ağ `kisitli`dir. `--ag acik` kullanıcının ayrı tercihidir; genel web
araması için teknik bir içerik sızıntısı önleme garantisi verilmez. Hassas not
okuma kapıları aynı kalır, fakat modele verilen kullanıcı isteğinin veya
yetkili kaynak içeriğinin başka sorgulara taşınmaması ayrıca talimatla belirtilir.
Bu nedenle açık ağ seçiminde kaynak ve isteğin paylaşım uygunluğu değerlendirilmelidir.

Bu aşamada Ctrl+Enter, masaüstü bildirimleri, aylık ajan günlüğü ve görünür
istemci penceresi yoktur. Durum `yakala ajan`, iş dosyaları ve yerel logdan izlenir.
