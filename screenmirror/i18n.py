"""English and Khmer text used by the ScreenMirror interface."""

from __future__ import annotations

import re
from collections.abc import Iterable

from PySide6.QtGui import QFontDatabase


SUPPORTED_LANGUAGES = ("en", "km")
LANGUAGE_NAMES = {"en": "English", "km": "ខ្មែរ"}


_KHMER = {
    "Dashboard": "ផ្ទាំងគ្រប់គ្រង",
    "Devices": "ឧបករណ៍",
    "Mirroring": "ឆ្លុះអេក្រង់",
    "Screenshots": "រូបថតអេក្រង់",
    "Recordings": "ការថត",
    "Diagnostics": "ព័ត៌មានវិនិច្ឆ័យ",
    "Settings": "ការកំណត់",
    "About": "អំពីកម្មវិធី",
    "Native scrcpy engine\nADB device manager": "ម៉ាស៊ីន scrcpy ដើម\nកម្មវិធីគ្រប់គ្រង ADB",
    "ADB · Starting": "ADB · កំពុងចាប់ផ្តើម",
    "{count} devices": "{count} ឧបករណ៍",
    "↻  Refresh": "↻  ធ្វើបច្ចុប្បន្នភាព",
    "Starting…": "កំពុងចាប់ផ្តើម…",
    "Checking ADB service…": "កំពុងពិនិត្យសេវា ADB…",
    "Your Android workspace": "កន្លែងគ្រប់គ្រង Android របស់អ្នក",
    "Checking…": "កំពុងពិនិត្យ…",
    "Stopped": "បានបញ្ឈប់",
    "ADB service": "សេវា ADB",
    "Ready devices": "ឧបករណ៍ត្រៀមរួច",
    "Selected device": "ឧបករណ៍ដែលបានជ្រើស",
    "No device selected": "មិនទាន់ជ្រើសឧបករណ៍",
    "Manage devices": "គ្រប់គ្រងឧបករណ៍",
    "Mirror profile": "ទម្រង់ឆ្លុះអេក្រង់",
    "Native video decoding and rendering are handled by scrcpy.": "scrcpy ជាអ្នកបកស្រាយ និងបង្ហាញវីដេអូដោយផ្ទាល់។",
    "Open mirroring controls": "បើកការគ្រប់គ្រងការឆ្លុះអេក្រង់",
    "Connection status": "ស្ថានភាពការតភ្ជាប់",
    "USB and wireless Android devices discovered by the host-matched ADB executable.": "ឧបករណ៍ Android តាម USB និង wireless ដែល ADB សម្រាប់ប្រព័ន្ធនេះរកឃើញ។",
    "Start ADB server": "ចាប់ផ្តើម ADB server",
    "Stop ADB server": "បញ្ឈប់ ADB server",
    "Disconnect selected": "ផ្តាច់ឧបករណ៍ដែលបានជ្រើស",
    "Available devices": "ឧបករណ៍ដែលមាន",
    "No Android devices detected. Connect by USB, enable USB debugging, and authorize this computer on the phone.": "រកមិនឃើញឧបករណ៍ Android ទេ។ ភ្ជាប់តាម USB បើក USB Debugging ហើយអនុញ្ញាតកុំព្យូទ័រនេះលើទូរស័ព្ទ។",
    "Wireless ADB": "ADB តាម Wireless",
    "Pairing code": "លេខកូដផ្គូផ្គង",
    "Host and port": "ម៉ាស៊ីន និង port",
    "Pair device": "ផ្គូផ្គងឧបករណ៍",
    "Connect": "ភ្ជាប់",
    "Mirror directly in scrcpy’s native window. OBS can capture that window independently.": "បង្ហាញការឆ្លុះអេក្រង់ក្នុងបង្អួច scrcpy ដោយផ្ទាល់។ OBS អាចថតបង្អួចនោះដោយឡែក។",
    "Session": "សម័យប្រើប្រាស់",
    "Start mirroring": "ចាប់ផ្តើមឆ្លុះអេក្រង់",
    "Stop session": "បញ្ឈប់សម័យ",
    "Selected device: none": "ឧបករណ៍ដែលបានជ្រើស៖ គ្មាន",
    "Current mirror profile": "ទម្រង់ឆ្លុះអេក្រង់បច្ចុប្បន្ន",
    "Audio is enabled; decoder selection and input methods use scrcpy defaults unless explicitly changed in Advanced Settings.": "សំឡេងបានបើក។ ការជ្រើស decoder និងវិធីបញ្ជាប្រើតម្លៃដើមរបស់ scrcpy លុះត្រាតែបានប្តូរក្នុងការកំណត់កម្រិតខ្ពស់។",
    "Edit profile": "កែទម្រង់",
    "Edit mirror profile": "កែទម្រង់ឆ្លុះអេក្រង់",
    "Advanced settings": "ការកំណត់កម្រិតខ្ពស់",
    "scrcpy capability status": "ស្ថានភាពសមត្ថភាព scrcpy",
    "Capability discovery is starting…": "កំពុងចាប់ផ្តើមស្វែងរកសមត្ថភាព…",
    "Capture a PNG from the selected Android device using asynchronous ADB output.": "ថតរូប PNG ពីឧបករណ៍ Android ដែលបានជ្រើស ដោយប្រើ ADB មិនរារាំងកម្មវិធី។",
    "Capture": "ថតរូប",
    "Save screenshot…": "រក្សាទុករូបថតអេក្រង់…",
    "Recent captures this session": "រូបថតថ្មីៗក្នុងសម័យនេះ",
    "Screenshots saved during this session will appear here. No files are scanned or assumed.": "រូបថតអេក្រង់ដែលបានរក្សាទុកក្នុងសម័យនេះនឹងបង្ហាញនៅទីនេះ។ កម្មវិធីមិនស្កេន ឬសន្មត់អំពីឯកសារផ្សេងទេ។",
    "Recording is performed by scrcpy at session launch. ScreenMirror does not capture or convert video frames.": "scrcpy ជាអ្នកថតនៅពេលចាប់ផ្តើមសម័យ។ ScreenMirror មិនថត ឬបម្លែងស៊ុមវីដេអូទេ។",
    "Recording destination": "ទីតាំងរក្សាទុកការថត",
    "No recording library exists yet; this page reports only the destination configured for future mirror sessions.": "មិនទាន់មានបណ្ណាល័យគ្រប់គ្រងការថតទេ។ ទំព័រនេះបង្ហាញតែទីតាំងដែលកំណត់សម្រាប់សម័យឆ្លុះអេក្រង់បន្ទាប់។",
    "Configure recording and mirror profile": "កំណត់ការថត និងទម្រង់ឆ្លុះអេក្រង់",
    "Live service information and bounded application diagnostics.": "ព័ត៌មានសេវាកម្មបច្ចុប្បន្ន និងកំណត់ហេតុវិនិច្ឆ័យដែលមានកំណត់។",
    "Environment": "បរិស្ថាន",
    "ADB not found": "រកមិនឃើញ ADB",
    "ADB version: Not checked": "កំណែ ADB៖ មិនទាន់ពិនិត្យ",
    "scrcpy version: Discovering…": "កំណែ scrcpy៖ កំពុងស្វែងរក…",
    "Recent messages": "សារថ្មីៗ",
    "Application preferences are saved using the existing ScreenMirror settings store.": "ចំណូលចិត្តកម្មវិធីត្រូវបានរក្សាទុកក្នុងកន្លែងកំណត់របស់ ScreenMirror។",
    "Mirror defaults": "តម្លៃលំនាំដើមសម្រាប់ការឆ្លុះអេក្រង់",
    "Configure discovered scrcpy options": "កំណត់ជម្រើស scrcpy ដែលបានរកឃើញ",
    "Android device management and native screen mirroring": "ការគ្រប់គ្រងឧបករណ៍ Android និងការឆ្លុះអេក្រង់ដោយផ្ទាល់",
    "Python and PySide6 manage the desktop interface and ADB operations. scrcpy remains an independent native process for video decoding, rendering, and input.": "Python និង PySide6 គ្រប់គ្រងផ្ទាំងកម្មវិធី និងប្រតិបត្តិការ ADB។ scrcpy ដំណើរការដាច់ដោយឡែក ដើម្បីបកស្រាយ និងបង្ហាញវីដេអូ ព្រមទាំងទទួលការបញ្ជា។",
    "OBS Studio can capture the native scrcpy window without a second Python capture pipeline.": "OBS Studio អាចថតបង្អួច scrcpy ដោយផ្ទាល់ ដោយមិនចាំបាច់មានប្រព័ន្ធថតវីដេអូ Python មួយទៀត។",
    "ADB executable: {path}": "កម្មវិធី ADB៖ {path}",
    "ADB version: {version}": "កំណែ ADB៖ {version}",
    "scrcpy version: {version}": "កំណែ scrcpy៖ {version}",
    "scrcpy {version} ready · {count} options discovered from bundled help.": "scrcpy {version} រួចរាល់ · រកឃើញជម្រើស {count} ពីឯកសារជំនួយដែលបានភ្ជាប់មកជាមួយ។",
    "scrcpy {version} capabilities ready.": "សមត្ថភាព scrcpy {version} រួចរាល់។",
    "ADB · Attention": "ADB · ត្រូវការពិនិត្យ",
    "ADB · Active": "ADB · សកម្ម",
    "ADB · Stopped": "ADB · បានបញ្ឈប់",
    "ADB · Ready": "ADB · រួចរាល់",
    "Active": "សកម្ម",
    "Ready": "រួចរាល់",
    "{ready} ready · {total} found": "រួចរាល់ {ready} · រកឃើញ {total}",
    "{count} ready": "រួចរាល់ {count}",
    "{count} found": "រកឃើញ {count}",
    "Android device": "ឧបករណ៍ Android",
    "Wireless": "Wireless",
    "USB / local": "USB / ក្នុងម៉ាស៊ីន",
    "Connected": "បានភ្ជាប់",
    "Unauthorized": "មិនទាន់អនុញ្ញាត",
    "Offline": "មិននៅលើបណ្តាញ",
    "Authorized and ready": "បានអនុញ្ញាត និងរួចរាល់",
    "Not ready · {state}": "មិនទាន់រួចរាល់ · {state}",
    "Selected device: {model} · {serial}": "ឧបករណ៍ដែលបានជ្រើស៖ {model} · {serial}",
    "Selected device: {model} · {serial} · {state}": "ឧបករណ៍ដែលបានជ្រើស៖ {model} · {serial} · {state}",
    "{serial}   ·   {transport}": "{serial}   ·   {transport}",
    "transport {value}": "transport {value}",
    "Connect an Android device and select it in Devices.": "ភ្ជាប់ឧបករណ៍ Android រួចជ្រើសវានៅក្នុងផ្នែក ឧបករណ៍។",
    "Select an authorized device in Devices first.": "សូមជ្រើសឧបករណ៍ដែលបានអនុញ្ញាតនៅក្នុងផ្នែក ឧបករណ៍ ជាមុនសិន។",
    "Selected: {model} · {readiness}": "បានជ្រើស៖ {model} · {readiness}",
    "Select a device before disconnecting.": "សូមជ្រើសឧបករណ៍មុនពេលផ្តាច់។",
    "Select an authorized, ready device before taking a screenshot.": "សូមជ្រើសឧបករណ៍ដែលបានអនុញ្ញាត និងរួចរាល់ មុនពេលថតរូបអេក្រង់។",
    "Save Android screenshot": "រក្សាទុករូបថតអេក្រង់ Android",
    "PNG image (*.png)": "រូបភាព PNG (*.png)",
    "Open file": "បើកឯកសារ",
    "Select a device before starting mirroring.": "សូមជ្រើសឧបករណ៍មុនពេលចាប់ផ្តើមឆ្លុះអេក្រង់។",
    "Device is not authorized or ready: {state}": "ឧបករណ៍មិនទាន់បានអនុញ្ញាត ឬមិនទាន់រួចរាល់៖ {state}",
    "Maximum resolution": "កម្រិតបង្ហាញអតិបរមា",
    "Maximum frame rate": "អត្រាស៊ុមអតិបរមា",
    "Video bitrate": "អត្រាប៊ីតវីដេអូ",
    "Video codec": "កូដិកវីដេអូ",
    "Forward device audio when supported": "បញ្ជូនសំឡេងពីឧបករណ៍ បើមានការគាំទ្រ",
    "Start fullscreen": "ចាប់ផ្តើមជារបៀបពេញអេក្រង់",
    "Keep device awake": "កុំឲ្យឧបករណ៍ចូលសម្រាក",
    "Turn device screen off while mirroring": "បិទអេក្រង់ឧបករណ៍ពេលកំពុងឆ្លុះ",
    "Optional .mp4 or .mkv output path": "ទីតាំងឯកសារលទ្ធផល .mp4 ឬ .mkv (ស្រេចចិត្ត)",
    "Browse…": "រកមើល…",
    "Record this session": "ថតសម័យនេះ",
    "Settings apply when the next scrcpy session starts. Recording is handled natively by scrcpy.": "ការកំណត់នឹងមានប្រសិទ្ធភាពនៅពេលចាប់ផ្តើម scrcpy លើកក្រោយ។ scrcpy ជាអ្នកដំណើរការការថតដោយផ្ទាល់។",
    "Save": "រក្សាទុក",
    "Cancel": "បោះបង់",
    "Record mirrored screen": "ថតអេក្រង់ដែលកំពុងឆ្លុះ",
    "MP4 video (*.mp4);;MKV video (*.mkv)": "វីដេអូ MP4 (*.mp4);;វីដេអូ MKV (*.mkv)",
    "{size}p max  ·  {fps} FPS  ·  {bitrate}  ·  {codec}  ·  Audio {audio}": "អតិបរមា {size}p  ·  {fps} FPS  ·  {bitrate}  ·  {codec}  ·  សំឡេង {audio}",
    "on": "បើក",
    "off": "បិទ",
    "Stay awake: {state} · Fullscreen: {fullscreen}": "កុំឲ្យចូលសម្រាក៖ {state} · ពេញអេក្រង់៖ {fullscreen}",
    "No recording destination configured": "មិនទាន់កំណត់ទីតាំងរក្សាទុកការថត",
    "Advanced scrcpy settings": "ការកំណត់ scrcpy កម្រិតខ្ពស់",
    "scrcpy capabilities are still loading.": "កំពុងផ្ទុកសមត្ថភាព scrcpy។",
    "scrcpy {version} · {count} supported options": "scrcpy {version} · ជម្រើសដែលគាំទ្រ {count}",
    "Exact command preview": "មើលពាក្យបញ្ជាពិតប្រាកដ",
    "Clear advanced overrides": "សម្អាតការកំណត់ជំនួសកម្រិតខ្ពស់",
    "Copy command": "ចម្លងពាក្យបញ្ជា",
    "Invalid settings: {error}": "ការកំណត់មិនត្រឹមត្រូវ៖ {error}",
    "Saved {count} advanced settings for scrcpy {version}.": "បានរក្សាទុកការកំណត់កម្រិតខ្ពស់ {count} សម្រាប់ scrcpy {version}។",
    "value; validate against scrcpy help": "តម្លៃ; សូមផ្ទៀងផ្ទាត់តាមជំនួយរបស់ scrcpy",
    "Error": "កំហុស",
    "ADB is shutting down.": "ADB កំពុងបិទ។",
    "Host-matched ADB executable was not found.": "រកមិនឃើញកម្មវិធី ADB ដែលត្រូវនឹងប្រព័ន្ធនេះទេ។",
    "ADB is busy; wait for the current operation to finish.": "ADB កំពុងរវល់។ សូមរង់ចាំឲ្យប្រតិបត្តិការបច្ចុប្បន្នបញ្ចប់។",
    "Unknown process error.": "មានកំហុសដំណើរការដែលមិនស្គាល់។",
    "ADB version verified.": "បានផ្ទៀងផ្ទាត់កំណែ ADB។",
    "ADB server started.": "បានចាប់ផ្តើម ADB server។",
    "ADB server stopped.": "បានបញ្ឈប់ ADB server។",
    "Wireless connection requires host:port.": "ការតភ្ជាប់ Wireless ត្រូវការ host:port។",
    "Wireless pairing requires host:port and a pairing code.": "ការផ្គូផ្គង Wireless ត្រូវការ host:port និងលេខកូដផ្គូផ្គង។",
    "Disconnect requires a device serial.": "ការផ្តាច់ត្រូវការលេខសម្គាល់ serial របស់ឧបករណ៍។",
    "Screenshot requires a device serial.": "ការថតរូបអេក្រង់ត្រូវការលេខសម្គាល់ serial របស់ឧបករណ៍។",
    "A screenshot is already in progress.": "កំពុងថតរូបអេក្រង់រួចហើយ។",
    "Screenshot timed out after 60 seconds.": "ការថតរូបអេក្រង់អស់ពេលក្រោយពី 60 វិនាទី។",
    "Screenshot failed": "ការថតរូបអេក្រង់បានបរាជ័យ",
    "ADB returned invalid PNG screenshot data.": "ADB បានផ្តល់ទិន្នន័យរូបថត PNG មិនត្រឹមត្រូវ។",
    "Screenshot process failed.": "ដំណើរការថតរូបអេក្រង់បានបរាជ័យ។",
    "scrcpy executable was not found.": "រកមិនឃើញកម្មវិធី scrcpy ទេ។",
    "scrcpy help output contained no recognizable options.": "មិនអាចស្គាល់ជម្រើសណាមួយក្នុងព័ត៌មានជំនួយរបស់ scrcpy បានទេ។",
    "scrcpy capabilities are unavailable.": "មិនមានព័ត៌មានសមត្ថភាព scrcpy ទេ។",
    "scrcpy is shutting down.": "scrcpy កំពុងបិទ។",
    "A scrcpy session is already running.": "មានសម័យ scrcpy កំពុងដំណើរការរួចហើយ។",
    "A device serial is required to start mirroring.": "ត្រូវការលេខសម្គាល់ serial របស់ឧបករណ៍ ដើម្បីចាប់ផ្តើមឆ្លុះអេក្រង់។",
    "Unsupported video codec value.": "តម្លៃកូដិកវីដេអូមិនត្រូវបានគាំទ្រទេ។",
    "Maximum size must be between 240 and 8192 pixels.": "កម្រិតបង្ហាញអតិបរមាត្រូវនៅចន្លោះ 240 និង 8192 pixels។",
    "Maximum FPS must be between 1 and 240.": "FPS អតិបរមាត្រូវនៅចន្លោះ 1 និង 240។",
    "Bitrate must be a positive number, optionally ending in K or M (for example 8M).": "អត្រាប៊ីតត្រូវជាចំនួនវិជ្ជមាន ហើយអាចបញ្ចប់ដោយ K ឬ M (ឧទាហរណ៍ 8M)។",
    "Recording destination must include a file extension, such as .mp4.": "ទីតាំងរក្សាទុកការថតត្រូវមានផ្នែកបន្ថែមឯកសារ ដូចជា .mp4។",
    "This scrcpy executable does not support device serial selection.": "កម្មវិធី scrcpy នេះមិនគាំទ្រការជ្រើសឧបករណ៍តាម serial ទេ។",
    "The bundled scrcpy does not support {codec}.": "scrcpy ដែលបានភ្ជាប់មកជាមួយមិនគាំទ្រ {codec} ទេ។",
    "--port must be a numeric port or an ascending numeric port range (1-65535).": "តម្លៃ --port ត្រូវជាលេខ port ឬជាចន្លោះ port លេខដែលកើនឡើង (1-65535)។",
    "scrcpy capability discovery failed.": "ការស្វែងរកសមត្ថភាព scrcpy បានបរាជ័យ។",
    "Maximum FPS": "FPS អតិបរមា",
    "Language": "ភាសា",
    "English": "English",
    "Khmer": "ខ្មែរ",
    "Choose the language used by ScreenMirror.": "ជ្រើសភាសាដែល ScreenMirror ប្រើ។",
    "Screenshot saved: {path}": "បានរក្សាទុករូបថតអេក្រង់៖ {path}",
    "Mirror settings saved. They apply to the next session.": "បានរក្សាទុកការកំណត់ឆ្លុះអេក្រង់។ វានឹងមានប្រសិទ្ធភាពនៅសម័យបន្ទាប់។",
    "scrcpy mirroring started.": "បានចាប់ផ្តើមឆ្លុះអេក្រង់ដោយ scrcpy។",
    "scrcpy mirroring stopped.": "បានបញ្ឈប់ការឆ្លុះអេក្រង់ដោយ scrcpy។",
}


