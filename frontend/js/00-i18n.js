/* ==========================================================================
   CropGuard Multilingual System (00-i18n.js)
   Supports 9 Indian & International Languages:
   - English (en)
   - हिन्दी (hi) - Hindi
   - ਪੰਜਾਬੀ (pa) - Punjabi
   - मराठी (mr) - Marathi
   - తెలుగు (te) - Telugu
   - தமிழ் (ta) - Tamil
   - ગુજરાતી (gu) - Gujarati
   - ಕನ್ನಡ (kn) - Kannada
   - বাংলা (bn) - Bengali
   ========================================================================== */

var SUPPORTED_LANGS = {
  en: { name: 'English', native: 'English', speech: 'en-IN', flag: '🇬🇧' },
  hi: { name: 'Hindi', native: 'हिन्दी', speech: 'hi-IN', flag: '🇮🇳' },
  pa: { name: 'Punjabi', native: 'ਪੰਜਾਬੀ', speech: 'pa-IN', flag: '🇮🇳' },
  mr: { name: 'Marathi', native: 'मराठी', speech: 'mr-IN', flag: '🇮🇳' },
  te: { name: 'Telugu', native: 'తెలుగు', speech: 'te-IN', flag: '🇮🇳' },
  ta: { name: 'Tamil', native: 'தமிழ்', speech: 'ta-IN', flag: '🇮🇳' },
  gu: { name: 'Gujarati', native: 'ગુજરાતી', speech: 'gu-IN', flag: '🇮🇳' },
  kn: { name: 'Kannada', native: 'ಕನ್ನಡ', speech: 'kn-IN', flag: '🇮🇳' },
  bn: { name: 'Bengali', native: 'বাংলা', speech: 'bn-IN', flag: '🇮🇳' }
};
if (typeof window !== 'undefined') window.SUPPORTED_LANGS = SUPPORTED_LANGS;

