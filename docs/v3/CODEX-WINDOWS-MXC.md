# Yakala Codex ajanı: Windows MXC sınırı

İnceleme: **20.10.2026 UTC**. Kaynak: kararlı Codex **0.163.0**, commit
`83086188ae0614bd882818ff1aa23f3194962012`; yayın **15.10.2026 21:30:38 UTC** [S1].

## Seçilen davranış

Windows'ta Yakala Codex ajanı artık **0.163.0+ ve native MXC** gerektirir.
Her işte rastgele adlandırılmış bir izin profili üretilir; tek filesystem
girdisi `":root"="deny"` olur. Windows'a ayrıca `windows.sandbox="mxc"`
verilir. Kullanıcı config'i değiştirilmez; yeni kalıcı ayar eklenmez.

```text
-c permissions.beyin_yakala_<32hex>.filesystem={":root"="deny"}
-c default_permissions="beyin_yakala_<32hex>"
-c windows.sandbox="mxc"
```

Destek veya yönetici izni yoksa iş durur. `-s read-only` geri dönüşü yoktur.
`prefer_mxc=true` kullanılmaz; o tercih legacy'e geri dönebilir [S2].
0.155.1 gibi eski Windows istemcileri ön kontrolde reddedilir. POSIX sürüm
alt sınırı 0.155.1 olarak kalır. Genel kabuk, diğer MCP'ler, private/sensitive
not kapıları ve işin ağ seçimi korunur; özellik varsayılan kapalı kalır.

**Bu dal için native Windows başarı ölçümü yoktur.** Linux sözleşme testleri
Windows argv/politika seçimini sınar; gerçek Windows izolasyonunu kanıtlamaz.
Kullanıcının Windows 11 / 0.155.1 elevated başlangıç hatası ve read-only
içerik tahmini ölçümü tarihsel kullanıcı kanıtıdır, bu dalın kabul sonucu değildir.

## Kaynak gerekçesi

`apply_patch` bağlamı yazma reddinden önce doğrular. Güncel handler doğrulamaya
seçili dosya sistemi sandbox bağlamını verir. Kısıtlı okumalar exec-server'ın
dosya sistemi yardımcısına, açık MXC seçimi ise ayrı WindowsMxc backend'ine gider.
Legacy elevated'ın effective kök okuma ön koşulu bu yola uygulanmaz [S3, S4].
MXC'nin `root_deny_keeps_only_narrow_explicit_grants` kaynak testi kök ret
çevirisini denetler. Rust testleri bu çalışmada çalıştırılmadı [S5].

Yardımcı Codex'in kendi minimum çalışma zamanı ve executable okuma izinlerini
ekler; bu modelin keyfi vault/home/state okuma yetkisi anlamına gelmez.
AGENTS keşfi de aynı kısıtlı dosya sistemi yolundadır. Windows'ta metadata
ret hatasının başlangıcı durdurup durdurmadığı canlı kabul testinin parçasıdır;
hata durumunda izin genişletilmez. Normal güvenilen hook'lar ve Yakala MCP
köprüsü kendi yetkileriyle çalışır [S4].

İzin profili yönetici varsayılana sessizce değişebildiği için mevcut profil
ön kontrolü Windows'ta da çalışır. Sistem policy dizini `FOLDERID_ProgramData`
KnownFolder API'sinden alınır; env alias tahmini yapılmaz. Konum veya config
doğrulanamazsa iş başlamaz [S6]. Explicit MXC için yönetilen yasak,
generic fallback'ten önce hata verir; `windows.allow_mxc=false` aşılmaz [S7].

## Seçilmeyen yollar

| Yol | Gerekçe |
| --- | --- |
| Kök read + vault/home/state/CODEX_HOME deny | Elevated kaynakta alt yol reddini kabul eder; listelenmeyen okunabilir dosyalarda kanalı tümüyle kapatmaz. Native başlangıç uyumu da ölçülmedi. |
| `--disable apply_patch_freeform` | Kaldırılmış özellik; güncel bir araç kapatma sınırı değildir. |
| `PreToolUse` ret | Hook hata/timeout durumları tek güvenlik sınırı için yeterli değildir. |
| Model kataloğunda `apply_patch_tool_type=null` | Tüm model kataloğunu yönetmeyi gerektirir. Daha dar desteklenen dosya sistemi seçimi tercih edildi. |
| `prefer_mxc=true` veya salt read-only | Legacy'e dönüş ya da içerik okumaya açık sınır, bu sözleşmeyi sağlamaz. |

Bağımsız, belgelenmiş bir `apply_patch` CLI kapatma anahtarı 0.163.0 şema,
yardım ve araç kayıt kodunda bulunmadı. Bu inceleme kapsamı dışında genel
bir yokluk iddiası değildir [S8].

## Linux doğrulaması

20.10.2026, Python 3.12, sentetik geçici vault/state:

| Koşu | Sonuç |
| --- | --- |
| Codex review + yeni Windows sözleşme modülü | 41/41; 12 yeni Windows mock testi dahil |
| Mevcut ajan/lifecycle/storage review | 255 test: 253 başarı, 2 native Windows atlaması |
| Resmî Codex 0.163.0 gerçek CLI canary | 2/2; 19.684 saniye |
| Eski c82761f üzerinde seçilmiş regresyon | 3 testte 5 hata; yeni koda dönünce hedefli koşu başarılı |

