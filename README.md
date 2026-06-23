# Smart Flashcard Generator - Backend API

A RESTful API built with FastAPI and Python that powers the Smart Flashcard Generator. It handles user authentication, processes study notes using local NLP models, and manages flashcard sets in MongoDB.

---

## Option Chosen

Option A: Smart Flashcard Generator

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI |
| Language | Python 3.10+ |
| Database | MongoDB Atlas (free tier) via PyMongo |
| Authentication | JWT (python-jose) + bcrypt password hashing (passlib) |
| NLP - Sentence Parsing | spaCy (en_core_web_sm) |
| NLP - Question Generation | Hugging Face Transformers (T5 model) |
| Server | Uvicorn (ASGI) |

---

## Project Structure

```
flashcard-backend/
├── main.py                  # App entry point, CORS middleware, router registration
├── db.py                    # MongoDB connection and collection references
├── .env                     # Environment variables (not committed to git)
├── requirements.txt         # Python dependencies
├── test_api.py              # Pytest test suite
├── routes/
│   ├── __init__.py
│   ├── auth.py              # POST /auth/signup, POST /auth/login
│   └── flashcards.py        # Flashcard generation, retrieval, and review endpoints
└── nlp/
    ├── __init__.py
    └── generator.py         # Core NLP logic using spaCy and T5
```

---

## How the AI/ML Component Works

The flashcard generation pipeline has two stages:

**Stage 1 - Sentence Extraction (spaCy)**

The input text is parsed using spaCy's English language model (`en_core_web_sm`). The parser splits the text into sentences and filters out sentences shorter than 40 characters, keeping only meaningful, information-dense sentences suitable for flashcard generation.

**Stage 2 - Question Generation (T5 Transformer)**

Each extracted sentence is treated as an answer. It is passed into a T5 model fine-tuned specifically for answer-aware question generation (`mrm8488/t5-base-finetuned-question-generation-ap`). The model generates a natural language question for each sentence. The input format is:

```
answer: <sentence> context: <full text>
```

The model outputs a question, which is paired with the original sentence to form a flashcard. A maximum of 8 cards are generated per set to keep response times acceptable on CPU.

Both models run entirely locally inside the FastAPI process. No external AI API is used.

**Spaced Repetition**

When a user reviews a set, cards marked as "not known" are placed before cards marked as "known" in the review order. This ensures weaker cards are encountered first in every session.

---

## API Endpoints

### Auth

| Method | Endpoint | Description |
|---|---|---|
| POST | /auth/signup | Register with email and password. Returns JWT. |
| POST | /auth/login | Login with email and password. Returns JWT. |

### Flashcards

| Method | Endpoint | Description |
|---|---|---|
| POST | /flashcards/generate | Generate flashcards from notes. Requires JWT. |
| GET | /flashcards/sets | Get all flashcard sets for logged-in user. Requires JWT. |
| GET | /flashcards/review/{set_id} | Get cards ordered for review (not_known first). Requires JWT. |
| PATCH | /flashcards/card/{set_id} | Mark a card as known or not_known. Requires JWT. |

All protected endpoints require the header:
```
Authorization: Bearer <token>
```

---

## Database Schema

**users collection**
```json
{
  "_id": "ObjectId",
  "email": "string",
  "password": "bcrypt hash",
  "created_at": "ISO datetime string"
}
```

**flashcard_sets collection**
```json
{
  "_id": "ObjectId",
  "user_id": "string",
  "title": "string",
  "created_at": "ISO datetime string",
  "cards": [
    {
      "question": "string",
      "answer": "string",
      "status": "not_known | known",
      "review_count": 0
    }
  ]
}
```

---

## Local Setup

### 1. Clone the repository and navigate to the backend folder

```bash
cd flashcard-backend
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 4. Configure environment variables

Create a `.env` file in the root of the backend folder:

```
MONGODB_URI=mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/flashcards?retryWrites=true&w=majority
JWT_SECRET=your_secret_key_here
```

Replace the MongoDB URI with your own Atlas connection string.

### 5. Start the development server

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.
Interactive API documentation is available at `http://localhost:8000/docs`.

---

## Running Tests

### Install test dependencies

```bash
pip install pytest httpx
```

### Run all tests

```bash
pytest test_api.py -v
```

### Run a specific test class

```bash
pytest test_api.py::TestSignup -v
pytest test_api.py::TestLogin -v
pytest test_api.py::TestGenerateFlashcards -v
pytest test_api.py::TestReview -v
pytest test_api.py::TestUpdateCard -v
```

Tests use mocked MongoDB collections and a mocked NLP generator, so they run without a live database connection or model download.

---

## Requirements File

Create `requirements.txt` with these contents:

```
fastapi
uvicorn
pymongo
python-jose[cryptography]
passlib[bcrypt]
bcrypt==4.0.1
spacy
transformers
torch
sentencepiece
protobuf
tiktoken
python-dotenv
pytest
httpx
```

---

## Deployment (Render)

1. Push the backend folder to a public GitHub repository
2. Go to render.com and create a new Web Service
3. Connect your GitHub repository
4. Set the following:
   - Build Command: `pip install -r requirements.txt && python -m spacy download en_core_web_sm`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables in Render dashboard:
   - `MONGODB_URI` - your Atlas connection string
   - `JWT_SECRET` - your secret key
6. Deploy

Note: The first request after deployment will be slow as the T5 model downloads to Render's cache. Subsequent requests will be faster.

---

## Security Notes

- Passwords are hashed using bcrypt before storage. Plain text passwords are never stored.
- JWT tokens expire after 7 days.
- The `.env` file is excluded from version control via `.gitignore`.
- MongoDB Atlas IP access is set to `0.0.0.0/0` to support Render's dynamic IPs on the free tier.
