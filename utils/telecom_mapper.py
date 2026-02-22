import phonenumbers
from phonenumbers import carrier, geocoder

class TelecomMapper:
    """
    Maps caller phone numbers to Indian telecom circles and suggests initial language.
    """
    def __init__(self):
        # Mapping of State/Circle to primary regional language
        self.circle_lang_map = {
            "Maharashtra": "mr",
            "Delhi": "hi",
            "Uttar Pradesh": "hi",
            "Odisha": "or",
            "West Bengal": "bn",
            "Tamil Nadu": "ta",
            "Karnataka": "kn",
            "Andhra Pradesh": "te",
            "Telangana": "te",
            "Gujarat": "gu",
            "Punjab": "pa",
            "Kerala": "ml",
            "Bihar": "hi",
            "Rajasthan": "hi",
            "Madhya Pradesh": "hi",
            "Haryana": "hi"
        }

    def detect_region_and_language(self, phone_number):
        """
        Detects the region (State) and suggests a language based on the phone number.
        Returns: (region, lang_code)
        """
        try:
            # Add +91 if not present for Indian numbers
            if not phone_number.startswith('+'):
                if len(phone_number) == 10:
                    phone_number = "+91" + phone_number
                else:
                    return "Unknown", "en"

            parsed_number = phonenumbers.parse(phone_number, "IN")
            region = geocoder.description_for_number(parsed_number, "en")
            
            # Extract state from region string (e.g., "Maharashtra, India")
            state = region.split(',')[0].strip()
            
            lang_code = self.circle_lang_map.get(state, "en")
            
            return state, lang_code
        except Exception:
            return "Unknown", "en"

if __name__ == "__main__":
    mapper = TelecomMapper()
    # Test cases
    print(mapper.detect_region_and_language("9820012345")) # Likely Maharashtra/Mumbai
    print(mapper.detect_region_and_language("9437012345")) # Likely Odisha
