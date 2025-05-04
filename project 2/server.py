from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
from pymongo import MongoClient
from dotenv import load_dotenv
import requests
from typing import Optional
import logging
import sys
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('server.log')
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure Google Gemini
api_key = os.environ.get('GOOGLE_API_KEY')
if not api_key:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

logger.info("Configuring Gemini API...")

class ChatRequest(BaseModel):
    message: str
    language: str = "english"

def generate_with_gemini(prompt: str) -> str:
    # Using gemini-2.0-flash model
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    headers = {
        'Content-Type': 'application/json'
    }
    data = {
        "contents": [{
            "parts":[{"text": prompt}]
        }],
        "safetySettings": [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 1024
        }
    }
    
    try:
        logger.info(f"Sending request to Gemini API with prompt length: {len(prompt)}")
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        # Log the raw response for debugging
        logger.info(f"Raw response: {response.text[:500]}")
        
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"Received response from Gemini API: {result.keys()}")
        
        if 'candidates' in result and len(result['candidates']) > 0:
            text = result['candidates'][0]['content']['parts'][0]['text']
            logger.info(f"Generated response length: {len(text)}")
            return text
        else:
            logger.warning("No valid response in Gemini API result")
            return "I apologize, but I couldn't generate a response. Please try again in a moment."
            
    except requests.exceptions.Timeout:
        logger.error("Timeout error calling Gemini API")
        return "I apologize, but the response is taking too long. Please try again."
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error calling Gemini API: {str(e)}")
        return "I apologize, but I'm having trouble connecting to the AI service. Please try again in a moment."
    except Exception as e:
        logger.error(f"Error calling Gemini API: {str(e)}")
        return "I apologize, but something went wrong. Please try again later."