Resmî Linux arşivi SHA-256:
`beb339e8ecd9ba057a6bb2dc81ad8ca474812edfbf0fc5056ca818797648dde4`.
Boyut 112589966 bayt; GitHub API digest ile eşleşti. Canary her testte 28
yama çağrısı, 5 gerçek MCP çağrısı ve güvenilen sentetik SessionStart hook'u
çalıştırır. Doğru/yanlış bağlam çiftleri aynı hata verdi; dosya hash'leri korundu;
normal not/AGENTS köprüden okunabildi, private not reddedildi, sonuç teslimi oluştu.
Yalnız loopback Responses fixture kullanılır; model hesabı/API anahtarı gerekmez.

## Windows kabul kapısı

Resmî belge Windows 11 24H2 build 26100.9278 / 25H2 build 26200.9278 ile gelen
yetenekleri belirtir. Build tek başına yeterli değildir; native capability probe
ve yönetici politikası belirleyicidir [S2, S5]. Önce temel başlangıcı dene:

```powershell
codex --version
codex -c windows.sandbox=mxc sandbox --include-managed-config --permission-profile :workspace -- cmd.exe /d /c echo MXC_OK
$LASTEXITCODE
```

Bu komutun başarılı olması root-deny kanıtı değildir. Sonra repo kökünde,
sentetik örnek yolu gerçek resmî native ikiliyle değiştirerek:

```powershell
$env:BEYIN_CODEX_BINARY = 'C:\SyntheticTools\codex.exe'
$env:BEYIN_CODEX_EVIDENCE = Join-Path $env:TEMP 'yakala-mxc-evidence.json'
py -3 -m unittest tests.v3_yakala_codex_windows_boundary_test -v
py -3 -m unittest tests.v3_yakala_codex_boundary_test -v
```

İsteğe bağlı gerçek testte Windows skip yoktur; destek yoksa test hata vermelidir.
İki görünümde AGENTS başlangıcını ve gerçek `read_note → write_note → complete
→ receipt → Last-Session` akışını ayrıca doğrula. Unsupported host,
`allow_mxc=false`, yönetilen izin profili ve eski CLI durumunda işin izin
genişletmeden durduğunu kaydet. Native junction/hardlink/8.3/UNC ve ConPTY
ölçümleri hâlâ açıktır. Linux sonucu Windows/macOS başarısı olarak yazılmamalı.

## Kaynaklar

- [S1] [0.163.0](https://github.com/openai/codex/releases/tag/rust-v0.163.0), [latest API](https://api.github.com/repos/openai/codex/releases/latest).
- [S2] [Resmî Windows sandbox belgesi](https://developers.openai.com/codex/windows/windows-sandbox).
- [S3] [ApplyPatchHandler](https://github.com/openai/codex/blob/83086188ae0614bd882818ff1aa23f3194962012/codex-rs/core/src/tools/handlers/apply_patch.rs), [elevated koşulu](https://github.com/openai/codex/blob/83086188ae0614bd882818ff1aa23f3194962012/codex-rs/windows-sandbox-rs/src/resolved_permissions.rs).
- [S4] [FS helper](https://github.com/openai/codex/blob/83086188ae0614bd882818ff1aa23f3194962012/codex-rs/exec-server/src/fs_sandbox.rs), [backend seçimi](https://github.com/openai/codex/blob/83086188ae0614bd882818ff1aa23f3194962012/codex-rs/exec-server/src/sandbox_selection.rs), [AGENTS](https://github.com/openai/codex/blob/83086188ae0614bd882818ff1aa23f3194962012/codex-rs/core/src/agents_md.rs).
- [S5] [MXC README](https://github.com/openai/codex/blob/83086188ae0614bd882818ff1aa23f3194962012/codex-rs/mxc-sandbox/README.md), [policy testleri](https://github.com/openai/codex/blob/83086188ae0614bd882818ff1aa23f3194962012/codex-rs/mxc-sandbox/src/policy_tests.rs).
- [S6] [KnownFolder/config yükleme](https://github.com/openai/codex/blob/83086188ae0614bd882818ff1aa23f3194962012/codex-rs/config/src/loader/mod.rs), [profil fallback](https://github.com/openai/codex/blob/83086188ae0614bd882818ff1aa23f3194962012/codex-rs/core/src/config/mod.rs).
- [S7] [Strict MXC doğrulaması](https://github.com/openai/codex/blob/83086188ae0614bd882818ff1aa23f3194962012/codex-rs/core/src/config/windows_sandbox_config.rs), [requirements](https://github.com/openai/codex/blob/83086188ae0614bd882818ff1aa23f3194962012/codex-rs/config/src/config_requirements.rs).
- [S8] [Config Reference](https://developers.openai.com/codex/config-reference), [araç kaydı](https://github.com/openai/codex/blob/83086188ae0614bd882818ff1aa23f3194962012/codex-rs/core/src/tools/spec_plan.rs), [özellik listesi](https://github.com/openai/codex/blob/83086188ae0614bd882818ff1aa23f3194962012/codex-rs/features/src/lib.rs), [hook hata davranışı](https://github.com/openai/codex/blob/83086188ae0614bd882818ff1aa23f3194962012/codex-rs/hooks/src/events/pre_tool_use.rs).