const I18N = {
  en: {
    announcement: "Smart Farming. A Healthier Tomorrow.",
    liveVit: "Live ViT-384 Model",
    hello: "Hello,",
    navDash: "Dashboard",
    navScan: "Scan Crop",
    navFarm: "My Farm",
    navHist: "History",
    navAdv: "Smart Advisory",
    navSet: "Settings",
    navHelp: "Help & KVK",
    tagline: "Healthy Crops,<br>Happy Farmers",
    scanTitle: "Scan Your Plant Leaf",
    scanSub: "Upload a leaf image or use your camera to detect diseases with AI",
    btnChoose: "Choose Image",
    btnCamera: "Use Camera",
    btnRunAgain: "Run again",
    btnAnalyse: "Analyse Leaf",
    diagComplete: "Diagnosis Complete",
    confidence: "Confidence",
    severity: "Severity",
    affectedArea: "Affected Leaf Area",
    symptomsTitle: "Identified Visual Symptoms",
    certifiedProtocol: "Certified Field Protocol",
    viewReport: "View Detailed Report →",
    readAloud: "Read aloud",
    diagFeedback: "Was this diagnosis accurate?",
    btnAccurate: "👍 Yes, accurate",
    btnReportErr: "👎 Report error",
    advHeading: "AI-Tailored Action Advisory",
    advAwaiting: "Awaiting Diagnosis",
    advSubtext: "Upload a plant leaf above to generate disease-specific agronomic interventions, precautions, and prevention steps.",
    advDoTitle: "What to Do Now",
    advDoSub: "Immediate Interventions",
    advDoStandby: "Scan a plant leaf to generate tailored immediate treatment steps.",
    advDontTitle: "What Not to Do",
    advDontSub: "Critical Precautions",
    advDontStandby: "Precautions against harmful spraying or practices will appear after diagnosis.",
    advPrevTitle: "Prevention",
    advPrevSub: "Long-Term Field Protocol",
    advPrevStandby: "Long-term cultural and crop rotation guidelines will populate post-analysis.",
    whTitle: "Crop Health Analytics",
    whSub: "NDVI & Canopy Vitality Index",
    whLive: "Live Telemetry",
    whCanopy: "Canopy Cover",
    whMoisture: "Leaf Moisture",
    whChloro: "Chlorophyll",
    whStress: "Stress Index",
    whStatus: "Crop Status: Optimal · Normal transpiration & vigorous biomass.",
    wrTitle: "Regional & Weather Alerts",
    wrSub: "Live Micro-Climate Telemetry",
    wrAlerts: "2 Alerts Active",
    wrNearKvk: "📍 Near KVK on Map ↗",
    wrViewDetails: "View Details →",
    aiTitle: "Ask CropGuard AI",
    aiSub: "Agronomic Doctor & Advisor",
    aiPlaceholder: "e.g. I sprayed 1L Mancozeb in 100L water — safe?",
    aiChip1: "🧪 1L Mancozeb in 100L?",
    aiChip2: "🧴 Chlorothalonil dose?",
    aiChip3: "🌧️ 85% humidity spray?",
    aiChip4: "⚠️ Leaf burn after spray?",
    setHeroTitle: "Application Settings",
    setHeroSub: "Personalise CropGuard — theme, language, AI model & API keys.",
    setAppTitle: "Appearance",
    setAppSub: "Personalise the look & feel of CropGuard",
    setThemeLabel: "🌓 Theme Mode",
    setLangLabel: "🌐 Language",
    setAiTitle: "AI Model",
    setAiSub: "Configure the ViT-384 diagnostic engine",
    setConfLabel: "🎯 Model Confidence Gate",
    setConfNote: "Predictions below this threshold are filtered out",
    setActiveModelLabel: "⚡ Active Model",
    setGroqTitle: "Groq LLM API",
    setGroqSub: "Power CropGuard AI with Llama 3.3 70B",
    setGroqBannerTitle: "Sub-second Agronomic Intelligence",
    setGroqBannerSub: "Connect your free Groq key for real-time pesticide dosage, disease diagnosis & spray advice.",
    setKeyLabel: "🔑 API Key",
    setKeyOptional: "(Optional — built-in engine always available)",
    btnSaveKey: "💾 Save Key",
    setAboutTitle: "About CropGuard",
    setAboutSub: "Version & system information",
    setTagline: "CropGuard — Empowering farmers with AI for a healthier tomorrow.",
    helpHeroTitle: "🌾 Krishi Vigyan Kendra (KVK) & Agricultural Support",
    helpHeroSub: "Locate verified KVK farm science centres, district diagnostic labs, and 24/7 government agronomists.",
    helpBackDash: "← Back to Dashboard",
    helpKvkTitle: "Nearest Krishi Vigyan Kendra",
    helpKvkDesc: "Locate the nearest ICAR Krishi Vigyan Kendra farm science centre on Google Maps with turn-by-turn driving directions.",
    helpKvkBtn: "Open KVK Near Me on Google Maps ↗",
    helpSoilTitle: "Soil & Pathology Testing Lab",
    helpSoilDesc: "Find accredited soil testing laboratories and plant diagnostic clinics near your district for leaf tissue analysis.",
    helpSoilBtn: "Find Soil Testing Labs on Map ↗",
    helpKisanTitle: "24/7 Kisan Call Centre Helpline",
    helpKisanDesc: "Speak directly with government agricultural scientists toll-free in your native language for emergency crop advisory.",
    helpKisanBtn: "Call Kisan Helpline 1800-180-1551 📞"
  },
  hi: {
    announcement: "स्मार्ट खेती। एक स्वस्थ कल।",
    liveVit: "लाइव ViT-384 मॉडल",
    hello: "नमस्ते,",
    navDash: "डैशबोर्ड",
    navScan: "फसल स्कैन",
    navFarm: "मेरा खेत",
    navHist: "इतिहास",
    navAdv: "स्मार्ट सलाह",
    navSet: "सेटिंग्स",
    navHelp: "मदद व केवीके",
    tagline: "स्वस्थ फसलें,<br>खुशहाल किसान",
    scanTitle: "पौधे की पत्ती स्कैन करें",
    scanSub: "रोग पहचानने के लिए पत्ती की फोटो अपलोड करें या कैमरे का उपयोग करें",
    btnChoose: "फोटो चुनें",
    btnCamera: "कैमरा इस्तेमाल करें",
    btnRunAgain: "दोबारा चलाएं",
    btnAnalyse: "पत्ती का विश्लेषण करें",
    diagComplete: "निदान पूरा हुआ",
    confidence: "सटीकता",
    severity: "गंभीरता",
    affectedArea: "प्रभावित पत्ती क्षेत्र",
    symptomsTitle: "पहचाने गए लक्षण",
    certifiedProtocol: "प्रमाणित फील्ड प्रोटोकॉल",
    viewReport: "विस्तृत रिपोर्ट देखें →",
    readAloud: "बोलकर सुनाएं",
    diagFeedback: "क्या यह निदान सही था?",
    btnAccurate: "👍 हाँ, सटीक है",
    btnReportErr: "👎 त्रुटि बताएं",
    advHeading: "एआई-आधारित उपचार सलाह",
    advAwaiting: "निदान की प्रतीक्षा",
    advSubtext: "रोग अनुसार उपचार, सावधानियां और रोकथाम जानने के लिए पत्ती स्कैन करें।",
    advDoTitle: "अभी क्या करें",
    advDoSub: "तुरंत किए जाने वाले उपाय",
    advDoStandby: "उपचार के कदम जानने के लिए पहले पत्ती स्कैन करें।",
    advDontTitle: "क्या न करें",
    advDontSub: "ज़रूरी सावधानियां",
    advDontStandby: "नुकसानदेह छिड़काव से बचने की सावधानियां स्कैन के बाद दिखेंगी।",
    advPrevTitle: "रोकथाम",
    advPrevSub: "दीर्घकालिक खेत प्रोटोकॉल",
    advPrevStandby: "फसल चक्र और बचाव के तरीके स्कैन के बाद दिखेंगे।",
    whTitle: "फसल स्वास्थ्य एनालिटिक्स",
    whSub: "NDVI व कैनोपी सूचकांक",
    whLive: "लाइव टेलीमेट्री",
    whCanopy: "कैनोपी कवर",
    whMoisture: "पत्ती नमी",
    whChloro: "क्लोरोफिल",
    whStress: "तनाव सूचकांक",
    whStatus: "फसल स्थिति: उत्तम · सामान्य वाष्पोत्सर्जन व स्वस्थ पौधे।",
    wrTitle: "क्षेत्रीय व मौसम अलर्ट",
    wrSub: "लाइव मौसम टेलीमेट्री",
    wrAlerts: "2 अलर्ट सक्रिय",
    wrNearKvk: "📍 नज़दीकी केवीके मैप ↗",
    wrViewDetails: "विवरण देखें →",
    aiTitle: "क्रॉपगार्ड एआई से पूछें",
    aiSub: "कृषि रसायन डॉक्टर व सलाहकार",
    aiPlaceholder: "उदा. मैंने 100L पानी में 1L मैनकोज़ेब डाला — सही या गलत?",
    aiChip1: "🧪 100L में 1L मैनकोज़ेब?",
    aiChip2: "🧴 क्लोरोथैलोनिल मात्रा?",
    aiChip3: "🌧️ 85% नमी में छिड़काव?",
    aiChip4: "⚠️ छिड़काव बाद पत्ती जलना?",
    setHeroTitle: "एप्लिकेशन सेटिंग्स",
    setHeroSub: "क्रॉपगार्ड अनुकूलित करें — थीम, भाषा, एआई मॉडल व एपीआई कुंजी।",
    setAppTitle: "दिखावट (Appearance)",
    setAppSub: "क्रॉपगार्ड का रंगरूप बदलें",
    setThemeLabel: "🌓 थीम मोड",
    setLangLabel: "🌐 भाषा",
    setAiTitle: "एआई मॉडल",
    setAiSub: "ViT-384 मॉडल कॉन्फ़िगर करें",
    setConfLabel: "🎯 मॉडल सटीकता सीमा",
    setConfNote: "इस सीमा से कम सटीकता वाले परिणाम छोड़ दिए जाते हैं",
    setActiveModelLabel: "⚡ सक्रिय मॉडल",
    setGroqTitle: "ग्रॉक (Groq) एलएलएम एपीआई",
    setGroqSub: "लामा 3.3 70B द्वारा संचालित क्रॉपगार्ड एआई",
    setGroqBannerTitle: "सेकंडों में सटीक कृषि सलाह",
    setGroqBannerSub: "कीटनाशक मात्रा और फसल सलाह के लिए अपनी मुफ्त ग्रॉक कुंजी जोड़ें।",
    setKeyLabel: "🔑 एपीआई कुंजी",
    setKeyOptional: "(वैकल्पिक — इनबिल्ट इंजन हमेशा चालू रहता है)",
    btnSaveKey: "💾 कुंजी सहेजें",
    setAboutTitle: "क्रॉपगार्ड के बारे में",
    setAboutSub: "संस्करण व प्रणाली विवरण",
    setTagline: "क्रॉपगार्ड — बेहतर कल के लिए किसानों को एआई शक्ति प्रदान करना।",
    helpHeroTitle: "🌾 कृषि विज्ञान केंद्र (KVK) व कृषि सहायता",
    helpHeroSub: "सत्यापित केवीके केंद्र, मृदा परीक्षण प्रयोगशालाएं और विशेषज्ञ कृषि अधिकारियों से संपर्क करें।",
    helpBackDash: "← डैशबोर्ड पर वापस जाएं",
    helpKvkTitle: "नज़दीकी कृषि विज्ञान केंद्र (KVK)",
    helpKvkDesc: "गूगल मैप्स पर ड्राइविंग निर्देशों के साथ अपने ज़िले का निकटतम आईसीएआर केवीके खोजें।",
    helpKvkBtn: "गूगल मैप्स पर नज़दीकी KVK खोलें ↗",
    helpSoilTitle: "मृदा व रोग परीक्षण लैब",
    helpSoilDesc: "मिट्टी और पत्ती ऊतक परीक्षण के लिए अपने ज़िले की प्रमाणित प्रयोगशालाएं देखें।",
    helpSoilBtn: "नक्शे पर मृदा परीक्षण लैब खोजें ↗",
    helpKisanTitle: "24/7 किसान कॉल सेंटर हेल्पलाइन",
    helpKisanDesc: "आपातकालीन फसल सलाह के लिए अपनी मातृभाषा में टोल-फ्री वैज्ञानिक परामर्श लें।",
    helpKisanBtn: "किसान हेल्पलाइन 1800-180-1551 डायल करें 📞"
  },
  pa: {
    announcement: "ਸਮਾਰਟ ਖੇਤੀ। ਖੁਸ਼ਹਾਲ ਭਲਕ।",
    liveVit: "ਲਾਈਵ ViT-384 ਮਾਡਲ",
    hello: "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ,",
    navDash: "ਡੈਸ਼ਬੋਰਡ",
    navScan: "ਫਸਲ ਸਕੈਨ",
    navFarm: "ਮੇਰਾ ਖੇਤ",
    navHist: "ਇਤਿਹਾਸ",
    navAdv: "ਸਮਾਰਟ ਸਲਾਹ",
    navSet: "ਸੈਟਿੰਗਾਂ",
    navHelp: "ਮਦਦ ਅਤੇ ਕੇਵੀਕੇ",
    tagline: "ਤੰਦਰੁਸਤ ਫਸਲਾਂ,<br>ਖੁਸ਼ਹਾਲ ਕਿਸਾਨ",
    scanTitle: "ਪੌਦੇ ਦਾ ਪੱਤਾ ਸਕੈਨ ਕਰੋ",
    scanSub: "ਬਿਮਾਰੀ ਦੀ ਜਾਂਚ ਲਈ ਪੱਤੇ ਦੀ ਫੋਟੋ ਅੱਪਲੋਡ ਕਰੋ ਜਾਂ ਕੈਮਰਾ ਵਰਤੋ",
    btnChoose: "ਤਸਵੀਰ ਚੁਣੋ",
    btnCamera: "ਕੈਮਰਾ ਵਰਤੋ",
    btnRunAgain: "ਦੁਬਾਰਾ ਚਲਾਓ",
    btnAnalyse: "ਪੱਤਾ ਪਰਖੋ",
    diagComplete: "ਜਾਂਚ ਪੂਰੀ ਹੋਈ",
    confidence: "ਭਰੋਸੇਯੋਗਤਾ",
    severity: "ਗੰਭੀਰਤਾ",
    affectedArea: "ਪ੍ਰਭਾਵਿਤ ਪੱਤੇ ਦਾ ਖੇਤਰ",
    symptomsTitle: "ਪਛਾਣੇ ਗਏ ਲੱਛਣ",
    certifiedProtocol: "ਪ੍ਰਮਾਣਿਤ ਖੇਤ ਪ੍ਰੋਟੋਕੋਲ",
    viewReport: "ਵੇਰਵੇ ਸਹਿਤ ਰਿਪੋਰਟ →",
    readAloud: "ਪੜ੍ਹ ਕੇ ਸੁਣਾਓ",
    diagFeedback: "ਕੀ ਇਹ ਜਾਂਚ ਸਹੀ ਸੀ?",
    btnAccurate: "👍 ਹਾਂ, ਬਿਲਕੁਲ ਸਹੀ",
    btnReportErr: "👎 ਗਲਤੀ ਦੱਸੋ",
    advHeading: "ਏਆਈ-ਅਧਾਰਿਤ ਇਲਾਜ ਸਲਾਹ",
    advAwaiting: "ਜਾਂਚ ਦੀ ਉਡੀਕ",
    advSubtext: "ਬਿਮਾਰੀ ਅਨੁਸਾਰ ਢੁਕਵੇਂ ਉਪਾਅ ਅਤੇ ਬਚਾਅ ਦੇ ਤਰੀਕੇ ਜਾਣਨ ਲਈ ਪੱਤਾ ਸਕੈਨ ਕਰੋ।",
    advDoTitle: "ਹੁਣ ਕੀ ਕਰਨਾ ਹੈ",
    advDoSub: "ਤੁਰੰਤ ਕੀਤੇ ਜਾਣ ਵਾਲੇ ਉਪਾਅ",
    advDoStandby: "ਇਲਾਜ ਦੇ ਕਦਮ ਦੇਖਣ ਲਈ ਪਹਿਲਾਂ ਪੱਤਾ ਸਕੈਨ ਕਰੋ।",
    advDontTitle: "ਕੀ ਨਹੀਂ ਕਰਨਾ",
    advDontSub: "ਜ਼ਰੂਰੀ ਸਾਵਧਾਨੀਆਂ",
    advDontStandby: "ਗਲਤ ਛਿੜਕਾਅ ਤੋਂ ਬਚਣ ਲਈ ਸਾਵਧਾਨੀਆਂ ਸਕੈਨ ਤੋਂ ਬਾਅਦ ਦਿਸਣਗੀਆਂ।",
    advPrevTitle: "ਰੋਕਥਾਮ",
    advPrevSub: "ਲੰਮੇ ਸਮੇਂ ਦੇ ਸੁਝਾਅ",
    advPrevStandby: "ਫਸਲ ਬਦਲੀ ਅਤੇ ਬਚਾਅ ਨਿਯਮ ਸਕੈਨ ਤੋਂ ਬਾਅਦ ਦਿਸਣਗੇ।",
    whTitle: "ਫਸਲ ਸਿਹਤ ਵਿਸ਼ਲੇਸ਼ਣ",
    whSub: "NDVI ਤੇ ਕੈਨੋਪੀ ਇੰਡੈਕਸ",
    whLive: "ਲਾਈਵ ਟੈਲੀਮੈਟਰੀ",
    whCanopy: "ਕੈਨੋਪੀ ਕਵਰ",
    whMoisture: "ਪੱਤਾ ਨਮੀ",
    whChloro: "ਕਲੋਰੋਫਿਲ",
    whStress: "ਤਣਾਅ ਸੂਚਕ",
    whStatus: "ਫਸਲ ਸਥਿਤੀ: ਵਧੀਆ · ਆਮ ਵਿਕਾਸ ਅਤੇ ਤੰਦਰੁਸਤ ਪੌਦੇ।",
    wrTitle: "ਖੇਤਰੀ ਅਤੇ ਮੌਸਮ ਚਿਤਾਵਨੀ",
    wrSub: "ਲਾਈਵ ਮੌਸਮ ਰਿਕਾਰਡ",
    wrAlerts: "2 ਚਿਤਾਵਨੀਆਂ",
    wrNearKvk: "📍 ਨੇੜਲਾ ਕੇਵੀਕੇ ਨਕਸ਼ਾ ↗",
    wrViewDetails: "ਵੇਰਵਾ ਦੇਖੋ →",
    aiTitle: "ਕਰੌਪਗਾਰਡ ਏਆਈ ਨੂੰ ਪੁੱਛੋ",
    aiSub: "ਖੇਤੀਬਾੜੀ ਡਾਕਟਰ ਅਤੇ ਸਲਾਹਕਾਰ",
    aiPlaceholder: "ਜਿਵੇਂ: ਮੈਂ 100L ਪਾਣੀ 'ਚ 1L ਮੈਨਕੋਜ਼ੇਬ ਪਾਇਆ — ਠੀਕ ਹੈ ਜਾਂ ਗਲਤ?",
    aiChip1: "🧪 100L 'ਚ 1L ਮੈਨਕੋਜ਼ੇਬ?",
    aiChip2: "🧴 ਕਲੋਰੋਥੈਲੋਨਿਲ ਮਾਤਰਾ?",
    aiChip3: "🌧️ 85% ਨਮੀ 'ਚ ਛਿੜਕਾਅ?",
    aiChip4: "⚠️ ਛਿੜਕਾਅ ਬਾਅਦ ਪੱਤੇ ਸੜਨਾ?",
    setHeroTitle: "ਐਪਲੀਕੇਸ਼ਨ ਸੈਟਿੰਗਾਂ",
    setHeroSub: "ਕਰੌਪਗਾਰਡ ਅਨੁਕੂਲਿਤ ਕਰੋ — ਥੀਮ, ਭਾਸ਼ਾ, ਏਆਈ ਮਾਡਲ ਅਤੇ ਕੁੰਜੀਆਂ।",
    setAppTitle: "ਦਿੱਖ (Appearance)",
    setAppSub: "ਕਰੌਪਗਾਰਡ ਦੀ ਦਿੱਖ ਬਦਲੋ",
    setThemeLabel: "🌓 ਥੀਮ ਮੋਡ",
    setLangLabel: "🌐 ਭਾਸ਼ਾ",
    setAiTitle: "ਏਆਈ ਮਾਡਲ",
    setAiSub: "ViT-384 ਮਾਡਲ ਸੈੱਟ ਕਰੋ",
    setConfLabel: "🎯 ਮਾਡਲ ਭਰੋਸਾ ਸੀਮਾ",
    setConfNote: "ਇਸ ਸੀਮਾ ਤੋਂ ਘੱਟ ਵਾਲੇ ਨਤੀਜੇ ਛੱਡ ਦਿੱਤੇ ਜਾਂਦੇ ਹਨ",
    setActiveModelLabel: "⚡ ਸਰਗਰਮ ਮਾਡਲ",
    setGroqTitle: "ਗਰੋਕ (Groq) ਐਲਐਲਐਮ",
    setGroqSub: "ਲਾਮਾ 3.3 70B ਦੁਆਰਾ ਚੱਲਣ ਵਾਲੀ ਏਆਈ",
    setGroqBannerTitle: "ਸਕਿੰਟਾਂ 'ਚ ਖੇਤੀਬਾੜੀ ਸਲਾਹ",
    setGroqBannerSub: "ਕੀਟਨਾਸ਼ਕ ਮਾਤਰਾ ਅਤੇ ਫਸਲ ਸਲਾਹ ਲਈ ਮੁਫ਼ਤ ਕੁੰਜੀ ਲਗਾਓ।",
    setKeyLabel: "🔑 ਏਪੀਆਈ ਕੁੰਜੀ",
    setKeyOptional: "(ਵਿਕਲਪਿਕ)",
    btnSaveKey: "💾 ਕੁੰਜੀ ਸਾਂਭੋ",
    setAboutTitle: "ਕਰੌਪਗਾਰਡ ਬਾਰੇ",
    setAboutSub: "ਵਰਜਨ ਅਤੇ ਸਿਸਟਮ ਜਾਣਕਾਰੀ",
    setTagline: "ਕਰੌਪਗਾਰਡ — ਖੁਸ਼ਹਾਲ ਭਲਕ ਲਈ ਕਿਸਾਨਾਂ ਨੂੰ ਏਆਈ ਦੀ ਤਾਕਤ।",
    helpHeroTitle: "🌾 ਕ੍ਰਿਸ਼ੀ ਵਿਗਿਆਨ ਕੇਂਦਰ (KVK) ਅਤੇ ਸਹਾਇਤਾ",
    helpHeroSub: "ਪ੍ਰਮਾਣਿਤ ਕੇਵੀਕੇ ਸਾਇੰਸ ਸੈਂਟਰ, ਲੈਬਾਂ ਅਤੇ ਸਰਕਾਰੀ ਖੇਤੀ ਮਾਹਿਰਾਂ ਨਾਲ ਸੰਪਰਕ ਕਰੋ।",
    helpBackDash: "← ਡੈਸ਼ਬੋਰਡ 'ਤੇ ਵਾਪਸ ਜਾਓ",
    helpKvkTitle: "ਨੇੜਲਾ ਕ੍ਰਿਸ਼ੀ ਵਿਗਿਆਨ ਕੇਂਦਰ (KVK)",
    helpKvkDesc: "ਗੂਗਲ ਮੈਪਸ 'ਤੇ ਰਸਤੇ ਦੀ ਅਗਵਾਈ ਨਾਲ ਆਪਣੇ ਜ਼ਿਲ੍ਹੇ ਦਾ ਨੇੜਲਾ ਕੇਵੀਕੇ ਲੱਭੋ।",
    helpKvkBtn: "ਗੂਗਲ ਮੈਪਸ 'ਤੇ ਨੇੜਲਾ KVK ਖੋਲ੍ਹੋ ↗",
    helpSoilTitle: "ਮਿੱਟੀ ਅਤੇ ਰੋਗ ਜਾਂਚ ਲੈਬ",
    helpSoilDesc: "ਪੱਤਿਆਂ ਅਤੇ ਮਿੱਟੀ ਦੀ ਜਾਂਚ ਲਈ ਜ਼ਿਲ੍ਹੇ ਦੀਆਂ ਪ੍ਰਮਾਣਿਤ ਲੈਬਾਂ ਲੱਭੋ।",
    helpSoilBtn: "ਨਕਸ਼ੇ 'ਤੇ ਮਿੱਟੀ ਜਾਂਚ ਲੈਬ ਲੱਭੋ ↗",
    helpKisanTitle: "24/7 ਕਿਸਾਨ ਕਾਲ ਸੈਂਟਰ ਹੈਲਪਲਾਈਨ",
    helpKisanDesc: "ਤੁਰੰਤ ਫਸਲ ਸਲਾਹ ਲਈ ਆਪਣੀ ਮਾਂ-ਬੋਲੀ ਵਿੱਚ ਟੋਲ-ਫਰੀ ਵਿਗਿਆਨੀਆਂ ਨਾਲ ਗੱਲ ਕਰੋ।",
    helpKisanBtn: "ਕਿਸਾਨ ਹੈਲਪਲਾਈਨ 1800-180-1551 ਕਾਲ ਕਰੋ 📞"
  },
  mr: {
    announcement: "स्मार्ट शेती. निरोगी उद्या.",
    liveVit: "थेट ViT-384 मॉडेल",
    hello: "नमस्कार,",
    navDash: "डॅशबोर्ड",
    navScan: "पीक स्कॅन करा",
    navFarm: "माझे शेत",
    navHist: "इतिहास",
    navAdv: "स्मार्ट सल्ला",
    navSet: "सेटिंग्ज",
    navHelp: "मदत व केव्हीके",
    tagline: "निरोगी पिके,<br>आनंदी शेतकरी",
    scanTitle: "रोपाचे पान स्कॅन करा",
    scanSub: "रोग ओळखण्यासाठी पानाचा फोटो अपलोड करा किंवा कॅमेरा वापरा",
    btnChoose: "फोटो निवडा",
    btnCamera: "कॅमेरा वापरा",
    btnRunAgain: "पुन्हा चालवा",
    btnAnalyse: "पानाचे विश्लेषण करा",
    diagComplete: "निदान पूर्ण झाले",
    confidence: "अचूकता",
    severity: "तीव्रता",
    affectedArea: "बाधित पानाचे क्षेत्र",
    symptomsTitle: "ओळखलेली लक्षणे",
    certifiedProtocol: "प्रमाणित शेत प्रोटोकॉल",
    viewReport: "सविस्तर अहवाल पहा →",
    readAloud: "वाचून दाखवा",
    diagFeedback: "हे निदान अचूक होते का?",
    btnAccurate: "👍 हो, अचूक आहे",
    btnReportErr: "👎 त्रुटी नोंदवा",
    advHeading: "एआय-आधारित कृती सल्ला",
    advAwaiting: "निदानाची प्रतीक्षा",
    advSubtext: "रोगानुसार योग्य उपचार आणि प्रतिबंधक उपाय जाणून घेण्यासाठी पान स्कॅन करा.",
    advDoTitle: "आता काय करावे",
    advDoSub: "त्वरित करावयाचे उपाय",
    advDoStandby: "उपचाराची माहिती मिळवण्यासाठी प्रथम पान स्कॅन करा.",
    advDontTitle: "काय करू नये",
    advDontSub: "महत्त्वाच्या खबरदाऱ्या",
    advDontStandby: "हानिकारक फवारणी टाळण्याच्या खबरदाऱ्या स्कॅननंतर दिसतील.",
    advPrevTitle: "प्रतिबंध",
    advPrevSub: "दीर्घकालीन शेत प्रोटोकॉल",
    advPrevStandby: "पीक फेरपालट आणि काळजी मार्गदर्शक तत्त्वे स्कॅननंतर दिसतील.",
    whTitle: "पीक आरोग्य विश्लेषण",
    whSub: "NDVI व कॅनोपी निर्देशांक",
    whLive: "थेट टेलीमेट्री",
    whCanopy: "कॅनोपी कव्हर",
    whMoisture: "पानातील ओलावा",
    whChloro: "क्लोरोफिल",
    whStress: "तणाव निर्देशांक",
    whStatus: "पिकाची स्थिती: उत्तम · सामान्य वाढ आणि जोमदार पिके.",
    wrTitle: "प्रादेशिक व हवामान सूचना",
    wrSub: "थेट हवामान टेलीमेट्री",
    wrAlerts: "२ सूचना सक्रिय",
    wrNearKvk: "📍 जवळचे KVK नकाशा ↗",
    wrViewDetails: "तपशील पहा →",
    aiTitle: "क्रॉपगार्ड एआय ला विचारा",
    aiSub: "कृषी रसायन शास्त्रज्ञ व सल्लागार",
    aiPlaceholder: "उदा. मी १००L पाण्यात १L मॅन्कोझेब फवारले — योग्य की अयोग्य?",
    aiChip1: "🧪 १००L मध्ये १L मॅन्कोझेब?",
    aiChip2: "🧴 क्लोरोथॅलोनिल प्रमाण?",
    aiChip3: "🌧️ ८५% आर्द्रतेत फवारणी?",
    aiChip4: "⚠️ फवारणीनंतर पाने जळणे?",
    setHeroTitle: "ॲप्लिकेशन सेटिंग्ज",
    setHeroSub: "क्रॉपगार्ड सानुकूलित करा — थीम, भाषा, एआय मॉडेल आणि कळा.",
    setAppTitle: "दिसणे (Appearance)",
    setAppSub: "क्रॉपगार्डचा लुक बदला",
    setThemeLabel: "🌓 थीम मोड",
    setLangLabel: "🌐 भाषा",
    setAiTitle: "एआय मॉडेल",
    setAiSub: "ViT-384 मॉडेल कॉन्फिगर करा",
    setConfLabel: "🎯 मॉडेल अचूकता मर्यादा",
    setConfNote: "या मर्यादेखालील अंदाज वगळले जातात",
    setActiveModelLabel: "⚡ सक्रिय मॉडेल",
    setGroqTitle: "ग्रॉक (Groq) एलएलएम एपीआय",
    setGroqSub: "लामा ३.३ ७०B द्वारे समर्थित क्रॉपगार्ड एआय",
    setGroqBannerTitle: "क्षणार्धात कृषी बुद्धिमत्ता",
    setGroqBannerSub: "कीटकनाशक प्रमाण आणि सल्ल्यासाठी मोफत Groq की जोडा.",
    setKeyLabel: "🔑 एपीआय की",
    setKeyOptional: "(पर्यायी — इनबिल्ट इंजिन उपलब्ध)",
    btnSaveKey: "💾 की जतन करा",
    setAboutTitle: "क्रॉपगार्ड बद्दल",
    setAboutSub: "आवृत्ती आणि प्रणाली माहिती",
    setTagline: "क्रॉपगार्ड — उज्ज्वल भविष्यासाठी शेतकऱ्यांना एआय सामर्थ्य.",
    helpHeroTitle: "🌾 कृषी विज्ञान केंद्र (KVK) व कृषी सहाय्य",
    helpHeroSub: "प्रमाणित केव्हीके केंद्र, माती परीक्षण प्रयोगशाळा आणि कृषी तज्ज्ञांशी संपर्क साधा.",
    helpBackDash: "← डॅशबोर्डवर परत जा",
    helpKvkTitle: "जवळचे कृषी विज्ञान केंद्र (KVK)",
    helpKvkDesc: "गुगल मॅप्सवर रस्त्याच्या दिशानिर्देशांसह आपल्या जिल्ह्यातील जवळचे केव्हीके शोधा.",
    helpKvkBtn: "गुगल मॅप्सवर KVK उघडा ↗",
    helpSoilTitle: "माती व वनस्पती रोग निदान प्रयोगशाळा",
    helpSoilDesc: "पान आणि माती परीक्षणासाठी जिल्ह्यातील अधिकृत प्रयोगशाळा शोधा.",
    helpSoilBtn: "नकाशावर माती परीक्षण लॅब शोधा ↗",
    helpKisanTitle: "२४/७ किसान कॉल सेंटर हेल्पलाईन",
    helpKisanDesc: "तातडीच्या सल्ल्यासाठी आपल्या भाषेत टोल-फ्री कृषी शास्त्रज्ञांशी थेट बोला.",
    helpKisanBtn: "किसान हेल्पलाईन १८००-१८०-१५५१ डायल करा 📞"
  },
  te: {
    announcement: "స్మార్ట్ వ్యవసాయం. ఆరోగ్యకరమైన రేపు.",
    liveVit: "లైవ్ ViT-384 మోడల్",
    hello: "నమస్కారం,",
    navDash: "డాష్‌బోర్డ్",
    navScan: "పంట స్కాన్",
    navFarm: "నా పొలం",
    navHist: "చరిత్ర",
    navAdv: "స్మార్ట్ సలహా",
    navSet: "సెట్టింగ్‌లు",
    navHelp: "సహాయం & KVK",
    tagline: "ఆరోగ్యకరమైన పంటలు,<br>సంతోషకరమైన రైతులు",
    scanTitle: "మొక్క ఆకును స్కాన్ చేయండి",
    scanSub: "వ్యాధులను గుర్తించడానికి ఆకు ఫోటో అప్‌లోడ్ చేయండి లేదా కెమెరా ఉపయోగించండి",
    btnChoose: "చిత్రం ఎంచుకోండి",
    btnCamera: "కెమెరా వాడండి",
    btnRunAgain: "మళ్లీ నడపండి",
    btnAnalyse: "ఆకును విశ్లేషించండి",
    diagComplete: "రోగ నిర్ధారణ పూర్తయింది",
    confidence: "ఖచ్చితత్వం",
    severity: "తీవ్రత",
    affectedArea: "ప్రభావిత ఆకు ప్రాంతం",
    symptomsTitle: "గుర్తించిన లక్షణాలు",
    certifiedProtocol: "ధృవీకరించబడిన ఫీల్డ్ ప్రోటోకాల్",
    viewReport: "వివరమైన నివేదిక →",
    readAloud: "చదివి వినిపించండి",
    diagFeedback: "ఈ నిర్ధారణ ఖచ్చితమైనదేనా?",
    btnAccurate: "👍 అవును, ఖచ్చితమైనది",
    btnReportErr: "👎 లోపాన్ని నివేదించండి",
    advHeading: "AI ఆధారిత చర్యల సలహా",
    advAwaiting: "నిర్ధారణ కోసం వేచి చూస్తోంది",
    advSubtext: "వ్యాధి నివారణ చర్యలు మరియు నివారణ మార్గదర్శకాలను రూపొందించడానికి ఆకును స్కాన్ చేయండి.",
    advDoTitle: "ఇప్పుడు ఏమి చేయాలి",
    advDoSub: "తక్షణ చర్యలు",
    advDoStandby: "చికిత్స దశల కోసం ముందుగా ఆకును స్కాన్ చేయండి.",
    advDontTitle: "ఏమి చేయకూడదు",
    advDontSub: "ముఖ్యమైన జాగ్రత్తలు",
    advDontStandby: "హానికరమైన పిచికారీ నివారణ జాగ్రత్తలు స్కాన్ తర్వాత కనిపిస్తాయి.",
    advPrevTitle: "నివారణ",
    advPrevSub: "దీర్ఘకాలిక ఫీల్డ్ ప్రోటోకాల్",
    advPrevStandby: "పంట మార్పిడి మరియు రక్షణ మార్గదర్శకాలు స్కాన్ తర్వాత వస్తాయి.",
    whTitle: "పంట ఆరోగ్య విశ్లేషణ",
    whSub: "NDVI & పందిరి సూచిక",
    whLive: "లైవ్ టెలిమెట్రీ",
    whCanopy: "పందిరి కవర్",
    whMoisture: "ఆకు తేమ",
    whChloro: "క్లోరోఫిల్",
    whStress: "ఒత్తిడి సూచిక",
    whStatus: "పంట స్థితి: ఉత్తమం · సాధారణ పెరుగుదల & బలమైన మొక్కలు.",
    wrTitle: "ప్రాంతీయ & వాతావరణ హెచ్చరికలు",
    wrSub: "ప్రత్యక్ష వాతావరణ సమాచారం",
    wrAlerts: "2 హెచ్చరికలు",
    wrNearKvk: "📍 సమీప KVK మ్యాప్ ↗",
    wrViewDetails: "వివరాలు చూడండి →",
    aiTitle: "క్రాప్‌గార్డ్ AI ని అడగండి",
    aiSub: "వ్యవసాయ రసాయన నిపుణుడు & సలహాదారు",
    aiPlaceholder: "ఉదా: 100L నీటిలో 1L మాంకోజెబ్ కలిపాను — సరియైనదా కాదా?",
    aiChip1: "🧪 100L లో 1L మాంకోజెబ్?",
    aiChip2: "🧴 క్లోరోథలోనిల్ మోతాదు?",
    aiChip3: "🌧️ 85% తేమలో పిచికారీ?",
    aiChip4: "⚠️ పిచికారీ తర్వాత ఆకులు మాడటం?",
    setHeroTitle: "అప్లికేషన్ సెట్టింగ్‌లు",
    setHeroSub: "క్రాప్‌గార్డ్ వ్యక్తిగతీకరించండి — థీమ్, భాష, AI మోడల్ & కీలు.",
    setAppTitle: "రూపం (Appearance)",
    setAppSub: "క్రాప్‌గార్డ్ రూపాన్ని మార్చండి",
    setThemeLabel: "🌓 థీమ్ మోడ్",
    setLangLabel: "🌐 భాష",
    setAiTitle: "AI మోడల్",
    setAiSub: "ViT-384 మోడల్‌ను కాన్ఫిగర్ చేయండి",
    setConfLabel: "🎯 మోడల్ ఖచ్చితత్వ పరిమితి",
    setConfNote: "ఈ పరిమితి కంటే తక్కువ అంచనాలు ఫిల్టర్ చేయబడతాయి",
    setActiveModelLabel: "⚡ సక్రియ మోడల్",
    setGroqTitle: "గ్రోక్ (Groq) LLM API",
    setGroqSub: "లామా 3.3 70B ద్వారా నడిచే క్రాప్‌గార్డ్ AI",
    setGroqBannerTitle: "తక్షణ వ్యవసాయ సలహాలు",
    setGroqBannerSub: "పురుగుమందుల మోతాదు మరియు సలహాల కోసం ఉచిత Groq కీని జోడించండి.",
    setKeyLabel: "🔑 API కీ",
    setKeyOptional: "(ఐచ్ఛికం)",
    btnSaveKey: "💾 కీని భద్రపరచండి",
    setAboutTitle: "క్రాప్‌గార్డ్ గురించి",
    setAboutSub: "వెర్షన్ & సిస్టమ్ సమాచారం",
    setTagline: "క్రాప్‌గార్డ్ — మెరుగైన రేపటి కోసం రైతులకు AI సాధికారత.",
    helpHeroTitle: "🌾 కృషి విజ్ఞాన కేంద్రం (KVK) & మద్దతు",
    helpHeroSub: "ధృవీకరించబడిన KVK కేంద్రాలు మరియు వ్యవసాయ శాస్త్రవేత్తలను సంప్రదించండి.",
    helpBackDash: "← డాష్‌బోర్డ్‌కు తిరిగి వెళ్లండి",
    helpKvkTitle: "సమీప కృషి విజ్ఞాన కేంద్రం (KVK)",
    helpKvkDesc: "గూగుల్ మ్యాప్స్‌లో దిశలతో సమీప KVK కేంద్రాన్ని కనుగొనండి.",
    helpKvkBtn: "గూగుల్ మ్యాప్స్‌లో KVK తెరవండి ↗",
    helpSoilTitle: "నేల మరియు రోగ నిర్ధారణ ప్రయోగశాల",
    helpSoilDesc: "మట్టి మరియు ఆకు పరీక్షల కోసం సమీప ల్యాబ్‌లను కనుగొనండి.",
    helpSoilBtn: "మ్యాప్‌లో నేల పరీక్ష ల్యాబ్‌ను కనుగొనండి ↗",
    helpKisanTitle: "24/7 కిసాన్ కాల్ సెంటర్ హెల్ప్‌లైన్",
    helpKisanDesc: "మీ మాతృభాషలో టోల్-ఫ్రీ వ్యవసాయ సలహాల కోసం నేరుగా మాట్లాడండి.",
    helpKisanBtn: "కిసాన్ హెల్ప్‌లైన్ 1800-180-1551 కి కాల్ చేయండి 📞"
  },
  ta: {
    announcement: "ஸ்மார்ட் விவசாயம். ஆரோக்கியமான நாளை.",
    liveVit: "நேரலை ViT-384 மாதிரி",
    hello: "வணக்கம்,",
    navDash: "டாஷ்போர்டு",
    navScan: "பயிரை ஸ்கேன் செய்க",
    navFarm: "என் பண்ணை",
    navHist: "வரலாறு",
    navAdv: "ஸ்மார்ட் ஆலோசனை",
    navSet: "அமைப்புகள்",
    navHelp: "உதவி & KVK",
    tagline: "ஆரோக்கியமான பயிர்கள்,<br>மகிழ்ச்சியான விவசாயிகள்",
    scanTitle: "தாவர இலையை ஸ்கேன் செய்க",
    scanSub: "நோய்களைக் கண்டறிய இலை புகைப்படத்தை பதிவேற்றவும் அல்லது கேமராவைப் பயன்படுத்தவும்",
    btnChoose: "படத்தை தேர்வுசெய்க",
    btnCamera: "கேமராவைப் பயன்படுத்துக",
    btnRunAgain: "மீண்டும் இயக்குக",
    btnAnalyse: "இலையை பகுப்பாய்வு செய்க",
    diagComplete: "கண்டறிதல் முடிந்தது",
    confidence: "நம்பகத்தன்மை",
    severity: "தீவிரம்",
    affectedArea: "பாதிக்கப்பட்ட இலை பகுதி",
    symptomsTitle: "கண்டறியப்பட்ட அறிகுறிகள்",
    certifiedProtocol: "சான்றளிக்கப்பட்ட கள நெறிமுறை",
    viewReport: "விரிவான அறிக்கை →",
    readAloud: "வாசித்துக் காட்டுக",
    diagFeedback: "இந்த கண்டறிதல் துல்லியமானதா?",
    btnAccurate: "👍 ஆம், துல்லியமானது",
    btnReportErr: "👎 பிழையைப் புகாரளி",
    advHeading: "AI ஆலோசனை வழிகாட்டி",
    advAwaiting: "கண்டறிதலுக்கு காத்திருக்கிறது",
    advSubtext: "நோய் சார்ந்த சிகிச்சை மற்றும் தடுப்பு வழிகாட்டுதல்களைப் பெற இலையை ஸ்கேன் செய்க.",
    advDoTitle: "இப்போது செய்ய வேண்டியவை",
    advDoSub: "உடனடி நடவடிக்கைகள்",
    advDoStandby: "சிகிச்சை படிகளுக்கு முதலில் இலையை ஸ்கேன் செய்க.",
    advDontTitle: "செய்யக்கூடாதவை",
    advDontSub: "முக்கிய முன்னெச்சரிக்கைகள்",
    advDontStandby: "தவறான தெளிப்பைத் தவிர்க்கும் முன்னெச்சரிக்கைகள் ஸ்கேனிற்குப் பின் தோன்றும்.",
    advPrevTitle: "தடுப்பு முறைகள்",
    advPrevSub: "நீண்ட கால கள நெறிமுறை",
    advPrevStandby: "பயிர் சுழற்சி மற்றும் பாதுகாப்பு வழிகாட்டுதல்கள் ஸ்கேனிற்குப் பின் தோன்றும்.",
    whTitle: "பயிர் ஆரோக்கிய பகுப்பாய்வு",
    whSub: "NDVI மற்றும் தாவர குறியீடு",
    whLive: "நேரலை டெலிமெட்ரி",
    whCanopy: "மேற்பரப்பு கவர்",
    whMoisture: "இலை ஈரப்பதம்",
    whChloro: "பச்சையம்",
    whStress: "அழுத்தக் குறியீடு",
    whStatus: "பயிர் நிலை: மிகச் சிறந்தது · இயல்பான வளர்ச்சி மற்றும் ஆரோக்கியமான பயிர்கள்.",
    wrTitle: "பிராந்திய & வானிலை எச்சரிக்கைகள்",
    wrSub: "நேரலை வானிலை தகவல்",
    wrAlerts: "2 எச்சரிக்கைகள்",
    wrNearKvk: "📍 அருகிலுள்ள KVK வரைபடம் ↗",
    wrViewDetails: "விவரங்களைக் காண்க →",
    aiTitle: "கிராப்கார்ட் AI-யிடம் கேளுங்கள்",
    aiSub: "விவசாய வேதியியல் மருத்துவர் & ஆலோசகர்",
    aiPlaceholder: "எ.கா: 100L தண்ணீரில் 1L மேங்கோசெப் தெளித்தேன் — சரியா தவறா?",
    aiChip1: "🧪 100L-ல் 1L மேன்கோசெப்?",
    aiChip2: "🧴 குளோரோதலோனில் அளவு?",
    aiChip3: "🌧️ 85% ஈரப்பதத்தில் தெளிப்பு?",
    aiChip4: "⚠️ தெளித்த பின் இலை கருகல்?",
    setHeroTitle: "பயன்பாட்டு அமைப்புகள்",
    setHeroSub: "கிராப்கார்டை தனிப்பயனாக்குங்கள் — தோற்றம், மொழி, AI மாதிரி & சாவிகள்.",
    setAppTitle: "தோற்றம் (Appearance)",
    setAppSub: "கிராப்கார்டின் தோற்றத்தை மாற்றவும்",
    setThemeLabel: "🌓 தீம் பயன்முறை",
    setLangLabel: "🌐 மொழி",
    setAiTitle: "AI மாதிரி",
    setAiSub: "ViT-384 மாதிரியை உள்ளமைக்கவும்",
    setConfLabel: "🎯 மாதிரி நம்பிக்கை வரம்பு",
    setConfNote: "இந்த வரம்பிற்கு குறைவான முடிவுகள் வடிகட்டப்படும்",
    setActiveModelLabel: "⚡ செயலில் உள்ள மாதிரி",
    setGroqTitle: "Groq LLM API",
    setGroqSub: "லாமா 3.3 70B மூலம் இயங்கும் கிராப்கார்ட் AI",
    setGroqBannerTitle: "நொடிகளில் விவசாய ஆலோசனை",
    setGroqBannerSub: "பூச்சிக்கொல்லி அளவு மற்றும் ஆலோசனைகளுக்கு இலவச Groq சாவியை இணைக்கவும்.",
    setKeyLabel: "🔑 API சாவி",
    setKeyOptional: "(விருப்பத்திற்குரியது)",
    btnSaveKey: "💾 சாவியைச் சேமி",
    setAboutTitle: "கிராப்கார்ட் பற்றி",
    setAboutSub: "பதிப்பு & கணினி தகவல்",
    setTagline: "கிராப்கார்ட் — சிறந்த நாளைக்காக விவசாயிகளுக்கு AI சக்தி.",
    helpHeroTitle: "🌾 வேளாண் அறிவியல் மையம் (KVK) & ஆதரவு",
    helpHeroSub: "அங்கீகரிக்கப்பட்ட KVK மையங்கள் மற்றும் வேளாண் விஞ்ஞானிகளைத் தொடர்பு கொள்ளுங்கள்.",
    helpBackDash: "← டாஷ்போர்டிற்குத் திரும்பு",
    helpKvkTitle: "அருகிலுள்ள வேளாண் அறிவியல் மையம் (KVK)",
    helpKvkDesc: "கூகிள் வரைபடத்தில் திசைகளுடன் அருகிலுள்ள கேவிகே மையத்தைக் கண்டறியவும்.",
    helpKvkBtn: "கூகிள் வரைபடத்தில் KVK திறக்கவும் ↗",
    helpSoilTitle: "மண் மற்றும் தாவர நோய் கண்டறியும் ஆய்வகம்",
    helpSoilDesc: "மண் மற்றும் இலை திசு பரிசோதனைக்கான அங்கீகரிக்கப்பட்ட ஆய்வகங்களைக் கண்டறியவும்.",
    helpSoilBtn: "வரைபடத்தில் மண் பரிசோதனை ஆய்வகத்தைக் காண்க ↗",
    helpKisanTitle: "24/7 கிசான் கால் சென்டர் உதவி எண்",
    helpKisanDesc: "உங்கள் தாய்மொழியில் கட்டணமில்லா விவசாய ஆலோசனைக்கு விஞ்ஞானிகளுடன் பேசுங்கள்.",
    helpKisanBtn: "கிசான் உதவி எண் 1800-180-1551 அழைக்கவும் 📞"
  },
  gu: {
    announcement: "સ્માર્ટ ખેતી. એક સ્વસ્થ આવતીકાલ.",
    liveVit: "લાઇવ ViT-384 મોડેલ",
    hello: "નમસ્તે,",
    navDash: "ડેશબોર્ડ",
    navScan: "પાક સ્કેન કરો",
    navFarm: "મારું ખેતર",
    navHist: "ઇતિહાસ",
    navAdv: "સ્માર્ટ સલાહ",
    navSet: "સેટિંગ્સ",
    navHelp: "મદદ અને KVK",
    tagline: "સ્વસ્થ પાક,<br>ખુશહાલ ખેડૂત",
    scanTitle: "છોડનું પાન સ્કેન કરો",
    scanSub: "રોગની ઓળખ માટે પાનનો ફોટો અપલોડ કરો અથવા કેમેરા વાપરો",
    btnChoose: "ફોટો પસંદ કરો",
    btnCamera: "કેમેરા વાપરો",
    btnRunAgain: "ફરી ચલાવો",
    btnAnalyse: "પાન તપાસો",
    diagComplete: "નિદાન પૂર્ણ થયું",
    confidence: "ચોકસાઈ",
    severity: "ગંભીરતા",
    affectedArea: "અસરગ્રસ્ત પાન વિસ્તાર",
    symptomsTitle: "ઓળખાયેલા લક્ષણો",
    certifiedProtocol: "પ્રમાણિત ખેતર પ્રોટોકોલ",
    viewReport: "વિગતવાર અહેવાલ જુઓ →",
    readAloud: "વાંચી સંભળાવો",
    diagFeedback: "શું આ નિદાન સાચું હતું?",
    btnAccurate: "👍 હા, સાચું છે",
    btnReportErr: "👎 ભૂલ જણાવો",
    advHeading: "AI-આધારિત સારવાર સલાહ",
    advAwaiting: "નિદાનની રાહ જુએ છે",
    advSubtext: "રોગ મુજબ યોગ્ય ઉપાયો અને બચાવ માટે પાન સ્કેન કરો.",
    advDoTitle: "હવે શું કરવું",
    advDoSub: "તાત્કાલિક પગલાં",
    advDoStandby: "સારવારના પગલાં જોવા માટે પહેલાં પાન સ્કેન કરો.",
    advDontTitle: "શું ન કરવું",
    advDontSub: "મહત્વપૂર્ણ સાવચેતી",
    advDontStandby: "ખોટા છંટકાવથી બચવાની સાવચેતીઓ સ્કેન પછી દેખાશે.",
    advPrevTitle: "અટકાવ",
    advPrevSub: "લાંબા ગાળાનો પ્રોટોકોલ",
    advPrevStandby: "પાકની ફેરબદલી અને બચાવ નિયમો સ્કેન પછી દેખાશે.",
    whTitle: "પાક આરોગ્ય વિશ્લેષણ",
    whSub: "NDVI અને કેનોપી ઇન્ડેક્સ",
    whLive: "લાઇવ ટેલિમેટ્રી",
    whCanopy: "કેનોપી કવર",
    whMoisture: "પાનની ભેજ",
    whChloro: "ક્લોરોફિલ",
    whStress: "તણાવ સૂચકાંક",
    whStatus: "પાકની સ્થિતિ: ઉત્તમ · સામાન્ય વૃદ્ધિ અને સ્વસ્થ છોડ.",
    wrTitle: "પ્રાદેશિક અને હવામાન ચેતવણી",
    wrSub: "લાઇવ હવામાન માહિતી",
    wrAlerts: "2 ચેતવણીઓ",
    wrNearKvk: "📍 નજીકનું KVK નકશો ↗",
    wrViewDetails: "વિગતો જુઓ →",
    aiTitle: "ક્રોપગાર્ડ AI ને પૂછો",
    aiSub: "કૃષિ રસાયણ ડૉક્ટર અને સલાહકાર",
    aiPlaceholder: "દા.ત: મેં 100L પાણીમાં 1L મેન્કોઝેબ છાંટ્યું — સારું કે ખરાબ?",
    aiChip1: "🧪 100L માં 1L મેન્કોઝેબ?",
    aiChip2: "🧴 ક્લોરોથેલોનિલ માત્રા?",
    aiChip3: "🌧️ 85% ભેજમાં છંટકાવ?",
    aiChip4: "⚠️ છંટકાવ પછી પાન બળવું?",
    setHeroTitle: "એપ્લિકેશન સેટિંગ્સ",
    setHeroSub: "ક્રોપગાર્ડ કસ્ટમાઇઝ કરો — થીમ, ભાષા, AI મોડેલ અને કી.",
    setAppTitle: "દેખાવ (Appearance)",
    setAppSub: "ક્રોપગાર્ડનો દેખાવ બદલો",
    setThemeLabel: "🌓 થીમ મોડ",
    setLangLabel: "🌐 ભાષા",
    setAiTitle: "AI મોડેલ",
    setAiSub: "ViT-384 મોડેલ રૂપરેખાંકિત કરો",
    setConfLabel: "🎯 મોડેલ ચોકસાઈ મર્યાદા",
    setConfNote: "આ મર્યાદાથી ઓછી ચોકસાઈવાળા પરિણામો ફિલ્ટર થાય છે",
    setActiveModelLabel: "⚡ સક્રિય મોડેલ",
    setGroqTitle: "Groq LLM API",
    setGroqSub: "લામા 3.3 70B સંચાલિત ક્રોપગાર્ડ AI",
    setGroqBannerTitle: "સેકન્ડોમાં ખેતી સલાહ",
    setGroqBannerSub: "જંતુનાશક માત્રા અને સલાહ માટે મફત Groq કી જોડો.",
    setKeyLabel: "🔑 API કી",
    setKeyOptional: "(વૈકલ્પિક)",
    btnSaveKey: "💾 કી સાચવો",
    setAboutTitle: "ક્રોપગાર્ડ વિશે",
    setAboutSub: "આવૃત્તિ અને સિસ્ટમ માહિતી",
    setTagline: "ક્રોપગાર્ડ — સ્વસ્થ આવતીકાલ માટે ખેડૂતોને AI શક્તિ.",
    helpHeroTitle: "🌾 કૃષિ વિજ્ઞાન કેન્દ્ર (KVK) અને સહાયતા",
    helpHeroSub: "પ્રમાણિત કેવીકે કેન્દ્રો, માટી પરીક્ષણ પ્રયોગશાળાઓ અને કૃષિ નિષ્ણાતોનો સંપર્ક કરો.",
    helpBackDash: "← ડેશબોર્ડ પર પાછા જાઓ",
    helpKvkTitle: "નજીકનું કૃષિ વિજ્ઞાન કેન્દ્ર (KVK)",
    helpKvkDesc: "ગૂગલ મેપ્સ પર દિશા નિર્દેશો સાથે તમારા જિલ્લાનું નજીકનું કેવીકે શોધો.",
    helpKvkBtn: "ગૂગલ મેપ્સ પર KVK ખોલો ↗",
    helpSoilTitle: "જમીન અને રોગ નિદાન પ્રયોગશાળા",
    helpSoilDesc: "માટી અને પાન પરીક્ષણ માટે જિલ્લાની માન્ય પ્રયોગશાળાઓ શોધો.",
    helpSoilBtn: "નકશા પર માટી પરીક્ષણ લેબ શોધો ↗",
    helpKisanTitle: "24/7 કિસાન કૉલ સેન્ટર હેલ્પલાઇન",
    helpKisanDesc: "તાત્કાલિક પાક સલાહ માટે તમારી માતૃભાષામાં ટોલ-ફ્રી વૈજ્ઞાનિકો સાથે વાત કરો.",
    helpKisanBtn: "કિસાન હેલ્પલાઇન 1800-180-1551 કૉલ કરો 📞"
  },
  kn: {
    announcement: "ಸ್ಮಾರ್ಟ್ ಕೃಷಿ. ಆರೋಗ್ಯಕರ ನಾಳೆ.",
    liveVit: "ಲೈವ್ ViT-384 ಮಾದರಿ",
    hello: "ನಮಸ್ಕಾರ,",
    navDash: "ಡ್ಯಾಶ್‌ಬೋರ್ಡ್",
    navScan: "ಬೆಳೆ ಸ್ಕ್ಯಾನ್ ಮಾಡಿ",
    navFarm: "ನನ್ನ ಕೃಷಿ",
    navHist: "ಇತಿಹಾಸ",
    navAdv: "ಸ್ಮಾರ್ಟ್ ಸಲಹೆ",
    navSet: "ಸೆಟ್ಟಿಂಗ್‌ಗಳು",
    navHelp: "ಸಹಾಯ ಮತ್ತು KVK",
    tagline: "ಆರೋಗ್ಯಕರ ಬೆಳೆಗಳು,<br>ಸಂತೋಷದ ರೈತರು",
    scanTitle: "ಸಸ್ಯದ ಎಲೆಯನ್ನು ಸ್ಕ್ಯಾನ್ ಮಾಡಿ",
    scanSub: "ರೋಗ ಪತ್ತೆಹಚ್ಚಲು ಎಲೆಯ ಫೋಟೋ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ ಅಥವಾ ಕ್ಯಾಮೆರಾ ಬಳಸಿ",
    btnChoose: "ಚಿತ್ರ ಆಯ್ಕೆಮಾಡಿ",
    btnCamera: "ಕ್ಯಾಮೆರಾ ಬಳಸಿ",
    btnRunAgain: "ಮತ್ತೆ ಚಲಾಯಿಸಿ",
    btnAnalyse: "ಎಲೆ ಪರೀಕ್ಷಿಸಿ",
    diagComplete: "ರೋಗನಿರ್ಣಯ ಪೂರ್ಣಗೊಂಡಿದೆ",
    confidence: "ನಿಖರತೆ",
    severity: "ತೀವ್ರತೆ",
    affectedArea: "ಬಾಧಿತ ಎಲೆ ಪ್ರದೇಶ",
    symptomsTitle: "ಗುರುತಿಸಲಾದ ಲಕ್ಷಣಗಳು",
    certifiedProtocol: "ದೃಢೀಕೃತ ಫೀಲ್ಡ್ ಪ್ರೋಟೋಕಾಲ್",
    viewReport: "ವಿವರವಾದ ವರದಿ →",
    readAloud: "ಓದಿ ಕೇಳಿಸಿ",
    diagFeedback: "ಈ ರೋಗನಿರ್ಣಯ ನಿಖರವಾಗಿತ್ತೇ?",
    btnAccurate: "👍 ಹೌದು, ನಿಖರವಾಗಿದೆ",
    btnReportErr: "👎 ದೋಷ ವರದಿ ಮಾಡಿ",
    advHeading: "AI ಆಧಾರಿತ ಕ್ರಿಯಾತ್ಮಕ ಸಲಹೆ",
    advAwaiting: "ರೋಗನಿರ್ಣಯಕ್ಕಾಗಿ ಕಾಯಲಾಗುತ್ತಿದೆ",
    advSubtext: "ರೋಗ ನಿರ್ದಿಷ್ಟ ಚಿಕಿತ್ಸೆ ಮತ್ತು ಮುನ್ನೆಚ್ಚರಿಕೆಗಳನ್ನು ತಿಳಿಯಲು ಎಲೆಯನ್ನು ಸ್ಕ್ಯಾನ್ ಮಾಡಿ.",
    advDoTitle: "ಈಗ ಏನು ಮಾಡಬೇಕು",
    advDoSub: "ತಕ್ಷಣದ ಕ್ರಮಗಳು",
    advDoStandby: "ಚಿಕಿತ್ಸಾ ಕ್ರಮಗಳನ್ನು ತಿಳಿಯಲು ಮೊದಲು ಎಲೆಯನ್ನು ಸ್ಕ್ಯಾನ್ ಮಾಡಿ.",
    advDontTitle: "ಏನು ಮಾಡಬಾರದು",
    advDontSub: "ಮುಖ್ಯ ಮುನ್ನೆಚ್ಚರಿಕೆಗಳು",
    advDontStandby: "ತಪ್ಪಾದ ಸಿಂಪಡಣೆ ತಡೆಗಟ್ಟುವ ಕ್ರಮಗಳು ಸ್ಕ್ಯಾನ್ ನಂತರ ಕಾಣಿಸುತ್ತವೆ.",
    advPrevTitle: "ತಡೆಗಟ್ಟುವಿಕೆ",
    advPrevSub: "ದೀರ್ಘಕಾಲೀನ ಪ್ರೋಟೋಕಾಲ್",
    advPrevStandby: "ಬೆಳೆ ಸರದಿ ಮತ್ತು ರಕ್ಷಣಾ ನಿಯಮಗಳು ಸ್ಕ್ಯಾನ್ ನಂತರ ಬರುತ್ತವೆ.",
    whTitle: "ಬೆಳೆ ಆರೋಗ್ಯ ವಿಶ್ಲೇಷಣೆ",
    whSub: "NDVI ಮತ್ತು ಮೇಲಾವರಣ ಸೂಚ್ಯಂಕ",
    whLive: "ಲೈವ್ ಟೆಲಿಮೆಟ್ರಿ",
    whCanopy: "ಮೇಲಾವರಣ ಹೊದಿಕೆ",
    whMoisture: "ಎಲೆ ತೇವಾಂಶ",
    whChloro: "ಕ್ಲೋರೊಫಿಲ್",
    whStress: "ಒತ್ತಡದ ಸೂಚ್ಯಂಕ",
    whStatus: "ಬೆಳೆ ಸ್ಥಿತಿ: ಅತ್ಯುತ್ತಮ · ಸಾಮಾನ್ಯ ಬೆಳವಣಿಗೆ ಮತ್ತು ಆರೋಗ್ಯಕರ ಸಸ್ಯಗಳು.",
    wrTitle: "ಪ್ರಾದೇಶಿಕ ಮತ್ತು ಹವಾಮಾನ ಎಚ್ಚರಿಕೆಗಳು",
    wrSub: "ಲೈವ್ ಹವಾಮಾನ ಮಾಹಿತಿ",
    wrAlerts: "2 ಎಚ್ಚರಿಕೆಗಳು",
    wrNearKvk: "📍 ಹತ್ತಿರದ KVK ನಕ್ಷೆ ↗",
    wrViewDetails: "ವಿವರಗಳನ್ನು ನೋಡಿ →",
    aiTitle: "ಕ್ರಾಪ್‌ಗಾರ್ಡ್ AI ಅನ್ನು ಕೇಳಿ",
    aiSub: "ಕೃಷಿ ರಾಸಾಯನಿಕ ತಜ್ಞ ಮತ್ತು ಸಲಹೆಗಾರ",
    aiPlaceholder: "ಉದಾ: 100L ನೀರಿಗೆ 1L ಮ್ಯಾಂಕೋಜೆಬ್ ಸಿಂಪಡಿಸಿದೆ — ಸರಿಯೇ ತಪ್ಪೇ?",
    aiChip1: "🧪 100L ನಲ್ಲಿ 1L ಮ್ಯಾಂಕೋಜೆಬ್?",
    aiChip2: "🧴 ಕ್ಲೋರೋಥಲೋನಿಲ್ ಪ್ರಮಾಣ?",
    aiChip3: "🌧️ 85% ತೇವಾಂಶದಲ್ಲಿ ಸಿಂಪರಣೆ?",
    aiChip4: "⚠️ ಸಿಂಪರಣೆ ನಂತರ ಎಲೆ ಸುಡುವುದು?",
    setHeroTitle: "ಅಪ್ಲಿಕೇಶನ್ ಸೆಟ್ಟಿಂಗ್‌ಗಳು",
    setHeroSub: "ಕ್ರಾಪ್‌ಗಾರ್ಡ್ ಕಸ್ಟಮೈಸ್ ಮಾಡಿ — ಥೀಮ್, ಭಾಷೆ, AI ಮಾದರಿ ಮತ್ತು ಕೀಗಳು.",
    setAppTitle: "ಗೋಚರತೆ (Appearance)",
    setAppSub: "ಕ್ರಾಪ್‌ಗಾರ್ಡ್ ನೋಟವನ್ನು ಬದಲಾಯಿಸಿ",
    setThemeLabel: "🌓 ಥೀಮ್ ಮೋಡ್",
    setLangLabel: "🌐 ಭಾಷೆ",
    setAiTitle: "AI ಮಾದರಿ",
    setAiSub: "ViT-384 ಮಾದರಿಯನ್ನು ಕಾನ್ಫಿಗರ್ ಮಾಡಿ",
    setConfLabel: "🎯 ಮಾದರಿ ವಿಶ್ವಾಸಾರ್ಹತೆ ಮಿತಿ",
    setConfNote: "ಈ ಮಿತಿಗಿಂತ ಕಡಿಮೆ ಇರುವ ಫಲಿತಾಂಶಗಳನ್ನು ಫಿಲ್ಟರ್ ಮಾಡಲಾಗುತ್ತದೆ",
    setActiveModelLabel: "⚡ ಸಕ್ರಿಯ ಮಾದರಿ",
    setGroqTitle: "Groq LLM API",
    setGroqSub: "ಲಾಮಾ 3.3 70B ಚಾಲಿತ ಕ್ರಾಪ್‌ಗಾರ್ಡ್ AI",
    setGroqBannerTitle: "ಕ್ಷಣಾರ್ಧದಲ್ಲಿ ಕೃಷಿ ಸಲಹೆ",
    setGroqBannerSub: "ಕೀಟನಾಶಕ ಪ್ರಮಾಣ ಮತ್ತು ಸಲಹೆಗಳಿಗಾಗಿ ಉಚಿತ Groq ಕೀ ಸೇರಿಸಿ.",
    setKeyLabel: "🔑 API ಕೀ",
    setKeyOptional: "(ಐಚ್ಛಿಕ)",
    btnSaveKey: "💾 ಕೀ ಉಳಿಸಿ",
    setAboutTitle: "ಕ್ರಾಪ್‌ಗಾರ್ಡ್ ಬಗ್ಗೆ",
    setAboutSub: "ಆವೃತ್ತಿ ಮತ್ತು ಸಿಸ್ಟಮ್ ಮಾಹಿತಿ",
    setTagline: "ಕ್ರಾಪ್‌ಗಾರ್ಡ್ — ಉತ್ತಮ ನಾಳೆಗಾಗಿ ರೈತರಿಗೆ AI ಶಕ್ತಿ.",
    helpHeroTitle: "🌾 ಕೃಷಿ ವಿಜ್ಞಾನ ಕೇಂದ್ರ (KVK) & ಬೆಂಬಲ",
    helpHeroSub: "ದೃಢೀಕೃತ KVK ಕೇಂದ್ರಗಳು ಮತ್ತು ಕೃಷಿ ವಿಜ್ಞಾನಿಗಳನ್ನು ಸಂಪರ್ಕಿಸಿ.",
    helpBackDash: "← ಡ್ಯಾಶ್‌ಬೋರ್ಡ್‌ಗೆ ಹಿಂತಿರುಗಿ",
    helpKvkTitle: "ಹತ್ತಿರದ ಕೃಷಿ ವಿಜ್ಞಾನ ಕೇಂದ್ರ (KVK)",
    helpKvkDesc: "ಗೂಗಲ್ ನಕ್ಷೆಯಲ್ಲಿ ನಿರ್ದೇಶನಗಳೊಂದಿಗೆ ಹತ್ತಿರದ KVK ಕೇಂದ್ರವನ್ನು ಹುಡುಕಿ.",
    helpKvkBtn: "ಗೂಗಲ್ ನಕ್ಷೆಯಲ್ಲಿ KVK ತೆರೆಯಿರಿ ↗",
    helpSoilTitle: "ಮಣ್ಣು ಮತ್ತು ರೋಗ ಪತ್ತೆ ಪ್ರಯೋಗಾಲಯ",
    helpSoilDesc: "ಮಣ್ಣು ಮತ್ತು ಎಲೆ ಪರೀಕ್ಷೆಗಾಗಿ ಪ್ರಮಾಣೀಕೃತ ಲ್ಯಾಬ್‌ಗಳನ್ನು ಹುಡುಕಿ.",
    helpSoilBtn: "ನಕ್ಷೆಯಲ್ಲಿ ಮಣ್ಣು ಪರೀಕ್ಷಾ ಲ್ಯಾಬ್ ಹುಡುಕಿ ↗",
    helpKisanTitle: "24/7 ಕಿಸಾನ್ ಕಾಲ್ ಸೆಂಟರ್ ಸಹಾಯವಾಣಿ",
    helpKisanDesc: "ತುರ್ತು ಬೆಳೆ ಸಲಹೆಗಾಗಿ ನಿಮ್ಮ ಮಾತೃಭಾಷೆಯಲ್ಲಿ ವಿಜ್ಞಾನಿಗಳೊಂದಿಗೆ ಮಾತನಾಡಿ.",
    helpKisanBtn: "ಕಿಸಾನ್ ಸಹಾಯವಾಣಿ 1800-180-1551 ಗೆ ಕರೆ ಮಾಡಿ 📞"
  },
  bn: {
    announcement: "স্মার্ট কৃষি। স্বাস্থ্যকর আগামী।",
    liveVit: "লাইভ ViT-384 মডেল",
    hello: "নমস্কার,",
    navDash: "ড্যাশবোর্ড",
    navScan: "ফসল স্ক্যান",
    navFarm: "আমার খামার",
    navHist: "ইতিহাস",
    navAdv: "স্মার্ট পরামর্শ",
    navSet: "সেটিংস",
    navHelp: "সাহায্য ও কেভিকে",
    tagline: "স্বাস্থ্যকর ফসল,<br>সুখী কৃষক",
    scanTitle: "গাছের পাতা স্ক্যান করুন",
    scanSub: "রোগ শনাক্ত করতে পাতার ছবি আপলোড করুন অথবা ক্যামেরা ব্যবহার করুন",
    btnChoose: "ছবি বাছুন",
    btnCamera: "ক্যামেরা ব্যবহার করুন",
    btnRunAgain: "আবার চালান",
    btnAnalyse: "পাতা বিশ্লেষণ করুন",
    diagComplete: "রোগ শনাক্তকরণ সম্পন্ন",
    confidence: "সঠিকতা",
    severity: "তীব্রতা",
    affectedArea: "আক্রান্ত পাতার অংশ",
    symptomsTitle: "শনাক্তকৃত লক্ষণসমূহ",
    certifiedProtocol: "প্রত্যয়িত মাঠ প্রোটোকল",
    viewReport: "বিস্তারিত রিপোর্ট দেখুন →",
    readAloud: "পড়ে শোনান",
    diagFeedback: "এই শনাক্তকরণ কি সঠিক ছিল?",
    btnAccurate: "👍 হ্যাঁ, নির্ভুল",
    btnReportErr: "👎 ত্রুটি জানান",
    advHeading: "এআই-ভিত্তিক প্রতিকার পরামর্শ",
    advAwaiting: "শনাক্তকরণের অপেক্ষায়",
    advSubtext: "রোগ অনুযায়ী চিকিৎসা এবং প্রতিরোধ নির্দেশিকা পেতে পাতা স্ক্যান করুন।",
    advDoTitle: "এখন কি করবেন",
    advDoSub: "তাৎক্ষণিক করণীয়",
    advDoStandby: "চিকিৎসার ধাপ দেখতে প্রথমে পাতা স্ক্যান করুন।",
    advDontTitle: "যা করবেন না",
    advDontSub: "জরুরী সতর্কতা",
    advDontStandby: "ভুল স্প্রে এড়ানোর সতর্কতা স্ক্যানের পর প্রদর্শিত হবে।",
    advPrevTitle: "প্রতিরোধ",
    advPrevSub: "দীর্ঘমেয়াদী মাঠ প্রোটোকল",
    advPrevStandby: "ফসল পর্যায়ক্রম এবং সুরক্ষা নির্দেশিকা স্ক্যানের পর আসবে।",
    whTitle: "ফসল স্বাস্থ্য বিশ্লেষণ",
    whSub: "NDVI এবং ক্যানোপি সূচক",
    whLive: "লাইভ টেলিমেট্রি",
    whCanopy: "ক্যানোপি কভার",
    whMoisture: "পাতার আর্দ্রতা",
    whChloro: "ক্লোরোফিল",
    whStress: "স্ট্রেস সূচক",
    whStatus: "ফসলের অবস্থা: চমৎকার · স্বাভাবিক বৃদ্ধি এবং স্বাস্থ্যকর গাছপালা।",
    wrTitle: "আঞ্চলিক ও আবহাওয়া সতর্কতা",
    wrSub: "লাইভ আবহাওয়া তথ্য",
    wrAlerts: "২টি সতর্কতা সক্রিয়",
    wrNearKvk: "📍 নিকটস্থ কেভিকে মানচিত্র ↗",
    wrViewDetails: "বিস্তারিত দেখুন →",
    aiTitle: "ক্রপগার্ড এআই-কে জিজ্ঞাসা করুন",
    aiSub: "কৃষি রসায়নবিদ ও পরামর্শক",
    aiPlaceholder: "উদা: ১০০L জলে ১L ম্যানকোজেব দিয়েছি — ঠিক না ভুল?",
    aiChip1: "🧪 ১০০L এ ১L ম্যানকোজেব?",
    aiChip2: "🧴 ক্লোরোথ্যালোনিল মাত্রা?",
    aiChip3: "🌧️ ৮৫% আর্দ্রতায় স্প্রে?",
    aiChip4: "⚠️ স্প্রে করার পর পাতা পোড়া?",
    setHeroTitle: "অ্যাপ্লিকেশন সেটিংস",
    setHeroSub: "ক্রপগার্ড কাস্টমাইজ করুন — থিম, ভাষা, এআই মডেল ও এপিআই কি।",
    setAppTitle: "রূপরেখা (Appearance)",
    setAppSub: "ক্রপগার্ডের দৃশ্যপট পরিবর্তন করুন",
    setThemeLabel: "🌓 থিম মোড",
    setLangLabel: "🌐 ভাষা",
    setAiTitle: "এআই মডেল",
    setAiSub: "ViT-384 মডেল কনফিগার করুন",
    setConfLabel: "🎯 মডেল সঠিকতার থ্রেশহোল্ড",
    setConfNote: "এই সীমার নিচের ফলাফলগুলো বাদ দেওয়া হয়",
    setActiveModelLabel: "⚡ সক্রিয় মডেল",
    setGroqTitle: "Groq LLM API",
    setGroqSub: "Llama 3.3 70B চালিত ক্রপগার্ড এআই",
    setGroqBannerTitle: "মুহূর্তেই কৃষি বুদ্ধিমত্তা",
    setGroqBannerSub: "কীটনাশক মাত্রা ও পরামর্শের জন্য ফ্রি Groq কি যোগ করুন।",
    setKeyLabel: "🔑 এপিআই কি",
    setKeyOptional: "(ঐচ্ছিক)",
    btnSaveKey: "💾 কি সংরক্ষণ করুন",
    setAboutTitle: "ক্রপগার্ড সম্পর্কে",
    setAboutSub: "সংস্করণ ও সিস্টেম তথ্য",
    setTagline: "ক্রপগার্ড — উন্নত আগামীর জন্য কৃষকদের এআই ক্ষমতায়ন।",
    helpHeroTitle: "🌾 কৃষি বিজ্ঞান কেন্দ্র (KVK) ও কৃষি সহায়তা",
    helpHeroSub: "প্রত্যয়িত কেভিকে কেন্দ্র, মাটি পরীক্ষা ল্যাব ও সরকারি কৃষি বিজ্ঞানীদের সাথে যোগাযোগ করুন।",
    helpBackDash: "← ড্যাশবোর্ডে ফিরে যান",
    helpKvkTitle: "নিকটস্থ কৃষি বিজ্ঞান কেন্দ্র (KVK)",
    helpKvkDesc: "গুগল ম্যাপে দিকনির্দেশনা সহ আপনার জেলার নিকটতম কেভিকে খুঁজুন।",
    helpKvkBtn: "গুগল ম্যাপে KVK খুলুন ↗",
    helpSoilTitle: "মাটি ও উদ্ভিদ রোগ নির্ণয় গবেষণাগার",
    helpSoilDesc: "মাটি ও পাতা পরীক্ষার জন্য নিকটস্থ অনুমোদিত ল্যাব খুঁজুন।",
    helpSoilBtn: "মানচিত্রে মাটি পরীক্ষা ল্যাব খুঁজুন ↗",
    helpKisanTitle: "২৪/৭ কিষাণ কল সেন্টার হেল্পলাইন",
    helpKisanDesc: "জরুরী কৃষি পরামর্শের জন্য আপনার মাতৃভাষায় টোল-ফ্রি বিজ্ঞানীদের সাথে কথা বলুন।",
    helpKisanBtn: "কিষাণ হেল্পলাইন ১৮০০-১৮০-১৫৫১ কল করুন 📞"
  }
};

