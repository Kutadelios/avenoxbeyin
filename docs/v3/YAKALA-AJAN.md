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
