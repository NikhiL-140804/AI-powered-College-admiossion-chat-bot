import json
import os
from datetime import datetime
import urllib.request
import urllib.parse

UNIVERSITY_CONTEXT = """
You are an AI assistant for SCSVMV University (Sri Chandrasekharendra Saraswathi Viswa Mahavidyalaya) in Kanchipuram, Tamil Nadu, India.

Key information about SCSVMV University (2024 Update):
- Located in Enathur, Kanchipuram, Tamil Nadu
- Established in 1981, named after the 68th Acharya of Kanchi Kamakoti Peetam
- Deemed-to-be University under Section 3 of UGC Act 1956
- NAAC Accredited with 'A' Grade (3rd Cycle)
- NBA Accredited Engineering Programs
- NIRF Ranked Institution
"""

class ChatProcessor:
    def __init__(self):
        self.api_key = os.environ.get('VITE_GOOGLE_API_KEY')
        self.api_url = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent'
        
    def detect_language(self, text):
        # Simple language detection based on character sets
        devanagari = range(0x0900, 0x097F)
        tamil = range(0x0B80, 0x0BFF)
        telugu = range(0x0C00, 0x0C7F)
        
        char_counts = {
            'hindi': 0,
            'tamil': 0,
            'telugu': 0,
            'english': 0
        }
        
        for char in text:
            code = ord(char)
            if code in devanagari:
                char_counts['hindi'] += 1
            elif code in tamil:
                char_counts['tamil'] += 1
            elif code in telugu:
                char_counts['telugu'] += 1
            elif char.isascii() and char.isalpha():
                char_counts['english'] += 1
        
        max_lang = max(char_counts.items(), key=lambda x: x[1])
        return max_lang[0] if max_lang[1] > 0 else 'english'

    def get_welcome_message(self, language):
        messages = {
            'tamil': 'வணக்கம்! SCSVMV பல்கலைக்கழக சேர்க்கை உதவியாளருக்கு வரவேற்கிறோம்!',
            'hindi': 'नमस्कार! SCSVMV विश्वविद्यालय प्रवेश सहायक में आपका स्वागत है!',
            'telugu': 'నమస్కారం! SCSVMV విశ్వవిద్యాలయం ప్రవేశ సహాయకుడికి స్వాగతం!',
            'english': 'Welcome to SCSVMV University Admissions Assistant!'
        }
        return messages.get(language, messages['english'])

    def process_message(self, message, language):
        try:
            if not self.api_key:
                raise Exception('API key not configured')

            # Prepare the request
            headers = {
                'Content-Type': 'application/json',
            }
            
            data = {
                'contents': [{
                    'parts': [{
                        'text': f"{UNIVERSITY_CONTEXT}\n\nRespond in {language}. User question: {message}"
                    }]
                }],
                'generationConfig': {
                    'temperature': 0.7,
                    'topK': 40,
                    'topP': 0.95,
                    'maxOutputTokens': 1024,
                },
                'safetySettings': [
                    {
                        'category': 'HARM_CATEGORY_HARASSMENT',
                        'threshold': 'BLOCK_MEDIUM_AND_ABOVE'
                    },
                    {
                        'category': 'HARM_CATEGORY_HATE_SPEECH',
                        'threshold': 'BLOCK_MEDIUM_AND_ABOVE'
                    },
                    {
                        'category': 'HARM_CATEGORY_SEXUALLY_EXPLICIT',
                        'threshold': 'BLOCK_MEDIUM_AND_ABOVE'
                    },
                    {
                        'category': 'HARM_CATEGORY_DANGEROUS_CONTENT',
                        'threshold': 'BLOCK_MEDIUM_AND_ABOVE'
                    }
                ]
            }
            
            # Make the request
            url = f"{self.api_url}?key={self.api_key}"
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result['candidates'][0]['content']['parts'][0]['text']
                
        except Exception as e:
            error_messages = {
                'tamil': 'மன்னிக்கவும், ஒரு பிழை ஏற்பட்டது. மீண்டும் முயற்சிக்கவும்.',
                'hindi': 'क्षमा करें, एक त्रुटि हुई। कृपया पुनः प्रयास करें।',
                'telugu': 'క్షమించండి, ఒక లోపం సంభవించింది. దయచేసి మళ్లీ ప్రయత్నించండి.',
                'english': 'Sorry, an error occurred. Please try again.'
            }
            return error_messages.get(language, error_messages['english'])