_MESSAGE_PREFIXES = (
    ("Could not start ADB command: ", "មិនអាចចាប់ផ្តើមពាក្យបញ្ជា ADB បានទេ៖ "),
    ("ADB process error: ", "កំហុសដំណើរការ ADB៖ "),
    ("ADB version check failed: ", "ការពិនិត្យកំណែ ADB បានបរាជ័យ៖ "),
    ("Could not start ADB server: ", "មិនអាចចាប់ផ្តើម ADB server បានទេ៖ "),
    ("Could not stop ADB server: ", "មិនអាចបញ្ឈប់ ADB server បានទេ៖ "),
    ("Could not list devices: ", "មិនអាចរាយបញ្ជីឧបករណ៍បានទេ៖ "),
    ("Could not connect to ", "មិនអាចភ្ជាប់ទៅកាន់ "),
    ("Could not pair with ", "មិនអាចផ្គូផ្គងជាមួយ "),
    ("Could not start screenshot process: ", "មិនអាចចាប់ផ្តើមដំណើរការថតរូបអេក្រង់បានទេ៖ "),
    ("Could not save screenshot: ", "មិនអាចរក្សាទុករូបថតអេក្រង់បានទេ៖ "),
    ("Could not run scrcpy: ", "មិនអាចដំណើរការ scrcpy បានទេ៖ "),
    ("Could not start scrcpy: ", "មិនអាចចាប់ផ្តើម scrcpy បានទេ៖ "),
    ("Could not start scrcpy version discovery: ", "មិនអាចចាប់ផ្តើមស្វែងរកកំណែ scrcpy បានទេ៖ "),
    ("Could not start scrcpy help discovery: ", "មិនអាចចាប់ផ្តើមស្វែងរកជំនួយ scrcpy បានទេ៖ "),
    ("Device is not authorized or ready: ", "ឧបករណ៍មិនទាន់បានអនុញ្ញាត ឬមិនទាន់រួចរាល់៖ "),
    ("The bundled scrcpy does not support ", "scrcpy ដែលបានភ្ជាប់មកជាមួយមិនគាំទ្រ "),
    ("Invalid settings: ", "ការកំណត់មិនត្រឹមត្រូវ៖ "),
)

