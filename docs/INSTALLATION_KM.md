# មគ្គុទ្ទេសក៍ដំឡើង ScreenMirror

[English](INSTALLATION.md) · [ខ្មែរ](INSTALLATION_KM.md) · [ត្រឡប់ទៅ README](../README_KM.md)

## ស្ថានភាពការទាញយក

GitHub repository មានស្ថានភាព private ដូច្នេះត្រូវមានសិទ្ធិអនុញ្ញាតដើម្បី clone source code។ អ្នកប្រើដែលមានសិទ្ធិអាចទាញយក source ពី repository បាន។ មិនទាន់បានផ្ទៀងផ្ទាត់ថាមាន GitHub Release package សម្រាប់ទាញយកទេ។

មិនអាចផ្ទៀងផ្ទាត់ថាមាន GitHub Release package ដែលអាចទាញយកបានទេ។ ថត `dist-easy-run\ScreenMirror` ដែល build ក្នុងម៉ាស៊ីនមិនមែនជា release ដែលបានបោះពុម្ពទេ។

## តម្រូវការប្រព័ន្ធ

| តម្រូវការ | ព័ត៌មាន |
|---|---|
| Desktop OS | Windows x64 ប៉ុណ្ណោះ។ បានអភិវឌ្ឍ និង smoke test លើ Windows 10 build 19045។ មិនបានកំណត់ Windows version អប្បបរមាជាផ្លូវការទេ។ |
| Android device | ត្រូវបើក ADB debugging និងអនុញ្ញាតកុំព្យូទ័រនេះ។ មិនមានតារាង Android version ដែលបានផ្ទៀងផ្ទាត់ទេ។ |
| USB | ត្រូវការ USB cable ដែលបញ្ជូនទិន្នន័យបាន។ Windows អាចត្រូវការ USB driver របស់ក្រុមហ៊ុនផលិតទូរស័ព្ទ។ |
| Wireless | ទូរស័ព្ទត្រូវមាន Wireless debugging/pairing ហើយទូរស័ព្ទនិងកុំព្យូទ័រត្រូវទាក់ទងគ្នាបានតាមបណ្តាញដែលទុកចិត្ត។ |
| Python សម្រាប់ source | បានប្រើ Python 3.13.3 សម្រាប់តេស្ត/build ចុងក្រោយ; មិនបានកំណត់ Python version អប្បបរមាទេ។ |
| Runtime ភ្ជាប់មកជាមួយ | Windows Platform-Tools 37.0.1 និង scrcpy 5.0.1។ មិនចាំបាច់ដំឡើង ADB/scrcpy ដាច់ដោយឡែកសម្រាប់ source/package នេះទេ។ |
| CPU/RAM/GPU | មិនបានវាស់ ឬកំណត់តម្រូវការអប្បបរមាទេ។ ល្បឿន mirroring អាស្រ័យលើឧបករណ៍ resolution network និង graphics driver។ |

## វិធី A — កម្មវិធីដែល build រួច

