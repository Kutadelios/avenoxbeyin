# Yakala: tek tuşla beyne at

Video, tweet, makale, mail, PDF ya da aklına gelen bir cümle: gördüğün yerde tek tuşla yakala,
ajanın sonra okuyup dersleri ikinci beynine bağlasın. İsteğe bağlıdır; kurmazsan hiçbir şey değişmez.

## Kurulum (bir kez)

Vault klasöründe:

```sh
python3 beyin.py yakala kur
```

Windows'ta `py -3 beyin.py yakala kur`. Ya da ajanına "yakala aracını kur" de.

Kurulum şunları yapar:

| | Mac | Windows |
|---|---|---|
| Her uygulamada kısayol | `Control+Option+B` | `Ctrl+Alt+B` |
| Dosya gönderme | Finder'da dosyayı seç, kısayola bas | Sağ tık > Gönder > Beyne At |
| Tarayıcı | Obsidian Web Clipper şablonu | Obsidian Web Clipper şablonu |
| Ajan | `beyin-yakala` skill'i | `beyin-yakala` skill'i |

Kısayol ek paket istemez; Python'un kendisiyle çalışır. Mac'te bir oturum açılış servisi
(LaunchAgent), Windows'ta oturum açılışında başlayan küçük bir dinleyici tuşu dinler.
Yalnız şablon ve skill istiyorsan: `python3 beyin.py yakala kur --kisayol-yok`.

