# 🌾 Agricultural AI — المستشار الزراعي الذكي

> تطبيق ويب متكامل للاستشارات الزراعية الذكية مدعوم بـ OpenAI API  
> A full-stack intelligent agricultural advisory web app powered by OpenAI API

---

## ✨ المميزات / Features

- 🤖 **استشارات زراعية ذكية** — نموذج GPT متخصص في الزراعة
- 💬 **واجهة دردشة تفاعلية** — تصميم حديث وسهل الاستخدام
- 🌐 **دعم اللغة العربية** — الواجهة والردود باللغة العربية
- 🗄️ **تخزين المحادثات** — قاعدة بيانات SQLite لحفظ السجل
- 📜 **سجل المحادثات** — استعراض وحذف المحادثات السابقة
- 🔒 **اتصال آمن بـ OpenAI** — إدارة المفاتيح عبر متغيرات البيئة
- 📱 **تصميم استجابي** — يعمل على الجوال والحاسوب
- 🐳 **جاهز لـ Docker** — نشر سريع باستخدام Docker Compose

---

## 🏗️ البنية / Project Structure

```
agricultural-ai/
├── backend/                    # Python + FastAPI
│   ├── main.py                 # نقطة دخول التطبيق
│   ├── config.py               # إعدادات التطبيق
│   ├── database.py             # إعداد SQLite
│   ├── models.py               # نماذج قاعدة البيانات
│   ├── routes/
│   │   ├── chat.py             # مسارات الدردشة
│   │   └── history.py          # مسارات السجل
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── frontend/                   # React
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── App.jsx
│   │   ├── index.js
│   │   ├── components/
│   │   │   ├── ChatWindow.jsx
│   │   │   ├── MessageList.jsx
│   │   │   └── InputField.jsx
│   │   ├── pages/
│   │   │   └── HomePage.jsx
│   │   ├── services/
│   │   │   └── api.js
│   │   └── styles/
│   │       ├── global.css
│   │       └── chat.css
│   ├── package.json
│   └── .env.example
├── docker-compose.yml
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🚀 التشغيل السريع / Quick Start

### المتطلبات / Prerequisites

- Python 3.10+
- Node.js 18+
- OpenAI API Key — [احصل عليه هنا](https://platform.openai.com/api-keys)

---

### 1️⃣ Backend (FastAPI)

```bash
cd backend

# تثبيت المكتبات
pip install -r requirements.txt

# إنشاء ملف البيئة
cp .env.example .env
# عدّل .env وأضف مفتاح OpenAI الخاص بك

# تشغيل الخادم
python main.py
# أو
uvicorn main:app --reload
```

الخادم يعمل على: `http://localhost:8000`  
توثيق API: `http://localhost:8000/docs`

---

### 2️⃣ Frontend (React)

```bash
cd frontend

# تثبيت المكتبات
npm install

# إنشاء ملف البيئة
cp .env.example .env

# تشغيل التطبيق
npm start
```

التطبيق يعمل على: `http://localhost:3000`

---

### 3️⃣ Docker Compose (الطريقة الموصى بها)

```bash
# أنشئ ملف .env في جذر المشروع
echo "OPENAI_API_KEY=sk-your-key-here" > .env

# شغّل التطبيق
docker-compose up --build
```

---

## ⚙️ متغيرات البيئة / Environment Variables

### Backend (`backend/.env`)

| المتغير | الوصف | الافتراضي |
|---------|-------|-----------|
| `OPENAI_API_KEY` | مفتاح OpenAI API | **مطلوب** |
| `DATABASE_URL` | رابط قاعدة البيانات | `sqlite:///./agricultural_ai.db` |
| `ALLOWED_ORIGINS` | النطاقات المسموح بها (CORS) | `http://localhost:3000` |
| `OPENAI_MODEL` | نموذج OpenAI | `gpt-3.5-turbo` |
| `MAX_TOKENS` | الحد الأقصى للرموز | `1000` |

### Frontend (`frontend/.env`)

| المتغير | الوصف | الافتراضي |
|---------|-------|-----------|
| `REACT_APP_API_URL` | رابط Backend API | `http://localhost:8000` |

---

## 📡 API Endpoints

| Method | Endpoint | الوصف |
|--------|----------|-------|
| `POST` | `/api/chat` | إرسال رسالة والحصول على رد |
| `GET` | `/api/history` | قائمة جميع المحادثات |
| `GET` | `/api/history/{id}` | تفاصيل محادثة محددة |
| `DELETE` | `/api/history/{id}` | حذف محادثة |
| `GET` | `/health` | فحص صحة الخادم |

---

## 🛠️ التقنيات المستخدمة / Tech Stack

| الطبقة | التقنية |
|--------|---------|
| Backend | Python 3.11, FastAPI, SQLAlchemy |
| AI | OpenAI GPT (gpt-3.5-turbo) |
| Database | SQLite |
| Frontend | React 18, Axios |
| Containerization | Docker, Docker Compose |

---

## 📄 الترخيص / License

MIT License — استخدم هذا المشروع بحرية.