/* ── Multilingual Crop & Disease Translation Engine ── */
const CROP_TRANSLATIONS = {
  tomato: {
    en: 'Tomato', hi: 'टमाटर', pa: 'ਟਮਾਟਰ', mr: 'टोमॅटो',
    te: 'టమోటా', ta: 'தக்காளி', gu: 'ટામેટાં', kn: 'ಟೊಮ್ಯಾಟೊ', bn: 'টমেটো'
  },
  potato: {
    en: 'Potato', hi: 'आलू', pa: 'ਆਲੂ', mr: 'बटाटा',
    te: 'బంగాళాదుంప', ta: 'உருளைக்கிழங்கு', gu: 'બટાકા', kn: 'ಆಲೂಗಡ್ಡೆ', bn: 'আলু'
  },
  corn: {
    en: 'Corn (Maize)', hi: 'मक्का', pa: 'ਮੱਕੀ', mr: 'मका',
    te: 'మొక్కజొన్న', ta: 'மக்காச்சோளம்', gu: 'મકાઈ', kn: 'ಮೆಕ್ಕೆಜೋಳ', bn: 'ভুট্টা'
  },
  maize: {
    en: 'Maize', hi: 'मक्का', pa: 'ਮੱਕੀ', mr: 'मका',
    te: 'మొక్కజొన్న', ta: 'மக்காச்சோளம்', gu: 'મકાઈ', kn: 'ಮೆಕ್ಕೆಜೋಳ', bn: 'ভুট্টা'
  },
  apple: {
    en: 'Apple', hi: 'सेब', pa: 'ਸੇਬ', mr: 'सफरचंद',
    te: 'ఆపిల్', ta: 'ஆப்பிள்', gu: 'સફરજન', kn: 'ಸೇಬು', bn: 'আপেল'
  },
  grape: {
    en: 'Grape', hi: 'अंगूर', pa: 'ਅੰਗੂਰ', mr: 'द्राक्षे',
    te: 'ద్రాక్ష', ta: 'திராட்சை', gu: 'દ્રાક્ષ', kn: 'ದ್ರಾಕ್ಷಿ', bn: 'আঙুর'
  },
  rice: {
    en: 'Rice (Paddy)', hi: 'धान', pa: 'ਝੋਨਾ', mr: 'भात',
    te: 'వరి', ta: 'நெல்', gu: 'ડાંગર', kn: 'ಭತ್ತ', bn: 'ধান'
  },
  wheat: {
    en: 'Wheat', hi: 'गेहूँ', pa: 'ਕਣਕ', mr: 'गहू',
    te: 'గోధుమ', ta: 'கோதுமை', gu: 'ઘઉં', kn: 'ಗೋಧಿ', bn: 'গম'
  },
  pepper: {
    en: 'Bell Pepper', hi: 'शिमला मिर्च', pa: 'ਸ਼ਿਮਲਾ ਮਿਰਚ', mr: 'ढोबळी मिरची',
    te: 'బెంగళూరు మిరప', ta: 'குடைமிளகாய்', gu: 'કેપ્સિકમ', kn: 'ದಪ್ಪಮೆಣಸಿನಕಾಯಿ', bn: 'ক্যাপসিকাম'
  }
};