**Mevcut kurulum:** [#299 güvenlik güncellemesini](YAKALA-GUVENLIK-299.md) aldıktan sonra
vault klasöründe `python3 beyin.py yakala kur` komutunu bir kez yeniden çalıştır
(Windows'ta `py -3 beyin.py yakala kur`). Böylece daha önce yazılmış `beyin-yakala` skill'i
yeni güvenilmeyen içerik ve rastgele sınır kurallarını alır. Yalnız şablon/skill kullanıyorsan
`--kisayol-yok` ekle; kullanıcının kendi işaretsiz skill'i korunur.

### Linux

Linux'ta arka planda dinleyen bir servis yok; kısayol masaüstünün kendi kısayol ayarına yazılır.
`kur`, `~/.local/share/applications/beyne-at.desktop` dosyasını yazar (`XDG_DATA_HOME` mutlak bir
yolsa orada). Komut `python3 <state>/yakala/beyin_v3_yakala.py pencere --vault <vault>` olur.
Betiğin bu kopyası state klasöründe durur ve pencereyi açarken vault'taki güncel betiğe geçer;
güncellemeden sonra `kur`'u yeniden çalıştırman gerekmez.

`Ctrl+Alt+B` (ya da `--tus`) masaüstüne göre kaydedilir:

| Masaüstü | Kısayol | Nerede denendi |
|---|---|---|
| KDE Plasma 6 (Wayland) | `kur` kurar | Gerçek masaüstünde: kısayol, bağlantı ve düz metin |
| GNOME | `kur` kurar | Gerçek masaüstünde denenmedi; yalnız birim testleri var |
| KDE Plasma 5 | `kur` dener (`kwriteconfig5`) | Denenmedi |
| Diğerleri (Hyprland, Sway, XFCE...) | Kurulmaz; `kur` bağlanacak komutu verir | Hyprland'de `kur` çıktısı ve `zenity` penceresi denendi |

- **KDE Plasma:** `kwriteconfig6` (yoksa `kwriteconfig5`) ile `kglobalshortcutsrc` içine yazılır,
  `gdbus` ile oturum kapatmadan etkinleştirilir. `kur` sonra tuşun kimde olduğunu kglobalaccel'e
  sorar: çıktıdaki `kisayol_calisiyor` ancak tuş bu kısayola bağlıysa `true` olur; tuş başka bir
  uygulamadaysa ya da soru yanıtsız kalırsa `false`. Sınır: kısayol daha önce başka bir komutla
  kurulduysa (vault taşındı, Python değişti) KDE çalışan oturumda eski komutu çalıştırmayı
  sürdürebilir; oturumu kapatıp açınca yenisi geçerli olur. İlk kurulumda bu sorun yok.
- **GNOME:** `gsettings` ile özel bir kısayol (`custom-keybindings`) eklenir; mevcut kısayolların
  korunur. Burada `kisayol_calisiyor` yalnız ayarın yazıldığını söyler, tuşun başka bir kısayolla
  çakışmadığını söylemez. Tuş çalışmazsa Ayarlar > Klavye altındaki özel kısayollarda `Beyne at`
  girdisine bak ve bir issue aç.
- **Diğer masaüstleri:** `.desktop` dosyası yazılır, kısayol kurulmaz. `kur` çıktısındaki `ipucu`
  bağlanacak komutun tamamını verir; onu masaüstünün kısayol ayarına ekle. KDE ya da GNOME'da kayıt
  doğrulanamazsa da aynı komut `ipucu` olarak verilir.

Linux'ta tuş Ctrl, Alt ya da Super ile birlikte bir harf, rakam, boşluk ya da F1-F12 olabilir.
Kısayol tek bir vault'a hizmet eder: başka bir vault'ta `kur` çalıştırırsan kısayol ona geçer ve
çıktıdaki `onceki_vault` eskisini söyler. `kaldir` yalnız bu vault'un kurduğu `.desktop` dosyasını
ve kısayolu siler. Masaüstü `XDG_CURRENT_DESKTOP` değişkeninden tanınır; `kur` ve `kaldir`'ı
masaüstü oturumundaki bir terminalden çalıştır. SSH gibi bu değişkenin olmadığı bir oturumda
kısayol kurulmaz, kaldırırken de masaüstündeki kısayol ayarı yerinde kalır.

Pencere neyi kaydedeceğini panodan okur: Wayland'da `wl-clipboard` paketi (`wl-paste`) gerekir.
Kurulu değilse kısayol çalışsa bile pano bağlantısı/metni pencereye gelmeyebilir; `yakala kur`,
`yakala durum` ve boş yakalama penceresi bunu belirtir. Paketi dağıtımının paket yöneticisiyle
kurduktan sonra `yakala durum` ile uyarının kaybolduğunu kontrol et; Yakala'yı yeniden kurman gerekmez.
X11'de tam pencere metni kendisi okur; kopyalanan dosyalar ve `kdialog`/`zenity` yolu için `xclip`
ya da `xsel` gerekir. Panoda tek bir bağlantı varsa bağlantı, dosya
yöneticisinden kopyalanan dosyalar (`file://` listesi) varsa dosyalar, başka metin varsa metin
yakalanır. Wayland'da yalnız bir PNG görsel kopyalandıysa tam pencerede küçük önizlemesi görünür;
başlangıçta eklenmez, `Tab` veya karta tıklama ile seçilip PNG dosya kartı olarak kaydedilebilir.
Metin ya da bağlantı varsa öncelik onlardadır. Görsel okunamıyorsa veya `wl-paste` yoksa mevcut
metin akışı değişmez. X11 pano görseli bu sürümde desteklenmez. Pano metninin en fazla 1 MB'ı,
görselin en fazla 64 MB'ı okunur; metin kesilirse kartta belirtilir.
Kopyalanan dosyaların yakalanması gerçek masaüstünde denenmedi, yalnız birim testleri var.

Tam pencere `tkinter` ister. Arch tabanlı dağıtımlarda Python'un `tk` paketi ayrıdır
(`sudo pacman -S tk`), Debian ve Ubuntu'da `sudo apt install python3-tk`. `tkinter` yoksa pencere
yerine `kdialog`, o da yoksa `zenity` ile yalnız "neden" sorulur; iptal edersen kart yazılmaz.
Üçü de yoksa hiçbir şey kaydedilmez ve `kur` bunu uyarı olarak söyler.
Bazı paketli Python/Tk sürümleri yalnız `fixed` yazı tipini görür; Türkçe karakterler ve oklar
pencerede Unicode kaçışları gibi görünebilir. Linux kısayolunun durum-kopyası, kendi Python'unun
Tk fontlarını kontrol eder; uygunsuzsa ve `/usr/bin/python3` kullanılabilir Tk fontlarına sahipse
pencereyi onunla açar. Sistem Tk yoksa dağıtımının paket yöneticisiyle kur; uygun başka Python da
yoksa mevcut yorumlayıcı ve `kdialog`/`zenity` geri dönüşleri korunur. Bu denetim kart içeriğini
başka bir yere göndermez. **Mevcut Yakala kurulumunda motor güncellemesinden sonra** kısayolun
önceden kopyalanmış kodunu yenilemek için vault kökünde `python3 beyin.py yakala kur` çalıştır.
Yalnız `yakala durum` veya `.desktop` dosyasını elle değiştirmek kopyayı yenilemez; KDE etkin
kısayolun eski `Exec` satırını ayrıca bellekte tutabilir. Bu yeniden kurulum eski kartları taşımaz
veya silmez; kayıtlı kısayol ve seçilmiş klasör kullanılır.

Doğrulamak için: `python3 beyin.py yakala durum` (`Kisayol dinleyicisi: calisiyor`), KDE'de
`gdbus call --session -d org.kde.kglobalaccel -o /component/beyne_at_desktop -m org.kde.kglobalaccel.Component.isActive`
(`(true,)` beklenir), sonra kısayola bas.

### Kısayolu değiştir

```sh
python3 beyin.py yakala kisayol 'cmd+"'
```

Tuşu yazdığın gibi tarif et: `cmd`, `ctrl`, `alt` (ya da `option`), `shift` ve en sonda tuş.
Örnekler: `ctrl+alt+b` (varsayılan), `cmd+shift+space`, `alt+f5`, `⌘⇧K`. Mac'te karakter etkin klavye
düzeninden bulunur; Türkçe Q'da `"` 1'in solundaki tuştur. Windows'ta kısayol
yalnız Ctrl/Alt/Shift ile harf, rakam ya da F tuşunu kabul eder. Argümansız `kisayol` mevcut tuşu
gösterir. Seçtiğin tuşu başka bir uygulama zaten kullanıyorsa komut uyarır; başka bir tuş dene.

Mac'te dinleyici arka planda çalışır, Dock'ta görünmez; kapanırsa sistem onu yeniden başlatır.
Dinleyici `kur`'un yazdığı bir kopyadan çalışır: bir güncellemeden sonra onu da yenilemek için
`python3 beyin.py yakala kur` komutunu yeniden çalıştır (tuşun korunur). Çalışıp çalışmadığını
`python3 beyin.py yakala durum` söyler.

### Tarayıcı: Obsidian Web Clipper

1. [Obsidian Web Clipper](https://obsidian.md/clipper) eklentisini kur (Chrome, Firefox, Safari, Edge, Arc, Brave).
2. Eklentinin ayarlarında **Şablonlar > İçe aktar** ile kurulumun kart klasörüne yazdığı
   `beyne-at-web-clipper.json` dosyasını seç (varsayılan `📥 000-Inbox/Yakala/`; tam yolu `kur` söyler).
3. Bir sayfada eklentiye bas, "Beyne at" şablonunu seç, istersen **Neden** bölümüne bir satır yaz, ekle.

Web Clipper sayfayı tarayıcının içinden okur; giriş isteyen sayfalar (Gmail, ücretli makale) da böylece yakalanır.

### Windows: kısayol dinleyicisi

Windows'ta kısayol, tarayıcının (Chrome/Edge/Brave/Vivaldi) adres çubuğunu okur. Adres çubuğu
odaktaysa (yazılıp Enter'a basılmamış taslak) veya değer iki okumada değişiyorsa URL sayılmaz.
Chromium şemayı gizlediği için şemasız adrese `https://` eklenir. Kısayol anında fare bir linkin
(ör. YouTube ana sayfasındaki bir video kartı) üstündeyse o link varsayılan kaynak olur; açık
sayfa **Alt+S**, imlecin altındaki link **Alt+I** ile seçilir. Okuma sırasında pencere veya sekme
değişirse (başlık değişir) iki link de atılır. Link yoksa kaynak pencerenin görüntüsü sunulur
(önce Windows.Graphics.Capture, olmazsa PrintWindow). Görüntü kapalı gelir; **Alt+W** veya satıra
tıklama ile eklenir, çünkü `isle` görseli ajana olduğu gibi okutur. History/oturum veritabanı okunmaz;
localhost/özel IP için mevcut ağ güvenliği sınırı korunur.

**Gönderiler (X, Instagram):** Tweet metni veya akıştaki video bir link değildir. Açık sayfa
X (`x.com`, `twitter.com`) ya da Instagram ise ve imleç bir linkin üstünde değilse, altındaki en
içteki ARIA `article` öğesi (tek gönderi) alınır ve içindeki ilk gönderi bağlantısı
(`x.com/<kullanıcı>/status/<id>`, `instagram.com/p|reel/<kod>/`) imleç linki olur. Başka sitelerde
bu yol çalışmaz: bir haber sayfasının gövdesi de tek bir `article` olabilir ve metnin andığı tweet,
imlecin üstünde durduğu gönderi değildir; orada kaynak açık sayfa kalır. Sayfa adresi
okunamazsa da bu yol kapalıdır. Aynı gönderideki ikinci, farklı gönderi bağlantısı alıntılanan
gönderidir; **Alt+A** ile seçilebilir, varsayılan seçili değildir. X'in fotoğraf/video/analytics
alt sayfaları gönderi adresine indirgenir; Instagram ses sayfası (`/reels/audio/<id>/`) gönderi
sayılmaz. Bağlantı sayfanın kendisinden okunur; gönderi adresi görselden veya kullanıcı adından
üretilmez.

**Opera (Opera Air dahil):** Süreç adı `opera` olan pencerede adres çubuğu okunmaz; sayfanın ayrı
Chromium alt penceresi okunur. Sayfa URL'si MSAA Document nesnesinin gerçek değerinden, imleç
bağlantısı aynı alt pencerenin UI Automation bağlantılarından alınır. Adres çubuğundaki taslak
okunmaz; açık sayfanın yüklenmiş adresi kullanılır. Eklenti, yeniden başlatma veya
erişilebilirlik başlatma bayrağı gerekmez. Tek görünür renderer, pencere/süreç sahipliği ve
okuma öncesi/sonrası sayfa URL'si doğrulanır. Birden fazla görünür renderer, görünmeyen belge,
değişen sayfa veya zaman aşımı varsa URL verilmez. Bağlantı iki okumada değişirse yalnız imleç
bağlantısı atılır. Sayfa ve imleç okuması tek bir yardımcı süreçte, 1 saniyelik bütçe içinde
yapılır.
Opera Air 136.0.6008.70 üzerinde bayraksız ayrı profilde temel sağlayıcı yolu ölçüldü;
oturum açılmış YouTube/Instagram akışlarında kullanıcı kabul testi ayrıca yapılmalıdır.

Tarayıcıdan okunan link (imlecin altındaki ya da açık sayfa) varsa varsayılan odur; pano içeriği
yalnız seçenek olarak, işaretsiz sunulur. Link yoksa dinleyicinin başlangıcından itibaren gözlenen,
başarılı kayıtta kullanılmamış pano revision'ı önceliklidir. İlk kullanım/yeniden başlatmada eldeki panonun yaşı bilinmez: içerik kapalı
seçenek olarak kalır. Snipping Tool dosya zamanı tek başına otomatik tazelik sağlamaz.
İptal ve yalnız sayfayı kaydetmek panoyu tüketmez. Pano değişimi yakalama tuşundan sonra
olduysa yeni içerik kendiliğinden kaynak seçilmez. Metin/görüntü aynı pano oturumundan
kopyalanır; gecikmeli veya tutarsız okuma güvenli biçimde atlanır.

Seçim yolları: **Alt+I** imlecin altındaki bağlantı, **Alt+S** etkin sayfa, **Alt+A** alıntılanan
gönderi, **Alt+P** pano bağlantısı, **Alt+M** metin, **Alt+G** pano görüntüsü, **Alt+W** pencere
görüntüsü.
Alternatifler birbirini silmez. Bir URL seçimi diğer URL'yi kapatır. Pano metni/dosya eklenen
mevcut URL kartı da `private` olur. Aynı popup'ın kayıt kimliği tekrar oynatılsa bile ikinci
commit yapılmaz.

Aynı sayfanın ikinci yakalaması yeni kart açmaz, mevcut karta eklenir. Sayfa kimliği her
sistemde aynı kuralla hesaplanır (senkronlanan bir vault'u Mac ve Windows birlikte okuyabilir):
aynı YouTube videosu (`youtu.be`, `watch?v=`, `shorts/`, `live/`, `embed/`, `music.youtube.com`)
ve aynı X/Twitter gönderisi tek kartta toplanır; alan adı tam eşleşir (`notyoutube.com` YouTube
sayılmaz). Diğer sayfalarda şema, `www.`/`m.` öneki, sondaki `/` ve bölüm işareti (`#baslik`)
fark yaratmaz; varsayılan dışı port (`:8443`) ve yönlendirme işaretleri (`#/sayfa`, `#!sayfa`)
ayrı sayfa sayılır.

**Tek aktif popup:** tekrar kısayol yeni pencere açmaz, mevcut metni ve kaynak seçimini
koruyarak açık popup'a odak isteği gönderir. Dinleyici ile warm pencere, instance/schema/
sürüm/HWND doğrulamalı READY → foreground izni → ACTIVATE konuşur. İkinci çağrı FOCUS'tur.
Eski protokol sessizce kabul edilmez; bu güncellemeden sonra `py -3 beyin.py yakala kur`
ile dinleyici kopyasını yenilemek gerekir. IPC pipe'ları hotkey thread'ini bloke etmez.
Dinleyici kapanışı önce STOP gönderir; yanıt vermeyen pencere ve okuyucuları sahip olunan
Job Object üzerinden sonlandırılır. Başka bir vault'a ait state silinmez.

Popup kaynak monitörde açılır. Windows tarafında Tk yönetilen pencere kullanır; özel
palet/canvas görünümü korunmak üzere yerel başlık/çerçeve stili kaldırılır. **Esc** yerel
odakta hemen iptal eder. Kaynaklar okunurken ve popup açık olduğu sürece, odak nerede olursa
olsun, düşük seviyeli bir klavye kancası (`WH_KEYBOARD_LL`) yalın Esc'i izler: popup öndeyse
Esc'i Tk işler; kaynak pencere öndeyse (odak reddedildi ya da sayfaya tıklandı) Esc tüketilir ve
popup kapanır; başka bir pencere öndeyse popup kapanır ve Esc o pencereye de iletilir. Kanca
popup kapanınca (kayıt, Esc, Kapat, Alt+F4, hata) kaldırılır; sonrasında hiçbir uygulamanın
Esc'i tutulmaz. Yeniden hotkey kancayı yeni kaynak pencereyle yeniden kurar, eski yakalama
içeriğini değiştirmez. Ctrl, Shift, Alt veya Win ile basılan Esc kancadan geçirilir; kanca bu
kombinasyonla popup'ı kapatmaz. Sol ve sağ değiştiricilerin basma/bırakma olayları ayrı izlenir;
Alt bağlam bayrağı da değerlendirilir. Kanca kurulurken zaten basılı tuşlar, callback dışında
bir kez `GetAsyncKeyState` yüksek bitiyle alınır; callback içinde bu API çağrılmaz.
`AttachThreadInput` kullanılmaz. Ctrl+Shift+Esc, Ctrl+Esc ve Alt+Esc için yerel Windows kabul
testi gerekir; bellek içi kanca testi işletim sisteminin kısayolu gerçekten açtığını kanıtlamaz.
Görünür **Kapat** ve Alt+F4 da iptaldir. Windows güvenli masaüstü/UIPI/hook reddi için
her durumda global Esc garantisi yoktur. Kartın disk commit'i başladıysa Esc kaydedilmiş
veriyi geriye dönük iptal etmez; yavaş disk I/O'su sırasında arayüz yanıtı gecikebilir.

URL doğrulanmışsa ek ekran görüntüsü işi yapılmaz. Diğer durumda **WGC → PrintWindow →
görüntü yok** sırası izlenir; her backend ayrı, sonlandırılabilir süreçtedir. Önizleme yöntem
adını gösterir. Ekran DC'sinden BitBlt yoktur. Kaynak pencere değişirse sonuç atılır.
WGC, Windows 10 1903+ API yoludur; destek/izin/sürücü başarısızsa PrintWindow denenir.
Korumalı/GPU/exclusive-fullscreen uygulamaların tamamı için başarı veya HDR renk doğruluğu
iddia edilmez. Herhangi bir başarısızlık eski panoyu otomatik kaynak yapmaz.

UIA/pano için dış bekleme 1 saniye, WGC için 2,5 saniye, PrintWindow için 1,2 saniyedir;
süreç başlatma/sonlandırma ek giderleri olabilir. PNG/DIB en fazla **16.777.216 piksel**,
görüntü payload'ı 64 MiB, metin UTF-8 payload'ı 4 MiB, IPC metadata'sı 64 KiB kabul eder.
Büyük ilan edilmiş PNG boyutu Tk'ye verilmez. Kart/ham geçici yazım hataları temizlenir;
hard kill/güç kesintisi veya dosya sisteminin silmeyi reddetmesi için mutlak silinme
sözü verilmez. Dinleyici normal/zorunlu popup kapanışında kendi TEMP ağacını da temizler.

`kur`, Başlangıç klasörüne (`shell:startup`) `Beyne At Dinleyici` kısayolu yazar ve dinleyiciyi
başlatır. Bir oturumda tek dinleyici vardır; başka vault'ta `kur` tuşu o vault'a devreder.
`py -3 beyin.py yakala durum` durumunu, state içindeki `yakala/dinleyici.log` hatayı gösterir.
Vault taşınmışsa eski yola yeniden yazılmaz; yeni konumda tekrar kurulum yapılır. Kısayol
geçici dosyada oluşturulup doğrulandıktan sonra değiştirilir; stop zaman aşımı başarı sayılmaz.

ABI kaynakları, sınırlamalar ve gerçek masaüstü kabul komutları:
[Windows yakalama ABI ve test rehberi](WINDOWS-CAPTURE-ABI.md).

## Kullanım

1. **Yakala.** Kısayola bas. Pencere neyin kaydedileceğini gösterir: tarayıcıdaki sayfa
   (Mac'te Chrome, Arc, Brave, Edge, Safari), Finder'da seçili dosya ya da panodaki metin.
   İstersen tek satır "neden" yaz, Enter. Esc vazgeçer.

   Windows'ta panoda görüntü varsa pencere onu küçük önizlemesiyle gösterir. Son başarılı kayıttan
   sonra panoya kopyalanan görüntü (ör. `Win+Shift+S`) eklenmeye hazır gelir: Enter onu kartların
   yanındaki `dosyalar/` klasörüne PNG olarak kaydeder ve Gönder > Beyne At ile aynı dosya kartını
   açar. Tazelik saatle değil pano sıra numarasıyla ölçülür; iptal (Esc) panoyu tüketmez.
   Tazeliği doğrulanamayan görüntü kapalıdır; **Alt+G** veya satıra tıklama ile değiştirilebilir.
   Pano metni/bağlantısı ve pencere görüntüsü yukarıdaki Windows seçim kurallarını izler.
2. **İşlet.** Ajanına "yakalananları işle" de. Oturum başında bekleyen kaynak sayısı da görünür.

Her yakalama kart klasöründe (varsayılan `📥 000-Inbox/Yakala/`) bir kart olur. Aynı videoyu ya da
sayfayı ikinci kez yakalarsan yeni kart açılmaz; yeni notun aynı karta eklenir.

### Kartların klasörü

Gelen kutusu klasörlerinden yalnız birinde `Yakala/` zaten varsa kartlar oraya yazılır; böyle tek
bir klasör yoksa başlangıç klasörü `📥 000-Inbox` kullanılır, o da yoksa vault'un en üstünde adı gelen
kutusu olan tek klasör (`000-Inbox`, `00_INBOX`, `Gelen Kutusu`). Karar verilemiyorsa tahmin edilmez
ve başlangıç yolu açılır. Nokta ile başlayan klasörler, sembolik bağlar, arşiv ve kasa türü adlar
gelen kutusu sayılmaz.

Başka bir yer istiyorsan kurarken söyle:

```sh
python3 beyin.py yakala kur --klasor "Notlar/Yakala"
```

- Klasör vault'un içinde olmalı. Dışarı çıkan bir yol reddedilir ve hiçbir şey yazılmaz.
- Web Clipper şablonu, skill, oturum bildirimi ve `durum` aynı klasörü gösterir. Klasörü
  değiştirdiysen şablonu Web Clipper'a yeniden aktar.
- Eski klasördeki kartlar taşınmaz. `kur` kaç kartın geride kaldığını söyler; işlenmelerini
  istiyorsan onları yeni klasöre sen taşı.
- Seçim bu makinenin durum klasöründe saklanır. Aynı vault'u başka bir makinede de kullanıyorsan
  orada da aynı komutu çalıştır.
- Kayıtlı klasör silinir ya da adı değişirse yukarıdaki kurala dönülür; `durum` kullanılan klasörü söyler.

## İsteğe bağlı: kaydet ve ajana ver

**Varsayılan kapalıdır.** Açtığında **Enter** yine yalnız kartı kaydeder. **Ctrl+Enter** veya
penceredeki **Kaydet ve ajana ver** satırı, önce kartı kaydeder, sonra bu kart için ayrı bir
Claude Code ya da Codex oturumu başlatır. Ajan vault içinde çalışır; sonucu kaynak bağlantılarıyla
hafızaya kaydeder. Pencere kapanabilir, başka bir ajan oturumunda çalışmaya devam edebilirsin.

Bu yol tam Tk penceresinde vardır. Linux'taki `kdialog`/`zenity` yedek pencereleri yalnız
yakalama yapar; kaydedilmiş kartı aşağıdaki `ajan-gonder` komutuyla gönderebilirsin.

### Aç, kullan, kapat

Vault klasöründe, Windows için:

```sh
py -3 beyin.py yakala kur --ajan claude
py -3 beyin.py yakala ajan
```

Otomatik seçim için `kur --ajan otomatik` veya `ajan otomatik` kullan. Önce kurulumu yapan
Claude Code ya da Codex oturumu, oturum işareti yoksa kurulu tek CLI seçilir. İkisi de kuruluysa
terminalde `1) claude / 2) codex` sorulur; JSON çıktıda veya etkileşimsiz kullanımda açıkça
`claude` ya da `codex` seçmen gerekir. Hiçbiri bulunamazsa hata verilir. Ayara somut istemci
yazılır; çıktının `secim` alanı `kurulum-ajani`, `tek-kurulu` veya `kullanici` yolunu gösterir.
Kurulumu yapan ajan, başka bir istemci istemediysen `--ajan otomatik` kullanır.
`--ajan` verilmezse varsayılan kapalı davranışı değişmez.

Codex seçmek için `--ajan codex` kullan. Yakala zaten kuruluysa `py -3 beyin.py yakala ajan claude`
veya `py -3 beyin.py yakala ajan codex` yeterlidir. Mac/Linux'ta `py -3` yerine `python3` yaz.
Bu Windows sürümüne ilk geçişte `kur` komutunu yeniden çalıştır: state'teki dinleyici kopyası da
ajan işinin popup'tan ayrılmasını sağlayan yeni süreç ayarını almalıdır.

**Görünüm: gizli ya da pencere.** Windows'ta Claude ve Codex için ajanın nasıl çalışacağını seçebilirsin:

- `gizli` (varsayılan): iş arka planda başsız bir oturumda çalışır, bitince bildirim gelir.
- `pencere`: Ctrl+Enter ekranda seçili istemcinin Claude Code veya Codex penceresini açar; ajanın ne yaptığını canlı
  izlersin, gerekirse aynı pencerede yazarak yön verirsin. Araç sınırı gizli çalışmayla aynıdır
  (genel kabuk kapalıdır; Codex'in dosya okuma profili ve ağ ayarı aşağıda). İş, ajan `complete` çağırınca
  teslim edilir; receipt ve kart güncellemesi yine çalışan tarafından doğrulanarak yapılır, pencere
  açık kalır ve konuşma sürdürülebilir. Pencereyi sonuç bırakmadan kapatırsan iş `onay-bekliyor`
  olur. Tur ve bütçe sınırları yalnız gizli çalışmada uygulanır; zaman sınırı ikisinde de
  geçerlidir. Pencere bir yalıtım değildir: aynı konsolda kullanıcının kendi istemci
  denetimleri (Claude'da ör. `!` ile komut) açıktır ve iş bittikten sonra pencere bir sonraki işle aynı anda
  açık kalabilir.

**Ağ: kısıtlı ya da açık.** Ajan aynı bağlamda hem güvenilmeyen kaynağı hem özel notlarını
okur; bir kaynağa gizlenmiş talimat, okunan not metnini bir URL'ye ya da arama sorgusuna
koydurmaya çalışabilir.

- `kisitli` (varsayılan): genel web araması kapalıdır. `fetch_source` ve `download` yalnız
  yakalanan ana adresi, açıkça seçilen ek adresleri ve izinli bir sayfadan çalışanın kendi ayrıştırdığı bağlantıları açar; modelin
  ürettiği yeni adresler reddedilir. Bağlantı seçimi ve zamanlama gibi yan kanallar kalır; bu tam
  bir veri sızıntısı koruması değildir.
- `acik`: Claude'un web araması (Codex'te hosted arama) ve herkese açık her adres kullanılabilir.
  Araştırma gerektiren işler (ör. bir videodaki müziği bulmak) için gerekir; özel notlar ile web
  aynı çıkış kanalını paylaşır. Bu kipte ajana ayrıca talimat verilir: arama ve indirme yalnız
  herkese açık bilgi içindir; notlardan, kişisel bilgilerden veya özel ya da kullanıcının kendi
  yüklediği içerikten hiçbir metin arama sorgusuna, adrese ya da dosya adına konmaz, bunu
  gerektiren iş kullanıcının izni için `onay-bekliyor` olur. Bu bir model talimatıdır, teknik bir
  engel değildir.

Çoklu kaynak kartındaki `ek_urller`, kuyruğa gönderilirken mevcut kart ve kuyruk kilitleri
altında doğrulanıp işin `extra_urls` listesine sabitlenir. Kart gövdesindeki bağlantılar,
modelin ürettiği URL'ler ve sonradan yapılan kart değişiklikleri bu işe yeni yetki vermez;
aynı teslimin tekrarı ilk listeyi korur. Eski işlerde alan yoksa yalnız ana kaynak kullanılır.
Ek liste en fazla 63 adres, adres başına 8192 karakter ve JSON olarak 64 KiB olabilir.
İstek, ayarlar ve kaynakların birlikte yazılacak ilk iş kaydı 96 KiB ile sınırlıdır;
128 KiB okuyucu sınırında sonraki çalışma/sonuç alanlarına yer bırakılır. Sınır aşılırsa
kart ajan durumuna geçirilmeden hata verilir; kartın kendisi korunur.

İki ağ kipinde de `fetch_source` ve `download` iş başına toplam **8 çağrı** paylaşır. Başarısız
izinli denemeler de bu bütçeden düşer. Sayaç dış isteğe çıkmadan önce diske kaydedilir;
köprüye yeniden bağlanmak veya aynı işi yeniden yüklemek bütçeyi sıfırlamaz. İzin verilmeyen
adres, ağa çıkmadan reddedilir. Sayaç bozuksa veya yazılamazsa ağ çağrısı yapılmaz. İş başına
izinli adres listesi en fazla 64 adrestir. Bu sınır MCP çağrısınadır; HTTP yönlendirmeleri,
istemcinin hosted web araması ve model hizmetinin normal trafiği için paket sayacı değildir.
Çağrı sırası, adres seçimi ve zamanlama yan kanalları devam eder. Bütçe bittiğinde mevcut
notları okumak, sonuç yazmak ve `complete` ile somut engeli bildirmek mümkündür.

```sh
py -3 beyin.py yakala ajan claude --ag acik
```

**Last-Session.** Çalışan, sonuç kartını companion düzeninde başlığın altına ekler. Okuma ile
yazma arasında dosya değişirse kart eklenmez; sonuç ve receipt korunur. Bu kontrol ile atomik
değiştirme arasındaki çok kısa aralıkta kilide katılmayan bir editörün yazısı kaybolabilir;
taşınabilir bir karşılaştır-ve-değiştir yolu olmadığından bu risk bilerek kabul edilmiştir.

```sh
py -3 beyin.py yakala kur --ajan claude --ajan-gorunum pencere
py -3 beyin.py yakala ajan codex --gorunum pencere
py -3 beyin.py yakala ajan claude --gorunum gizli
```

`kur --ajan claude`, `kur --ajan codex` veya `kur --ajan otomatik` bir terminalde `--ajan-gorunum` olmadan
çalıştırılırsa hangisini istediğini sorar. Kurulumu bir ajana yaptırıyorsan ajan bu seçimi sana sormalıdır.

1. Kısayola bas, kaynağı seç ve **Neden** alanına yapılacak işi yaz. Özellik açıkken altta
   `Ctrl+Enter · Kaydet ve ajana ver (claude)` veya `(codex)` görünür. Kapalıyken bu satır
   görünmez; Ctrl+Enter bir ajan işi başlatmaz ve yanlışlıkla düz Enter kaydına dönüşmez.
2. **Ctrl+Enter**'a bas. Boş istek gönderilmez; pencere `Ajana vereceğin isteği yaz` der.
   Başarılı kayıt ve kuyruğa ekleme sonrasında `Kaydedildi · Ajan sırasında` görünür, pencere kapanır.
   Kuyruk doluysa veya bağımsız süreç açılamazsa kart korunur, pencerede kayıt ile ajan hatası
   ayrı belirtilir. Aynı URL'nin yeni isteği, karta daha önce eklenmiş eski isteklerle karıştırılmaz.
3. İş gerçekten başladığında **Beyin ajanı başladı** bildirimi gelir. Kuyrukta bekleme, modelin
   çalışmaya başladığı anlamına gelmez. Bir makinedeki bu vault kuyruğu aynı anda **bir iş** çalıştırır.
4. Doğrulanmış sonuç, receipt ve Last-Session kaydı tamamlanınca **Beyin ajanı bitirdi** görünür.
   Bir engel varsa **Beyin ajanı onay bekliyor**, çalışma hatasında **Beyin ajanı tamamlayamadı**
   görünür. Kartın `ajan_notu` alanı ve günlük nedenini söyler.

Yeni işleri kapatmak için:

```sh
py -3 beyin.py yakala ajan kapali
```

Çalışan iş ayarı yeniden okuduğunda durdurulur; oluşmuş dosyalar geri alınmaz. Bekleyen işler
yeniden uyandırıldığında otomatik çalıştırılmaz. Kapalıyken yakalama ve düz Enter çalışmayı sürdürür.
İstemciyi değiştirmek daha önce kuyruğa alınmış işlerin kayıtlı istemcisini veya sınırlarını değiştirmez.
Yeni seçilen istemci için eski `extra_args` ve `executable` sıfırlanır; aynı komutta verilen
`--ayar` değerleri bundan sonra uygulanır. Böylece Claude'un `--model haiku`, `--effort` veya
özel binary yolu Codex'e taşınmaz. Aynı istemcinin diğer ayarlarını değiştirmek bu seçenekleri
korur. `kapali` durumundan yeniden açarken eski seçeneklerin hangi istemciye ait olduğu
bilinmediğinden model/binary varsayılanına dönülür; isteniyorsa yeniden açıkça belirtilir.

Kaydedilmiş tek bir kart için açık bir istek de verebilirsin:

```sh
py -3 beyin.py yakala ajan-gonder KART_ID --istek "Bu kaynağı incele, üç önemli bulguyu kaynaklarıyla not et"
py -3 beyin.py yakala ajan-devam
py -3 beyin.py yakala ajan-serbest KART_ID
```

`ajan-devam` kalıcı kuyruğu uyandırır; kesilmiş bir işi tekrar çalıştırma izni vermez.
`ajan-serbest`, incelediğin `hata` veya `onay-bekliyor` kartını `bekliyor` yaparak normal
`isle`/`bitti` akışına bırakır. Çalışan kartı serbest bırakamazsın. Bu komut yeni bir ajan işi
başlatmaz ve geniş araç izni vermez. Yeniden otomatik deneme istersen önce kısmi sonuçları incele,
sonra `ajan-gonder` ile yeni, açık bir istek ver.

### Kart, oturum ve hafıza

| Kartın `durum` değeri | Anlamı |
|---|---|
| `bekliyor` | Normal yakalama; ajan işi verilmedi veya kullanıcı normal işleme bıraktı |
| `ajanda` | Bu karta ait iş sırada ya da çalışıyor; `ajan_asama` ayrıntıyı verir |
| `islendi` | Sonuç ve hafıza kapanışı doğrulandı |
| `hata` | Çalışma tamamlanamadı; kart ve mevcut sonuçlar korunur |
| `onay-bekliyor` | İzin, kurulum, belirsiz kesilme veya hafıza doğrulaması insan incelemesi gerektiriyor |

Normal bekleyen listesi `ajanda` kartlarını tekrar işleme almaz. `isle` ve `bitti` bu kartı
başka oturumdan kapatmaz; oturum bildirimi ayrılmış ve onay bekleyen kartları ayrıca bildirir.
Aynı kartın yakalanması yeni notu korur; devam eden iş ikinci kez başlatılmaz.

Karttaki `ajan_isi` iş UUID'sidir; `ajan_oturum` istemcinin oturum UUID'sidir. Claude için UUID
başlamadan üretilir ve `--session-id` ile verilir; başarı için CLI çıktısında aynı gerçek oturumun
görülmesi gerekir. Başlamamış bir Claude işinde ayrılmış UUID'nin yazması, oturumun oluştuğunu
kanıtlamaz. Codex UUID'si gizli kipte ilk `thread.started` olayının `thread_id` alanından alınır;
pencere kipinde `CODEX_HOME/sessions` (varsayılan `~/.codex/sessions`) altındaki yeni oturumların
yalnız ilk satır meta verisi okunur. Başlangıç zamanı ve vault yolu eşleşen tek bir oturum
bulunmalıdır. Kimlik bulunamazsa veya birden fazla aday varsa sonuç korunur, iş `onay-bekliyor`
olur; hafıza kapanışı yapılmaz. Aynı vault'ta eşzamanlı açılan Codex oturumları bu eşleştirmeyi
belirsizleştirebilir. İş UUID'si Codex oturumu yerine kullanılmaz.
[belge: aşağıdaki CLI ve başsız çalışma kaynakları]

Vault klasöründeki terminalden aynı oturumu açmak için:

```sh
claude --resume OTURUM_UUID
codex resume OTURUM_UUID
```

Sonuç notları kart klasörünün `Ajan/<iş-UUID>/` altına yeni dosyalar olarak yazılır. Kart, sonuç,
kaynak ve varsa indirilen dosyanın yolu birlikte kaydedilir. `ajan_sonuc` ile `ajan_receipt`
kapanış kayıtlarını gösterir. Last-Session'a bunların bağlantıları eklenir. Sonraki oturumda
"o indirdiğin müzik" gibi bir isteği bu kaynak kayıtları üzerinden bulmak mümkündür; bunun için
normal vault hafıza kurallarının ve hook'larının kurulmuş olması gerekir.

**Receipt entegrasyonu, varsayım:** Bu modül `beyin.py receipt` uygulamasını içermez. Adaptör,
yerel `receipt --help` çıktısında `--file` ve `--harness` desteğini arar; oturum kimliği dosyadaki `session` alanıyla gider; `--json`
ile makinece okunur yanıt bekler. Dosya girdisinin `event_id`, `summary`, `refs`, `session`
alanlarını kabul etmesi; yanıtın aynı `event_id`, başarı durumu ve vault içindeki gerçek `source`
yolunu vermesi beklenen entegrasyon sözleşmesidir. Kod yalnız `status: succeeded` kabul eder;
başka bir değer, bilinmeyen durum veya boş durum başarılı kapanış sayılmaz.
Kaynak dosyası geri okunarak olay kimliği
kontrol edilir. Bu JSON şemasının ve yerel başarı durumunun upstream runtime ile kabul testinde
eşleşmesi gerekir; yardım çıktısı tek başına veri şemasını kanıtlamaz. Sözleşme, receipt veya
Last-Session doğrulanamazsa indirilmiş dosya ve notlar korunur, kart tamamlandı sayılmaz.

### Gelişmiş JSON ayarı

Ayarlar makinedeki `<state>/yakala/ajan/config.json` içinde saklanır. Vault'a ve kullanıcıya ait
CLI oturumuna bağlıdır; başka makinede kendiliğinden etkinleşmez. Ayar dosyasında değiştirmek
istediğin alanları ver, ardından istemciyi açıkça seç:

```json
{
  "timeout_seconds": 600,
  "max_queue": 8,
  "max_budget_usd": 1.0,
  "extra_args": ["--model", "sonnet"]
}
```

```sh
py -3 beyin.py yakala ajan claude --ayar yakala-ajan.json
```

| Alan | Varsayılan ve sınır |
|---|---|
| `client` | `kapali`; CLI üzerinden `claude`, `codex` veya `kapali` seçilir |
| `timeout_seconds` | 900 saniye; 30 ile 3600 arası. CLI çalışma süresidir; hazırlık ve hafıza kapanışı ayrıca sürebilir |
| `max_queue` | 32; çalışan dahil 1 ile 32 arası aktif iş. Eşzamanlı çalışma sınırı sabit 1'dir |
| `max_budget_usd` | 1.0; 0.05 ile 20 arası. Claude'un tahmini harcama sınırıdır; Codex'e uygulanmaz, kesin fatura tavanı değildir |
| `extra_args` | `[]`; yalnız `--model DEĞER` ve Claude için `--effort DEĞER`, her biri en fazla bir kez |
| `executable` | `null`; PATH'ten bulunur. Özelleştirilecekse tek bir mutlak executable veya tanınan npm shim yolu |
| `downloads_dir` | İlk kurulumda işletim sisteminin İndirilenler klasörü, bulunamazsa `~/Downloads`; mutlak yerel klasör |
| `last_session_path` | `null`; yalnız vault'un ilk düzeyindeki companion kimliği bulunur. Belirsizse mevcut notun vault-göreli yolunu ver |
| `schema`, `vault` | Modülün sürüm ve vault sahipliği alanları; başka vault'a taşımak için değiştirme |

JSON en fazla 16 KiB olabilir; bilinmeyen anahtarlar, serbest komut şablonları ve izin bayrakları
reddedilir. Windows'ta `\` karakterini JSON içinde `\\` yaz. CLI kullanıcı notunu UTF-8 stdin'den
alır; istek en fazla 16.000 karakterdir. Kullanıcı metni kabuk komutuna gömülmez. Npm `.cmd`/`.bat`
dosyası çalıştırılmaz; yalnız bilinen Claude/Codex paket girişleri doğrudan Node ile açılır.
Tanımsız shim için komut yorumlayıcıya geri düşülmez.

Otomatik Last-Session bulma vault'un alt ağacını taramaz. İlk düzeyde en fazla 2048 girdi
incelenir; gizli, arşiv veya bağlı klasörler aday değildir. Companion/Echo adlı klasörler,
`Core.md` veya `Soul.md` içeren kimlik klasörlerinden önce gelir. Birden fazla kimlik,
bulunamayan mevcut not veya tarama sınırı açık ayar ister; derindeki rastgele bir
`Last-Session.md` seçilmez. Gerekirse `last_session_path` ile mevcut güvenli not belirtilir.

### Ajan neleri yapabilir?

Bu oturum normal vault klasöründe, mevcut istemci ayarlarıyla açılır. Claude'da `--bare`,
`--safe-mode` ve `--no-session-persistence` kullanılmaz; hafıza yüklemesini veya oturum saklamayı
kapatan bilinen ortam ayarları sessizce aşılmaz. Codex'in proje/hook güveni önceden normal bir
oturumda verilmiş olmalıdır. Yeni bir giriş, UAC veya onay penceresi açılması bu akışın parçası değildir.

Görevin yerel okuma ve yazma işlemleri için aynı Python modülü stdin/stdout üzerinden altı
yeteneği sunar; genel komut çalıştırma ve serbest yazma yetkisi açılmaz:

| Araç | Yetki |
|---|---|
| `read_note` | Sınırlar içinde mevcut Markdown/metin notunu ve bu kartın bağlı metnini okur |
| `search_notes` | Görünür notlarda sınırlı arama yapar; en fazla 30 sonuç verir |
| `fetch_source` | Herkese açık HTTP(S) kaynağından sınırlı metin okur; `kisitli` ağda yalnız yakalanan adres ve izinli sayfanın bağlantıları; `download` ile toplam 8 çağrı |
| `download` | Doğrudan medya/metin/PDF dosyasını en fazla 50 MiB olarak hazırlar; `fetch_source` ile toplam 8 çağrı; manifestteki ek 10 dosya tavanı korunur; adres kuralı `fetch_source` ile aynı |
| `write_note` | Yalnız bu işin klasöründe en fazla 30 yeni sonuç notu oluşturur; mevcut notu değiştirmez |
| `complete` | Doğrulanacak sonuç bildirir; kartı, receipt'i ve Last-Session'ı güvenilen çalışan günceller |

İndirme için dosya türü ve hash denetlenir; çalıştırılabilir dosya türleri verilmez. Başarılı
dosya, İndirilenler'e iş kimliği eklenmiş yeni adla yazılır; var olan kullanıcı dosyasının üzerine
yazılmaz. Önce `.part` dosyası oluşturulur; tamamlanan kopya SHA-256 ile doğrulanıp aynı dosya
sisteminde son adına yayımlanır. Önce hard link denenir; desteklenmiyorsa Linux'ta
`renameat2(RENAME_NOREPLACE)`, macOS'ta `renamex_np(RENAME_EXCL)`, Windows'ta mevcut hedefi
reddeden `os.rename` kullanılır. Sonuç notu ve tamamlama dosyaları da aynı yardımcıdan geçer.
Var olan hedefin üzerine yazılmaz, son ad altında yarım kopya oluşturulmaz. Dosya sistemi hem
hard link hem özel yeniden adlandırmayı reddederse, disk dolarsa veya hedef çakışırsa indirme
`.part` dosyası korunur ve kart inceleme bekler. Her ağ dosya sistemi için destek garantisi
yoktur. Birden fazla dosyada önceki
başarılar kaybolmaz: her yayın niyeti ve tamamlanan dosya ayrı kaydedilir, kısmi sonuç da
receipt ve Last-Session kapanışına dahil edilir.
Bridge gizli/hassas yolları, sembolik bağları ve Windows junction'larını reddeder.
Ajan kendisine verilen karti adi ne olursa olsun okur; diger hassas notlara erisim degismez.
`remote_allowed: false`, hassas `sensitivity` veya engellenmiş `kaynak_guveni` metadata'sı olan
notları okumaz. `visibility: private` notlar hook bağlamına girmediği gibi bu işe de açılmaz;
yalnız işin kendi kartı, ham metni, ekleri ve kendi sonuç notları okunur.
`Dosyalar` adı tek başına engelleme nedeni değildir. Güncel yakalama klasörünün ve kart ya da
Yakala'nın `*` içeren `.gitignore` iziyle tanınan eski yakalama klasörlerinin ek depoları
korunur; ilgisiz `knowledge/Dosyalar` notları diğer notlarla aynı politikadan geçer. Kartları
taşınmış eski bir ek deposu, bu iz duruyorsa aramaya açılmaz. Kart/ham metin/izinli eklerin
`read_note` cevabı `source_trust: untrusted` taşır; sıradan hafıza notları `vault-data` kalır.
Bu mahremiyet kontrolü canonical JSON frontmatter ve düz skaler YAML alanlarını okur;
tekrarlanan anahtar, bozuk/kapanmamış metadata veya desteklenmeyen biçim sessizce atlanmaz.

Claude profili `dontAsk`, `--permission-prompts none`, sınırlı built-in araçlar ve yalnız bu
MCP yapılandırmasıyla çalışır; `--permission-prompts` için en az 2.1.259 gerekir. Codex için
desteklenen en eski kararlı sürüm **0.155.1**'dir. Codex profili `-a never`, `--strict-config`
ve `-c agents.enabled=false` kullanır. Linux/macOS'ta her çalıştırmaya rastgele adlı bir
izin profili verilir. Tek dosya sistemi girdisi `":root"="deny"` olduğu için yerel
araçlara okuma/yazma kökü verilmez. Bu profil `-c default_permissions=...` ile seçilir;
POSIX'te `-s read-only` eklenmez: eski seçici adlı profili devre dışı bırakır.
**Windows'ta `-s read-only` uyumluluk yolu kullanılır; içerik tahmini kanalı açık kalır.**
Windows `elevated` sandbox kök okuma izni istediği için root-deny başlangıcı durdurmuştur;
Windows komutuna named profile eklenmez. Kullanıcının sandbox türü/config'i değiştirilmez.
Gizli çalışmada `--ignore-rules` da kullanılır. Ön kontrol önce bayraksız
`codex features list` düz tablosunu okur; bu komuta `--json` verilmez. Ardından işin kapatma
bayraklarıyla etkin durumları doğrular. Eksik, kaldırılmış, yinelenen veya ayrıştırılamayan
gerekli özellik; eski/ön sürüm; başarısız ya da aşırı büyük envanter çıktısı işi durdurur.

Her iş için şu 14 özellik kapatılır: `shell_tool`, `unified_exec`, `view_image`, `apps`,
`multi_agent`, `multi_agent_v2`, `plugins`, `remote_plugin`, `computer_use`, `browser_use`,
`browser_use_external`, `in_app_browser`, `image_generation`, `goals`. Her iki alt ajan kapısı
ve `agents.enabled=false` birlikte gereklidir; model metadatasından V2 seçimi de engellenir.
Ölçülen 0.155.1, `--disable unified_exec` verilse de bu özelliği `true` gösterir. Yalnız
`shell_tool=false` doğrulanmışsa bu durum kabul edilir: resmî kaynakta kabuk araçlarının
tamamı bu ana kapının arkasındadır. Diğer gerekli etkin özellikler için böyle bir istisna yoktur.

Mevcut MCP sunucuları adlarıyla yalnız o işte kapatılır ve sonuç yeniden denetlenir; kullanıcının
config dosyası değiştirilmez. Eklenti/app kapıları da iş bazında kapanır. Envanter veya etkin
durum doğrulanamazsa iş durur; etkin MCP'si bulunan her makine topluca reddedilmez.
Codex'in MCP araçlarını çağıran kod modu korunur. Genel kabuk veya yerel dosya sistemi aracı
olarak açılmaz. Web araması yalnız `ag: acik` iken
açıktır (Claude `WebSearch`, Codex `web_search="live"`). `bypassPermissions` ve tam dosya sistemi yazma izni verilmez. [belge: CLI, config ve izin kaynakları]

Önceki dalın bakımcı ölçümü (18.10.2026; Claude Code 2.1.302, Codex 0.160.0, macOS): `kisitli` ağda Claude oturumunun araç listesi
yalnız altı `mcp__yakala__*` aracıdır, `acik` ağda buna `WebSearch` eklenir; Bash ve dosya araçları
yoktur. `kisitli` ağda model URL'ye not metni ekleyince köprü adresi reddetti. Bu kayıt güncel
dalın Windows üzerinde ölçümü değildir. [#384 bakımcı yorumu](https://github.com/avenoxai/avenoxbeyin/pull/384#issuecomment-6243678257)

Önceki `read-only` profilinin ölçümü (19.10.2026 Türkiye saati; 18.10.2026 23:12-23:14 UTC): resmî Linux Codex 0.155.1,
boş/geçici `CODEX_HOME`, zararsız test dosyaları ve yerel sahte Responses API kullanıldı.
Gerçek hesaba/model hizmetine istek gönderilmedi. Zorlanan `view_image`, `exec_command` ve
`spawn_agent` çağrıları desteklenmeyen araç olarak reddedildi. Vault içinde/dışında mevcut
dosyayı değiştirme ve yeni dosya oluşturma olmak üzere dört `apply_patch` yazması reddedildi;
test dosyaları değişmedi. Etkin `local_mcp` bulunan ayrı ön kontrol onu iş için kapattı,
config dosyasının hash'i aynı kaldı. Bu deneme gerçek modelin altı MCP aracıyla bir işi
bitirdiğini veya Windows sandbox davranışını ölçmez.

**Codex `apply_patch`, #384 bulgu 2 için yeni düzeltme (19.10.2026 UTC):** Araç yüzeyinde
`apply_patch` kalabilir; `apply_patch_freeform` 0.155.1 ve güncel kararlı 0.163.0'da
kaldırılmıştır ve güvenlik anahtarı değildir. Eski `read-only` profili 0.163.0'da da doğru
ve yanlış satır tahminine farklı hatalar verdi. Bu dal Linux/macOS'ta resmî belgelerdeki
**adlı dosya sistemi izin profilini** kullanır. `":root"="deny"`, yama doğrulamasının
dosya okumasına da uygulanır. Kullanıcının aynı ad altındaki daha dar izinleri birleşerek
yeniden açılmasın diye her komut için yeni 128 bit rastgele profil adı üretilir; config
dosyası düzenlenmez. `:minimal`, vault, geçici dizin veya Python köküne ek okuma izni verilmez.

Resmî **Linux 0.155.1, 0.160.0 ve 0.163.0** ikilileriyle, her sürümde iki testin her birinde
28 zorlanmış `apply_patch` çağrısı sınandı: göreli/mutlak, vault içi/dışı yollar; Update/Move için doğru
ve yanlış bağlam; Delete; mevcut/yeni dosyaya Add. Doğru/yanlış çiftleri aynı okuma hatasıyla
reddedildi, içerik açığa çıkmadı ve mevcut dosya hash'leri değişmedi. Her sürümde ayrıca gerçek
Yakala MCP köprüsü izinli notu ve `AGENTS.md`'yi okudu, private notu reddetti, sonuç notunu
yazdı ve `complete` teslimini kabul etti. Normal hash güveni verilmiş sentetik `SessionStart`
hook'u ilk isteğe hafıza bağlamı ekledi. Yerel sahte Responses API kullanıldı; gerçek hesap
ve model hizmeti kullanılmadı. Bu, `complete` teslim kanıtıdır; canlı masaüstünde receipt,
Last-Session ve bildirimin tamamlandığı ölçümü değildir. Testler mevcut kullanıcı
config'inde `workspace-write` ile ayrıca seçilmiş config profilinde `read-only` bulunan
durumları kapsar; yeni izin seçiminin bu legacy ayarlar altında da etkinliği ölçüldü.

İzin profilleri resmî belgede **beta** durumundadır. `--strict-config`, bilinmeyen üst düzey
ayarların sessizce yok sayılmasını önler; gelecekteki bütün davranış değişikliklerini
saptayan bir güvenlik kanıtı değildir. En yeni görülen ön sürüm **0.164.0-alpha.3** yalnız
kaynakta incelendi; mevcut kararlı sürüm kapısı bunu kabul etmez. Linux'ta bu tahmin kanalı
kapatıldı; macOS native sonucu henüz ölçülmedi. **Windows bulgu 2 kısmen açıktır:**
kullanıcı 19.10.2026'da gerçek Windows 11 / Codex 0.155.1 üzerinde `dc2a1bc2` root-deny
profilinin `AGENTS.md` başlangıcını durdurduğunu, eski `69ac79c` salt okuma yolunun iki
görünümde de tamamlandığını bildirdi. Bu dal Windows'a salt okuma seçicisini geri getirir;
yazma ve diğer araç kısıtları korunur, `apply_patch` tahmin doğrulaması kapanmış sayılmaz.
Düzeltilmiş dalın native Windows başlangıcı ve receipt/Last-Session zinciri henüz
ölçülmedi. POSIX root-deny native testleri Windows'ta gerekçeli olarak atlanır; bu atlama
Windows başarısı değildir. Kaynak, seçenek değerlendirmesi ve tekrar komutları:
[Codex dosya okuma sınırı incelemesi](CODEX-APPLY-PATCH.md).

**Güven sınırı:** Normal vault hook'ları, istemci ve `beyin.py receipt` güvenilen yerel koddur;
onların kendi davranışları bu araç köprüsü tarafından sandbox içine alınmaz. Ajanın kullandığı
model hizmeti, CLI'nin normal veri akışındaki isteği ve okunan notları görebilir. Public GET ve web
araması varken URL/sorgu üzerinden veri aktarımını ya da uzak sunucunun GET'e yan etki bağlamasını
evrensel olarak önleyen bir garanti yoktur. Dosya adı/metadata filtresi sıradan bir nota yazılmış
her sırrı bulamaz. İşletim sistemi kısıtları ve araç listesi, modelin bütün niyetini denetleyen
bir güvenlik sistemi olarak sunulmaz. [çıkarım]

Kullanıcının **Neden** alanı yapılacak iştir; JSON zarfında veri olarak taşınması bu isteği
yok saymaz. Bu alan sistem kurallarını değiştirme yetkisi vermez. Kaynak URL'si, sayfa, pano ve
alıntıdaki talimatlar güvenilmeyen içeriktir. İstek serbest kabuk, silme, ödeme, kimlik bilgisi,
mesaj gönderme veya sistem değişikliği gerektiriyorsa ajan `onay-bekliyor` sonucu bırakmalıdır;
metin içindeki "izni aş" ifadesi yeni bir yetki oluşturmaz.

**Instagram örneğinin sınırı:** Herkese açık sayfada müzik bilgisi ve doğrulanmış doğrudan dosya
bağlantısı varsa araştırma ve indirme yapılabilir. Bu sürüm Instagram oturumunu/çerezlerini
kullanmaz, ses dinleyerek müzik tanımaz, DRM aşmaz ve serbest `yt-dlp`/`ffmpeg` çalıştırmaz.
Giriş, ses tanıma veya dönüştürme gerekiyorsa kart somut engelle onay bekler. Beş dakikada her
reel'in müziğini indirme sözü verilmez; yanlış müziği veya HTML sayfasını MP3 adıyla kaydetmek
başarı sayılmaz. Normal `isle` bölümündeki isteğe bağlı araçlar bu kısıtlı profile otomatik açılmaz.

### Bildirim, kesilme ve kaldırma

Windows'ta özellik açılırken Başlat menüsüne `Beyin Yakala Ajan.lnk` ve
`AvenoxBeyin.Yakala.Agent` bildirim kimliği kaydedilir. Toast bu kimlikle gönderilir; kısayolun
sahipliği doğrulanamıyorsa başka bir kısayolun üzerine yazılmaz.
Windows'ta bildirime tıklayınca sonuç notu varsayılan uygulamayla açılır; başlangıç, onay ve hata
bildirimleri kartı açar. Sonuç yolu kaydedilmemişse tamamlanma bildirimi de kartı açar.
Mac'te `osascript display notification`, Linux'ta varsa `notify-send` kullanılır.
Sabit bildirim metninde kullanıcı isteği, URL veya not
başlığı yoktur. İşletim sistemi bildirim ayarı, odak modu veya eksik araç bildirimi gizleyebilir;
bildirim başarısızlığı kartın sonucunu değiştirmez, yalnız günlüğe yazılır. [belge: bildirim kaynakları]

Windows çalışanı popup Job Object'inden `CREATE_BREAKAWAY_FROM_JOB | CREATE_NO_WINDOW` ile
ayrılır; izin verilmezse gizlice daha geniş bir süreç yoluna geçilmez. Ajanın kendi süreç ağacı
ayrı sonlandırılabilir Job Object'inde tutulur. Mac/Linux'ta bağımsız bir gözetmen süreç kendi
oturum ve süreç grubunu açar; CLI bu grupta çalışır. Yalnız worker'ın yazma ucunu tuttuğu
pipe kapanınca, CLI çıkınca veya monoton zaman bütçesi dolunca gözetmen kendi grubunu
sonlandırır. Worker SIGKILL ile ölse de bu sınır worker'ın finally bloğuna bağlı değildir.
Kalıcı kayıttan alınan eski PID'ye sinyal gönderilmez. CLI bütçesi ön kontrol/hazırlık bittikten
sonra başlar; CLI'yi başlatmadan tükenmiş bütçe kabul edilmez. Popup veya dinleyicinin kapanması
normal işi iptal etmez; timeout veya `ajan kapali` çalışan işi sonlandırır.
Bu masaüstü özelliği yeni bir ağ sunucusu ya da sürekli çalışan bulut görevi kurmaz.

İş ve köprü yetkisi yalnız PID sayısına değil süreç oluşturulma kimliğine bağlıdır: Linux'ta
boot kimliği ve `/proc` başlangıç sayacı, macOS'ta `proc_pidinfo` başlangıç zamanı, Windows'ta
aynı handle üzerinden canlılık ve `GetProcessTimes` kullanılır. Her MCP isteğinde, araç
kilidi alındıktan sonra ve veri döndürmeden önce worker kimliği/zaman sınırı doğrulanır.
`complete` yalnız teslim alınan anlık sonucu `submitted` diye onaylar; başarılı kapanışı
çalışan yapar. Worker'ı ölen görünür Windows konsolu açık kalabilir, ancak eski işin köprü
araçları kapalıdır. Eski şemalı, yeniden kullanılmış veya sorgulanamayan PID içeren kesilmiş
işler yeniden çalıştırılmaz; belirsiz iş incelemeye alınır ve sıradaki işe geçilir.

Tanı için `<state>/yakala/ajan/<kart-id>.log` ve `ajan` durumunu kullan. İş dosyaları
`<state>/yakala/ajan/jobs/<iş-UUID>/` altındadır. Günlüklerde istek, kaynak ve araç çıktıları
bulunabilir; bunları herkese açık issue'ya kontrol etmeden ekleme. Ağ/giriş/limit hatasında kart
korunur. Süreç veya bilgisayar beklenmedik şekilde kapanırsa kısmi etkiler bilinmeyebilir;
`ajan-devam` aynı işi kendiliğinden tekrar etmez, inceleme gerektirir.

Yakala işlerinin kendi yazıları kilitlenir; normal başka bir ajan veya editör aynı kilidi
kullanmıyorsa Last-Session'ı sonradan bütünüyle değiştirip eklenen satırı kaybedebilir. Bağımsız
sonuç notu ve receipt bağlantısı bu nedenle korunur. Ortak vault'u iki makinede açmak tek bir
dağıtık kuyruk veya bütün ajanlar arasında ortak dosya kilidi sağlamaz.

POSIX kart kilidi artık vault köküne `.beyin-yakala-card.lock` yazmaz; kullanıcının yerel
state alanındaki ortak kilit dizinindedir. Kilit mevcut vault'un dosya sistemi kimliğine
bağlanır; aynı dizine ait yol takma adları ve farklı özel state seçimleri tek kilitte buluşur.
Ajan kapalıyken normal yakalama da bu kilidi kullanır. Windows named mutex yolu korunur.
Güncellemede bütün eski Yakala dinleyici/worker süreçlerini kapatıp `yakala kur` ile yenile;
eski ve yeni kilit düzenini kullanan sürümleri aynı vault'ta birlikte çalıştırma.

`yakala kaldir`, ajan ayarını önce `kapali` yapar ve mevcut Yakala kısayol/skill kaldırmasını
uygular. Kartlar, ajan sonuçları, receipt'ler, indirilmiş dosyalar ve tanı kayıtları silinmez.
Bu sürüm yeni `Beyin Yakala Ajan.lnk` toast kısayolunu ve kayıt işaretini de korur; istersen
Başlat menüsündeki bu adlı kısayolu ayrıca kaldırabilirsin. Kaldırma, önceden yapılmış dosya
etkilerini geri alma işlemi değildir. Bu bölümdeki ağ davranışı yalnız açıkça gönderilen ajan
işleri içindir; aşağıdaki normal yakalama akışı kart yazarken ağa çıkmaz.

### Windows kabul testi

Birim testleri gerçek model hizmeti çalıştırmaz. POSIX yaşam döngüsü testleri gerçek geçici
Python süreçleri açıp sonlandırır; Windows/macOS API modelleri yerel ölçüm yerine geçmez.
Depo kökünde bütün Yakala paketini çalıştır:

```sh
py -3 -m unittest discover -s tests -p "v3_yakala*_test.py"
```

Windows 11 üzerinde aşağıdakileri ayrıca dene. Her kayda tarih, Windows/Python/CLI sürümü,
istemci, `gizli`/`pencere`, `kisitli`/`acik`, dosya sistemi ve beklenen/gerçek sonucu ekle.
Gerçek kullanıcı sırları yerine ayırt edilebilir zararsız test notları kullan.

1. `kur --ajan kapali` ile düz Enter'ın eski kaydı yaptığını ve Ctrl+Enter satırının görünmediğini doğrula.
2. Normal terminalde seçilen CLI'ye giriş yap, vault/hook güvenini ve `beyin.py receipt --help`
   sözleşmesini kontrol et; `kur --ajan claude` veya `codex` çalıştır.
3. Zararsız bir not araştırmasını Ctrl+Enter ile gönder. Popup'ı ve dinleyiciyi kapat; konsol
   penceresi açılmadan işin ilerlediğini, karttaki gerçek oturum kimliğini ve bildirimi doğrula.
4. Bilinen herkese açık küçük bir dosyayı indir. Yeni hedef adı, hash, sonuç notu, receipt ve
   Last-Session bağlantısı birlikte doğrulandıktan sonra `islendi` olmasını kontrol et.
5. Silme/giriş isteyen bir iş, özel IP URL'si, eksik CLI, ağ hatası ve kısa timeout dene.
   Kartların korunduğunu, gerekçenin yazıldığını ve başarı bildirimi verilmediğini doğrula.
6. Art arda iki istek gönder; tek CLI çalıştığını kontrol et. Aynı kartta normal `isle`/`bitti`
   çağrılarını, kesilme sonrası `ajan-devam` davranışını ve açık `ajan-serbest` devrini dene.
7. Bildirimleri kapatıp işi tekrarla; sonuç ve günlük oluşmalıdır. Yeni normal oturumdan önceki
   kartı ve indirme yolunu bulmayı, son olarak `ajan kapali` ve `kaldir` davranışını doğrula.
8. Claude ve Codex'i hem `gizli` hem `pencere` kipinde çalıştır. Codex 0.155.1 ve kullanılacak
   yeni sürümde `codex --version`, bayraksız `codex features list` ve işin kapatma bayraklı
   tablosunu kaydet. `view_image`/kabuk/alt ajan çağrılarının reddini, `kisitli` kipte web
   aramasının yokluğunu doğrula. Kod moduyla Yakala MCP çağrısı ve gerçek oturum UUID'si
   eşleşmelidir. Claude pencere argv'sindeki `--` ve `--tools ""` davranışını ayrıca gözle.
9. Önceden etkin MCP ve eklenti bulunan geçici CLI profilinde işi çalıştır; başka sunucunun
   aracı açılmamalı, kullanıcı config hash'i değişmemeli. Claude `--model haiku` ve özel
   executable seçildikten sonra Codex'e geç; yeni iş varsayılan Codex seçeneğiyle başlamalı.
10. Windows Codex salt okuma uyumluluk yolunu hem gizli hem pencere kipinde doğrula:
    `AGENTS.md` ve normal hafıza başlangıcı, izinli MCP okuması, private reddi, sonuç,
    receipt ve Last-Session zinciri çalışmalı. Sandbox türünü ve CLI sürümünü kaydet.
    Zararsız notlarla vault içinde/dışında Update/Move/Delete ve mevcut/yeni Add yazmaları
    reddedilmeli; hiçbir mevcut dosyanın hash'i değişmemeli. Doğru/yanlış bağlam hataları
    farklı olabilir: Windows `-s read-only` yolunu kapalı içerik tahmin sınırı olarak sunma.
11. İzinli `fetch_source`/`download` çağrılarını karışık ve başarısız denemelerle toplam 8'e
    getir. Dokuzuncu çağrı ağdan önce reddedilmeli. Aynı işe yeni MCP bağlantısı açmak hakkı
    yenilememeli; `complete` yine çalışmalı. `acik` araç açıklaması yeni public URL'yi
    yasakladığını söylememeli; hosted web araması bu sayaçta değildir.
12. Gizli işin yalnız worker sürecini beklenmedik biçimde kapat; CLI/alt süreç Job Object
    kapanışıyla sonlanmalı. Görünür konsol açık kalsa da ölen worker'ın MCP'si not
    döndürmemeli. Kısa timeout, `ajan kapali`, `ajan-devam` ve `ajan-serbest` sonuçlarını
    incele. PID nesli uyuşmazlığı ve AccessDenied regresyonlarını otomatik testte çalıştır;
    rastgele sistem sürecini sonlandırarak PID yeniden kullanımını üretmeye çalışma.
13. NTFS, gerçek exFAT/FAT USB ve kullanılacak ağ paylaşımında yeni not ve indirme yayımla.
    Var olan hedefin hash'i değişmemeli; yarışta tek yayın kazanmalı; yazma ortasında hata
    son ad altında yarım dosya bırakmamalı. Hem hard link hem exclusive rename desteklenmiyorsa
    açık hata ve korunmuş `.part` beklenir. Junction/symlink reddi devam etmelidir.
14. İlgisiz `knowledge/Dosyalar` notu okunmalı; başka kartın ekleri, eski kartları taşınmış
    ek deposu, private/hassas notlar açılmamalı. Kendi kart/ham metin/bağlı metin ekinin
    güven etiketi `untrusted` olmalı. Büyük/küçük harf yol takma adlarını da dene.
15. Ajan kapalı normal yakalama vault köküne yeni kilit yazmamalı. Farklı `--state` seçimleri
    aynı kartı eşzamanlı güncellerken kayıt kaybolmamalı. Derin arşivdeki Last-Session'lar
    otomatik seçimi etkilememeli; birden fazla ilk düzey companion açık ayar istemeli.

**Linux/macOS için ayrı Codex okuma sınırı ölçümü:**
[isteğe bağlı gerçek CLI regresyonunu](CODEX-APPLY-PATCH.md) çalıştır. Root-deny altında
göreli/mutlak, vault içi/dışı Update/Move/Delete ve Add denemelerinde dosyalar korunmalı;
aynı yol/işlemde doğru ve yanlış bağlam aynı içeriksiz hataya dönmeli. Aynı oturumdaki
normal hook ve izinli MCP teslimi de geçmeli. Başlangıç/politika hatasını başarı sayma;
bu POSIX profilini salt okuma seçicisi veya ek okuma köküyle otomatik genişletme. Linux
ölçümü macOS native ölçümü değildir; platform, CLI ve gerçek sonucu ayrı kaydet.

**Esc ve Opera One/GX, #383 için ek masaüstü ölçümü:**

- Kaynak pencere, popup ve başka pencere öndeyken yalın Esc davranışını dene. Ctrl+Shift+Esc,
  Ctrl+Esc, Alt+Esc, Shift+Esc ve Win+Esc kancadan geçmeli. Değiştiriciyi popup açılmadan
  önce basılı tutmayı, sol/sağ Ctrl birlikteyken yalnız birini bırakmayı ve sonrasında yalın
  Esc'i dene. Windows'un ayırdığı kısayolun gerçekten çalıştığını ekran üzerinden kaydet.
- Opera Air, One ve GX için tam sürüm/build ve profil/eklenti durumunu kaydet. Normal
  makale, X tek gönderi, giriş yapılmış ağır X akışı ve Instagram'da adres/metin/bağlantı
  seçimini ölç. `abc2h` gibi kullanıcı adı ile `2h` zaman etiketinin başlığı bozmadığını dene.
- Her senaryoda en az 20 tekrar için okuma süresini ms, doğru URL oranını, URL'siz dönüşü ve
  bir saniyelik bütçe aşımını kaydet; medyan, p95 ve en büyük süreyi raporla. Bunlar ölçüm
  hedefidir, bu dal için yapılmış performans ölçümü değildir.
- İki görünür renderer, yabancı renderer, iki okuma arasında belge/foreground değişimi ve
  yoğun UIA ağacında belirsiz sonuç URL'siz kalmalı. Main/base ile aynı koşulları karşılaştır;
  omnibox kaldırılmasının One/GX üzerindeki etkisini doğru URL ve süreyle birlikte ölç.
  Belirsizliği gizlemek için eski omnibox yolunu kendiliğinden açma.

### Teknik kaynaklar

İlk CLI/bildirim bağlantılarının erişim tarihi **17.10.2026**; aşağıdaki sürüm sabitli Codex,
süreç, atomik yayın ve klavye kaynakları ilk düzeltmede **19.10.2026 Türkiye saati** ile
incelenmiştir (UTC kayıtları 18.10.2026). Adlı Codex izin profili araştırması ve üç resmî
ikiliyle regresyon **19.10.2026 UTC** tarihinde yapıldı. CLI seçenekleri değişebilir;
belge desteği bu bilgisayarda canlı çalıştırma kanıtı değildir.

- İnceleme: [#384 ana yorum](https://github.com/avenoxai/avenoxbeyin/pull/384#issuecomment-6243678257),
  [özellik tablosu ek notu](https://github.com/avenoxai/avenoxbeyin/pull/384#issuecomment-6243771486),
  [#383 merge yorumu](https://github.com/avenoxai/avenoxbeyin/pull/383#issuecomment-6243513321),
  tümü 18.10.2026 UTC.
- Codex 0.155.1: [resmî binary](https://github.com/openai/codex/releases/tag/rust-v0.155.1),
  [özellik adları](https://github.com/openai/codex/blob/rust-v0.155.1/codex-rs/features/src/lib.rs),
  [kabuk/view_image/apply_patch kayıtları](https://github.com/openai/codex/blob/rust-v0.155.1/codex-rs/core/src/tools/spec_plan.rs),
  [alt ajan seçimi](https://github.com/openai/codex/blob/rust-v0.155.1/codex-rs/core/src/config/mod.rs),
  [apply_patch doğrulama sırası](https://github.com/openai/codex/blob/rust-v0.155.1/codex-rs/core/src/tools/handlers/apply_patch.rs).
  Linux musl binary SHA-256: `a0ef8b2debc3bf747e07b1a039354de31300ac0dcc2276498ba281470b5d9115`.
  [0.160.0 özellik tablosu](https://github.com/openai/codex/blob/rust-v0.160.0/codex-rs/features/src/lib.rs)
  kaynakta karşılaştırıldı; bu düzeltmede 0.160.0 ikilisiyle de sentetik CLI/MCP testi yapıldı.
- Codex izin sınırı: [resmî beta profiller ve kapsam](https://learn.chatgpt.com/docs/permissions),
  [0.163.0 sürümü](https://github.com/openai/codex/releases/tag/rust-v0.163.0),
  [0.164.0-alpha.3 ön sürümü](https://github.com/openai/codex/releases/tag/rust-v0.164.0-alpha.3),
  [0.163.0 yama doğrulaması](https://github.com/openai/codex/blob/rust-v0.163.0/codex-rs/core/src/tools/handlers/apply_patch.rs),
  [izin profilinin derlenmesi](https://github.com/openai/codex/blob/rust-v0.163.0/codex-rs/core/src/config/permissions.rs),
  [CLI profil seçimi](https://github.com/openai/codex/blob/rust-v0.163.0/codex-rs/core/src/config/mod.rs),
  [normal hook güven sözleşmesi](https://learn.chatgpt.com/docs/hooks).
  Ayrıntı ve SHA-256 listesi [araştırma notunda](CODEX-APPLY-PATCH.md).
- Süreç: [Linux /proc](https://docs.kernel.org/filesystems/proc.html),
  [Windows GetProcessTimes](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getprocesstimes),
  [WaitForSingleObject](https://learn.microsoft.com/en-us/windows/win32/api/synchapi/nf-synchapi-waitforsingleobject),
  [Apple proc_info.h](https://github.com/apple/darwin-xnu/blob/main/bsd/sys/proc_info.h).
- Atomik yayın: [Python 3.12 os.rename](https://docs.python.org/3.12/library/os.html#os.rename),
  [Linux rename(2)](https://man7.org/linux/man-pages/man2/rename.2.html),
  [Apple RENAME_EXCL](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/sys/stdio.h).
- Klavye: [LowLevelKeyboardProc](https://learn.microsoft.com/en-us/windows/win32/winmsg/lowlevelkeyboardproc),
  [KBDLLHOOKSTRUCT](https://learn.microsoft.com/en-us/windows/win32/api/winuser/ns-winuser-kbdllhookstruct),
  [GetAsyncKeyState](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getasynckeystate).

- Claude Code: [CLI referansı](https://code.claude.com/docs/en/cli-reference),
  [başsız çalışma](https://code.claude.com/docs/en/headless),
  [izin modları](https://code.claude.com/docs/en/permission-modes),
  [sandbox sınırları](https://code.claude.com/docs/en/sandboxing),
  [yönetilen MCP](https://code.claude.com/docs/en/managed-mcp).
- Codex: [CLI komutları](https://learn.chatgpt.com/docs/developer-commands?surface=cli),
  [başsız çalışma ve thread kimliği](https://learn.chatgpt.com/docs/non-interactive-mode),
  [config referansı](https://learn.chatgpt.com/docs/config-file/config-reference),
  [onay ve güvenlik](https://learn.chatgpt.com/docs/agent-approvals-security),
  [rules](https://learn.chatgpt.com/docs/agent-configuration/rules),
  [hook güveni](https://learn.chatgpt.com/docs/hooks),
  [Windows sandbox](https://learn.chatgpt.com/docs/windows/windows-sandbox).
- Microsoft: [süreç oluşturma bayrakları](https://learn.microsoft.com/en-us/windows/win32/procthread/process-creation-flags)
  ve [Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects)
  (güncelleme 14.07.2025),
  [AUMID ile masaüstü toast kaydı](https://learn.microsoft.com/en-us/windows/win32/shell/enable-desktop-toast-with-appusermodelid)
  (07.01.2021),
  [masaüstü toast gönderme](https://learn.microsoft.com/en-us/windows/win32/shell/quickstart-sending-desktop-toast)
  (20.06.2022).
- Apple: [Display Notifications](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/DisplayNotifications.html)
  (güncelleme 13.06.2016).
- Freedesktop: [Desktop Notifications 1.3](https://specifications.freedesktop.org/notification/latest-single/)
  (18.08.2024); GNOME: [libnotify](https://gnome.pages.gitlab.gnome.org/libnotify/).

## İşleme nasıl çalışır

`python3 beyin.py yakala isle` bekleyen kartların metnini çıkarır, sonra ajan dersleri
`knowledge/` notlarına bağlar ve kartı `bitti` ile kapatır.

| Kaynak | Yol |
|---|---|
| Web Clipper ile gelen sayfa | Yakalanan metin kullanılır, ağa çıkılmaz |
| YouTube | [Defuddle](https://github.com/kepano/defuddle) ile bölümlü transkript; olmazsa ya da dili konuşma diliyle uyuşmazsa `yt-dlp` altyazısı; o da yoksa yalnız ses indirilir, yerel Whisper ile yazıya dökülür, ses silinir |
| X, Reddit, GitHub, makale | Defuddle; yoksa düz HTTP ile metin |
| Mail | Seçili metin; tamamı için ajanın Gmail/Outlook bağlantısı |
| PDF, metin dosyası | `pdftotext` ya da doğrudan okuma; görselleri ajan açar |

Ham metin kart klasörünün içinde `.ham/` altında durur. Nokta ile başlayan klasör olduğu için
aramaya ve Obsidian'a karışmaz. `.ham/` ve yakalanan dosyaların durduğu `dosyalar/`, içlerine yazılan
`.gitignore` ile kart klasörü hangisi olursa olsun depoya da girmez.

### Videoda transkriptin dili

Otomatik dublajlı bir videoda YouTube her dublaj için ayrı bir altyazı izi sunar. `isle`,
`yt-dlp` kuruluysa videoda konuşulan dili videonun bilgisinden öğrenir, Defuddle'dan o dildeki
transkripti ister ve gelen dili kontrol eder. Uyuşmazsa `yt-dlp` ile yalnız konuşma dilindeki
izi indirir; elle yazılmış altyazı otomatik olandan önce gelir. Sonuç kartın frontmatter'ına yazılır:

- `dil`: kaydedilen transkriptin dili.
- `altyazi`: `yt-dlp` ile alınan iz, örneğin `en-orig (otomatik)` ya da `tr (elle)`.
- `uyari`: yalnız bir sorun belirtisi varsa yazılır: transkript konuşma dilinde alınamadıysa ya da
  video dublajlıyken (birden çok dilde ses ya da `-orig` izi) konuşulan dil belirlenemediyse.

`yt-dlp` kurulu değilse dil doğrulanamaz: Defuddle'ın seçtiği transkript eskisi gibi kaydedilir ve
dili `dil` alanına yazılır. `dil` videoda konuşulan dil değilse `yt-dlp` kurup
`python3 beyin.py yakala isle <id>` ile yeniden dene; `uyari` olan kart da aynı komutla yeniden
denenir. Daha önce işlenmiş kartlar değişmez.

### İsteğe bağlı araçlar

Hiçbiri zorunlu değil; varsa işleme genişler, yoksa elde olanla devam edilir.
`python3 beyin.py yakala durum` hangilerinin bulunduğunu söyler.

- **Node.js** (`npx`): Defuddle için. Sabit sürüm (`defuddle@0.19.4`) çalıştırılır.
- **yt-dlp**: videoda konuşulan dil, altyazı ve ses.
- **Whisper**: Mac'te `mlx_whisper`, diğerlerinde `whisper` ya da `whisper-ctranslate2`. Ses indirmeyi istemezsen `isle --ses-yok`.
  Videoda konuşulan dili `yt-dlp` söyleyebildiyse Whisper'a `--language` olarak verilir; dil bilinmiyor ya da video
  dublajlıysa Whisper dili kendisi tanır. Model seçmek için `BEYIN_WHISPER_MODEL` ortam değişkeni
  (ör. `large-v3-turbo`) `--model` olarak geçer. `whisper-ctranslate2`'nin varsayılanı `small`; Türkçe gibi
  dillerde terimleri bozabilir (likidite → "liquidite"). GPU varsa daha büyük bir model seç.
  NVIDIA kartlı makinede `whisper-ctranslate2` CUDA'yı kendisi seçer; CUDA kütüphanesi yüklenemezse (ör.
  `cublas64_12.dll` yok) ses bir kez CPU ile yeniden yazıya dökülür ve kartın uyarısı hatayı adıyla söyler.
  Hızlandırmak için eksik kütüphaneyi kur (ör. `pip install nvidia-cublas-cu12` ve klasörünü PATH'e ekle).
  Whisper hiç metin üretmezse kartta Whisper'ın kendi son hata satırı yazar.
- **pdftotext** (Poppler): PDF metni.

Windows'ta bu araçlar bir `.cmd`/`.bat` sarmalayici olarak kuruluysa, argumanlar komut
yorumlayicidan (cmd.exe) gecmeden dogrudan calistirilir; bu mumkun degilse o arac atlanir ve
elde olanla devam edilir.

## Gizlilik

- Yakalama ağa çıkmaz; yalnız vault'a bir dosya yazar.
- Ağ yalnız `isle` adımında ve yalnız yakaladığın kaynaklar için kullanılır. Defuddle,
  X gönderisi sayfada yoksa gönderi adresini FxTwitter API'sine sorar.
- Mail, pano metni ve dosya kartları `visibility: private` ile yazılır.
- Kaldırmak için `python3 beyin.py yakala kaldir`: kısayol, skill ve bildirim gider, kartların kalır.

## Komutlar

```text
beyin.py yakala              yakalama penceresi
beyin.py yakala ekle URL|DOSYA|METIN [--neden "..."]
beyin.py yakala liste [--durum bekliyor|cikarildi|islendi|hata]
beyin.py yakala isle [ID ...] [--ses-yok] [--tekrar]
beyin.py yakala bitti ID --bilgi knowledge/concepts/x.md [--ozet "..."]
beyin.py yakala kur [--kisayol-yok] [--tus 'ctrl+alt+b'] [--klasor "Notlar/Yakala"]
beyin.py yakala kisayol ['cmd+"']
beyin.py yakala kaldir | durum | sablon
```

### Kaynak güvenliği

Yakala kartı oluşturmak ağ kullanmaz. HTTP(S) kaynağını işlemeden önce yerel/özel IP adresleri,
URL kullanıcı bilgileri ve bozuk adresler reddedilir. Defuddle ve yt-dlp'ye URL gönderilmeden önce
DNS yanıtları da denetlenir; Python HTTP yolunun yönlendirmeleri aynı kapıdan geçer. DNS geçici
olarak çözümlenemezse kart hata notuyla kalır, sıradaki kartlar işlenmeye devam eder.

Bu denetimler ilk hedefteki özel adresleri engeller. Yardımcı araçların kendi yönlendirmeleri ve
DNS rebinding için tam ağ izolasyonu sağlamaz. Ham kaynak metni güvenilmeyen veri olarak işaretlenir;
metnin içindeki rol değişikliği, komut çalıştırma ve dosya silme istekleri talimat sayılmaz.
