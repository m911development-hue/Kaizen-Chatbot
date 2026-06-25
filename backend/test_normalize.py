import re
from num2words import num2words

def normalize_text_for_english(text: str) -> str:
    """
    Converts numbers in text to their English word equivalents.
    Handles standard numbers, currencies, percentages, and years.
    """
    if not text:
        return text
        
    # Replace rupees
    text = re.sub(r'₹\s*([0-9,.]+)', r'\1 rupees', text)
    # Replace dollars
    text = re.sub(r'\$\s*([0-9,.]+)', r'\1 dollars', text)
    # Replace percentages
    text = re.sub(r'([0-9,.]+)\s*%', r'\1 percent', text)

    def replace_num(match):
        num_str = match.group(0).replace(',', '')
        try:
            # Simple heuristic for years
            if len(num_str) == 4 and num_str.isdigit() and 1900 <= int(num_str) <= 2099:
                return num2words(int(num_str), to='year')
            
            # General numbers
            if '.' in num_str:
                return num2words(float(num_str))
            else:
                return num2words(int(num_str))
        except:
            return match.group(0)

    # Find all standalone numbers or numbers with commas/decimals
    normalized = re.sub(r'\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b|\b\d+(?:\.\d+)?\b', replace_num, text)
    
    return normalized

tests = [
    "1, 2, 3, 4, 5",
    "10, 25, 50, 100",
    "In 2026, we will grow by 75%.",
    "The cost is ₹5000.",
    "The population is 1,234,567.",
    "Call me at 9876543210."
]

for t in tests:
    print(f"Original: {t}")
    print(f"Normalized: {normalize_text_for_english(t)}")
    print("-" * 40)