const DISEASE_TERMS = {
  early_blight: {
    en: 'Early Blight', hi: 'अगेती झुलसा', pa: 'ਅਗੇਤੀ ਝੁਲਸਾ', mr: 'लवकर येणारा करपा',
    te: 'ముందస్తు ముడత', ta: 'முன்கூட்டிய கருகல்', gu: 'વહેલો સુકારો', kn: 'ಆರಂಭಿಕ ಕಮರು ರೋಗ', bn: 'আগাম ধ্বসা'
  },
  late_blight: {
    en: 'Late Blight', hi: 'पछेती झुलसा', pa: 'ਪਛੇਤੀ ਝੁਲਸਾ', mr: 'उशिरा येणारा करपा',
    te: 'ఆలస్యపు ముడత', ta: 'பின்கூட்டிய கருகல்', gu: 'પાછોતરો સુકારો', kn: 'ತಡವಾದ ಕಮರು ರೋಗ', bn: 'নাবি ধ্বসা'
  },
  healthy: {
    en: 'Healthy', hi: 'स्वस्थ', pa: 'ਸਿਹਤਮੰਦ', mr: 'निरोगी',
    te: 'ఆరోగ్యకరమైనది', ta: 'ஆரோக்கியமானது', gu: 'તંદુરસ્ત', kn: 'ಆರೋಗ್ಯಕರ', bn: 'স্বাস্থ্যকর'
  },
  rust: {
    en: 'Common Rust', hi: 'रतुआ (गेरुआ)', pa: 'ਕੁੰਗੀ', mr: 'तांबेरा',
    te: 'తుప్పు తెగులు', ta: 'துரு நோய்', gu: 'ગેરુ', kn: 'ತುಕ್ಕು ರೋಗ', bn: 'মরিচা রোগ'
  },
  leaf_scorch: {
    en: 'Leaf Scorch', hi: 'पत्ती झुलसन', pa: 'ਪੱਤਾ ਝੁਲਸ', mr: 'पान करपणे',
    te: 'ఆకు ఎండు తెగులు', ta: 'இலை கருகல்', gu: 'પાનનો સુકારો', kn: 'ಎಲೆ ಸುಡುವ ರೋಗ', bn: 'পাতা ঝলসানো'
  },
  northern_leaf_blight: {
    en: 'Northern Leaf Blight', hi: 'उत्तरी पत्ती झुलसा', pa: 'ਉੱਤਰੀ ਪੱਤਾ ਝੁਲਸ', mr: 'उत्तर पाने करपा',
    te: 'ఉత్తర ఆకు ముడత', ta: 'வடக்கு இலை கருகல்', gu: 'ઉત્તરીય પાન સુકારો', kn: 'ಉತ್ತರದ ಎಲೆ ಕಮರು', bn: 'উত্তরাঞ্চলীয় পাতা ধ্বসা'
  }
};

