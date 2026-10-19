# Yakala: Codex `apply_patch` okuma sınırı

Araştırma ve Linux ölçümü: **19 Ekim 2026 UTC**. İlgili upstream PR: [#384](https://github.com/avenoxai/avenoxbeyin/pull/384).

## Sonuç ve uygulanan değişiklik

`apply_patch` aracının yazmasını engellemek, mevcut dosya içeriği hakkında tahmin
doğrulamasını tek başına engellemiyor. `-a never -s read-only` altında doğru yama
bağlamı yazma politikasına kadar ilerlerken yanlış bağlam doğrulamada hata veriyor.
Bu ayrım güncel kararlı Codex **0.163.0** ile de tekrarlandı.

Desteklenen bir çözüm bulundu: Codex'in belgelenmiş **adlı izin profili**, yama
doğrulamasının kullandığı dosya sistemi okumasını da kısıtlıyor. Yakala her komutta
yeni bir `beyin_yakala_<32 hex karakter>` adı üretip şu iki `-c` ayarını veriyor:

```text
permissions.beyin_yakala_<rastgele>.filesystem={":root"="deny"}
default_permissions="beyin_yakala_<rastgele>"
```

Profilin başka dosya sistemi girdisi veya `extends` atası yok. `:minimal`, Python
dizini, vault ve geçici dizin için ek okuma izni eklenmiyor. İstemciye `-s read-only`
verilmiyor; bu eski seçici adlı profilin yerine geçer. Kullanıcının mevcut
config dosyası değişmiyor. Rastgele ad, aynı adlı kullanıcı profilinden daha dar
bir `read`/`write` girdisinin derin birleştirme yoluyla miras kalmasını önlüyor.
128 bit rastgeleliğin çakışmayı pratikte ihmal edilebilir kılması bir olasılık
değerlendirmesidir; bütün sistem durumlarını tarayarak ispatlanmış benzersizlik değildir.

`--strict-config` bilinmeyen üst düzey ayarları hata yapar. Desteklenmeyen bayraklar
ve eski/ön sürümler zaten ön kontrolde reddedilir. En eski ikili ölçümü **0.155.1**
olduğu için sürüm alt sınırı değişmedi. Genel kabuk, görüntü okuma, alt ajan, app,
eklenti ve diğer MCP kapıları önceki iş bazındaki kapatma kontrollerini korur.

Bu profil **beta** olarak belgelenmiştir. Bir ayarın kabul edilmesi, gelecekteki
her sürümde aynı güvenlik davranışını garanti etmez. Bu nedenle gerçek ikiliyle
tekrarlanabilen, isteğe bağlı regresyon da eklendi. Native Windows ve macOS için
aşağıdaki ölçümler tamamlanmadan Linux sonucu o platformlara genellenmemelidir.

## Neden bu çözüm?

0.163.0 kaynak kodunda `ApplyPatchHandler::handle_call`, seçili ortamın
`FileSystemSandboxContext` değerini `verify_apply_patch_args` çağrısına geçiriyor.
`Update`/`Move` işlemlerinde bağlam eşleştirme ve `Delete` işleminde eski içerik
okuma bu dosya sistemi üzerinden gerçekleşiyor. `Add` için mevcut içerik
okunmadan yazma kararı veriliyor. Bu yüzden okuma ve yazmayı birlikte reddeden
profil, tahmin sonucuna göre farklılaşan içerik kontrolünden önce uygulanıyor.
Kaynak yolu aşağıdaki [S4] ve [S5] bağlantılarında.

İzin derleyicisi özel profili boş bir kısıtlı dosya sistemi politikasıyla
başlatıyor; kendiliğinden vault veya `:minimal` okuması eklemiyor [S6].
Daha özgül bir izin geniş kök reddini açabileceğinden, salt kök reddini
mevcut sabit adlı profile eklemek yeterli değildir [S2].

Resmî izin sayfası eski sandbox ayarlarıyla yeni profilleri karıştırmama uyarısı
verir [S2]. İncelenen üç sürümde kaynak ve gerçek ikili ölçümü daha özel bir
öncelik kuralını da doğruladı: `SessionFlags` içindeki açık
`default_permissions`, yüklenmiş dosyadaki eski `sandbox_mode` ayarına üstün
geliyor; gerçek `--sandbox`/`-s` komut satırı seçicisi ise profili devre dışı
bırakıyor [S7]. Regresyonun geçici config dosyasında kasıtlı olarak
`sandbox_mode="workspace-write"` bulunuyor. İkinci test ayrıca desteklenen
`--profile fixture_legacy` seçicisiyle `fixture_legacy.config.toml` içindeki
`sandbox_mode="read-only"` değerini yükletiyor. İkisinde de bütün native dosya
okuma/yazma denemeleri reddediliyor. Yakala üretim komutu bu ek `--profile`
bayrağını kullanmaz; ikinci test Codex'in katman önceliğini zorlar. Bu ayrıntı
yalnız incelenen sürümler için kaynak ve çalıştırma kanıtıyla söylenmektedir.

### İncelenen alternatifler

| Yol | Kanıt ve karar |
| --- | --- |
| `--disable apply_patch_freeform` | 0.155.1 ve 0.163.0 özellik listesi/kaynağında `removed`. 0.163.0 ikilisinde bayrağa rağmen aynı içerik tahmini ayrımı oluştu. Kullanılmadı. |
| Salt `read-only` ve `never` | Yazmalar reddedildi; doğru/yanlış bağlam hataları farklı kaldı. Bu bulgunun nedeni. |
| `PreToolUse` içinde `apply_patch` reddi | Desteklenen hook, handler doğrulamasından önce çalışabilir. Ancak sıradan hook hata/timeout/bozuk çıktısında çağrı devam edebilir; tek güvenlik sınırı olarak seçilmedi [S8, S9]. |
| `model_catalog_json` ile `apply_patch_tool_type=null` | Resmî 0.163.0 ikilisinin geçici katalog denemesinde aracı kaldırdı; zorlanmış çağrı `unsupported custom tool call` oldu. Bu, model kataloğunu bütünüyle yönetmeyi gerektiren daha geniş bir müdahale. Model özelliklerini değiştirmeyen dosya sistemi profili seçildi [S3, S10]. |
| Model prompt'unda araç yasağı | Araç seviyesindeki sınırı sağlamaz. Güvenlik çözümü sayılmadı. |

Bağımsız, sadece `apply_patch` aracını kapatan güncel bir CLI anahtarı bulunmadı;
bu sonuç incelenen config şeması, CLI yardım metni, özellik listesi ve kayıt
koduyla sınırlıdır. Dosya okuma tahmin kanalını kapatan belgelenmiş profil
bulunduğu için Codex deposuna issue açılması bu düzeltmenin ön koşulu değildir.

## Gerçek ikiliyle test

`tests/v3_yakala_codex_boundary_test.py` Python stdlib kullanır. Codex projenin
bağımlılığı değildir; `BEYIN_CODEX_BINARY` verilmedikçe normal CI testi atlar.
İkili otomatik indirilmez. Bilinen resmî ikili açıkça seçilir:

```bash
BEYIN_CODEX_BINARY=/absolute/path/to/codex \
BEYIN_CODEX_EVIDENCE=/absolute/path/to/codex-boundary.json \
python3 -m unittest tests.v3_yakala_codex_boundary_test -v
```

PowerShell örneği; `.cmd` npm sarmalayıcısı yerine gerçek `codex.exe` yolunu ver:

```powershell
$env:BEYIN_CODEX_BINARY = 'C:\CodexTest\codex.exe'
$env:BEYIN_CODEX_EVIDENCE = "$PWD\codex-boundary-windows.json"
py -3 -m unittest tests.v3_yakala_codex_boundary_test -v
Remove-Item Env:BEYIN_CODEX_BINARY, Env:BEYIN_CODEX_EVIDENCE
```

Test yeni geçici `CODEX_HOME`, vault, state ve zararsız notlar oluşturur. Yalnız
`127.0.0.1` üzerinde Responses protokolü taklit edilir; model hesabı, API anahtarı
ve dış model servisi kullanılmaz. Çıkışlar gerçek Codex ikilisinden gelir;
sahte sunucu yalnız modelin araç çağrısını belirler. Girdi olarak seçilen
`gpt-5.5` adı, bu sürümlerin doğrudan custom-tool taşımasını sınamak içindir;
barındırılan bir modelin yetenek, fiyat veya kalitesi ölçülmez.

Her sürümde iki uçtan uca regresyonun her birinde şunlar doğrulandı:

- **28 yama çağrısı:** dört yol yazımı (göreli/mutlak, vault içi/dışı) için
  doğru/yanlış bağlamlı Update ve Move, Delete, mevcut ve yeni dosyaya Add.
  Aynı yol/işlemdeki doğru/yanlış çiftleri birebir aynı çıktı verdi. Update/Move
  ve Delete, dosya okuma hatasıyla; Add, yazma politikasıyla reddedildi.
  İşlem türleri arasında tek bir hata metni kullanıldığı iddia edilmez.
- Dört başlangıç dosyasının SHA-256 değeri korundu. Yeni ya da taşınmış hedef
  oluşmadı; hiçbir yama çıktısı sentetik doğru/yanlış içerik satırını taşımadı.
- **5 gerçek MCP çağrısı:** normal not ve `AGENTS.md` okundu; private not
  okunmadı; yeni sonuç notu yazıldı; `complete` kabul edilip manifest oluştu.
  Yakala'nın işi/PID neslini doğrulayan gerçek stdio MCP süreci çalıştı.
- **Normal hafıza başlangıcı:** testin ürettiği tek sentetik `SessionStart`
  hook'u, `hooks/list` ile görülen kendi hash'i için güven kaydı alır.
  Güven atlama bayrağı verilmez. Hook dosyadan okuduğu bağlamı ilk model
  isteğine ekler; native yama okumaları aynı oturumda yine reddedilir.
- Bilinmeyen üst düzey config anahtarı `--strict-config` altında model
  isteği oluşmadan reddedilir. Çalıştırma sonrasında config hash'i aynıdır.

`--strict-config` için ölçüm kapsamı üst düzey bilinmeyen anahtardır. Araştırmada
`permissions.<başka profil>.unknown_field` gibi iç içe bilinmeyen bir alanın
bu üç sürümde her zaman reddedilmediği de görüldü. Bu bayrak tek başına genel
bir profil doğrulama kanıtı olarak sunulmaz. Kök reddinin etkinliği doğrudan
yama çağrılarıyla sınandı; özel profilde eksik/boş filesystem tablosu da
kısıtlı başlar [S2, S6].

| İkili | Resmî yayın zamanı (UTC) | Linux sonucu |
| --- | --- | --- |
| 0.155.1 | 18.09.2026 20:03:04 | 2/2 gerçek CLI regresyonu geçti; test başına 28 patch + 5 MCP + hook |
| 0.160.0 | 01.10.2026 20:19:13 | 2/2 gerçek CLI regresyonu geçti; test başına 28 patch + 5 MCP + hook |
| 0.163.0 | 15.10.2026 21:30:38 | 2/2 gerçek CLI regresyonu geçti; test başına 28 patch + 5 MCP + hook |
| 0.164.0-alpha.3 | 17.10.2026 04:03:25 | Yalnız kaynak karşılaştırması; gerçek ikili çalıştırılmadı, Yakala ön sürümü reddeder |

Üç ikilideki toplam **6 başarılı gerçek CLI testine** ek olarak
`v3_yakala_ajan*_test.py` keşfi **261 test** çalıştırdı:
**259 başarı, 2 Windows'a özgü atlama**. Bunlar yeni gerçek Codex testinden
ayrıdır. Test sayısı, `subTest` döngülerindeki her kontrolü ayrı test saymaz.
Bu rapor tam V3 birleşim testinin yerini almaz.

### İkili bütünlüğü

Resmî `codex-x86_64-unknown-linux-musl.tar.gz` varlıkları indirildi; aşağıdaki
SHA-256 değerleri GitHub release API'sindeki `digest` alanıyla eşleşti.

```text
0.155.1 a0ef8b2debc3bf747e07b1a039354de31300ac0dcc2276498ba281470b5d9115
0.160.0 306865417d4ee7a927785852910a527f41e1e159add390ac5ae3accb67d44a13
0.163.0 beb339e8ecd9ba057a6bb2dc81ad8ca474812edfbf0fc5056ca818797648dde4
```

## Windows ve macOS'ta kalan doğrulama

Linux ölçümü, Windows MXC/elevated/unelevated veya macOS Seatbelt çalıştırması
değildir. Resmî belge desteklenmeyen bazı politikaların reddedileceğini belirtir;
bir kuruluma özel gerçek sonuç yine ölçülmelidir [S2]. İzin profilini gevşeten
bir otomatik geri dönüş eklenmedi.

1. Gerçek ikili regresyonunu kullanılan CLI sürümünde çalıştır; Windows,
   Python, Codex, sandbox türü ve dosya sistemi bilgisini kaydet.
2. Native Windows'ta `gizli` ve `pencere` görünümlerinde aynı doğru/yanlış
   bağlam denemelerini yap. UNC, farklı sürücü, büyük/küçük harf ve 8.3 yol
   yazımı gibi platforma özgü yolları ayrıca ölç.
3. Normal, önceden güvenilmiş gerçek hafıza hook'larının çalıştığını ve
   `read_note → write_note → complete → receipt → Last-Session` zincirini
   masaüstünde doğrula. Sentetik test yalnız MCP teslimine kadar gider;
   receipt/Last-Session yayınını veya toast davranışını ölçmez.
4. Etkin kullanıcı MCP/eklenti ve eski sandbox ayarı bulunan ayrı test
   profilinde araç sınırını/config hash'ini doğrula. İzin derleme hatası varsa
   bunu açık uyumluluk hatası olarak kaydet; daha geniş kök izniyle gizleme.

Normal hook'lar ve Yakala MCP güvenilen yerel koddur ve kendi dosya erişimini
sürdürür. Profil bu kodları veya CLI'nin başlangıç bağlamı yüklemesini genel
bir süreç sandbox'ına dönüştürmez. Modelin araca sunduğu patch içeriğinin
tahmin doğrulaması burada incelenen somut sınırdır.

## Kaynaklar

Aşağıdaki resmî İngilizce kaynaklar **19.10.2026 UTC** tarihinde incelendi.
Sürüm bilgisi GitHub release listesi, `latest` yönlendirmesi ve release API ile
doğrulandı. Web görünümü bazı GitHub kaynak sayfalarını açamadığında aynı
resmî repo salt okunur `git` checkout ile incelendi.

- **[S1] Sürümler:** [liste](https://github.com/openai/codex/releases),
  [latest](https://github.com/openai/codex/releases/latest),
  [0.155.1](https://github.com/openai/codex/releases/tag/rust-v0.155.1),
  [0.160.0](https://github.com/openai/codex/releases/tag/rust-v0.160.0),
  [0.163.0](https://github.com/openai/codex/releases/tag/rust-v0.163.0),
  [0.164.0-alpha.3](https://github.com/openai/codex/releases/tag/rust-v0.164.0-alpha.3),
  [release API](https://api.github.com/repos/openai/codex/releases?per_page=30).
- **[S2] Adlı profiller, beta, deny, öncelik, MCP kapsamı ve platform sınırları:**
  [Permissions](https://learn.chatgpt.com/docs/permissions).
- **[S3] CLI/config sözleşmesi:**
  [Configuration Reference](https://learn.chatgpt.com/docs/config-file/config-reference),
  [CLI source](https://github.com/openai/codex/blob/rust-v0.163.0/codex-rs/cli/src/main.rs).
- **[S4] Yama handler'ı ve sandbox'ın doğrulamaya aktarılması:**
  [0.163.0 apply_patch handler](https://github.com/openai/codex/blob/83086188ae0614bd882818ff1aa23f3194962012/codex-rs/core/src/tools/handlers/apply_patch.rs).
- **[S5] Update/Move/Delete ön okumaları:**
  [apply-patch invocation](https://github.com/openai/codex/blob/83086188ae0614bd882818ff1aa23f3194962012/codex-rs/apply-patch/src/invocation.rs).
- **[S6] Özel profilin derlenmesi:**
  [config/permissions.rs](https://github.com/openai/codex/blob/83086188ae0614bd882818ff1aa23f3194962012/codex-rs/core/src/config/permissions.rs).
- **[S7] `resolve_permission_config_syntax` ve legacy seçici önceliği:**
  [config/mod.rs](https://github.com/openai/codex/blob/83086188ae0614bd882818ff1aa23f3194962012/codex-rs/core/src/config/mod.rs).
- **[S8] Hook güveni, araç sırası ve callback hata sınırları:**
  [Hooks](https://learn.chatgpt.com/docs/hooks).
- **[S9] Hook kararı ve handler çağrısı:**
  [hook_runtime.rs](https://github.com/openai/codex/blob/83086188ae0614bd882818ff1aa23f3194962012/codex-rs/core/src/hook_runtime.rs),
  [tools/registry.rs](https://github.com/openai/codex/blob/83086188ae0614bd882818ff1aa23f3194962012/codex-rs/core/src/tools/registry.rs).
- **[S10] Araç kaydı ve kaldırılmış bayrak:**
  [spec_plan.rs](https://github.com/openai/codex/blob/83086188ae0614bd882818ff1aa23f3194962012/codex-rs/core/src/tools/spec_plan.rs),
  [features/lib.rs](https://github.com/openai/codex/blob/83086188ae0614bd882818ff1aa23f3194962012/codex-rs/features/src/lib.rs).
- **[S11] Strict config yükleme:**
  [config/loader/mod.rs](https://github.com/openai/codex/blob/83086188ae0614bd882818ff1aa23f3194962012/codex-rs/config/src/loader/mod.rs).

İncelenen tag'lerin çözülmüş commit'leri:

```text
rust-v0.155.1       be2951ea34f0d295ed0becf97079f92fa5f6950e
rust-v0.160.0       a956835d020762cb2b570053af06f643a11c0ecc
rust-v0.163.0       83086188ae0614bd882818ff1aa23f3194962012
rust-v0.164.0-alpha.3 bd43893f3db678fcb7124296905a65b2dfa9dac0
```
