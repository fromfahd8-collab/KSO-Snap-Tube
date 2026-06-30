# KSO SnapTube Turbo V2

محمل فيديوهات سريع بواجهة عربية RTL - Dark Mode

## خطوات البناء على Windows

### المتطلبات
- Windows 10/11 (64-bit)
- Python 3.11 أو أحدث — https://www.python.org/downloads/

### تشغيل البناء
1. افتح Command Prompt بصلاحيات **Administrator**
2. انتقل لمجلد المشروع:
   ```
   cd KSO_SnapTube_Turbo_V2
   ```
3. شغّل:
   ```
   build.bat
   ```
   سيقوم السكريبت تلقائياً بـ:
   - تثبيت Chocolatey
   - تثبيت FFmpeg و Aria2c
   - تثبيت متطلبات Python
   - بناء EXE بـ PyInstaller
   - إنشاء مثبت Setup.exe بـ Inno Setup

### الملف النهائي
```
installer_output\KSO_SnapTube_Turbo_V2_Setup.exe
```

## مميزات التطبيق

| الميزة | التفاصيل |
|--------|----------|
| واجهة | Dark Mode #0F0F0F + RTL عربي |
| البحث | YouTube + Playlists + روابط مباشرة |
| السرعة | aria2c -x16 -s16 + concurrent_fragment_downloads=8 |
| التوازي | ThreadPoolExecutor (1-8 تحميلات متزامنة) |
| الصيغة | MP4 أفضل جودة (bestvideo+bestaudio) |
| الاستكمال | يكمل التحميل لو انقطع |

## هيكل الملفات

```
KSO_SnapTube_Turbo_V2/
├── src/
│   ├── main.py          # الواجهة الرئيسية PyQt6
│   ├── downloader.py    # محرك التحميل yt-dlp + aria2c
│   └── searcher.py      # محرك البحث
├── build.bat            # سكريبت البناء الكامل
├── KSO_SnapTube_Turbo_V2.spec  # إعدادات PyInstaller
├── setup.iss            # إعدادات Inno Setup
└── requirements.txt     # متطلبات Python
```