/**
 * Translates a given disease / diagnosis string into the user's selected language
 */
function translateDiagnosisName(rawName, l) {
  if (!rawName) return '';
  if (l === 'en') return rawName;
  const s = String(rawName).toLowerCase();

  // Find crop
  let cropStr = '';
  for (const c of ['tomato', 'potato', 'corn', 'maize', 'apple', 'grape', 'rice', 'wheat', 'pepper']) {
    if (s.includes(c)) {
      cropStr = CROP_TRANSLATIONS[c][l] || CROP_TRANSLATIONS[c].en;
      break;
    }
  }

  // Find disease
  let disStr = '';
  if (s.includes('healthy')) disStr = DISEASE_TERMS.healthy[l];
  else if (s.includes('early') && s.includes('blight')) disStr = DISEASE_TERMS.early_blight[l];
  else if (s.includes('late') && s.includes('blight')) disStr = DISEASE_TERMS.late_blight[l];
  else if (s.includes('northern')) disStr = DISEASE_TERMS.northern_leaf_blight[l];
  else if (s.includes('rust')) disStr = DISEASE_TERMS.rust[l];
  else if (s.includes('scorch')) disStr = DISEASE_TERMS.leaf_scorch[l];

  if (cropStr && disStr) {
    return `${cropStr} · ${disStr}`;
  }
  if (disStr) return disStr;
  return rawName;
}