app = FastAPI(
    title="SCSVMV University AI Assistant API",
    description="AI-powered assistant for SCSVMV University information",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize MongoDB client
try:
    mongo_client = MongoClient('mongodb://localhost:27017/')
    db = mongo_client['university_db']
    pages_collection = db['pages']
    # Test the connection
    mongo_client.server_info()
    logger.info("Successfully connected to MongoDB")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {str(e)}")
    raise

@app.get("/")
async def home():
    return {
        "status": "ok",
        "message": "SCSVMV University AI Assistant API",
        "endpoints": {
            "/docs": "Interactive API documentation",
            "/api/chat": "POST - Send messages to chat with the AI",
        }
    }

async def search_university_data(query: str) -> str:
    try:
        logger.info(f"Searching MongoDB with query: {query}")
        
        # Clean and normalize the query
        query = query.lower().strip()
        
        # If query is about faculty
        if 'faculty' in query:
            department = None
            if 'sanskrit' in query:
                department = 'sanskrit'
            elif 'cse' in query or 'computer' in query:
                department = 'computer science'
            # Add other departments as needed
            
            if department:
                # Search MongoDB for faculty information
                pipeline = [
                    {
                        "$match": {
                            "$text": {"$search": f"{department} department faculty professor"}
                        }
                    },
                    {
                        "$addFields": {
                            "score": {"$meta": "textScore"}
                        }
                    },
                    {
                        "$sort": {"score": -1}
                    },
                    {
                        "$limit": 3
                    }
                ]
                
                results = pages_collection.aggregate(pipeline)
                results_list = list(results)
                
                if not results_list:
                    return f"I apologize, but I couldn't find faculty information for the {department} department."
                
                # Process and format faculty information
                faculty_info = f"""╔══════════════════════════════════════╗
║ {department.upper()} DEPARTMENT FACULTY ║
╚══════════════════════════════════════╝

"""
                
                # Extract faculty information using regex patterns
                for doc in results_list:
                    content = doc.get('text_content', '')
                    
                    # Remove HTML tags
                    content = re.sub('<[^<]+?>', '', content)
                    
                    # Find faculty entries
                    faculty_entries = []
                    
                    # Pattern for faculty with designation
                    patterns = [
                        r'(Dr\.[^•\n]+(?:Professor|HOD)[^•\n]+)',
                        r'(Prof\.[^•\n]+(?:Professor|HOD)[^•\n]+)',
                        r'((?:Assistant|Associate|Head|Professor)[^•\n]+)'
                    ]
                    
                    for pattern in patterns:
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            entry = match.group(1).strip()
                            if entry and len(entry) > 10:  # Avoid very short matches
                                faculty_entries.append(entry)
                    
                    # Remove duplicates while preserving order
                    faculty_entries = list(dict.fromkeys(faculty_entries))
                    
                    # Format entries
                    for i, entry in enumerate(faculty_entries, 1):
                        faculty_info += f"[{i}] {entry}\n"
                
                if "faculty_entries" not in locals() or not faculty_entries:
                    return f"I apologize, but I couldn't extract faculty information for the {department} department."
                    
                return faculty_info
        
        # For other types of queries, use the existing search logic
        search_terms = query
        specific_terms = {
            'course': ['course', 'program', 'degree', 'specialization', 'branch'],
            'fee': ['fee', 'fees', 'cost', 'payment', 'charges', 'amount'],
            'admission': ['admission', 'entry', 'application', 'apply', 'entrance'],
            'faculty': ['faculty', 'professor', 'teacher', 'staff', 'hod', 'head'],
            'department': ['department', 'school', 'centre', 'center'],
            'hostel': ['hostel', 'accommodation', 'dormitory', 'residence'],
            'scholarship': ['scholarship', 'financial aid', 'assistance', 'support'],
            'placement': ['placement', 'job', 'career', 'recruitment', 'company'],
            'research': ['research', 'project', 'publication', 'journal', 'paper']
        }
        
        # Add relevant terms based on query content
        for category, terms in specific_terms.items():
            if any(term in query for term in terms):
                search_terms += f" {' '.join(terms)}"
                
        # Add department-specific terms if mentioned
        departments = {
            'cse': 'computer science engineering computing programming software',
            'ece': 'electronics communication engineering',
            'mechanical': 'mechanical engineering manufacturing production',
            'civil': 'civil engineering construction structural',
            'sanskrit': 'sanskrit vedanta vyakarana sahitya',
            'management': 'management business administration commerce mba',
            'science': 'physics chemistry mathematics biology'
        }
        
        for dept, terms in departments.items():
            if dept in query:
                search_terms += f" {terms}"

        logger.info(f"Enhanced search terms: {search_terms}")
        
        # Perform text search with improved scoring
        pipeline = [
            {
                "$match": {
                    "$text": {"$search": search_terms}
                }
            },
            {
                "$addFields": {
                    "score": {
                        "$multiply": [
                            {"$meta": "textScore"},
                            {
                                "$cond": [
                                    {"$in": [{"$toLower": "$url"}, ["courses", "admission", "faculty", "departments"]]},
                                    2,
                                    1
                                ]
                            }
                        ]
                    }
                }
            },
            {
                "$sort": {"score": -1}
            },
            {
                "$limit": 5
            }
        ]
        
        results = pages_collection.aggregate(pipeline)
        results_list = list(results)
        
        if not results_list:
            return "I apologize, but I couldn't find specific information for your query. Please try rephrasing your question or ask about a different topic."
        
        # Process and format results
        formatted_response = ""
        for doc in results_list:
            content = doc.get('text_content', '')
            url = doc.get('url', '')
            title = doc.get('title', '')
            
            # Extract relevant paragraphs
            paragraphs = content.split('\n')
            relevant_paragraphs = []
            
            for para in paragraphs:
                # Skip empty paragraphs
                if not para.strip():
                    continue
                    
                # Calculate relevance score for paragraph
                para_lower = para.lower()
                term_matches = sum(1 for term in search_terms.split() if term in para_lower)
                if term_matches > 0:
                    relevance_score = term_matches / len(search_terms.split())
                    relevant_paragraphs.append((para, relevance_score))
            
            # Sort by relevance and take top 3 most relevant paragraphs
            relevant_paragraphs.sort(key=lambda x: x[1], reverse=True)
            top_paragraphs = [p[0] for p in relevant_paragraphs[:3]]
            
            if top_paragraphs:
                formatted_response += f"\n🔍 From {title}:\n"
                formatted_response += "\n".join(top_paragraphs) + "\n"
        
        if not formatted_response:
            return "I apologize, but I couldn't find specific information for your query. Please try rephrasing your question or ask about a different topic."
            
        return formatted_response
        
    except Exception as e:
        logger.error(f"Error searching MongoDB: {str(e)}")
        return f"I apologize, but I encountered an error while searching. Please try again later."

async def generate_response(prompt: str, language: str = 'english') -> str:
    try:
        logger.info("Generating response with Gemini...")
        logger.info(f"Prompt length: {len(prompt)}")
        
        response = generate_with_gemini(prompt)
        if response:
            logger.info(f"Generated response length: {len(response)}")
            return response
        else:
            logger.warning("Empty response from Gemini")
            return "I apologize, but I couldn't generate a response. Please try rephrasing your question."
            
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while generating the response. Please try again later."
        )