_MESSAGE_PATTERNS = (
    (
        re.compile(
            r"^ADB command '(?P<command>[^']*)' timed out after (?P<seconds>\d+) seconds\.$"
        ),
        "ពាក្យបញ្ជា ADB '{command}' អស់ពេលក្រោយពី {seconds} វិនាទី។",
    ),
    (
        re.compile(r"^Detected (?P<count>\d+) device\(s\)\.$"),
        "បានរកឃើញឧបករណ៍ {count}។",
    ),
    (
        re.compile(r"^Connected to (?P<target>.+)\.$"),
        "បានភ្ជាប់ទៅកាន់ {target}។",
    ),
    (
        re.compile(r"^Paired with (?P<target>.+)\.$"),
        "បានផ្គូផ្គងជាមួយ {target}។",
    ),
    (
        re.compile(r"^(?P<state>connected|already connected) to (?P<target>.+)$", re.I),
        "{state} to {target}",
    ),
    (
        re.compile(r"^Successfully paired to (?P<target>.+)$", re.I),
        "បានផ្គូផ្គងដោយជោគជ័យទៅកាន់ {target}",
    ),
    (
        re.compile(
            r"^scrcpy (?P<stage>version|help) discovery timed out after (?P<seconds>\d+) seconds\.$"
        ),
        "ការស្វែងរក {stage} របស់ scrcpy អស់ពេលក្រោយពី {seconds} វិនាទី។",
    ),
    (
        re.compile(r"^scrcpy (?P<stage>version|help) discovery failed\.$"),
        "ការស្វែងរក {stage} របស់ scrcpy បានបរាជ័យ។",
    ),
    (
        re.compile(
            r"^scrcpy exited with code (?P<code>-?\d+); see diagnostics for its output\.$"
        ),
        "scrcpy បានបិទដោយលេខកូដ {code}។ សូមពិនិត្យកំណត់ហេតុវិនិច្ឆ័យ។",
    ),
    (
        re.compile(
            r"^Video codec '(?P<codec>[^']+)' is not supported by this scrcpy build\.$"
        ),
        "scrcpy ជំនាន់នេះមិនគាំទ្រកូដិកវីដេអូ '{codec}' ទេ។",
    ),
    (
        re.compile(
            r"^The bundled scrcpy does not support (?P<codec>.+)\.$"
        ),
        "scrcpy ដែលបានភ្ជាប់មកជាមួយមិនគាំទ្រ {codec} ទេ។",
    ),
    (
        re.compile(r"^(?P<option>--[\w-]+) must be one of: (?P<choices>.+)\.$"),
        "ជម្រើស {option} ត្រូវមានតម្លៃមួយក្នុងចំណោម៖ {choices}។",
    ),
    (
        re.compile(r"^Duplicate setting for (?P<option>--[\w-]+)\.$"),
        "បានកំណត់ជម្រើស {option} ស្ទួនគ្នា។",
    ),
    (
        re.compile(
            r"^The installed scrcpy does not support required option (?P<option>--[\w-]+)\.$"
        ),
        "scrcpy ដែលបានដំឡើងមិនគាំទ្រជម្រើសចាំបាច់ {option} ទេ។",
    ),
    (
        re.compile(
            r"^Could not start scrcpy (?P<stage>\w+) discovery: (?P<detail>.+)$"
        ),
        "មិនអាចចាប់ផ្តើមស្វែងរក{stage} scrcpy បានទេ៖ {detail}",
    ),
    (
        re.compile(r"^Maximum size must be between (?P<minimum>\d+) and (?P<maximum>\d+) pixels\.$"),
        "កម្រិតបង្ហាញអតិបរមាត្រូវនៅចន្លោះ {minimum} និង {maximum} pixels។",
    ),
)