const PIPELINE_STAGES = {
  en: [
    'Captures & verifies leaf photo',
    'Resizes & balances image for AI',
    'Separates leaf from background',
    'Scans for 38 disease patterns',
    'Highlights infection spots',
    'Measures damage & spread %',
    'Prepares safe spray advice'
  ],
  hi: [
    'पत्ती की फोटो लेता और जांचता है',
    'AI के लिए फोटो का आकार व रंग ठीक करता है',
    'पत्ती को पृष्ठभूमि से अलग करता है',
    '38 फसल रोगों के पैटर्न की पहचान करता है',
    'संक्रमित व क्षतिग्रस्त हिस्सों को दर्शाता है',
    'संक्रमण का फैलाव व नुकसान मापता है',
    'सुरक्षित छिड़काव व उपचार सलाह तैयार करता है'
  ],
  pa: [
    'ਪੱਤੇ ਦੀ ਫੋਟੋ ਲੈਂਦਾ ਅਤੇ ਜਾਂਚਦਾ ਹੈ',
    'AI ਲਈ ਫੋਟੋ ਦਾ ਸਾਈਜ਼ ਤੇ ਰੰਗ ਠੀਕ ਕਰਦਾ ਹੈ',
    'ਪੱਤੇ ਨੂੰ ਪਿੱਠਭੂਮੀ ਤੋਂ ਵੱਖ ਕਰਦਾ ਹੈ',
    '38 ਫ਼ਸਲ ਬਿਮਾਰੀਆਂ ਦੇ ਪੈਟਰਨ ਦੀ ਪਛਾਣ ਕਰਦਾ ਹੈ',
    'ਬਿਮਾਰੀ ਨਾਲ ਪ੍ਰਭਾਵਿਤ ਹਿੱਸਿਆਂ ਨੂੰ ਦਿਖਾਉਂਦਾ ਹੈ',
    'ਬਿਮਾਰੀ ਦਾ ਫੈਲਾਅ ਅਤੇ ਨੁਕਸਾਨ ਮਾਪਦਾ ਹੈ',
    'ਸੁਰੱਖਿਅਤ ਛਿੜਕਾਅ ਤੇ ਇਲਾਜ ਸਲਾਹ ਤਿਆਰ ਕਰਦਾ ਹੈ'
  ],
  mr: [
    'पानाचा फोटो घेतो आणि तपासतो',
    'AI साठी फोटोचा आकार व रंग संतुलित करतो',
    'पानाला पार्श्वभूमीपासून वेगळे करतो',
    '३८ पीक रोगांच्या लक्षणांची तपासणी करतो',
    'बाधित व नुकसान झालेले भाग दाखवतो',
    'संसर्गाचा प्रसार व नुकसान मोजतो',
    'सुरक्षित फवारणी व उपचार सल्ला देतो'
  ],
  te: [
    'ఆకు ఫోటోను తీసి ధృవీకరిస్తుంది',
    'AI కోసం పరిమాణం & రంగులను సర్దుబాటు చేస్తుంది',
    'నేపథ్యం నుండి ఆకును వేరు చేస్తుంది',
    '38 పంట వ్యాధుల లక్షణాలను గుర్తిస్తుంది',
    'వ్యాధి సోకిన భాగాలను హైలైట్ చేస్తుంది',
    'నష్టం & వ్యాప్తి శాతాన్ని లెక్కిస్తుంది',
    'సురక్షిత పిచికారీ సలహాను సిద్ధం చేస్తుంది'
  ],
  ta: [
    'இலை புகைப்படத்தை எடுத்து சரிபார்க்கிறது',
    'AI-க்காக படத்தின் அளவு & வண்ணத்தை சரிசெய்கிறது',
    'பின்னணியில் இருந்து இலையை பிரிக்கிறது',
    '38 பயிர் நோய் வடிவங்களை ஸ்கேன் செய்கிறது',
    'பாதிக்கப்பட்ட பகுதிகளைக் காட்டுகிறது',
    'தொற்று பரவல் சதவீதம் & சேதத்தை அளவிடுகிறது',
    'பாதுகாப்பான தெளிப்பு ஆலோசனையை வழங்குகிறது'
  ],
  gu: [
    'પાંદડાનો ફોટો કેપ્ચર અને તપાસે છે',
    'AI માટે ચિત્રનું કદ અને રંગ સંતુલિત કરે છે',
    'પૃષ્ઠભૂમિથી પાંદડાને અલગ કરે છે',
    '38 પાક રોગોના લક્ષણોની ઓળખ કરે છે',
    'ક્ષતિગ્રસ્ત ભાગોને હાઇલાઇટ કરે છે',
    'ચેપનો ફેલાવો અને નુકસાન માપે છે',
    'સુરક્ષિત છંટકાવની સલાહ તૈયાર કરે છે'
  ],
  kn: [
    'ಎಲೆಯ ಫೋಟೋವನ್ನು ತೆಗೆದು ಪರಿಶೀಲಿಸುತ್ತದೆ',
    'AI ಗಾಗಿ ಚಿತ್ರದ ಗಾತ್ರ ಮತ್ತು ಬಣ್ಣವನ್ನು ಸರಿಹೊಂದಿಸುತ್ತದೆ',
    'ಹಿನ್ನೆಲೆಯಿಂದ ಎಲೆಯನ್ನು ಪ್ರತ್ಯೇಕಿಸುತ್ತದೆ',
    '38 ಬೆಳೆ ರೋಗಗಳ ಲಕ್ಷಣಗಳನ್ನು ಗುರುತಿಸುತ್ತದೆ',
    'ರೋಗಪೀಡಿತ ಹಾನಿಯ ಭಾಗಗಳನ್ನು ತೋರಿಸುತ್ತದೆ',
    'ಸೋಂಕಿನ ಹರಡುವಿಕೆ ಮತ್ತು ಹಾನಿಯನ್ನು ಅಳೆಯುತ್ತದೆ',
    'ಸುರಕ್ಷಿತ ಸಿಂಪಡಣೆ ಸಲಹೆಯನ್ನು ಸಿದ್ಧಪಡಿಸುತ್ತದೆ'
  ],
  bn: [
    'পাতার ছবি তোলে ও যাচাই করে',
    'AI এর জন্য ছবির আকার ও রঙ ঠিক করে',
    'পটভূমি থেকে পাতাকে আলাদা করে',
    '৩৮টি ফসলের রোগের লক্ষণ স্ক্যান করে',
    'ক্ষতিগ্রস্ত অংশগুলো চিহ্নিত করে',
    'সংক্রমণের বিস্তার ও ক্ষতি পরিমাপ করে',
    'নিরাপদ স্প্রে ও চিকিৎসার পরামর্শ প্রস্তুত করে'
  ]
};

