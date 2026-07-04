# AI-Powered Data Analysis Platform using Natural Language Querying

A full-stack AI platform that enables users to upload datasets and query them in plain English — no SQL knowledge required. The system converts natural language questions into optimised SQL queries using Groq LLM, executes them, and returns results with AI-generated insights and interactive visualisations.

🔗 **Live Demo:** [https://nl-data-platform.vercel.app](https://nl-data-platform.vercel.app)  
📂 **GitHub:** [https://github.com/Harish-S28/nl-data-platform](https://github.com/Harish-S28/nl-data-platform)

---

## Features

- 📁 Upload datasets in CSV, Excel (.xlsx), or JSON format
- 🔍 Ask questions in plain English — e.g. *"What is the total revenue by product?"*
- 🤖 Groq LLM (LLaMA 3.3 70B) converts questions into optimised DuckDB SQL
- 🛡️ SQL safety validation — blocks dangerous queries (DROP, DELETE, INSERT, etc.)
- 📊 Auto-generated visualisations — bar, line, and pie charts based on results
- 💡 AI-generated business insights in plain English
- ⚡ Real-time query execution using DuckDB
- 🌐 Fully deployed and accessible from anywhere

---

## Tech Stack

### Backend
| Technology | Purpose |
|---|---|
| Python | Core backend language |
| FastAPI | REST API framework |
| DuckDB | Embedded analytical database |
| Pandas | ETL pipeline and data processing |
| Groq API (LLaMA 3.3 70B) | NL to SQL generation and insight generation |
| Uvicorn | ASGI server |
| python-dotenv | Environment variable management |

### Frontend
| Technology | Purpose |
|---|---|
| React | UI framework |
| Vite | Build tool |
| Recharts | Data visualisation (bar, line, pie charts) |

### Deployment
| Platform | Purpose |
|---|---|
| Render | Backend hosting |
| Vercel | Frontend hosting |
| GitHub | Version control and CI/CD |

---

## How It Works

```
User uploads CSV/Excel/JSON
        ↓
ETL Pipeline (detect delimiter, clean columns, infer types)
        ↓
Data loaded into DuckDB table
        ↓
User asks question in plain English
        ↓
Schema + question sent to Groq LLM
        ↓
LLM generates SQL query
        ↓
Safety validation (SELECT only, no DDL/DML)
        ↓
Query executed on DuckDB
        ↓
Results sent to LLM → Business insight generated
        ↓
Frontend displays: Insight + SQL + Chart + Table
```

---

## Project Structure

```
nl-data-platform/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app entry point
│   │   ├── config.py        # Groq client and config
│   │   ├── db.py            # DuckDB connection and helpers
│   │   ├── etl.py           # File ingestion and schema detection
│   │   ├── nl_to_sql.py     # NL to SQL conversion and insight generation
│   │   └── routers/
│   │       ├── upload.py    # Upload endpoint
│   │       └── query.py     # Query endpoint
│   ├── requirements.txt
│   ├── Procfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main React component
│   │   ├── App.css          # Styles
│   │   └── index.css        # Global styles and design tokens
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
└── vercel.json
```

---

## Getting Started (Run Locally)

### Prerequisites
- Python 3.10+
- Node.js 18+
- Groq API key (free at [https://console.groq.com](https://console.groq.com))

### Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
```

Create a `.env` file inside the `backend` folder:
```
GROQ_API_KEY=gsk_your_actual_key_here
```

Start the backend:
```bash
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

Open a second terminal:
```bash
cd frontend
npm install
npm run dev
```

Open your browser at **http://localhost:5173**

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Health check |
| POST | `/api/upload` | Upload a dataset file |
| GET | `/api/tables` | List all uploaded tables |
| POST | `/api/query` | Ask a question in plain English |
| DELETE | `/api/tables` | Clear all uploaded tables |

---

## Environment Variables

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Your Groq API key (required) |
| `GROQ_MODEL` | Model to use (default: `llama-3.3-70b-versatile`) |

---

## Screenshots

> Upload a dataset → Ask a question → Get insights, SQL, and charts instantly.

---

## Author

**Harish S**  
[GitHub](https://github.com/Harish-S28)

---

## License

This project is open source and available under the [MIT License](LICENSE).
