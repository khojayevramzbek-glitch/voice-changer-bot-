# 🎙 Telegram Voice Changer Bot

Siz yuborgan ovozli xabarlarni (voice), audio fayllarni va yumaloq video xabarlarni qiziqarli ovoz effektlariga o'zgartirib beruvchi Telegram bot!

---

## 🎭 Mavjud Ovoz Effektlari:
- 🐿 **Chipmunk (Burunduk / Sincap)** — O'ta kulgili ingichka tez ovoz
- 👽 **Alien (O'zga sayyoralik)** — Kosmik titroq va robotik effekt
- 🤖 **Robot (Kiborg)** — Mexanik metall ovoz
- 👹 **Monster (Maxluq)** — Chuqur qalin qo'rqinchli bas ovoz
- 🎈 **Geliy gazi (Helium)** — Geliy sharidan nafas olgandek ingichka ovoz
- 🏔 **Aks-sado (Echo / G'or)** — Katta gumbaz yoki g'or aks-sadosi
- 📻 **Ratsiya (Walkie-Talkie)** — Politsiya/harbiy ratsiyasi
- ☎️ **Eski telefon** — 90-yillar uy telefoni effekti
- ⚡ **Tezlashtirish (1.5x)** — Tezkor nutq
- 🐢 **Sekinlashtirish (0.7x)** — Sekin va og'ir nutq
- 🔄 **Orqaga (Reverse)** — Ovozni teskari o'qish
- 🎧 **8D Ovoz (Aylanma)** — Quloqchinlarda aylanib turuvchi ovoz

---

## 🚀 Botni ishga tushirish:

### 1-qadam: Bot Token olish
1. Telegramda [@BotFather](https://t.me/BotFather) botiga kiring.
2. `/newbot` buyrug'ini yuboring va botingizga nom hamda username bering.
3. BotFather sizga bergan **API Token**ni nusxalab oling (masalan: `1234567890:ABCdefGhIJKlmNoPQRsTUVwxyZ`).

### 2-qadam: Tokenni `.env` fayliga yozish
Loyiha papkasidagi `.env` faylini oching va bot tokeningizni kiriting:
```env
BOT_TOKEN=1234567890:ABCdefGhIJKlmNoPQRsTUVwxyZ
```

### 3-qadam: Botni ishga tushirish
* `run.bat` fayliga 2 marta bosing (yoki terminalda `python bot.py` buyrug'ini bering).

---

## 📁 Loyiha tuzilishi:
- `bot.py` — Botning asosiy boshqaruvi va Telegram hodisalari
- `audio_processor.py` — FFmpeg orqali ovoz effektlarini qo'llash moduli
- `keyboards.py` — Chiroyli inline tugmalar menyusi
- `config.py` — Sozlamalar va .env yuklagich
- `run.bat` — Windows uchun 1-bosishda ishga tushiruvchi fayl
- `requirements.txt` — Python kutubxonalari
