# មគ្គុទ្ទេសក៍ប្រើ ScreenMirror

[English](USER_GUIDE.md) · [ខ្មែរ](USER_GUIDE_KM.md) · [ត្រឡប់ទៅ README](../README_KM.md)

មគ្គុទ្ទេសក៍នេះពិពណ៌នាប៊ូតុង និងមុខងារដែលមានក្នុងកម្មវិធី Windows បច្ចុប្បន្ន។ មិនទាន់បានផ្ទៀងផ្ទាត់ឥរិយាបថជាមួយ Android hardware ទេ; ការអនុញ្ញាតឧបករណ៍ និងជម្រើស scrcpy អាចខុសគ្នាតាមទូរស័ព្ទ និង Android version។

## 1. បើកកម្មវិធី

- ដំណើរការពី source៖ បើក virtual environment របស់ project រួចប្រើ `python -m screenmirror.main`។
- ដំណើរការពី Windows package៖ បើក `ScreenMirror.exe` ពីថត `ScreenMirror` ដែលបានស្រាយចេញពេញលេញ។
- ពេលចាប់ផ្តើម ScreenMirror ពិនិត្យ ADB ដែលត្រូវនឹង host និងស្វែងរកសមត្ថភាព scrcpy ដែលភ្ជាប់មកជាមួយ។ ទំព័រ Devices មានប៊ូតុងគ្រប់គ្រង ADB server និងធ្វើបច្ចុប្បន្នភាពឧបករណ៍។
- ដើម្បីប្តូរភាសា សូមបើក **Settings** ហើយជ្រើស **English** ឬ **ខ្មែរ**។ ជម្រើសនេះត្រូវបានរក្សាទុកសម្រាប់ពេលបើកក្រោយ។

## 2. ភ្ជាប់តាម USB

1. លើ Android បើក Developer options និង USB debugging។ ឈ្មោះ និងទីតាំងក្នុង Settings ខុសគ្នាតាមក្រុមហ៊ុនផលិត។
2. ភ្ជាប់ទូរស័ព្ទដោយខ្សែ USB ដែលបញ្ជូនទិន្នន័យបាន។
3. ដោះសោទូរស័ព្ទ ហើយទទួលយក USB debugging authorization prompt សម្រាប់កុំព្យូទ័រនេះ។ កុំអនុញ្ញាតកុំព្យូទ័រដែលមិនទុកចិត្ត។
4. បើក **Devices** ហើយចុច **Refresh** បើមិនឃើញទូរស័ព្ទ។ មុន mirror ឬថតរូប ឧបករណ៍ត្រូវមានស្ថានភាព ready/`device`។
5. ជ្រើសកាតឧបករណ៍។ Dashboard និងទំព័រ Mirroring បង្ហាញឧបករណ៍ដែលបានជ្រើស និងស្ថានភាពបច្ចុប្បន្ន។

ឧបករណ៍ខ្លះលើ Windows ត្រូវការ OEM USB driver។ ScreenMirror ភ្ជាប់ ADB tools មកជាមួយ ប៉ុន្តែមិនដំឡើង driver ជាក់លាក់របស់ទូរស័ព្ទទេ។

## 3. ភ្ជាប់តាម Wireless ADB

ប្រើតែបណ្តាញដែលអ្នកទុកចិត្ត។

1. លើទូរស័ព្ទ បើក **Wireless debugging** និងបើកផ្នែក pairing code។
2. ក្នុង **Devices → Wireless ADB** បញ្ចូល pairing endpoint (`host:port`) ដែលទូរស័ព្ទបង្ហាញ និង pairing code បច្ចុប្បន្ន។
3. ចុច **Pair device**។ ប្រអប់ code ត្រូវបានលាក់ និងលុបចេញមុនបញ្ជូនសំណើ។
4. បន្ទាប់ពី pair ជោគជ័យ សូមប្តូរ target ទៅ connection endpoint (`host:port`) ដែលទូរស័ព្ទបង្ហាញ រួចចុច **Connect**។ Pairing endpoint និង connection endpoint អាចប្រើ port ខុសគ្នា។
5. ធ្វើបច្ចុប្បន្នភាពបញ្ជីឧបករណ៍ ហើយជ្រើសឧបករណ៍ដែលបានភ្ជាប់។
6. ដើម្បីផ្តាច់ ជ្រើសឧបករណ៍ Wireless ហើយចុច **Disconnect selected**។

Pairing code ត្រូវបានលាក់ក្នុង ADB output ដែលកម្មវិធីចាប់បាន ប៉ុន្តែវាត្រូវបានផ្ញើទៅ ADB ជា process argument ហើយឧបករណ៍ពិនិត្យ process ក្នុងម៉ាស៊ីនអាចមើលឃើញក្នុងអំឡុងពេល command ដំណើរការ។ ជៀសវាងកុំព្យូទ័រ និងបណ្តាញដែលអ្នកមិនទុកចិត្ត។

