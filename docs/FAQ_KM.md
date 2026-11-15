# សំណួរដែលជួបញឹកញាប់ និងការដោះស្រាយបញ្ហា ScreenMirror

[English](FAQ.md) · [ខ្មែរ](FAQ_KM.md) · [ត្រឡប់ទៅ README](../README_KM.md)

## ហេតុអ្វីមិនឃើញ Android device ក្នុងបញ្ជី?

1. ភ្ជាប់ទូរស័ព្ទដោយខ្សែ USB ដែលបញ្ជូនទិន្នន័យបាន ឬបញ្ចប់ Wireless ADB pairing និង connection។
2. បើក USB debugging និងទទួលយក authorization prompt លើទូរស័ព្ទដែលបានដោះសោ។
3. បើក **Devices** ហើយចុច **Refresh**។ បើ ADB server ឈប់ សូមចុច **Start ADB server**។
4. លើ Windows ពិនិត្យថាឧបករណ៍ត្រូវការ OEM USB driver ឬអត់។
5. ឧបករណ៍ដែលបង្ហាញ `unauthorized` មិនទាន់រួចរាល់សម្រាប់ mirroring ទេ; សូមទទួលយក prompt លើទូរស័ព្ទ ហើយធ្វើបច្ចុប្បន្នភាពបញ្ជី។

## ADB បង្ហាញ `unauthorized`។ ត្រូវធ្វើដូចម្តេច?

ដោះសោទូរស័ព្ទ ហើយទទួលយក USB debugging authorization prompt សម្រាប់កុំព្យូទ័រនេះ។ បើមិនឃើញ prompt សូមដកខ្សែហើយភ្ជាប់វិញ រួច Refresh។ អនុញ្ញាតតែកុំព្យូទ័រដែលអ្នកទុកចិត្ត។ ScreenMirror មិនរំលង Android authorization ទេ។

## ហេតុអ្វី wireless pairing បរាជ័យ?

- ប្រើ pairing `host:port` និង one-time code បច្ចុប្បន្នពី Wireless debugging pairing screen លើទូរស័ព្ទ។
- Pair ជាមុន បន្ទាប់មកប្តូរ target ទៅ connection `host:port` របស់ទូរស័ព្ទ រួចចុច **Connect**។ Endpoint ទាំងពីរអាចប្រើ port ខុសគ្នា។
- ពិនិត្យថាទូរស័ព្ទ និងកុំព្យូទ័រទាក់ទងគ្នាបានលើបណ្តាញដែលទុកចិត្ត និងគ្មាន network isolation រារាំង។
- Pairing code មានអាយុកាលកំណត់ និងមិនគួរប្រើឡើងវិញ។ កម្មវិធីលាក់ និងលុប code ប៉ុន្តែ ADB ទទួលវាជា process argument។

## ហេតុអ្វី mirroring មិនចាប់ផ្តើម?

- ជ្រើសឧបករណ៍ដែលមានស្ថានភាព ready/`device`។
- រង់ចាំឲ្យ scrcpy capability discovery ចប់ ហើយពិនិត្យថាមិនមាន session ផ្សេងកំពុងដំណើរការ។
- មើល scrcpy version និង error ថ្មីៗនៅទំព័រ **Diagnostics**។
- ក្នុង mirror profile ជ្រើស codec ដែល scrcpy ភ្ជាប់មកជាមួយគាំទ្រ។ Advanced controls បង្ហាញតែជម្រើសដែលបានរកឃើញពី executable នោះ។
- គម្រោងមិនទាន់បានផ្ទៀងផ្ទាត់ជាមួយ Android ម៉ូដែល/version ផ្សេងៗទេ; បញ្ហាអាចពាក់ព័ន្ធនឹងឧបករណ៍ ឬ OS ជាក់លាក់។

## ហេតុអ្វីបង្អួច scrcpy បើកដាច់ដោយឡែក?

នេះជារចនាសម្ព័ន្ធបច្ចុប្បន្ន។ scrcpy គ្រប់គ្រងការបកស្រាយ និងបង្ហាញវីដេអូ ព្រមទាំង input controls ដែលវាគាំទ្រ។ ScreenMirror គ្រប់គ្រង ADB, settings និង process lifecycle ប៉ុន្តែមិនបង្កប់ផ្ទាំងវីដេអូទេ។