_SCRCPY_CATEGORIES = {
    "Audio": "សំឡេង",
    "Video": "វីដេអូ",
    "Camera": "កាមេរ៉ា",
    "Recording": "ការថត",
    "Connection": "ការតភ្ជាប់",
    "Window": "បង្អួច",
    "Input and Control": "ការបញ្ចូល និងការគ្រប់គ្រង",
    "Device": "ឧបករណ៍",
    "Advanced": "កម្រិតខ្ពស់",
}

_SCRCPY_BOOLEAN_DESCRIPTIONS = {
    "--always-on-top": "រក្សាបង្អួច scrcpy ឲ្យនៅពីលើបង្អួចផ្សេងទៀត",
    "--audio-dup": "ចម្លងសំឡេង ដោយថតសំឡេង និងបន្តចាក់លើឧបករណ៍",
    "--camera-high-speed": "បើករបៀបថតកាមេរ៉ាល្បឿនលឿន",
    "--camera-torch": "បើកភ្លើងពិលកាមេរ៉ានៅពេលចាប់ផ្តើម",
    "--select-usb": "ប្រើឧបករណ៍ USB ប្រសិនបើមានតែមួយ (ដូចជា adb -d)",
    "--disable-screensaver": "បិទ screensaver ខណៈ scrcpy កំពុងដំណើរការ",
    "--select-tcpip": "ប្រើឧបករណ៍ TCP/IP ប្រសិនបើមានតែមួយ (ដូចជា adb -e)",
    "--fullscreen": "ចាប់ផ្តើមជារបៀបពេញអេក្រង់",
    "--force-adb-forward": "កុំប្រើ adb reverse ដើម្បីភ្ជាប់ទៅឧបករណ៍",
    "--ignore-video-encoder-constraints": "មិនពិនិត្យសមត្ថភាពរបស់ video encoder ទេ",
    "--keep-active": "រក្សាអេក្រង់ឲ្យបើកដោយក្លែងសកម្មភាពអ្នកប្រើ",
    "--kill-adb-on-close": "បិទ ADB នៅពេល scrcpy បិទ",
    "--legacy-paste": "បញ្ចូលអត្ថបទពី clipboard កុំព្យូទ័រជាព្រឹត្តិការណ៍ចុចគ្រាប់ចុចពេលចុច Ctrl+v",
    "--list-apps": "បង្ហាញបញ្ជីកម្មវិធី Android ដែលបានដំឡើងលើឧបករណ៍",
    "--list-cameras": "បង្ហាញបញ្ជីកាមេរ៉ារបស់ឧបករណ៍",
    "--list-camera-sizes": "បង្ហាញទំហំថតដែលកាមេរ៉ាគាំទ្រ",
    "--list-displays": "បង្ហាញបញ្ជីអេក្រង់របស់ឧបករណ៍",
    "--list-encoders": "បង្ហាញបញ្ជី video encoder និង audio encoder ដែលឧបករណ៍គាំទ្រ",
    "--no-control": "បិទការបញ្ជាឧបករណ៍; អាចមើលអេក្រង់តែប៉ុណ្ណោះ",
    "--no-playback": "បិទការចាក់វីដេអូ និងសំឡេងលើកុំព្យូទ័រ",
    "--no-video-playback": "បិទការចាក់វីដេអូលើកុំព្យូទ័រ",
    "--no-audio": "បិទការបញ្ជូនសំឡេង",
    "--no-audio-playback": "បិទការចាក់សំឡេងលើកុំព្យូទ័រ",
    "--no-cleanup": "មិនលុប server binary ពីឧបករណ៍ និងមិនស្តារស្ថានភាពឧបករណ៍ក្រោយបិទទេ",
    "--no-clipboard-autosync": "បិទការធ្វើសមកាលកម្ម clipboard រវាងកុំព្យូទ័រ និងឧបករណ៍ដោយស្វ័យប្រវត្តិ",
    "--no-downsize-on-error": "មិនសាកល្បងម្តងទៀតដោយបន្ថយ resolution ពេល MediaCodec មានកំហុសទេ",
    "--no-key-repeat": "មិនបញ្ជូនព្រឹត្តិការណ៍ចុចគ្រាប់ចុចដដែលៗទេ",
    "--no-mipmaps": "បិទការប្រើ mipmaps ក្នុង OpenGL renderer",
    "--no-mouse-hover": "មិនបញ្ជូនចលនាកណ្ដុរដោយគ្មានការចុចទេ",
    "--no-power-on": "មិនបើកឧបករណ៍នៅពេលចាប់ផ្តើមទេ",
    "--no-terminal-title": "មិនធ្វើបច្ចុប្បន្នភាពចំណងជើង terminal ទេ",
    "--no-vd-destroy-content": "បិទជម្រើស virtual display ដែលលុបមាតិកាពេលដកចេញ",
    "--no-vd-system-decorations": "បិទការតុបតែងប្រព័ន្ធលើ virtual display",
    "--no-video": "បិទការបញ្ជូនវីដេអូ",
    "--no-window": "មិនបង្ហាញបង្អួច scrcpy ទេ",
    "--no-window-aspect-ratio-lock": "បិទការចាក់សោសមាមាត្របង្អួច",
    "--otg": "ប្រើរបៀប OTG ដើម្បីឲ្យក្តារចុច និងកណ្ដុរកុំព្យូទ័រធ្វើដូចជាភ្ជាប់ផ្ទាល់ទៅឧបករណ៍",
    "--power-off-on-close": "បិទអេក្រង់ឧបករណ៍ពេលបិទ scrcpy",
    "--prefer-text": "បញ្ចូលអក្សរ និងដកឃ្លាជាអត្ថបទ ជំនួសព្រឹត្តិការណ៍ចុចគ្រាប់ចុច",
    "--print-fps": "បង្ហាញចំនួន FPS ក្នុង console",
    "--raw-key-events": "បញ្ជូនតែព្រឹត្តិការណ៍ចុចគ្រាប់ចុច ហើយមិនបញ្ជូនព្រឹត្តិការណ៍អត្ថបទ",
    "--require-audio": "កុំបន្តតែវីដេអូ ប្រសិនបើការចាប់សំឡេងលើឧបករណ៍បរាជ័យ",
    "--turn-screen-off": "បិទអេក្រង់ឧបករណ៍ភ្លាមៗ",
    "--show-touches": "បង្ហាញទីតាំងប៉ះ ហើយស្តារស្ថានភាពដើមពេលបិទ",
    "--stay-awake": "រក្សាឧបករណ៍ឲ្យភ្ញាក់ ខណៈភ្ជាប់ទៅកុំព្យូទ័រ និង scrcpy កំពុងដំណើរការ",
    "--window-borderless": "ដកស៊ុមតុបតែងបង្អួចចេញ",
    "--flex-display": "ប្តូរទំហំ virtual display ឲ្យត្រូវនឹងបង្អួចជាបន្តបន្ទាប់",
}