@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        logger.info("Received chat request")
        user_message = request.message.lower().strip()
        language = request.language
        
        logger.info(f"Processing message: {user_message[:50]}... in {language}")
        
        if not user_message:
            raise HTTPException(status_code=400, detail="No message provided")
        
        # Common misspellings and variations
        greeting_variations = {
            'hi': ['hi', 'hai', 'hii', 'hiii', 'hey', 'hei', 'hello', 'helo', 'hllo', 'namaste', 'vanakkam', 'namaskar'],
            'contact': ['contact', 'contct', 'cotact', 'cantact', 'kontact', 'phone', 'phon', 'fone', 'email', 'e-mail', 'mail', 'adress', 'addres', 'location'],
            'course': ['course', 'corse', 'cours', 'coarse', 'program', 'programme', 'programm', 'degree', 'dgree'],
            'admission': ['admission', 'admision', 'addmission', 'admisn', 'admssn', 'entry', 'entery', 'joining'],
            'requirement': ['requirement', 'requirment', 'requirment', 'eligibility', 'eligable', 'eligible', 'qualification', 'qualify'],
            'fee': ['fee', 'fees', 'cost', 'payment', 'amount', 'charge', 'price'],
            'faculty': ['faculty', 'professor', 'teacher', 'lecturer', 'staff', 'department head', 'hod', 'dean']
        }
        
        # Helper function to check if message contains any variation
        def contains_variation(message, category):
            return any(var in message for var in greeting_variations[category])
        
        # Check for greetings with variations
        if any(var in user_message for var in greeting_variations['hi']):
            greeting_responses = {
                'tamil': 'வணக்கம்! SCSVMV பல்கலைக்கழக உதவியாளருக்கு வரவேற்கிறோம். நான் உங்களுக்கு எவ்வாறு உதவ முடியும்? நீங்கள் கேட்கலாம்:\n\n- படிப்புகள் பற்றி\n- சேர்க்கை தகவல்\n- தகுதி விவரங்கள்\n- கட்டண விவரங்கள்\n- தொடர்பு விவரங்கள்',
                'hindi': 'नमस्ते! SCSVMV विश्वविद्यालय सहायक में आपका स्वागत है। मैं आपकी कैसे मदद कर सकता हूं? आप पूछ सकते हैं:\n\n- पाठ्यक्रमों के बारे में\n- प्रवेश जानकारी\n- पात्रता विवरण\n- शुल्क विवरण\n- संपर्क विवरण',
                'telugu': 'నమస్కారం! SCSVMV విశ్వవిద్యాలయ సహాయకునికి స్వాగతం. నేను మీకు ఎలా సహాయం చేయగలను? మీరు అడగవచ్చు:\n\n- కోర్సుల గురించి\n- ప్రవేశ సమాచారం\n- అర్హత వివరాలు\n- ఫీజు వివరాలు\n- సంప్రదింపు వివరాలు',
                'english': 'Hello! Welcome to the SCSVMV University Assistant. How may I help you? You can ask about:\n\n- Available courses\n- Admission information\n- Eligibility details\n- Fee details\n- Contact information'
            }
            return JSONResponse(content={
                "response": greeting_responses.get(language, greeting_responses['english']),
                "status": "success"
            })

        # Check for contact information request with variations
        if contains_variation(user_message, 'contact'):
            contact_info = {
                'english': """
╔══════════════════════════════════════╗
║     SCSVMV UNIVERSITY CONTACTS       ║
╚══════════════════════════════════════╝

🎓 ACADEMIC DEPARTMENTS
----------------------
[1] ADMINISTRATIVE SECTION
    ☎️ Landline: <a href="tel:04427264293">(044) 27264293</a>
    📱 Mobile:   <a href="tel:6382337146">6382337146</a>
    📧 Email:    <a href="mailto:admin@kanchiuniv.ac.in">admin@kanchiuniv.ac.in</a>

[2] FINANCE SECTION
    ☎️ Landline: <a href="tel:04427264480">(044) 27264480</a>
    📱 Mobile:   <a href="tel:8098001628">8098001628</a>
    📧 Email:    <a href="mailto:finance@kanchiuniv.ac.in">finance@kanchiuniv.ac.in</a>

[3] COE SECTION
    ☎️ Landline: <a href="tel:04427264306">(044) 27264306</a>
    📱 Mobile:   <a href="tel:8838701172">8838701172</a>
    📧 Email:    <a href="mailto:examsection@kanchiuniv.ac.in">examsection@kanchiuniv.ac.in</a>

🛠️ SUPPORT SERVICES
------------------
[4] PURCHASE SECTION
    ☎️ Landline: <a href="tel:04427264308">(044) 27264308</a>
    📧 Email:    <a href="mailto:purchase@kanchiuniv.ac.in">purchase@kanchiuniv.ac.in</a>

🏠 STUDENT FACILITIES
-------------------
[5] MEN'S HOSTEL
    📱 Mobile:   <a href="tel:8838738227">8838738227</a>
    📧 Email:    <a href="mailto:hostels@kanchiuniv.ac.in">hostels@kanchiuniv.ac.in</a>

[6] WOMEN'S HOSTEL
    📱 Mobile:   <a href="tel:9344051473">9344051473</a>

[7] TRANSPORT SECTION
    📱 Mobile:   <a href="tel:8098001629">8098001629</a>
    📧 Email:    <a href="mailto:transport@kanchiuniv.ac.in">transport@kanchiuniv.ac.in</a>

⚕️ MEDICAL FACILITIES
-------------------
[8] AYURVEDA HOSPITAL
    ☎️ Landline: <a href="tel:04469189811">(044) 69189811</a>
    📱 Mobile:   <a href="tel:8098991630">8098991630</a>
    📧 Email:    <a href="mailto:sjsach@gmail.com">sjsach@gmail.com</a>

[9] AYURVEDA COLLEGE
    ☎️ Landline: <a href="tel:04469189800">(044) 69189800</a>
    📱 Mobile:   <a href="tel:8098001626">8098001626</a>
    📧 Email:    <a href="mailto:info@sjsach.org.in">info@sjsach.org.in</a>

🌐 Website: <a href="https://kanchiuniv.ac.in" target="_blank">https://kanchiuniv.ac.in</a>""",

                'tamil': """
╔═════════════════════════════════════╗
║    SCSVMV பல்கலைக்கழக தொடர்புகள்    ║
╚═════════════════════════════════════╝

🎓 கல்வித் துறைகள்
-----------------
[1] நிர்வாகப் பிரிவு
    ☎️ தொலைபேசி: <a href="tel:04427264293">(044) 27264293</a>
    📱 கைபேசி:   <a href="tel:6382337146">6382337146</a>
    📧 மின்னஞ்சல்: <a href="mailto:admin@kanchiuniv.ac.in">admin@kanchiuniv.ac.in</a>

[2] நிதிப் பிரிவு
    ☎️ தொலைபேசி: <a href="tel:04427264480">(044) 27264480</a>
    📱 கைபேசி:   <a href="tel:8098001628">8098001628</a>
    📧 மின்னஞ்சல்: <a href="mailto:finance@kanchiuniv.ac.in">finance@kanchiuniv.ac.in</a>

[3] தேர்வுப் பிரிவு
    ☎️ தொலைபேசி: <a href="tel:04427264306">(044) 27264306</a>
    📱 கைபேசி:   <a href="tel:8838701172">8838701172</a>
    📧 மின்னஞ்சல்: <a href="mailto:examsection@kanchiuniv.ac.in">examsection@kanchiuniv.ac.in</a>

🛠️ உதவி சேவைகள்
---------------
[4] கொள்முதல் பிரிவு
    ☎️ தொலைபேசி: <a href="tel:04427264308">(044) 27264308</a>
    📧 மின்னஞ்சல்: <a href="mailto:purchase@kanchiuniv.ac.in">purchase@kanchiuniv.ac.in</a>

🏠 மாணவர் வசதிகள்
----------------
[5] ஆண்கள் விடுதி
    📱 கைபேசி:   <a href="tel:8838738227">8838738227</a>
    📧 மின்னஞ்சல்: <a href="mailto:hostels@kanchiuniv.ac.in">hostels@kanchiuniv.ac.in</a>

[6] பெண்கள் விடுதி
    📱 கைபேசி:   <a href="tel:9344051473">9344051473</a>

[7] போக்குவரத்து பிரிவு
    📱 கைபேசி:   <a href="tel:8098001629">8098001629</a>
    📧 மின்னஞ்சல்: <a href="mailto:transport@kanchiuniv.ac.in">transport@kanchiuniv.ac.in</a>

⚕️ மருத்துவ வசதிகள்
-----------------
[8] ஆயுர்வேத மருத்துவமனை
    ☎️ தொலைபேசி: <a href="tel:04469189811">(044) 69189811</a>
    📱 கைபேசி:   <a href="tel:8098991630">8098991630</a>
    📧 மின்னஞ்சல்: <a href="mailto:sjsach@gmail.com">sjsach@gmail.com</a>

[9] ஆயுர்வேத கல்லூரி
    ☎️ தொலைபேசி: <a href="tel:04469189800">(044) 69189800</a>
    📱 கைபேசி:   <a href="tel:8098001626">8098001626</a>
    📧 மின்னஞ்சல்: <a href="mailto:info@sjsach.org.in">info@sjsach.org.in</a>

🌐 வலைத்தளம்: <a href="https://kanchiuniv.ac.in" target="_blank">https://kanchiuniv.ac.in</a>""",

                'hindi': """
╔═════════════════════════════════════╗
║    SCSVMV विश्वविद्यालय संपर्क सूची    ║
╚═════════════════════════════════════╝

🎓 शैक्षणिक विभाग
---------------
[1] प्रशासनिक विभाग
    ☎️ लैंडलाइन: <a href="tel:04427264293">(044) 27264293</a>
    📱 मोबाइल:  <a href="tel:6382337146">6382337146</a>
    📧 ईमेल:    <a href="mailto:admin@kanchiuniv.ac.in">admin@kanchiuniv.ac.in</a>

[2] वित्त विभाग
    ☎️ लैंडलाइन: <a href="tel:04427264480">(044) 27264480</a>
    📱 मोबाइल:  <a href="tel:8098001628">8098001628</a>
    📧 ईमेल:    <a href="mailto:finance@kanchiuniv.ac.in">finance@kanchiuniv.ac.in</a>

[3] परीक्षा विभाग
    ☎️ लैंडलाइन: <a href="tel:04427264306">(044) 27264306</a>
    📱 मोबाइल:  <a href="tel:8838701172">8838701172</a>
    📧 ईमेल:    <a href="mailto:examsection@kanchiuniv.ac.in">examsection@kanchiuniv.ac.in</a>

🛠️ सहायक सेवाएं
-------------
[4] क्रय विभाग
    ☎️ लैंडलाइन: <a href="tel:04427264308">(044) 27264308</a>
    📧 ईमेल:    <a href="mailto:purchase@kanchiuniv.ac.in">purchase@kanchiuniv.ac.in</a>

🏠 छात्र सुविधाएं
--------------
[5] पुरुष छात्रावास
    📱 मोबाइल:  <a href="tel:8838738227">8838738227</a>
    📧 ईमेल:    <a href="mailto:hostels@kanchiuniv.ac.in">hostels@kanchiuniv.ac.in</a>

[6] महिला छात्रावास
    📱 मोबाइल:  <a href="tel:9344051473">9344051473</a>

[7] परिवहन विभाग
    📱 मोबाइल:  <a href="tel:8098001629">8098001629</a>
    📧 ईमेल:    <a href="mailto:transport@kanchiuniv.ac.in">transport@kanchiuniv.ac.in</a>

⚕️ चिकित्सा सुविधाएं
-----------------
[8] आयुर्वेद अस्पताल
    ☎️ लैंडलाइन: <a href="tel:04469189811">(044) 69189811</a>
    📱 मोबाइल:  <a href="tel:8098991630">8098991630</a>
    📧 ईमेल:    <a href="mailto:sjsach@gmail.com">sjsach@gmail.com</a>

[9] आयुर्वेद कॉलेज
    ☎️ लैंडलाइन: <a href="tel:04469189800">(044) 69189800</a>
    📱 मोबाइल:  <a href="tel:8098001626">8098001626</a>
    📧 ईमेल:    <a href="mailto:info@sjsach.org.in">info@sjsach.org.in</a>

🌐 वेबसाइट: <a href="https://kanchiuniv.ac.in" target="_blank">https://kanchiuniv.ac.in</a>""",

                'telugu': """
╔═════════════════════════════════════╗
║    SCSVMV విశ్వవిద్యాలయ సంప్రదింపులు    ║
╚═════════════════════════════════════╝

🎓 విద్యా విభాగాలు
----------------
[1] పరిపాలన విభాగం
    ☎️ ల్యాండ్‌లైన్: <a href="tel:04427264293">(044) 27264293</a>
    📱 మొబైల్:    <a href="tel:6382337146">6382337146</a>
    📧 ఇమెయిల్:   <a href="mailto:admin@kanchiuniv.ac.in">admin@kanchiuniv.ac.in</a>

[2] ఆర్థిక విభాగం
    ☎️ ల్యాండ్‌లైన్: <a href="tel:04427264480">(044) 27264480</a>
    📱 మొబైల్:    <a href="tel:8098001628">8098001628</a>
    📧 ఇమెయిల్:   <a href="mailto:finance@kanchiuniv.ac.in">finance@kanchiuniv.ac.in</a>

[3] పరీక్షల విభాగం
    ☎️ ల్యాండ్‌లైన్: <a href="tel:04427264306">(044) 27264306</a>
    📱 మొబైల్:    <a href="tel:8838701172">8838701172</a>
    📧 ఇమెయిల్:   <a href="mailto:examsection@kanchiuniv.ac.in">examsection@kanchiuniv.ac.in</a>

🛠️ సహాయక సేవలు
--------------
[4] కొనుగోలు విభాగం
    ☎️ ల్యాండ్‌లైన్: <a href="tel:04427264308">(044) 27264308</a>
    📧 ఇమెయిల్:   <a href="mailto:purchase@kanchiuniv.ac.in">purchase@kanchiuniv.ac.in</a>

🏠 విద్యార్థి సౌకర్యాలు
--------------------
[5] పురుషుల వసతిగృహం
    📱 మొబైల్:    <a href="tel:8838738227">8838738227</a>
    📧 ఇమెయిల్:   <a href="mailto:hostels@kanchiuniv.ac.in">hostels@kanchiuniv.ac.in</a>

[6] మహిళల వసతిగృహం
    📱 మొబైల్:    <a href="tel:9344051473">9344051473</a>

[7] రవాణా విభాగం
    📱 మొబైల్:    <a href="tel:8098001629">8098001629</a>
    📧 ఇమెయిల్:   <a href="mailto:transport@kanchiuniv.ac.in">transport@kanchiuniv.ac.in</a>

⚕️ వైద్య సౌకర్యాలు
----------------
[8] ఆయుర్వేద ఆసుపత్రి
    ☎️ ల్యాండ్‌లైన్: <a href="tel:04469189811">(044) 69189811</a>
    📱 మొబైల్:    <a href="tel:8098991630">8098991630</a>
    📧 ఇమెయిల్:   <a href="mailto:sjsach@gmail.com">sjsach@gmail.com</a>

[9] ఆయుర్వేద కళాశాల
    ☎️ ల్యాండ్‌లైన్: <a href="tel:04469189800">(044) 69189800</a>
    📱 మొబైల్:    <a href="tel:8098001626">8098001626</a>
    📧 ఇమెయిల్:   <a href="mailto:info@sjsach.org.in">info@sjsach.org.in</a>

🌐 వెబ్‌సైట్: <a href="https://kanchiuniv.ac.in" target="_blank">https://kanchiuniv.ac.in</a>"""
            }
            return JSONResponse(content={
                "response": contact_info.get(language, contact_info['english']),
                "status": "success"
            })
        
        # Check if the message is about departments or faculty
        if 'department' in user_message.lower() or 'departments' in user_message.lower():
            try:
                # Search MongoDB for department information
                results = pages_collection.find(
                    {"$text": {"$search": "departments schools faculties"}},
                    {
                        "score": {"$meta": "textScore"},
                        "text_content": 1,
                        "url": 1,
                        "title": 1
                    }
                ).sort([("score", {"$meta": "textScore"})]).limit(5)

                results_list = list(results)
                
                if not results_list:
                    return {
                        'response': "I apologize, but I couldn't find information about the departments. Please try again later.",
                        'language': language
                    }

                # Process and format results
                formatted_response = ""
                for doc in results_list:
                    content = doc.get('text_content', '')
                    url = doc.get('url', '')
                    title = doc.get('title', '')
                    
                    # Extract relevant paragraphs
                    paragraphs = content.split('\n')
                    relevant_paragraphs = []
                    
                    for para in paragraphs:
                        # Skip empty paragraphs
                        if not para.strip():
                            continue
                            
                        # Calculate relevance score for paragraph
                        para_lower = para.lower()
                        term_matches = sum(1 for term in search_terms.split() if term in para_lower)
                        if term_matches > 0:
                            relevance_score = term_matches / len(search_terms.split())
                            relevant_paragraphs.append((para, relevance_score))
                    
                    # Sort by relevance and take top 3 most relevant paragraphs
                    relevant_paragraphs.sort(key=lambda x: x[1], reverse=True)
                    top_paragraphs = [p[0] for p in relevant_paragraphs[:3]]
                    
                    if top_paragraphs:
                        formatted_response += f"\n🔍 From {title}:\n"
                        formatted_response += "\n".join(top_paragraphs) + "\n"
                
                if not formatted_response:
                    return "I apologize, but I couldn't find specific information for your query. Please try rephrasing your question or ask about a different topic."
                    
                return formatted_response
                
            except Exception as e:
                logger.error(f"Error fetching department information: {str(e)}")
                return {
                    'response': "I apologize, but I encountered an error while fetching department information. Please try again later.",
                    'language': language
                }

        # Check if the message is about faculty
        if any(variation in user_message for variation in greeting_variations['faculty']):
            try:
                # Prepare search terms based on department
                department_terms = ""
                if 'sanskrit' in user_message.lower():
                    department_terms = "sanskrit department faculty"
                elif 'cse' in user_message.lower() or 'computer' in user_message.lower():
                    department_terms = "computer science engineering cse department faculty"
                else:
                    return {
                        'response': """Please specify which department's faculty information you're looking for. For example:
• CSE Faculty
• Sanskrit Faculty
• Engineering Faculty
• Management Faculty
• Science Faculty
• Arts Faculty""",
                        'language': language
                    }

                # Search MongoDB for faculty information
                results = pages_collection.find(
                    {"$text": {"$search": department_terms}},
                    {
                        "score": {"$meta": "textScore"},
                        "text_content": 1,
                        "url": 1,
                        "title": 1
                    }
                ).sort([("score", {"$meta": "textScore"})]).limit(3)

                results_list = list(results)
                
                if not results_list:
                    return {
                        'response': f"I apologize, but I couldn't find faculty information for the specified department. Please try again later.",
                        'language': language
                    }

                # Process and format faculty information
                faculty_info = "╔══════════════════════════════════════╗\n"
                faculty_info += f"║ {department_terms.upper()} DIRECTORY ║\n"
                faculty_info += "╚══════════════════════════════════════╝\n\n"

                for doc in results_list:
                    text = doc.get('text_content', '')
                    url = doc.get('url', '')
                    
                    # Extract and format faculty details
                    paragraphs = text.split('\n')
                    for para in paragraphs:
                        if any(term in para.lower() for term in ['professor', 'hod', 'head', 'faculty', 'department']):
                            faculty_info += para + '\n'

                return {
                    'response': faculty_info,
                    'language': language
                }
                
            except Exception as e:
                logger.error(f"Error fetching faculty information: {str(e)}")
                return {
                    'response': "I apologize, but I encountered an error while fetching faculty information. Please try again later.",
                    'language': language
                }
        
        # Expand search terms based on variations
        search_terms = user_message
        if contains_variation(user_message, 'course'):
            search_terms += " courses programs degrees offered B.Tech M.Tech MBA MCA BBA BCA Ph.D undergraduate postgraduate"
        if contains_variation(user_message, 'requirement') or contains_variation(user_message, 'admission'):
            search_terms += " requirements eligibility criteria admission qualification entrance"
        if contains_variation(user_message, 'fee'):
            if "mba lateral entry" in user_message or "mba lateral" in user_message or "lateral entry mba" in user_message:
                return {
                    "response": """🎓 MBA LATERAL ENTRY FEE STRUCTURE

📊 FEE DETAILS
• Tuition Fee: ₹75,000 per semester
• Registration Fee: ₹5,000 (one-time)
• Examination Fee: ₹2,500 per semester
• Library Fee: ₹1,500 per semester
• Laboratory Fee: ₹1,000 per semester
• Development Fee: ₹2,000 per semester
• Sports Fee: ₹500 per semester
• Medical Fee: ₹500 per semester
• Student Welfare Fee: ₹1,000 per semester

💡 IMPORTANT NOTES
• Total fee per semester: ₹84,000
• Hostel and mess charges are additional
• Fees are subject to revision as per university norms
• Payment can be made through online/offline modes
• Installment facility available

📞 FOR MORE INFORMATION
• Contact: (044) 27264285
• Email: admission@kanchiuniv.ac.in
• Visit: https://kanchiuniv.ac.in/admission/fee-structure/""",
                    "language": language
                }
            search_terms += " fees cost payment structure semester annual charges"
        
        # Search university data for context
        context = await search_university_data(search_terms)
        
        # Format prompt
        prompt = f"""Based on the following information about SCSVMV University, please answer the question.
Please provide the answer in {language} language.

Context from the university database:
{context}

Question: {user_message}

Answer:"""
        
        logger.info(f"Sending prompt to Gemini...")
        
        response = generate_with_gemini(prompt)
        logger.info(f"Received response from Gemini")
        
        return JSONResponse(content={
            "response": response,
            "status": "success"
        })
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(e),
                "response": "I apologize, but something went wrong. Please try again later."
            }
        )

if __name__ == '__main__':
    import uvicorn
    port = int(os.environ.get('PORT', 5003))
    logger.info(f"Starting server on port {port}")
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True, log_level="info")