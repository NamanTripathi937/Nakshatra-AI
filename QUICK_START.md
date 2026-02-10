# Quick Start Commands

## 🚀 Development

Start both backend and frontend with a single command:

```bash
npm start
```

Or using the shell script:
```bash
./start.sh
```

This will start:
- ✅ Backend on http://localhost:8000
- ✅ Frontend on http://localhost:3000

Press `Ctrl+C` to stop all services.

## 📝 Other Useful Commands

### Backend Only
```bash
cd backend
uvicorn main:app --reload
```

### Frontend Only  
```bash
cd frontend
npm run dev
```

### View API Docs
```bash
# After starting backend, visit:
http://localhost:8000/docs
```

## 🛠️ Troubleshooting

**Port already in use:**
```bash
# Kill process on port 8000 (backend)
lsof -ti:8000 | xargs kill -9

# Kill process on port 3000 (frontend)
lsof -ti:3000 | xargs kill -9
```

**MongoDB not connected:**
```bash
# Start MongoDB locally
brew services start mongodb-community
```

**Python packages missing:**
```bash
cd backend
pip install -r requirements.txt
```

**Node packages missing:**
```bash
cd frontend
npm install
```