## រូបថតអេក្រង់ត្រូវបានរក្សាទុកនៅទីណា?

ទីតាំងត្រូវបានជ្រើសក្នុង Windows save dialog។ ScreenMirror ថត PNG ហើយបង្ហាញរូបថ្មីៗរហូតដល់ 12 ក្នុងសម័យកម្មវិធីបច្ចុប្បន្ន។ វាមិនស្កេន folder ឬរក្សាបណ្ណាល័យ screenshot អចិន្ត្រៃយ៍ទេ។

## Audio និង recording ដំណើរការយ៉ាងដូចម្តេច?

Audio forwarding បើកតាមលំនាំដើម បើឧបករណ៍ និង scrcpy គាំទ្រ។ Recording កំណត់ដោយ output path ក្នុង mirror profile; path នេះត្រូវបានផ្ញើទៅ scrcpy ហើយអនុវត្តនៅពេលចាប់ផ្តើម mirror session ថ្មី។ វាបញ្ឈប់ជាមួយ session នោះ។ ScreenMirror មិនមាន live recording toggle ទេ ហើយមិនទាន់បានសាកល្បងលើ hardware។

## បើ ScreenMirror បិទ ឬ ADB/scrcpy ឈប់ដោយមិនរំពឹង ត្រូវធ្វើអ្វី?

បើ UI នៅបើក សូមមើល **Diagnostics** ដើម្បីពិនិត្យ process output និង versions។ បើកកម្មវិធីវិញ ហើយសាកល្បងបន្ទាប់ពីពិនិត្យស្ថានភាពឧបករណ៍។ UI បច្ចុប្បន្នមិនមាន crash-report viewer ដែលរក្សាទុកអចិន្ត្រៃយ៍ទេ; សូមចម្លងសារកំហុសដែលបង្ហាញពេលរាយការណ៍បញ្ហា។

## ត្រូវបញ្ឈប់ mirroring និងបិទកម្មវិធីដោយសុវត្ថិភាពដូចម្តេច?

ចុច **Stop session** ឬបិទបង្អួច scrcpy។ ដើម្បីចាកចេញ សូមបិទ ScreenMirror តាមធម្មតា; កម្មវិធីសម្របសម្រួលការបិទ process ADB និង scrcpy។ ជៀសវាង force-end process លុះត្រាតែកម្មវិធីមិនឆ្លើយតប។

## តើមាន Windows prebuilt ដែលទាញយកជាសាធារណៈទេ?

មិនអាចផ្ទៀងផ្ទាត់ GitHub Release ដែលអាចទាញយកបានទេ។ Repository ដែលបានផ្តល់មានស្ថានភាព private នៅពេលពិនិត្យ ហើយថត `dist-easy-run` ក្នុងម៉ាស៊ីនមិនមែនជា release ដែលបានបោះពុម្ពទេ។ សូមពិនិត្យ [Releases page](https://github.com/cyberscout168/kh3mren-mirror/releases) បើអ្នកមានសិទ្ធិចូល។

## តើ ScreenMirror គាំទ្រ macOS ឬ Linux ទេ?

មិនទេ។ UI desktop, scrcpy runtime និង packaging បច្ចុប្បន្នកំណត់សម្រាប់ Windows x64។ ឯកសារ ADB របស់ macOS/Linux នៅក្នុង workspace ប៉ុន្តែមិនមែនជាកញ្ចប់ desktop ដែលគាំទ្រទេ។

## តើត្រូវផ្ញើសំណួរ ឬរាយការណ៍បញ្ហាទៅណា?

ទាក់ទងម្ចាស់គម្រោងតាម [sankhemren117@gmail.com](mailto:sankhemren117@gmail.com)។ សូមបញ្ចូល Windows version, ScreenMirror/ADB/scrcpy versions, device state និងសារពាក់ព័ន្ធពី Diagnostics។ កុំផ្ញើ pairing code, password ឬ secret ផ្សេងៗ។
