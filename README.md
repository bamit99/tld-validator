# TLD Validator API & Web Interface

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Framework](https://img.shields.io/badge/Framework-FastAPI-green.svg)](https://fastapi.tiangolo.com/)

A comprehensive, self-hosted web application for validating Top-Level Domains (TLDs) against the official IANA list. It features a clean web UI, a secure RESTful API, and a local SQLite database for persistence.

![Screenshot of TLD Validator](placeholder.png)  <!-- Placeholder for a project screenshot -->

---

## ✨ Features

- ✅ **Real-time TLD Validation**: Checks against the latest IANA TLD list.
- ✅ **Responsive Web UI**: Simple interface for manual domain and TLD validation.
- ✅ **Secure RESTful API**: All endpoints are protected with API key authentication.
- ✅ **Local-First**: Uses a local SQLite database for API keys and TLD caching. No external database required.
- ✅ **Automatic Data Updates**: Periodically fetches the latest TLD list from IANA (configurable).
- ✅ **Multi-level TLD Support**: Correctly identifies complex TLDs like `co.uk` and `com.au`.
- ✅ **Zero External Dependencies**: Only requires Python and an internet connection for IANA updates.

---

## 🛠️ Tech Stack

- **Backend**: Python, FastAPI, Uvicorn
- **Database**: SQLite
- **Frontend**: HTML, CSS, Vanilla JavaScript
- **HTTP Client**: httpx
- **Scheduling**: APScheduler

---

## 🚀 Getting Started

Follow these instructions to get a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

- Python 3.8+
- `pip` for package management

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/tld-validator.git
    cd tld-validator
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r backend/requirements.txt
    ```

4.  **Set up environment variables:**
    Create a `.env` file in the project root by copying the example:
    ```bash
    # No need to copy, the app will run with defaults if this file is not present.
    # You can create a .env file to override default settings.
    ```
    Default `.env` values:
    ```env
    PORT=8000
    HOST=0.0.0.0
    TLD_URL=https://data.iana.org/TLD/tlds-alpha-by-domain.txt
    TLD_UPDATE_INTERVAL_HOURS=24
    API_KEY_HEADER=X-API-Key
    DATABASE_PATH=./data/tld_cache.db
    ```

5.  **Run the application:**
    ```bash
    cd backend
    python app.py
    ```
    The application will be available at `http://localhost:8000`.

---

## 📖 API Documentation

All API endpoints (except `/api/generate-key` and `/api/health`) require an API key sent in the `X-API-Key` header.

### Authentication

1.  **Generate a Key**:
    ```bash
    curl -X POST http://localhost:8000/api/generate-key
    ```
    Response:
    ```json
    {
      "key": "YOUR_UNIQUE_API_KEY",
      "message": "API key generated successfully"
    }
    ```

2.  **Use the Key**: Include the key in the header of your requests.
    ```bash
    -H "X-API-Key: YOUR_UNIQUE_API_KEY"
    ```

### Endpoints

| Method | Endpoint                    | Description                                      |
| :----- | :-------------------------- | :----------------------------------------------- |
| `POST` | `/api/generate-key`         | Generate a new API key.                          |
| `POST` | `/api/validate-tld`         | Validate a TLD or a full domain name.            |
| `GET`  | `/api/validate-tld`         | Validate a TLD via query parameters.             |
| `GET`  | `/api/keys`                 | List all API keys and their usage stats.         |
| `GET`  | `/api/cache-info`           | Get the status of the TLD cache.                 |
| `GET`  | `/api/health`               | Check the health of the application.             |
| `POST` | `/api/update-tlds`          | Manually trigger an update of the TLD list.      |

#### Example: Validate a Domain

```bash
curl -X POST http://localhost:8000/api/validate-tld \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{"domain": "example.co.uk"}'
```

Response:
```json
{
  "is_valid": true,
  "message": "TLD 'CO.UK' is valid",
  "tld": "CO.UK",
  "domain": "example.co.uk"
}
```

---

## 📁 Project Structure

```
tld-validator/
├── backend/
│   ├── app.py              # FastAPI application entry point
│   ├── database.py         # SQLite database logic
│   ├── models.py           # Pydantic data models
│   ├── tld_service.py      # TLD fetching and validation logic
│   ├── auth_service.py     # API key generation and validation
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── index.html          # Main web interface
│   ├── styles.css          # CSS for the frontend
│   └── script.js           # JavaScript for UI interactivity
├── data/                   # (Auto-generated)
│   └── tld_cache.db        # SQLite database file
├── .env                    # (Optional) Environment variables
└── README.md               # This file
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue to discuss proposed changes.

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.