def _catalog(language: str) -> dict[str, str]:
    return _KHMER if language == "km" else {}


def translate(text: str, language: str = "en", **values: object) -> str:
    translated = _catalog(language).get(text, text)
    if values:
        try:
            return translated.format(**values)
        except (KeyError, ValueError):
            return translated
    return translated


def translate_message(message: str, language: str = "en") -> str:
    if language != "km":
        return message
    translated = _KHMER.get(message)
    if translated is not None:
        return translated
    for pattern, template in _MESSAGE_PATTERNS:
        match = pattern.fullmatch(message)
        if match:
            values = match.groupdict()
            if values.get("stage"):
                values["stage"] = {
                    "version": "កំណែ",
                    "help": "ជំនួយ",
                }.get(values["stage"], values["stage"])
            if values.get("state"):
                values["state"] = (
                    "បានភ្ជាប់ទៅកាន់"
                    if values["state"].casefold() == "connected"
                    else "បានភ្ជាប់រួចហើយទៅកាន់"
                )
                return f"{values['state']} {values['target']}"
            try:
                return template.format(**values)
            except (KeyError, ValueError):
                return template
    for prefix, translated_prefix in _MESSAGE_PREFIXES:
        if message.startswith(prefix):
            return translated_prefix + message[len(prefix):]
    return message


def translate_scrcpy_category(category: str, language: str = "en") -> str:
    if language == "km":
        return _SCRCPY_CATEGORIES.get(category, category)
    return category


def translate_scrcpy_description(option: str, description: str, language: str = "en") -> str:
    if language == "km":
        return _SCRCPY_BOOLEAN_DESCRIPTIONS.get(option, description)
    return description


def font_family_for_language(
    language: str,
    families: Iterable[str] | None = None,
) -> str:
    installed = list(families) if families is not None else QFontDatabase.families()
    by_casefold = {family.casefold(): family for family in installed}
    preferred = (
        ("Khmer UI", "Noto Sans Khmer UI", "Noto Sans Khmer", "Segoe UI")
        if language == "km"
        else ("Segoe UI", "Arial")
    )
    for family in preferred:
        if family.casefold() in by_casefold:
            return by_casefold[family.casefold()]
    return preferred[-1]