## 4. ចាប់ផ្តើម និងបញ្ឈប់ការឆ្លុះអេក្រង់

1. ជ្រើសឧបករណ៍ដែលបានអនុញ្ញាតនៅក្នុង **Devices**។
2. បើក **Mirroring** ហើយចុច **Start mirroring**។
3. scrcpy នឹងបើកបង្អួច native ដាច់ដោយឡែក។ ប្រើបង្អួចនោះសម្រាប់មើលអេក្រង់ និងប្រើ input controls ដែល scrcpy គាំទ្រ។ ScreenMirror មិនបង្ហាញ video stream ក្នុងផ្ទាំងរបស់វាទេ។
4. ដើម្បីបញ្ឈប់ ចុច **Stop session** ក្នុង ScreenMirror ឬបិទបង្អួច scrcpy។

បច្ចុប្បន្នគាំទ្រតែមួយ scrcpy session ក្នុងពេលតែមួយ។ បើ Start មិនអាចចុចបាន សូមពិនិត្យថាបានជ្រើសឧបករណ៍ ready, ADB មិនកំពុងរវល់ និងមិនមាន session កំពុងដំណើរការ។

## 5. កំណត់ mirror profile

បើក **Edit profile** ពី Mirroring ឬ Settings។ Profile ស្តង់ដាររួមមាន៖

- resolution អតិបរមា (លំនាំដើម 720p)។
- frame rate អតិបរមា (លំនាំដើម 30 FPS)។
- video bitrate (លំនាំដើម 4M)។
- video codec ដែល scrcpy ភ្ជាប់មកជាមួយគាំទ្រ (លំនាំដើម H.264)។
- audio forwarding (បើកតាមលំនាំដើម)។
- fullscreen, keep-device-awake និង screen-off។
- ទីតាំងរក្សាទុក recording (ស្រេចចិត្ត)។

រក្សាទុកការកំណត់ មុនចាប់ផ្តើម session បន្ទាប់។ Advanced settings ត្រូវបានបង្កើតពី `--help` របស់ scrcpy ដែលបានភ្ជាប់មកជាមួយ; បង្ហាញតែជម្រើសដែលបានរកឃើញ។ ជម្រើសដែលមិនមានក្នុង scrcpy version ផ្សេងអាចមិនបង្ហាញ។

## 6. ថតរូបអេក្រង់

1. ជ្រើសឧបករណ៍ដែលបានអនុញ្ញាត និង ready។
2. បើក **Screenshots** ហើយចុច **Save screenshot…**។
3. ជ្រើសទីតាំងក្នុង Windows save dialog។
4. ScreenMirror ថត PNG ដោយប្រើ ADB ហើយបង្ហាញរូបថ្មីៗក្នុងសម័យកម្មវិធីបច្ចុប្បន្ន។ បញ្ជីនេះជាបណ្តោះអាសន្ន; កម្មវិធីមិនស្កេនឯកសារចាស់ ឬរក្សាបណ្ណាល័យ screenshot ទេ។

Native Windows file dialog អាចប្រើភាសាដែលបានកំណត់ក្នុង Windows។

## 7. កំណត់ការថតវីដេអូ

ក្នុង mirror profile បញ្ចូល ឬរកមើលទីតាំងឯកសារ `.mp4` ឬ `.mkv`។ បើមាន recording destination វានឹងបញ្ជូនទៅ scrcpy សម្រាប់ mirror session ថ្មីៗ។ ការថតចាប់ផ្តើមពេល session ចាប់ផ្តើម ហើយបញ្ចប់ពេល scrcpy session បញ្ឈប់; ScreenMirror មិនមាន live recording toggle ឬបម្លែងវីដេអូដោយខ្លួនឯងទេ។

លុប recording destination ក្នុង profile បើមិនចង់ឲ្យការថតអនុវត្តលើ session បន្ទាប់ៗ។ ការថតអាស្រ័យលើឧបករណ៍ និង scrcpy; មិនទាន់បានសាកល្បងជាមួយ Android hardware ទេ។

## 8. Diagnostics និងបិទកម្មវិធីដោយសុវត្ថិភាព

- បើក **Diagnostics** ដើម្បីមើល ADB executable, ADB version, scrcpy capability status, ឧបករណ៍ដែលបានជ្រើស និងសារថ្មីៗដែលមានកំណត់។
- ដើម្បីបិទធម្មតា សូមបិទបង្អួច ScreenMirror។ កម្មវិធីសម្របសម្រួលការបិទ ADB និង scrcpy ដោយ asynchronous មុនពេលចេញ។
- កុំលុប ឬផ្លាស់ទីឯកសារក្នុង `_internal` របស់ package ពេលកម្មវិធីកំពុងដំណើរការ។

សម្រាប់បញ្ហាការតភ្ជាប់ និងការចាប់ផ្តើម សូមមើល [FAQ](FAQ_KM.md)។
