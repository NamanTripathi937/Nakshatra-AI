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

### 2. Install Dependencies

**Backend:**
```bash
cd backend
pip install -r requirements.txt
cd ..
```

**Frontend:**
```bash
cd frontend
npm install
cd ..
```

### 3. Set Environment Variables

Create `.env` file in `backend/`:
```env
GROQ_API_KEY=your_groq_api_key_here
MONGODB_URI=mongodb://localhost:27017/
```

Create `.env.local` file in `frontend/`:
```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your_google_client_id_here
NEXT_PUBLIC_ADSENSE_CLIENT_ID=ca-pub-your_adsense_client_id_here
NEXT_PUBLIC_ADSENSE_CHAT_BANNER_SLOT=your_banner_slot_id_here
NEXT_PUBLIC_ADSENSE_CHAT_INTERSTITIAL_SLOT=your_interstitial_slot_id_here
```

### 4. Run the Application

**Option 1 - Single Command (Recommended):**
```bash
# Using npm (recommended - organized output)
npm start

# OR using shell script
./start.sh
```

**Option 2 - Separate Terminals:**
```bash
# Terminal 1 - Backend
cd backend
uvicorn main:app --reload

# Terminal 2 - Frontend
cd frontend
npm run dev
```

---

## 🌐 Deployment

### Deploying on Render (Backend)

* Root directory: `backend`
* Start command:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Frontend

* Host on Vercel or Render static site

Ensure the `NEXT_PUBLIC_BACKEND` is updated with the deployed backend URL.

---

## 📚 Example Usage

1. Fill in birth details
2. Start chatting with the AI
3. Ask anything from daily predictions to marriage compatibility

---

## 🙏 Acknowledgements

* LangChain
* Groq
* FastAPI
* Next

---

## 📄 License

MIT License

---

Built with ❤️ by Naman Tripathi
