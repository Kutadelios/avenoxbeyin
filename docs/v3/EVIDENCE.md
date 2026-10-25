# Seçilen kanıtın taşınması

`PackedContext.sources` kırpılmamış dar pasajları, `wider` varsa ikinci pasajla
genişletilmiş görünümü taşır. `evidence` aynı kaynakların kimliğini, SHA-256 ve
revizyonunu, geldiği kanalı ve seçilen kaynak aralıklarını taşır. Aralıklar ham
Markdown baytlarına değil indekslenmiş `record.text` karakterlerine göredir.
Her görünüm, kopyalanan kaynak aralığının çıktıdaki yerini de tutar; böylece
son zarfın ortasında kesilen bir pasajın yalnız gösterilen kısmı hatırlanır.
Bu üçü Python nesnesinin attribute'larıdır; zarf JSON'una eklenmez.

Strict arama seçimini değiştirmez. Jev kartı dar ve varsa geniş seçimin her
pasajına yer ayırır; uzun parçada sorguya uyan pencereyi kullanır. Gevşek adayın
ilgili pasajı karttan önce yerelde seçilir, kurtarıldığında aynı seçim paketlenir.
Kartın toplam excerpt sınırı 600 karakterdir; başlık ve aralık işaretleri bu
sınıra dahildir. Tam metne ihtiyaç duyan bir semantik kararı bu görünüm garanti
etmez. Sağlayıcı eşikleri değiştirilmemiştir; yeni görünüm canlı ölçülmelidir.

`render_context` kanıt referanslarını yalnız teslim ettiği kaynaklarla birlikte
döndürür. `remember` bu teslim projeksiyonunu kullanır. Continuity dosyasının
ikinci sürümü yalnız kaynak kimliği/revizyon/hash ve sayısal `[başlangıç, bitiş)`
aralıkları saklar; not metni, bölüm başlığı ve kullanıcı istemi saklamaz.
Kaynak değişince eski aralıklar kullanılmaz. Her devam turunda görünürlük,
güven, proje, supersession, durum, hash ve güncel strict dışlamalar yeniden
denetlenir. Başlık yolu güncel ve hash'i doğrulanmış kaynaktan yeniden üretilir.
Yalnız gösterilen metin korunur; daha büyük devam bütçesi görünmemiş metni açmaz.

Kimlikten ibaret eski (sürüm 1) continuity dosyaları aralık bilinmediği için
kullanılmaz. Bir sonraki somut, başarılı teslim bunları sürüm 2 olarak yeniler.
Yirmi dakikalık süre, oturum/istemci/proje sınırı ve belirsiz devamın süreyi
uzatmaması değişmez. Bozuk veya doğrulanamayan referans yerel sorgu sonucuna
düşer. Pasaj motoru olmadan çalışan not düzeyi fallback de tam doğrulanabilen
metin önekini aralık olarak saklayabilir; pasajın yerini tahmin etmez.

Tekrar süzgeci kalan kaynakların `sources`, `wider` ve `evidence` attribute'larını
korur. Hook, o oturumda daha önce gösterildiği için süzülen kayıtları da kendi
kanıt referanslarıyla continuity'ye aktarır.
