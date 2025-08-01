# 🌌 Nakshatra AI

Nakshatra AI is an intelligent Vedic astrology chatbot that provides personalized Kundali-based insights using your birth details. Built using LangChain, FastAPI, and React, it merges traditional Indian astrology with state-of-the-art generative AI to deliver meaningful guidance and interactive conversations.

---

## 🔧 Tech Stack

### Frontend

* Next.js
* Tailwind CSS
* Rest API

### Backend

* FastAPI (Python)
* LangChain + Groq
* LangChain Memory
* Uvicorn

---

## 📅 Features

* 🔍 Input your name, date/time/place of birth to generate your Kundali
* 🧠 LangChain memory allows the chatbot to remember and refer to user details till the user converses .
* 👥 Chat naturally with an AI astrologer for insights based on your astrological chart
* 🚀 Deployable easily using platforms like Render or Vercel
* ⏳ Frontend handles loading, API errors, and user feedback gracefully

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/NamanTripathi937/Nakshatra-AI.git
cd Nakshatra-AI
```

### 2. Backend Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

> Set your `OPENAI_API_KEY` as an environment variable in the backend.

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

> Add a `.env` file inside `frontend/`:

```env
VITE_BACKEND_URL=http://localhost:8000
```

---

## 🌐 Deployment

### Deploying on Render (Backend)

* Root directory: `backend`
* Start command:

```bash
uvicorn main:app --host 0.0.0.0 --port 10000
```

### Frontend

* Host on Vercel or Render static site

Ensure the `VITE_BACKEND_URL` is updated with the deployed backend URL.

---

## 📚 Example Usage

1. Fill in birth details
2. Start chatting with the AI
3. Ask anything from daily predictions to marriage compatibility

---

## 🙏 Acknowledgements

* LangChain
* OpenAI
* FastAPI
* React

---

## 📄 License

MIT License

---

Built with ❤️ by Naman Tripathi