**មិនទាន់បានផ្ទៀងផ្ទាត់ release asset ទេ។** បើអ្នកមានសិទ្ធិចូល សូមពិនិត្យ [Releases page](https://github.com/cyberscout168/kh3mren-mirror/releases) ហើយប្រើវិធីនេះតែបន្ទាប់ពីម្ចាស់គម្រោងបានបោះពុម្ព package សម្រាប់ Windows x64។

នៅពេលមាន package ផ្លូវការ៖

1. ទាញយក Windows x64 release archive ពី Releases page។
2. ស្រាយ **ថត `ScreenMirror` ទាំងមូល** ទៅទីតាំងដែលអាចសរសេរបាន។
3. ទុក `ScreenMirror.exe` នៅជាមួយថត `_internal` និង runtime files ទាំងអស់។
4. ដំណើរការ `ScreenMirror.exe`។
5. បើ Windows បង្ហាញសារព្រមានអំពីប្រភព ឬសុវត្ថិភាព សូមផ្ទៀងផ្ទាត់ប្រភពទាញយកមុនអនុញ្ញាត។ Local build បច្ចុប្បន្នមិនមាន digital signature ទេ។

កុំចាត់ទុកថត local `dist-easy-run` ជា release សាធារណៈ។ វាជា build លើម៉ាស៊ីនអភិវឌ្ឍន៍ ហើយមិនទាន់បានសាកល្បងលើ Windows ដែលដំឡើងថ្មីទេ។

## វិធី B — ដំណើរការពី source

ពាក្យបញ្ជាខាងក្រោមត្រូវនឹងរចនាសម្ព័ន្ធ project។ អ្នកត្រូវមានសិទ្ធិអនុញ្ញាតដើម្បី clone GitHub repository ដែលជា private។

1. ដំឡើង Git និង Python 3.13 (64-bit ណែនាំ; បានប្រើ 3.13.3 សម្រាប់ការផ្ទៀងផ្ទាត់បច្ចុប្បន្ន)។
2. Clone repository ហើយចូលទៅថតគម្រោង៖

   ```powershell
   git clone https://github.com/cyberscout168/kh3mren-mirror.git
   Set-Location kh3mren-mirror
   ```

3. បង្កើត និង activate virtual environment៖

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   បើ PowerShell រារាំង activation script សូមប្រើ Python ក្នុង environment ដោយផ្ទាល់ ជំនួសឲ្យការប្តូរ execution policy ទូទាំងម៉ាស៊ីន៖

   ```powershell
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   .\.venv\Scripts\python.exe -m screenmirror.main
   ```

4. ដំឡើង dependencies ដែល project កំណត់៖

   ```powershell
   python -m pip install -r requirements.txt
   ```

   `requirements.txt` កំណត់ PySide6 `>=6.8,<7` និង PyInstaller `>=6.10,<7`។

5. បើក ScreenMirror៖

   ```powershell
   python -m screenmirror.main
   ```

កម្មវិធីជ្រើស `platform-tools(Windows)\adb.exe` និង scrcpy runtime សម្រាប់ Windows x64 ដែលភ្ជាប់មកជាមួយ។ កុំចម្លង ឬដំណើរការ ADB សម្រាប់ Linux/macOS លើ Windows។

## Build កញ្ចប់ Windows

ពីថត root របស់ project ដំណើរការ៖

```powershell
.\build_windows.ps1
```

Script ប្រើ `.venv`, `ScreenMirror.spec` និង runtime folders ដែលបានភ្ជាប់មកជាមួយ។ វាបង្កើត package នៅ៖

```text
dist-easy-run\ScreenMirror\
```

បើកកម្មវិធីដោយ៖

```powershell
.\dist-easy-run\ScreenMirror\ScreenMirror.exe
```

Build script ជំនួសថត output នោះ និងធ្វើបច្ចុប្បន្នភាព shortcut `ScreenMirror` លើ Desktop។ សូមបិទកម្មវិធី packaged មុន build ម្តងទៀត។ បើចែកចាយ សូម archive ថត `ScreenMirror` ទាំងមូល; កុំចែកចាយតែ `.exe`។

## ភ្ជាប់ Android លើកដំបូង

ការដំឡើងកម្មវិធីមិនទាន់អនុញ្ញាត Android device ដោយស្វ័យប្រវត្តិទេ។ បើក Developer options និង USB debugging លើទូរស័ព្ទ ភ្ជាប់វា ហើយទទួលយក authorization prompt។ សម្រាប់ wireless pairing សូមប្រើ host/port និង pairing code ម្តងប្រើដែលបង្ហាញលើ Wireless debugging របស់ទូរស័ព្ទ។ សូមមើល [មគ្គុទ្ទេសក៍ប្រើប្រាស់](USER_GUIDE_KM.md) សម្រាប់ជំហានពេញលេញ។

## បើកម្មវិធីមិនចាប់ផ្តើម

- ពិនិត្យថា source tree ពេញលេញ និងបានដំឡើង dependencies ក្នុង `.venv` ត្រឹមត្រូវ។
- ដំណើរការ `python -m screenmirror.main` ពី PowerShell ដើម្បីឃើញ Python startup errors។
- សម្រាប់ package សូមទុក `_internal` នៅជាមួយ `ScreenMirror.exe`; បើឯកសារខ្វះ ស្រាយ archive ទាំងមូលម្តងទៀត។
- ប្រើទំព័រ Diagnostics ដើម្បីមើល ADB/scrcpy paths, versions និងសារថ្មីៗ។
- បើ ADB រកមិនឃើញ USB device សូមពិនិត្យខ្សែ USB, debugging authorization និង Windows device driver ដែលត្រូវការ។

## អាជ្ញាបណ្ណ

GitHub repository ដែលបានផ្តល់មាន `LICENSE` ប្រភេទ MIT។ ADB និង scrcpy ដែលភ្ជាប់មកជាមួយមាន notice/license របស់ខ្លួនផងដែរ។ សូមរក្សា និងពិនិត្យ notice ដែលអនុវត្ត មុនចែកចាយបន្ត។
