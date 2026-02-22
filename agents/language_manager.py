class LanguageManager:
    def __init__(self):
        self.languages = {
            "English": "en",
            "Hindi": "hi",
            "Odia": "or",
            "Marathi": "mr"
        }
        
        # Dictionary of UI terms
        self.dictionary = {
            "title": {
                "en": "Agricultural Market Intelligence System",
                "hi": "कृषि बाजार खुफिया प्रणाली",
                "or": "କୃଷି ବଜାର ଗୁପ୍ତଚର ପ୍ରଣାଳୀ"
            },
            "market_overview": {
                "en": "Market Overview",
                "hi": "बाजार अवलोकन",
                "or": "ବଜାର ସମୀକ୍ଷା"
            },
            "price_forecast": {
                "en": "Price Forecast",
                "hi": "मूल्य पूर्वानुमान",
                "or": "ମୂଲ୍ୟ ପୂର୍ବାନୁମାନ"
            },
            "risk_shocks": {
                "en": "Risk & Shocks",
                "hi": "जोखिम और झटके",
                "or": "ବିପଦ ଏବଂ ଝଟକା"
            },
            "news_insights": {
                "en": "News & Insights",
                "hi": "समाचार और अंतर्दृष्टि",
                "or": "ଖବର ଏବଂ ସୂଚନା"
            },
            "ai_consultant": {
                "en": "AI Consultant",
                "hi": "एआई सलाहकार",
                "or": "AI ପରାମର୍ଶଦାତା"
            },
            "select_commodity": {
                "en": "Select Commodity",
                "hi": "वस्तु चुनें",
                "or": "ସାମଗ୍ରୀ ଚୟନ କରନ୍ତୁ"
            },
            "select_mandi": {
                "en": "Select Mandi",
                "hi": "मंडी चुनें",
                "or": "ମଣ୍ଡି ଚୟନ କରନ୍ତୁ"
            },
            "current_price": {
                "en": "Current Price",
                "hi": "वर्तमान मूल्य",
                "or": "ବର୍ତ୍ତମାନର ମୂଲ୍ୟ"
            },
            "reliability": {
                "en": "Reliability",
                "hi": "विश्वसनीयता",
                "or": "ବିଶ୍ୱାସଯୋଗ୍ୟତା"
            },
            "whatsapp_bot": {
                "en": "WhatsApp Bot (Demo)",
                "hi": "व्हाट्सएप बॉट (डेमो)",
                "or": "WhatsApp ବଟ୍ (ଡେମୋ)"
            }
        }

    def get_text(self, key, lang_code="en"):
        """
        Returns the translated text for a given key.
        """
        if key not in self.dictionary:
            return key
            
        return self.dictionary[key].get(lang_code, self.dictionary[key]["en"])

    def get_lang_code(self, lang_name):
        return self.languages.get(lang_name, "en")
