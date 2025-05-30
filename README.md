# 🤖 AI-Powered College Admission Chatbot

A multilingual chatbot developed using **Python** and **FastAPI**,
designed to assist prospective students with college admission queries
by scraping and analyzing information from the official college website.

## 🚀 Features

- **Multilingual Support**: Handles queries in Tamil, Telugu, Hindi, and English.
- **Real-Time Web Scraping**: Fetches up-to-date information from the college website.
- **Natural Language Processing**: Understands and processes user queries effectively.
- **FastAPI Integration**: Ensures high performance and scalability.
- **Interactive API Documentation**: Accessible via Swagger UI.

## 🧰 Tech Stack

- **Programming Language**: Python
- **Framework**: FastAPI
- **Web Scraping**: BeautifulSoup, Requests
- **Language Detection**: langdetect
- **Translation**: Google Translate API
- **Deployment**: Uvicorn

## 📁 Project Structure

├── main.py # Entry point with FastAPI routes
├── chatbot_logic.py # Core NLP and response generation logic
├── scraper.py # Web scraping utilities
├── languages.py # Language detection and translation functions
├── requirements.txt # Project dependencies
└── README.md # Project documentation

bash
Copy
Edit

## 🖥️ Getting Started

1. **Clone the repository**:
   ```bash
   git clone https://github.com/NikhiL-140804/AI-powered-College-admiossion-chat-bot.git
   cd AI-powered-College-admiossion-chat-bot
Install dependencies:

bash
Copy
Edit
pip install -r requirements.txt
Run the application:

bash
Copy
Edit
uvicorn main:app --reload
Access the API documentation:
Open your browser and navigate to http://localhost:8000/docs

🔮 Future Enhancements
Implement user authentication and session management.

Deploy the application using Docker and cloud services.

Integrate advanced NLP models for improved query understanding.

Develop a frontend interface using React or Vue.js.

📬 Contact
Nikhil MVR
📧 Email: 11229a024@kanchiuniv.ac.in
🔗 LinkedIn: https://www.linkedin.com/in/nikhil-mvr-366b0835a/
