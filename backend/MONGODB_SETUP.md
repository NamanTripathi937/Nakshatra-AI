# MongoDB Setup for Nakshatra AI

## Overview
This project uses MongoDB to store:
- **Kundali Form Data**: User birth details and generated chart information
- **Chat History**: All conversations between users and the AI astrologer

## Database Structure

### Collections

#### 1. `kundli_data`
Stores birth chart information for each user session.

```javascript
{
  session_id: String,          // Unique session identifier
  full_name: String,           // User's full name
  birth_details: {             // Birth information
    fullName: String,
    year: Number,
    month: Number,
    date: Number,
    hours: Number,
    minutes: Number,
    seconds: Number,
    latitude: Number,
    longitude: Number,
    timezone: String,
    settings: {
      observation_point: String,
      ayanamsha: String
    }
  },
  kundli_result: Object,       // Generated astrological chart data
  created_at: DateTime         // Timestamp
}
```

#### 2. `chat_history`
Stores all chat messages between users and the AI.

```javascript
{
  session_id: String,          // Unique session identifier
  role: String,                // 'user' or 'assistant'
  message: String,             // Message content
  timestamp: DateTime          // Message timestamp
}
```

## Setup Instructions

### Option 1: Local MongoDB (Development)

1. **Install MongoDB**
   - macOS: `brew install mongodb-community`
   - Ubuntu: `sudo apt-get install mongodb`
   - Windows: Download from [MongoDB Download Center](https://www.mongodb.com/try/download/community)

2. **Start MongoDB**
   ```bash
   # macOS/Linux
   brew services start mongodb-community
   # or
   mongod --dbpath /path/to/data/directory
   ```

3. **Configure Environment**
   ```bash
   # In backend/.env
   MONGODB_URI=mongodb://localhost:27017/
   ```

### Option 2: MongoDB Atlas (Production)

1. **Create MongoDB Atlas Account**
   - Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
   - Create a free cluster

2. **Get Connection String**
   - Click "Connect" on your cluster
   - Choose "Connect your application"
   - Copy the connection string

3. **Configure Environment**
   ```bash
   # In backend/.env
   MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
   ```

4. **Whitelist IP Address**
   - In Atlas, go to Network Access
   - Add your IP address or allow access from anywhere (0.0.0.0/0)

## Environment Variables

Create a `.env` file in the backend directory:

```env
# Groq API Configuration
GROQ_API_KEY=your_groq_api_key_here

# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017/
# or for Atlas:
# MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
```

## Testing the Connection

1. **Start the backend server**
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

2. **Check logs**
   You should see: `Successfully connected to MongoDB: nakshatra_db`

3. **Test with MongoDB Compass** (Optional)
   - Download [MongoDB Compass](https://www.mongodb.com/products/compass)
   - Connect using your MONGODB_URI
   - View the `nakshatra_db` database and its collections

## Querying Data

### Using MongoDB Compass
- Connect to your database
- Browse collections: `kundli_data` and `chat_history`
- Use the built-in query builder

### Using MongoDB Shell
```bash
# Connect to local MongoDB
mongosh

# Switch to database
use nakshatra_db

# View all kundli records
db.kundli_data.find().pretty()

# View chat history for a session
db.chat_history.find({session_id: "your-session-id"}).pretty()

# Count total kundlis
db.kundli_data.countDocuments()

# Count total messages
db.chat_history.countDocuments()
```

### Using Python (pymongo)
```python
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["nakshatra_db"]

# Get all kundlis
kundlis = list(db.kundli_data.find())

# Get chat history for a session
chats = list(db.chat_history.find({"session_id": "your-session-id"}))

# Get recent kundlis
recent = list(db.kundli_data.find().sort("created_at", -1).limit(10))
```

## Data Privacy & Security

### Best Practices
1. **Use Environment Variables**: Never commit `.env` file with credentials
2. **Enable Authentication**: For production, enable MongoDB authentication
3. **Encrypt Connections**: Use SSL/TLS for MongoDB connections
4. **Regular Backups**: Set up automated backups for production data
5. **Index Optimization**: Add indexes for frequently queried fields

### Recommended Indexes
```javascript
// session_id index for faster queries
db.kundli_data.createIndex({ session_id: 1 })
db.chat_history.createIndex({ session_id: 1 })

// Timestamp index for sorting
db.kundli_data.createIndex({ created_at: -1 })
db.chat_history.createIndex({ timestamp: -1 })

// Compound index for session-based time queries
db.chat_history.createIndex({ session_id: 1, timestamp: -1 })
```

## Troubleshooting

### Connection Issues
- **Error: MongoNetworkError**
  - Check if MongoDB is running: `brew services list` (macOS)
  - Verify MONGODB_URI in `.env`
  - Check firewall settings

- **Authentication Failed**
  - Verify username/password in connection string
  - For Atlas, check Network Access whitelist

### Performance Issues
- Add indexes for frequently queried fields
- Use projection to limit returned fields
- Consider pagination for large result sets

## Migration & Maintenance

### Backup Data
```bash
# Export entire database
mongodump --db nakshatra_db --out /path/to/backup

# Export specific collection
mongoexport --db nakshatra_db --collection kundli_data --out kundli_backup.json
```

### Restore Data
```bash
# Restore entire database
mongorestore --db nakshatra_db /path/to/backup/nakshatra_db

# Import specific collection
mongoimport --db nakshatra_db --collection kundli_data --file kundli_backup.json
```

## Future Enhancements

1. **User Authentication**: Link kundli data to user accounts
2. **Data Analytics**: Track popular birth times, locations, queries
3. **Caching**: Implement Redis for frequently accessed kundli data
4. **Search**: Add full-text search on chat history
5. **Archival**: Move old data to archival storage
