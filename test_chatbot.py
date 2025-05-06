import requests
import json
import time

def test_chatbot():
    base_url = "http://localhost:5003/api/chat"
    headers = {"Content-Type": "application/json"}
    
    # Test cases
    test_cases = [
        # Basic greetings
        {"message": "Hello", "language": "english"},
        {"message": "வணக்கம்", "language": "tamil"},
        {"message": "नमस्ते", "language": "hindi"},
        
        # Department queries
        {"message": "What are the departments available?", "language": "english"},
        {"message": "Tell me about CSE department", "language": "english"},
        
        # Fee queries
        {"message": "What is the fee for BE CSE?", "language": "english"},
        {"message": "What are the fees for all departments?", "language": "english"},
        
        # HOD queries
        {"message": "Who is the HOD of CSE?", "language": "english"},
        {"message": "Who is the head of Sanskrit department?", "language": "english"},
        
        # Contact information
        {"message": "What are the admission contact details?", "language": "english"},
        {"message": "Give me the contact information", "language": "english"},
        
        # Course information
        {"message": "What courses are offered in CSE?", "language": "english"},
        {"message": "Tell me about the MBA program", "language": "english"}
    ]
    
    print("Starting chatbot tests...\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"Query: {test_case['message']}")
        print(f"Language: {test_case['language']}")
        print("-" * 50)
        
        try:
            response = requests.post(base_url, headers=headers, json=test_case)
            if response.status_code == 200:
                result = response.json()
                print("Response:")
                print(result['response'])
            else:
                print(f"Error: Status code {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"Error: {str(e)}")
        
        print("-" * 50)
        time.sleep(1)  # Add a small delay between requests

if __name__ == "__main__":
    test_chatbot() 