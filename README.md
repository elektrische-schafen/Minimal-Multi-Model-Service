# Minimal-Multi-Model-Service

A demo application for Multi-Model service analyzing images using AI-powered services. This project consists of a FastAPI backend that processes up to 4 images simultaneously and a Streamlit frontend for user interaction.

## 🚀 Features

- **Multi-Image Analysis**: Analyze up to 4 images in a single request
- **AI-Powered**: Integrated with Gemini and Groq APIs for advanced image processing
- **PostgreSQL Database**: Robust data storage and management
- **Real-time Processing**: Fast API responses with health monitoring
- **User-friendly Interface**: Clean Streamlit frontend for easy interaction

## 🏗️ Architecture

- **Backend**: FastAPI with Python 3.10+
- **Frontend**: Streamlit web application
- **Database**: PostgreSQL
- **AI Services**: Gemini API, Groq API
- **Server**: Uvicorn ASGI server

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.10 or higher
- PostgreSQL database
- Git (for cloning the repository)

## 🛠️ Installation & Setup

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd <your-repository-name>
```

### 2. Environment Setup

#### Create Virtual Environment

**On Linux/macOS:**
```bash
python -m venv env
source env/bin/activate
```

**On Windows:**
```bash
python -m venv env
env\Scripts\activate
```

#### Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Database Configuration

Ensure PostgreSQL is installed and running on your system. Create a database for the application:

```sql
CREATE DATABASE yourdbname;
CREATE USER yourdbuser WITH PASSWORD 'yourdbpassword';
GRANT ALL PRIVILEGES ON DATABASE yourdbname TO yourdbuser;
```

### 4. Environment Variables

Create a `.env` file in the backend folder with the following configuration:

```env
# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=yourdbname
POSTGRES_USER=yourdbuser
POSTGRES_PASSWORD=yourdbpassword

# API Keys
GEMINI_API=your_gemini_api_key
GROQ_API=your_groq_api_key
```

**⚠️ Important**: 
- Replace the placeholder values with your actual database credentials
- Obtain API keys from [Google AI Studio](https://makersuite.google.com/app/apikey) for Gemini
- Get your Groq API key from [Groq Console](https://console.groq.com/)

## 🚀 Running the Application

### Backend Server

Start the FastAPI backend server:

```bash
uvicorn Backend:app --reload
```

The backend will be available at: `http://127.0.0.1:8000`

**Available Endpoints:**
- `POST /v1/items/analyze` - Analyze up to 4 images
- `GET /v1/status` - Check API health status

### Frontend Application

In a new terminal (with the same virtual environment activated), start the Streamlit frontend:

```bash
streamlit run frontend.py
```

The frontend will be available at: `http://localhost:8501`

## 📡 API Documentation

### Analyze Images Endpoint

**Endpoint:** `POST /v1/items/analyze`

**Description:** Analyzes up to 4 uploaded images using AI services.

**Request Format:**
- Content-Type: `multipart/form-data`
- Maximum 4 image files supported

**Response Format:**
```json
{
    "status":200,
    "id":"300206a8-8691-11f0-bf1f-902b34d046b2",
    "attributes":{
        "category":"dress",
        "brand":"CLAUDIE PIERLOT",
        "color":"white",
        "material":"82% Triacetate, 18% Polyester blend",
        "condition":"like_new",
        "style":"shift dress with short sleeves, round neck, and scalloped hem",
        "gender":"female",
        "season":"spring/summer",
        "pattern":"solid",
        "sleeve_length":"short sleeve",
        "neckline":"round neck",
        "closure_type":"zipper",
        "fit":"regular"
        },
    "model_info":{
        "gemini":{
            "model":"gemini-2.5-flash",
            "latency_ms":7109.92,
            "attributes":["category","brand","material","condition","style","gender","season","pattern","fit"]
                },
        "cloud":{
            "model":"Google Cloud Vision",
            "latency_ms":8615.98,
            "attributes":["color"]
                },
        "llama":{
            "model":"meta-llama/llama-4-scout-17b-16e-instruct",
            "latency_ms":3945.62,
            "attributes":["sleeve_length","neckline","closure_type"]
               }
        },
    "processing":{
        "status":"200 Success",
        "total_latency_ms":19671.52,
        "per_model_latency":{
            "gemini":7109.92,
            "cloud":8615.98,
            "llama":3945.62
                            }
                }
}
```

### Health Check Endpoint

**Endpoint:** `GET /v1/status`

**Description:** Returns the current health status of the API.

**Response Format:**
```json
{
    "status": "ok",
    "message": "API is running smoothly",
    "version": "1.0.0"
}
```

## 🔧 Configuration

### Database Settings

Modify the database configuration in your `.env` file:

```env
POSTGRES_HOST=your_host        # Default: localhost
POSTGRES_PORT=your_port        # Default: 5432
POSTGRES_DB=your_database_name
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
```

### API Configuration

Configure your AI service API keys:

```env
GEMINI_API=your_gemini_api_key_here
GROQ_API=your_groq_api_key_here
```