if (typeof window !== 'undefined') {
  window.translateDiagnosisName = translateDiagnosisName;
  window.applyLanguage = applyLanguage;
  window.I18N = I18N;
  window.PIPELINE_STAGES = PIPELINE_STAGES;
}
function applyLanguage(selectedLang) {
  if (!SUPPORTED_LANGS[selectedLang]) selectedLang = 'en';
  lang = selectedLang;
  window.lang = selectedLang;
  if (typeof localStorage !== 'undefined') {
    try {
      localStorage.setItem('cropguard_lang', selectedLang);
    } catch (_) {}
  }

  if (typeof document !== 'undefined') {
    document.documentElement.lang = selectedLang;
  }

  const t = I18N[selectedLang] || I18N.en;
  if (typeof document === 'undefined') return;

  // Sync Dropdown in Header
  const langSel = document.getElementById('langSel');
  if (langSel && langSel.value !== selectedLang) {
    langSel.value = selectedLang;
  }

  // Sync Segmented Buttons in Settings
  document.querySelectorAll('[data-l]').forEach(btn => {
    const isCurrent = (btn.dataset.l === selectedLang);
    btn.classList.toggle('active', isCurrent);
    btn.classList.toggle('on', isCurrent);
  });

  // 1. Header Bar
  const annPill = document.querySelector('.announcement-pill span:last-child');
  if (annPill) annPill.textContent = t.announcement;

  const demoChip = document.getElementById('demoChip');
  if (demoChip) {
    demoChip.innerHTML = `<i class="led-dot">●</i> ${t.liveVit}`;
  }

  const uNameBox = document.querySelector('.user-name-box span');
  if (uNameBox) {
    uNameBox.innerHTML = `${t.hello} <b>Ramesh Ji</b>`;
  }

  // 2. Sidebar Navigation
  const navMap = [
    { sel: 'a[href="#dashboard"] span', key: 'navDash' },
    { sel: 'a[href="#scan"] span', key: 'navScan' },
    { sel: 'a[href="#farmMon"] span', key: 'navFarm' },
    { sel: 'a[href="#history"] span', key: 'navHist' },
    { sel: 'a[href="#pipeline"] span', key: 'navAdv' },
    { sel: 'a[href="#settings"] span', key: 'navSet' },
    { sel: 'a[href="#help"] span', key: 'navHelp' }
  ];
  navMap.forEach(({ sel, key }) => {
    const el = document.querySelector(sel);
    if (el && t[key]) el.textContent = t[key];
  });

  const tagline = document.querySelector('.farmer-tagline');
  if (tagline && t.tagline) tagline.innerHTML = t.tagline;

  // 3. Scan Leaf Card
  const scanTitle = document.querySelector('.scan-card-head h3');
  if (scanTitle) {
    scanTitle.innerHTML = `<span class="scan-ico">🌿</span> ${t.scanTitle}`;
  }
  const scanSub = document.querySelector('.scan-card-head .sub');
  if (scanSub) scanSub.textContent = t.scanSub;

  const btnChoose = document.querySelector('#lblChoose span');
  if (btnChoose) btnChoose.textContent = t.btnChoose;

  const btnCamera = document.querySelector('#lblCamera span');
  if (btnCamera) btnCamera.textContent = t.btnCamera;

  const runBtnText = document.querySelector('#run span:last-child');
  if (runBtnText) {
    runBtnText.textContent = (typeof R !== 'undefined' && R) ? t.btnRunAgain : t.btnAnalyse;
  }

  // 4. Recent Diagnosis Card
  const diagPill = document.querySelector('.diag-status-pill span');
  if (diagPill) diagPill.textContent = t.diagComplete;

  const repBtn = document.querySelector('#rep span');
  if (repBtn) repBtn.textContent = t.viewReport;

  const sayBtn = document.querySelector('#say span:last-child');
  if (sayBtn) sayBtn.textContent = t.readAloud;

  const feedPrompt = document.querySelector('.diag-feedback-prompt');
  if (feedPrompt) feedPrompt.textContent = t.diagFeedback;

  const feedYes = document.querySelector('#feedbackYes span:last-child');
  if (feedYes) feedYes.textContent = t.btnAccurate;

  const feedNo = document.querySelector('#feedbackNo span:last-child');
  if (feedNo) feedNo.textContent = t.btnReportErr;

  const metricCaptions = document.querySelectorAll('.metric-caption');
  if (metricCaptions[0]) metricCaptions[0].textContent = t.confidence;
  if (metricCaptions[1]) metricCaptions[1].textContent = t.severity;

  const sevAreaLabel = document.querySelector('.sev-track-label span:last-child');
  if (sevAreaLabel) sevAreaLabel.textContent = t.affectedArea;

  const symTitle = document.querySelector('.diag-sec-title span:last-child');
  if (symTitle) symTitle.textContent = t.symptomsTitle;

  const protoBadge = document.querySelector('.advisory-badge-row span:last-child');
  if (protoBadge) protoBadge.textContent = t.certifiedProtocol;

  // 5. 3 Advisory Action Cards
  const advHeading = document.querySelector('.advisory-main-heading span:last-child');
  if (advHeading) advHeading.textContent = t.advHeading;

  const advPill = document.getElementById('advisoryStatePill');
  if (advPill && (!advPill.classList.contains('active'))) {
    advPill.textContent = t.advAwaiting;
  }

  const advSub = document.getElementById('advisorySubtext');
  if (advSub && (!advPill || !advPill.classList.contains('active'))) {
    advSub.textContent = t.advSubtext;
  }

  const card1Head = document.querySelector('.action-card-header.navy h4');
  if (card1Head) card1Head.textContent = t.advDoTitle;
  const card1Sub = document.getElementById('subDo');
  if (card1Sub && (!advPill || !advPill.classList.contains('active'))) {
    card1Sub.textContent = t.advDoSub;
  }

  const card2Head = document.querySelector('.action-card-header.red h4');
  if (card2Head) card2Head.textContent = t.advDontTitle;
  const card2Sub = document.getElementById('subDont');
  if (card2Sub && (!advPill || !advPill.classList.contains('active'))) {
    card2Sub.textContent = t.advDontSub;
  }

  const card3Head = document.querySelector('.action-card-header.green h4');
  if (card3Head) card3Head.textContent = t.advPrevTitle;
  const card3Sub = document.getElementById('subPrevent');
  if (card3Sub && (!advPill || !advPill.classList.contains('active'))) {
    card3Sub.textContent = t.advPrevSub;
  }

  // Standby placeholder list items
  const standbyDo = document.querySelector('#actionDoList .standby-item');
  if (standbyDo) standbyDo.textContent = t.advDoStandby;
  const standbyDont = document.querySelector('#actionDontList .standby-item');
  if (standbyDont) standbyDont.textContent = t.advDontStandby;
  const standbyPrev = document.querySelector('#actionPreventList .standby-item');
  if (standbyPrev) standbyPrev.textContent = t.advPrevStandby;

  // 6. Bottom 3 Widgets
  const whTitle = document.querySelector('#farmMon .widget-head h4');
  if (whTitle) whTitle.textContent = t.whTitle;
  const whSub = document.querySelector('#farmMon .widget-head-sub');
  if (whSub) whSub.textContent = t.whSub;
  const whLive = document.querySelector('.live-status-pill');
  if (whLive) whLive.innerHTML = `<i class="led-blink">●</i> ${t.whLive}`;

  const hMetrics = document.querySelectorAll('.h-metric-item small');
  if (hMetrics[0]) hMetrics[0].textContent = t.whCanopy;
  if (hMetrics[1]) hMetrics[1].textContent = t.whMoisture;
  if (hMetrics[2]) hMetrics[2].textContent = t.whChloro;
  if (hMetrics[3]) hMetrics[3].textContent = t.whStress;

  const whFooter = document.querySelector('.health-footer-msg span:last-child');
  if (whFooter) whFooter.textContent = t.whStatus;

  const wrTitle = document.querySelector('#regAlerts .widget-head h4');
  if (wrTitle) wrTitle.textContent = t.wrTitle;
  const wrSub = document.querySelector('#regAlerts .widget-head-sub');
  if (wrSub) wrSub.textContent = t.wrSub;
  const wrKvk = document.querySelector('#dashKvkLink span');
  if (wrKvk) wrKvk.textContent = t.wrNearKvk;
  const wrView = document.getElementById('viewAlertDetails');
  if (wrView) wrView.textContent = t.wrViewDetails;

  const aiTitle = document.querySelector('#askAi .widget-head h4');
  if (aiTitle) aiTitle.textContent = t.aiTitle;
  const aiSub = document.querySelector('#askAi .widget-head-sub');
  if (aiSub) aiSub.textContent = t.aiSub;
  const aiInput = document.getElementById('aiInput');
  if (aiInput) aiInput.placeholder = t.aiPlaceholder;

  // Quick Chips
  const chips = document.querySelectorAll('.ai-chip');
  if (chips[0]) chips[0].textContent = t.aiChip1;
  if (chips[1]) chips[1].textContent = t.aiChip2;
  if (chips[2]) chips[2].textContent = t.aiChip3;
  if (chips[3]) chips[3].textContent = t.aiChip4;

  // 7. Settings Page
  const setHeroTitle = document.querySelector('.settings-hero-title');
  if (setHeroTitle) setHeroTitle.textContent = t.setHeroTitle;
  const setHeroSub = document.querySelector('.settings-hero-sub');
  if (setHeroSub) setHeroSub.textContent = t.setHeroSub;

  const setCardTitles = document.querySelectorAll('.settings-card-title');
  const setCardSubs = document.querySelectorAll('.settings-card-sub');
  if (setCardTitles[0]) setCardTitles[0].textContent = t.setAppTitle;
  if (setCardSubs[0]) setCardSubs[0].textContent = t.setAppSub;
  if (setCardTitles[1]) setCardTitles[1].textContent = t.setAiTitle;
  if (setCardSubs[1]) setCardSubs[1].textContent = t.setAiSub;
  if (setCardTitles[2]) setCardTitles[2].textContent = t.setGroqTitle;
  if (setCardSubs[2]) setCardSubs[2].textContent = t.setGroqSub;
  if (setCardTitles[3]) setCardTitles[3].textContent = t.setAboutTitle;
  if (setCardSubs[3]) setCardSubs[3].textContent = t.setAboutSub;

  const setLabels = document.querySelectorAll('.settings-label');
  if (setLabels[0]) setLabels[0].textContent = t.setThemeLabel;
  if (setLabels[1]) setLabels[1].textContent = t.setLangLabel;
  if (setLabels[2]) setLabels[2].textContent = t.setConfLabel;
  if (setLabels[3]) setLabels[3].textContent = t.setActiveModelLabel;

  const confNote = document.querySelector('.settings-conf-note');
  if (confNote) confNote.textContent = t.setConfNote;

  const groqBannerHead = document.querySelector('.settings-groq-banner b');
  if (groqBannerHead) groqBannerHead.textContent = t.setGroqBannerTitle;
  const groqBannerDesc = document.querySelector('.settings-groq-banner p');
  if (groqBannerDesc) groqBannerDesc.textContent = t.setGroqBannerSub;

  const saveKeyBtnText = document.querySelector('#saveSettingsGroqKey span:last-child');
  if (saveKeyBtnText) saveKeyBtnText.textContent = t.btnSaveKey;

  const setTaglineText = document.querySelector('.settings-about-tagline span:last-child');
  if (setTaglineText) setTaglineText.textContent = t.setTagline;

  // 8. Help Page
  const helpHeroTitle = document.querySelector('.help-title-box h2');
  if (helpHeroTitle) helpHeroTitle.textContent = t.helpHeroTitle;
  const helpHeroSub = document.querySelector('.help-title-box p');
  if (helpHeroSub) helpHeroSub.textContent = t.helpHeroSub;

  const helpBackBtn = document.querySelector('#helpBackDashBtn span:last-child');
  if (helpBackBtn) helpBackBtn.textContent = t.helpBackDash;

  const helpCards = document.querySelectorAll('.help-action-card');
  if (helpCards[0]) {
    const h3 = helpCards[0].querySelector('h3');
    const p = helpCards[0].querySelector('p');
    const span = helpCards[0].querySelector('a span');
    if (h3) h3.textContent = t.helpKvkTitle;
    if (p) p.textContent = t.helpKvkDesc;
    if (span) span.textContent = t.helpKvkBtn;
  }
  if (helpCards[1]) {
    const h3 = helpCards[1].querySelector('h3');
    const p = helpCards[1].querySelector('p');
    const span = helpCards[1].querySelector('a span');
    if (h3) h3.textContent = t.helpSoilTitle;
    if (p) p.textContent = t.helpSoilDesc;
    if (span) span.textContent = t.helpSoilBtn;
  }
  if (helpCards[2]) {
    const h3 = helpCards[2].querySelector('h3');
    const p = helpCards[2].querySelector('p');
    const span = helpCards[2].querySelector('a span');
    if (h3) h3.textContent = t.helpKisanTitle;
    if (p) p.textContent = t.helpKisanDesc;
    if (span) span.textContent = t.helpKisanBtn;
  }

  // 8.5. Pipeline Stage Explanations in easy-to-understand plain language
  const stageDescs = PIPELINE_STAGES[selectedLang] || PIPELINE_STAGES.en;
  if (stageDescs) {
    for (let i = 0; i < 7; i++) {
      const el = document.getElementById('ndDesc' + i);
      if (el && stageDescs[i]) el.textContent = stageDescs[i];
    }
  }

  // 9. If a diagnosis is active, re-render with translated disease name and localized advice
  if (typeof R !== 'undefined' && R && typeof show === 'function') {
    try {
      show();
    } catch (e) {
      console.warn('show() re-render error:', e);
    }
  }
}

// Initialise language system on DOM ready
(function initI18n() {
  let savedLang = 'en';
  if (typeof localStorage !== 'undefined') {
    try {
      savedLang = localStorage.getItem('cropguard_lang') || 'en';
    } catch (_) {}
  }
  lang = savedLang;
  if (typeof window !== 'undefined') {
    window.lang = savedLang;
  }

  const onReady = () => {
    applyLanguage(savedLang);

    // Bind dropdown
    const langSel = document.getElementById('langSel');
    if (langSel) {
      langSel.addEventListener('change', function () {
        applyLanguage(this.value);
      });
    }

    // Bind all buttons with data-l
    document.querySelectorAll('[data-l]').forEach(btn => {
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        applyLanguage(this.dataset.l);
      });
    });
  };

  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', onReady);
    } else {
      setTimeout(onReady, 10);
    }
  }
})();
