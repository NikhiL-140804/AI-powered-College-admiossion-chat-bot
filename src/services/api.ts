import { Message } from '../types';

type Language = 'english' | 'tamil' | 'hindi' | 'telugu';

const API_URL = 'http://localhost:5003/api/chat';

const UNIVERSITY_CONTEXT = `
You are an AI assistant for SCSVMV University (Sri Chandrasekharendra Saraswathi Viswa Mahavidyalaya) in Kanchipuram, Tamil Nadu, India.

Key information about SCSVMV University (2024 Update):
- Located in Enathur, Kanchipuram, Tamil Nadu
- Established in 1981, named after the 68th Acharya of Kanchi Kamakoti Peetam
- Deemed-to-be University under Section 3 of UGC Act 1956
- NAAC Accredited with 'A' Grade (3rd Cycle)
- NBA Accredited Engineering Programs
- NIRF Ranked Institution
`;

const LANGUAGE_INSTRUCTIONS: Record<Language, string> = {
  english: 'Respond in English only.',
  tamil: 'Respond in Tamil (தமிழ்) only. Use proper Tamil script and formal academic language.',
  hindi: 'Respond in Hindi (हिंदी) only. Use proper Devanagari script and formal academic language.',
  telugu: 'Respond in Telugu (తెలుగు) only. Use proper Telugu script and formal academic language.'
};

export async function getAIResponse(userMessage: string, language: Language = 'english'): Promise<string> {
  try {
    console.log('Sending request to:', API_URL);
    console.log('Request data:', { message: userMessage, language });

    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({
        message: userMessage,
        language: language
      })
    });

    console.log('Response status:', response.status);
    
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('API endpoint not found. Please check if the server is running.');
      }
      if (response.status === 500) {
        throw new Error('Server error occurred. Please try again later.');
      }
      throw new Error(`API request failed with status ${response.status}`);
    }

    const data = await response.json();
    console.log('Response data:', data);

    if (data.status === 'error') {
      throw new Error(data.error || 'Server error occurred');
    }

    if (!data.response) {
      throw new Error('No response received from server');
    }

    return data.response;
  } catch (error) {
    console.error('Error calling AI API:', error);
    
    // Network error (e.g., server not running)
    if (error instanceof TypeError && error.message === 'Failed to fetch') {
      const errorMessages: Record<Language, string> = {
        tamil: 'சேவையகத்துடன் தொடர்பு கொள்ள முடியவில்லை. சேவையகம் இயங்குகிறதா என்பதை சரிபார்க்கவும்.',
        hindi: 'सर्वर से संपर्क नहीं हो पा रहा है। कृपया जांचें कि सर्वर चल रहा है।',
        telugu: 'సర్వర్‌తో కనెక్ట్ చేయడం సాధ్యం కాలేదు. సర్వర్ రన్నింగ్‌లో ఉందో లేదో తనిఖీ చేయండి.',
        english: 'Could not connect to server. Please check if the server is running.'
      };
      throw new Error(errorMessages[language] || errorMessages.english);
    }

    // Other errors
    const errorMessages: Record<Language, string> = {
      tamil: 'மன்னிக்கவும், ஒரு பிழை ஏற்பட்டது. மீண்டும் முயற்சிக்கவும்.',
      hindi: 'क्षमा करें, एक त्रुटि हुई। कृपया पुनः प्रयास करें।',
      telugu: 'క్షమించండి, ఒక లోపం సంభవించింది. దయచేసి మళ్లీ ప్రయత్నించండి.',
      english: error instanceof Error ? error.message : 'Sorry, an error occurred. Please try again.'
    };
    throw new Error(errorMessages[language] || errorMessages.english);
  }
}