"""Generate full, high-quality, schema-valid knowledge base entries for the 23 missing classes.

Strict safety:
- Exactly 3 symptoms, 3 do_now, 3 prevent (both EN and HI)
- Any fungicide / miticide / copper reference in EN MUST contain the word 'label'
- NO dosage numbers (ml, g, kg, %, etc.)
- Fully adheres to contracts/knowledge.schema.json
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KB_DIR = ROOT / "knowledge_base" / "broad"
KB_DIR.mkdir(parents=True, exist_ok=True)

HEALTHY_CROPS = [
    ("Apple___healthy", "Apple", "सेब"),
    ("Blueberry___healthy", "Blueberry", "ब्लूबेरी"),
    ("Cherry_including_sour___healthy", "Cherry", "चेरी"),
    ("Corn_maize___healthy", "Maize", "मक्का"),
    ("Grape___healthy", "Grape", "अंगूर"),
    ("Peach___healthy", "Peach", "आड़ू"),
    ("Raspberry___healthy", "Raspberry", "रसभरी"),
    ("Soybean___healthy", "Soybean", "सोयाबीन"),
    ("Strawberry___healthy", "Strawberry", "स्ट्रॉबेरी"),
]

def make_healthy_entry(cid, en_crop, hi_crop):
    return {
        "id": cid,
        "crop": {"en": en_crop, "hi": hi_crop},
        "disease": {"en": "Healthy", "hi": "स्वस्थ"},
        "scientific_name": None,
        "type": "healthy",
        "healthy": True,
        "symptoms": {
            "en": [
                "Even green colour across the leaf surface",
                "No visible spots, blotches, powdery residue or curling",
                "Foliage tissue is firm, vigorous and undamaged"
            ],
            "hi": [
                "पत्ती की सतह पर एक समान हरा रंग",
                "कोई धब्बा, फफूंद, चूर्ण या मुड़ाव नहीं",
                "पत्ती का ऊतक स्वस्थ, मजबूत और अक्षत है"
            ]
        },
        "do_now": {
            "en": [
                "Continue regular monitoring of the crop canopy each week",
                "Maintain adequate irrigation and balanced soil nutrient management",
                "Inspect leaf undersides periodically for early pest activity"
            ],
            "hi": [
                "हर हफ्ते फसल की नियमित रूप से निगरानी करते रहें",
                "उचित सिंचाई और संतुलित पोषण प्रबंधन बनाए रखें",
                "शुरुआती कीटों के संकेतों के लिए पत्तियों की निचली सतह की जांच करें"
            ]
        },
        "avoid_extra": {
            "en": [
                "Do not apply unnecessary chemical pesticides on healthy foliage"
            ],
            "hi": [
                "स्वस्थ पत्तियों पर अनावश्यक रासायनिक कीटनाशकों का छिड़काव न करें"
            ]
        },
        "prevent": {
            "en": [
                "Ensure proper plant spacing to facilitate sunlight and air flow",
                "Remove fallen crop debris and weeds around field borders",
                "Source certified pathogen-free seeds and planting material"
            ],
            "hi": [
                "धूप और हवा के लिए पौधों के बीच उचित दूरी रखें",
                "खेत के आसपास गिरी पत्तियाँ और खरपतवार हटाएँ",
                "प्रमाणित और रोगमुक्त रोपण सामग्री का उपयोग करें"
            ]
        },
        "sources": [
            {"name": "UC IPM Pest Management Guidelines", "url": "https://ipm.ucanr.edu/"},
            {"name": "Penn State Extension", "url": "https://extension.psu.edu/"}
        ],
        "review": {
            "status": "draft",
            "note": f"Draft entry for {en_crop} healthy foliage."
        }
    }

DISEASE_ENTRIES = [
    {
        "id": "Apple___Apple_scab",
        "crop": {"en": "Apple", "hi": "सेब"},
        "disease": {"en": "Apple Scab", "hi": "सेब का स्कैब (पपड़ी रोग)"},
        "scientific_name": "Venturia inaequalis",
        "type": "fungal",
        "healthy": False,
        "symptoms": {
            "en": [
                "Olive-green or brown velvety spots developing on leaf surfaces",
                "Spots darken, become scabby and cause leaf distortion",
                "Infected leaves turn yellow and drop prematurely from the tree"
            ],
            "hi": [
                "पत्ती की सतह पर जैतून जैसे हरे या भूरे मखमली धब्बे",
                "धब्बे काले होकर पपड़ीदार और विकृत हो जाते हैं",
                "संक्रमित पत्तियाँ पीली होकर समय से पहले गिर जाती हैं"
            ]
        },
        "do_now": {
            "en": [
                "Prune and dispose of severely infected leaves and twigs",
                "Rake and destroy fallen orchard leaves to lower fungal spores",
                "If necessary, apply a registered protective fungicide strictly per label instructions and local agricultural officer advice"
            ],
            "hi": [
                "गंभीर रूप से संक्रमित पत्तियों और टहनियों को काटकर नष्ट करें",
                "फंगल बीजाणुओं को कम करने के लिए गिरी हुई पत्तियों को नष्ट करें",
                "आवश्यकता होने पर पंजीकृत फफूंदनाशक का उपयोग केवल लेबल और कृषि अधिकारी की सलाह पर करें"
            ]
        },
        "avoid_extra": {"en": [], "hi": []},
        "prevent": {
            "en": [
                "Select scab-resistant apple cultivars for new orchard blocks",
                "Prune tree canopies annually to allow rapid drying of leaves",
                "Avoid overhead irrigation that keeps foliage wet for long periods"
            ],
            "hi": [
                "नए रोपण के लिए स्कैब-प्रतिरोधी सेब की किस्मों का चयन करें",
                "पत्तियों को जल्दी सुखाने के लिए छतरी की उचित छंटाई करें",
                "ऊपर से पानी देने से बचें जिससे पत्तियाँ लंबे समय तक गीली रहें"
            ]
        },
        "sources": [
            {"name": "Cornell Fruit Resources - Apple Scab", "url": "https://cals.cornell.edu/fruit-resources"},
            {"name": "Penn State Extension - Apple Diseases", "url": "https://extension.psu.edu/"}
        ],
        "review": {"status": "draft", "note": "Draft entry for Apple scab based on extension guidance."}
    },
    {
        "id": "Apple___Black_rot",
        "crop": {"en": "Apple", "hi": "सेब"},
        "disease": {"en": "Black Rot", "hi": "काला सड़न रोग (ब्लैक रॉट)"},
        "scientific_name": "Botryosphaeria obtusa",
        "type": "fungal",
        "healthy": False,
        "symptoms": {
            "en": [
                "Small purple specks on leaves enlarging into frog-eye spots",
                "Spots develop tan centres bordered by distinct dark purple margins",
                "Infected fruit exhibits firm dark rotting concentric rings"
            ],
            "hi": [
                "पत्तियों पर छोटे बैंगनी धब्बे जो बाद में मेंढक की आंख जैसे बन जाते हैं",
                "धब्बों का केंद्र भूरा-बादामी और किनारा गहरा बैंगनी होता है",
                "संक्रमित फलों पर सख्त काले सड़न के छल्ले दिखाई देते हैं"
            ]
        },
        "do_now": {
            "en": [
                "Prune out dead wood, twigs, and mummified fruit clusters",
                "Clear and dispose of infected orchard debris from the ground",
                "Apply an approved copper fungicide adhering strictly to product label directions and expert advice"
            ],
            "hi": [
                "पेड़ से सूखी लकड़ी, टहनियाँ और सड़े हुए फल काटकर हटाएँ",
                "बगीचे से संक्रमित अवशेषों को इकट्ठा कर सुरक्षित नष्ट करें",
                "पंजीकृत तांबा (कॉपर) युक्त फफूंदनाशक लेबल और अधिकारी की सलाह अनुसार डालें"
            ]
        },
        "avoid_extra": {"en": [], "hi": []},
        "prevent": {
            "en": [
                "Maintain tree vigour through balanced organic and mineral nutrition",
                "Treat pruning wounds promptly to prevent pathogen entry",
                "Inspect tree limbs during dormant periods to remove old cankers"
            ],
            "hi": [
                "संतुलित खाद देकर पेड़ को मजबूत और स्वस्थ रखें",
                "फंगस के प्रवेश को रोकने के लिए छाल के घावों का तुरंत उपचार करें",
                "कवक के घावों की जांच के लिए नियमित रूप से पेड़ों का निरीक्षण करें"
            ]
        },
        "sources": [
            {"name": "Penn State Extension - Apple Black Rot", "url": "https://extension.psu.edu/"},
            {"name": "University of Kentucky Plant Pathology", "url": "https://plantpathology.ca.uky.edu/"}
        ],
        "review": {"status": "draft", "note": "Draft entry for Apple Black Rot."}
    },
    {
        "id": "Apple___Cedar_apple_rust",
        "crop": {"en": "Apple", "hi": "सेब"},
        "disease": {"en": "Cedar Apple Rust", "hi": "सीडर एप्पल रस्ट"},
        "scientific_name": "Gymnosporangium juniperi-virginianae",
        "type": "fungal",
        "healthy": False,
        "symptoms": {
            "en": [
                "Bright yellow-orange or reddish spots on upper leaf surfaces",
                "Tiny black fruiting bodies form inside the orange lesions",
                "Tubular fungal projections develop underneath infected leaves"
            ],
            "hi": [
                "पत्ती की ऊपरी सतह पर चमकीले पीले-नारंगी या लाल धब्बे",
                "नारंगी धब्बों के अंदर छोटे काले बिंदु दिखाई देते हैं",
                "पत्ती की निचली सतह पर नलिकाकार कवक संरचनाएं बनती हैं"
            ]
        },
        "do_now": {
            "en": [
                "Remove nearby juniper or red cedar galls within proximity if feasible",
                "Pick off isolated infected leaves during early disease detection",
                "Apply an approved rust fungicide strictly according to product label guidelines and agricultural officer advice"
            ],
            "hi": [
                "यदि संभव हो तो आसपास लगे जुनिपर या देवदार की गांठों को हटाएँ",
                "शुरुआती लक्षण दिखने पर संक्रमित पत्तियों को तोड़ लें",
                "अनुमोदित रस्ट फफूंदनाशक का छिड़काव लेबल और कृषि अधिकारी के निर्देशानुसार करें"
            ]
        },
        "avoid_extra": {"en": [], "hi": []},
        "prevent": {
            "en": [
                "Plant rust-immune or resistant apple cultivars",
                "Avoid planting apple trees adjacent to ornamental juniper trees",
                "Monitor orchard foliage closely from early bud break onward"
            ],
            "hi": [
                "रस्ट-प्रतिरोधी सेब की किस्मों को प्राथमिकता दें",
                "जुनिपर के पेड़ों के एकदम पास सेब के पेड़ न लगाएँ",
                "कलियाँ खिलने के समय पेड़ों पर विशेष ध्यान दें"
            ]
        },
        "sources": [
            {"name": "University of Minnesota Extension - Cedar Apple Rust", "url": "https://extension.umn.edu/"},
            {"name": "Penn State Extension", "url": "https://extension.psu.edu/"}
        ],
        "review": {"status": "draft", "note": "Draft entry for Cedar Apple Rust."}
    },
    {
        "id": "Cherry_including_sour___Powdery_mildew",
        "crop": {"en": "Cherry", "hi": "चेरी"},
        "disease": {"en": "Powdery Mildew", "hi": "चूर्णिल आसिता (पाउडरी मिल्ड्यू)"},
        "scientific_name": "Podosphaera clandestina",
        "type": "fungal",
        "healthy": False,
        "symptoms": {
            "en": [
                "White powdery fungal patches on young leaves and shoot tips",
                "Infected leaves curl upward, distort and become brittle",
                "Severe infection stunts shoot elongation and blemishes fruit"
            ],
            "hi": [
                "युवा पत्तियों और हरी टहनियों पर सफेद चूर्ण जैसी फफूंद",
                "संक्रमित पत्तियाँ ऊपर की ओर मुड़ जाती हैं और विकृत होती हैं",
                "गंभीर संक्रमण से नई टहनियों का विकास रुक जाता है"
            ]
        },
        "do_now": {
            "en": [
                "Prune affected terminal shoot tips to lower fungal inoculum",
                "Improve sunlight penetration and air movement within the tree",
                "Apply a registered sulfur or triazole fungicide strictly per label directions and expert consultation"
            ],
            "hi": [
                "फफूंद को कम करने के लिए प्रभावित टहनियों की हल्की छंटाई करें",
                "पेड़ के बीच धूप और हवा का आवागमन सुधारें",
                "पंजीकृत सल्फर या अन्य फफूंदनाशक का उपयोग लेबल और विशेषज्ञ की सलाह अनुसार करें"
            ]
        },
        "avoid_extra": {"en": [], "hi": []},
        "prevent": {
            "en": [
                "Avoid excessive nitrogen fertilizers that stimulate tender growth",
                "Water trees using ground-level drip rather than overhead sprinklers",
                "Sanitize pruning shears with disinfectant between cuts"
            ],
            "hi": [
                "अत्यधिक नाइट्रोजन खाद से बचें जो कोमल कमजोर पत्तियों को बढ़ावा देती है",
                "ऊपर से फुहार देने के बजाय ड्रिप से सिंचाई करें",
                "छंटाई के औज़ारों को नियमित रूप से सैनिटाइज़ करें"
            ]
        },
        "sources": [
            {"name": "Washington State University Extension - Cherry Powdery Mildew", "url": "http://treefruit.wsu.edu/"},
            {"name": "UC IPM - Cherry Powdery Mildew", "url": "https://ipm.ucanr.edu/"}
        ],
        "review": {"status": "draft", "note": "Draft entry for Cherry Powdery Mildew."}
    },
    {
        "id": "Corn_maize___Cercospora_leaf_spot_Gray_leaf_spot",
        "crop": {"en": "Maize", "hi": "मक्का"},
        "disease": {"en": "Cercospora / Gray Leaf Spot", "hi": "सर्कोस्पोरा / ग्रे पत्ती धब्बा"},
        "scientific_name": "Cercospora zeae-maydis",
        "type": "fungal",
        "healthy": False,
        "symptoms": {
            "en": [
                "Small tan spots with yellow halos expanding into rectangular lesions",
                "Lesions are restricted by parallel leaf veins into blocky stripes",
                "Gray fungal spores develop inside lesions under warm humid weather"
            ],
            "hi": [
                "पीले घेरे वाले छोटे बादामी धब्बे जो आयताकार घावों में बदलते हैं",
                "नसों की बनावट के कारण धब्बे आयताकार पट्टियों जैसे दिखते हैं",
                "गर्म और आर्द्र मौसम में धब्बों पर धूसर फफूंद जम जाती है"
            ]
        },
        "do_now": {
            "en": [
                "Scout lower leaves around flowering to gauge infection severity",
                "Tear away heavily diseased lower foliage if managing small farm plots",
                "If threshold warrants, apply a recommended foliar fungicide strictly following label directions and extension guidance"
            ],
            "hi": [
                "फूल आने के समय संक्रमण की जांच के लिए निचली पत्तियों को देखें",
                "छोटे खेतों में अत्यधिक रोगग्रस्त निचली पत्तियों को हटाएँ",
                "यदि आवश्यकता हो, तो अनुशंसित फफूंदनाशक का उपयोग केवल लेबल और कृषि सलाह अनुसार करें"
            ]
        },
        "avoid_extra": {"en": [], "hi": []},
        "prevent": {
            "en": [
                "Plant maize hybrids with proven genetic resistance to gray leaf spot",
                "Rotate fields with non-host crops like soybean or wheat",
                "Incorporate crop residue into the soil after harvest to hasten decomposition"
            ],
            "hi": [
                "ग्रे लीफ स्पॉट प्रतिरोधी मक्का की संकर किस्मों को बोएं",
                "सोयाबीन या गेहूं जैसी गैर-फसलों के साथ फसल चक्र अपनाएँ",
                "कटाई के बाद अवशेषों को मिट्टी में दबाकर नष्ट करें"
            ]
        },
        "sources": [
            {"name": "Purdue Extension - Gray Leaf Spot of Corn", "url": "https://extension.purdue.edu/"},
            {"name": "Iowa State University Extension", "url": "https://crops.extension.iastate.edu/"}
        ],
        "review": {"status": "draft", "note": "Draft entry for Gray Leaf Spot of Maize."}
    },
    {
        "id": "Corn_maize___Common_rust",
        "crop": {"en": "Maize", "hi": "मक्का"},
        "disease": {"en": "Common Rust", "hi": "सामान्य रतुआ (रस्ट)"},
        "scientific_name": "Puccinia sorghi",
        "type": "fungal",
        "healthy": False,
        "symptoms": {
            "en": [
                "Golden-brown to cinnamon-brown pustules scattered on both leaf surfaces",
                "Pustules erupt through the leaf surface releasing powdery spores",
                "Pustules turn brownish-black later in the growing season"
            ],
            "hi": [
                "पत्ती की दोनों सतहों पर सुनहरे-भूरे रंग के फफोले (पस्ट्यूल)",
                "फफोले फटकर चूर्ण जैसे बीजाणु बिखेरते हैं",
                "मौसम के अंत में फफोले काले-भूरे रंग के हो जाते हैं"
            ]
        },
        "do_now": {
            "en": [
                "Inspect upper leaves prior to silking to assess rust intensity",
                "Maintain optimal plant nutrition to support crop vigour",
                "If rust progresses aggressively, apply an approved fungicide strictly following product label and expert guidance"
            ],
            "hi": [
                "जांचें कि क्या बालियां निकलने से पहले ऊपरी पत्तियों पर रस्ट के धब्बे हैं",
                "तनाव से निपटने के लिए संतुलित पोषण दें",
                "यदि रोग तेजी से फैले तो पंजीकृत फफूंदनाशक का प्रयोग लेबल और अधिकारी की सलाह पर करें"
            ]
        },
        "avoid_extra": {"en": [], "hi": []},
        "prevent": {
            "en": [
                "Plant rust-tolerant hybrid corn varieties with resistance genes",
                "Time sowing early in the planting window to escape spore migration",
                "Destroy volunteer maize plants that harbor overwintering rust spores"
            ],
            "hi": [
                "रस्ट-सहनशील मक्के की किस्मों का प्रयोग करें",
                "समय पर बुवाई करें ताकि बीजाणुओं के फैलाव से बचा जा सके",
                "खेत के आसपास उग आए आवारा मक्के के पौधों को नष्ट करें"
            ]
        },
        "sources": [
            {"name": "University of Illinois Extension - Corn Rust", "url": "https://extension.illinois.edu/"},
            {"name": "Iowa State University Extension", "url": "https://crops.extension.iastate.edu/"}
        ],
        "review": {"status": "draft", "note": "Draft entry for Common Rust of Maize."}
    },
    {
        "id": "Corn_maize___Northern_Leaf_Blight",
        "crop": {"en": "Maize", "hi": "मक्का"},
        "disease": {"en": "Northern Leaf Blight", "hi": "उत्तरी पत्ती झुलसा"},
        "scientific_name": "Exserohilum turcicum",
        "type": "fungal",
        "healthy": False,
        "symptoms": {
            "en": [
                "Long, elliptical grayish-green or tan lesions shaped like cigars",
                "Lesions can reach several inches long and coalesce across the leaf",
                "Dark fuzzy spores appear in lesion centres during humid weather"
            ],
            "hi": [
                "सिगार के आकार के लंबे, अंडाकार धूसर-हरे या बादामी घाव",
                "धब्बे कई इंच लंबे होकर आपस में मिल जाते हैं",
                "आर्द्र मौसम में धब्बों के बीच में गहरे रंग के बीजाणु दिखते हैं"
            ]
        },
        "do_now": {
            "en": [
                "Assess whether leaf lesions have reached the ear leaves during tasseling",
                "Avoid late afternoon overhead watering to minimize leaf wetness",
                "Apply an approved foliar fungicide strictly following product label and local agronomic guidelines"
            ],
            "hi": [
                "नर मंजरी आने के समय देखें कि क्या रोग कान की पत्ती के ऊपर पहुंच गया है",
                "पत्तियों को रात में गीला रहने से बचाने के लिए सिंचाई का समय सुधारें",
                "अनुमोदित फफूंदनाशक का उपयोग उत्पाद लेबल और कृषि निर्देशों के अनुसार करें"
            ]
        },
        "avoid_extra": {"en": [], "hi": []},
        "prevent": {
            "en": [
                "Select maize hybrids possessing multi-gene resistance to northern leaf blight",
                "Practice two-year crop rotation out of continuous corn",
                "Till diseased corn stubble into the ground after harvest to speed breakdown"
            ],
            "hi": [
                "उत्तरी पत्ती झुलसा प्रतिरोधी संकर किस्मों का चयन करें",
                "लगातार मक्का बोने के बजाय दो साल का फसल चक्र अपनाएँ",
                "कटाई के बाद अवशेषों की गहरी जुताई करें"
            ]
        },
        "sources": [
            {"name": "Purdue Extension - Northern Corn Leaf Blight", "url": "https://extension.purdue.edu/"},
            {"name": "University of Minnesota Extension", "url": "https://extension.umn.edu/"}
        ],
        "review": {"status": "draft", "note": "Draft entry for Northern Corn Leaf Blight."}
    },
    {
        "id": "Grape___Black_rot",
        "crop": {"en": "Grape", "hi": "अंगूर"},
        "disease": {"en": "Black Rot", "hi": "काला सड़न रोग (ब्लैक रॉट)"},
        "scientific_name": "Guignardia bidwellii",
        "type": "fungal",
        "healthy": False,
        "symptoms": {
            "en": [
                "Small circular reddish-brown spots surrounded by dark borders on leaves",
                "Tiny black pycnidia pimples form a ring inside leaf spots",
                "Berries turn dark brown, shrivel into hard black wrinkled mummies"
            ],
            "hi": [
                "पत्तियों पर लाल-भूरे गोल धब्बे जिनके चारों ओर गहरा किनारा होता है",
                "धब्बों के अंदर छोटे काले दानों की एक गोल लकीर बनती है",
                "अंगूर के दाने सूखकर काले, सिकुड़े हुए पत्थर जैसे हो जाते हैं"
            ]
        },
        "do_now": {
            "en": [
                "Prune and remove all mummified fruit clusters hanging on the vines",
                "Strip off early spotted leaves to restrict initial spore dispersal",
                "Apply an approved systemic fungicide strictly per label directions and agricultural advisor recommendations"
            ],
            "hi": [
                "बेलों पर लटके सभी सूखे और सड़े हुए अंगूरों के गुच्छों को तोड़कर नष्ट करें",
                "बीजाणुओं के प्रसार को रोकने के लिए शुरुआती संक्रमित पत्तियों को हटाएँ",
                "अनुमोदित फफूंदनाशक का उपयोग केवल लेबल और कृषि विशेषज्ञ की सलाह अनुसार करें"
            ]
        },
        "avoid_extra": {"en": [], "hi": []},
        "prevent": {
            "en": [
                "Open up vine canopies through trellising and summer pruning for maximum airflow",
                "Mow ground cover and remove vineyard floor debris that hosts spores",
                "Maintain a protective spray schedule during critical spring shoot growth"
            ],
            "hi": [
                "हवा के आवागमन के लिए बेलों की उचित छंटाई और सहारा दें",
                "जमीन पर गिरे हुए संक्रमित अवशेषों को साफ़ रखें",
                "वसंत ऋतु में नई टहनियों के निकलने के समय विशेष निगरानी रखें"
            ]
        },
        "sources": [
            {"name": "Penn State Extension - Grape Black Rot", "url": "https://extension.psu.edu/"},
            {"name": "Cornell Fruit Resources - Grape Diseases", "url": "https://cals.cornell.edu/fruit-resources"}
        ],
        "review": {"status": "draft", "note": "Draft entry for Grape Black Rot."}
    },
    {
        "id": "Grape___Esca_Black_Measles",
        "crop": {"en": "Grape", "hi": "अंगूर"},
        "disease": {"en": "Esca (Black Measles)", "hi": "एस्का (ब्लैक मीज़ल्स)"},
        "scientific_name": "Phaeomoniella chlamydospora",
        "type": "fungal",
        "healthy": False,
        "symptoms": {
            "en": [
                "Interveinal yellowing and necrosis producing a distinct tiger-stripe leaf pattern",
                "Berries develop small dark purple to brown measles-like spots",
                "Wood develops internal dark brown or black vascular streaking"
            ],
            "hi": [
                "पत्तियों की नसों के बीच पीलापन और सूखापन, जिससे बाघ जैसी धारियां बनती हैं",
                "अंगूरों पर चेचक जैसे छोटे गहरे बैंगनी या भूरे धब्बे पड़ते हैं",
                "लकड़ी के अंदर गहरे भूरे या काले रंग की धारियाँ बन जाती हैं"
            ]
        },
        "do_now": {
            "en": [
                "Mark symptomatic vines during summer for delayed winter pruning",
                "Cut out dead cordons and trunk wood well below the infected zone",
                "Apply an approved wound protectant paste strictly following product label and expert instructions"
            ],
            "hi": [
                "सर्दियों में छंटाई के लिए गर्मियों में ही रोगग्रस्त बेलों पर निशान लगा लें",
                "संक्रमित हिस्से से काफी नीचे तक की सूखी लकड़ी को काटकर हटाएँ",
                "विशेषज्ञ की सलाह से ताज़े कटे हुए हिस्सों पर घाव भरने वाला लेप लगाएँ"
            ]
        },
        "avoid_extra": {"en": [], "hi": []},
        "prevent": {
            "en": [
                "Prune vines late in the dormant season during dry weather conditions",
                "Disinfect pruning shears regularly with alcohol or disinfectant",
                "Source certified disease-free rootstocks and nursery benchgrafts"
            ],
            "hi": [
                "सर्दियों के अंत में सूखे मौसम में ही बेलों की छंटाई करें",
                "कटाई के औज़ारों को नियमित रूप से सैनिटाइज़र से साफ़ करें",
                "प्रमाणित और रोगमुक्त नर्सरी पौधों का ही उपयोग करें"
            ]
        },
        "sources": [
            {"name": "UC IPM - Esca (Black Measles)", "url": "https://ipm.ucanr.edu/"},
            {"name": "Penn State Extension - Grape Trunk Diseases", "url": "https://extension.psu.edu/"}
        ],
        "review": {"status": "draft", "note": "Draft entry for Grape Esca / Black Measles."}
    },
    {
        "id": "Grape___Leaf_blight_Isariopsis_Leaf_Spot",
        "crop": {"en": "Grape", "hi": "अंगूर"},
        "disease": {"en": "Leaf Blight (Isariopsis Leaf Spot)", "hi": "पत्ती झुलसा (इसारियोप्सिस पत्ती धब्बा)"},
        "scientific_name": "Pseudocercospora cladosporioides",
        "type": "fungal",
        "healthy": False,
        "symptoms": {
            "en": [
                "Irregular reddish-brown lesions with faint yellow halos on mature leaves",
                "Lesions coalesce into large dry blighted areas causing leaf scorch",
                "Premature defoliation exposes fruit clusters to direct sun damage"
            ],
            "hi": [
                "परिपक्व पत्तियों पर हल्के पीले घेरे वाले अनियमित लाल-भूरे धब्बे",
                "धब्बे मिलकर बड़े सूखे क्षेत्रों में बदल जाते हैं जिससे पत्ती झुलस जाती है",
                "पत्तियों के झड़ने से अंगूर के गुच्छे धूप से जलने लगते हैं"
            ]
        },
        "do_now": {
            "en": [
                "Remove and destroy heavily blighted leaves around fruit clusters",
                "Improve canopy ventilation to facilitate quick morning drying",
                "Spray a recommended copper fungicide strictly according to product label directions and agricultural advisor recommendations"
            ],
            "hi": [
                "गुच्छों के आसपास की अत्यधिक रोगग्रस्त पत्तियों को तोड़कर नष्ट करें",
                "हवा के संचार को सुधारें ताकि पत्तियाँ सुबह जल्दी सूख सकें",
                "लेबल और विशेषज्ञ के निर्देशानुसार अनुशंसित कॉपर फफूंदनाशक का छिड़काव करें"
            ]
        },
        "avoid_extra": {"en": [], "hi": []},
        "prevent": {
            "en": [
                "Ensure balanced vine nutrition without over-fertilizing with nitrogen",
                "Collect and compost or bury fallen vineyard leaves in autumn",
                "Inspect lower canopy leaves regularly following periods of warm rain"
            ],
            "hi": [
                "संतुलित खाद दें और अत्यधिक नाइट्रोजन के प्रयोग से बचें",
                "शरद ऋतु में बगीचे की गिरी हुई पत्तियों को इकट्ठा कर नष्ट करें",
                "बारिश के बाद बेल की निचली पत्तियों की नियमित जांच करें"
            ]
        },
        "sources": [
            {"name": "UC IPM - Grape Diseases", "url": "https://ipm.ucanr.edu/"},
            {"name": "ICAR-National Research Centre for Grapes", "url": "https://nrcgrapes.icar.gov.in/"}
        ],
        "review": {"status": "draft", "note": "Draft entry for Grape Isariopsis Leaf Spot."}
    },
    {
        "id": "Orange___Haunglongbing_Citrus_greening",
        "crop": {"en": "Orange", "hi": "संतरा"},
        "disease": {"en": "Citrus Greening (Huanglongbing)", "hi": "सिट्रस ग्रीनिंग (हुआंगलोंगबिंग)"},
        "scientific_name": "Candidatus Liberibacter asiaticus",
        "type": "bacterial",
        "healthy": False,
        "symptoms": {
            "en": [
                "Asymmetric, blotchy yellow mottling across the leaf blade",
                "Thickened, corky, or raised leaf veins on infected shoots",
                "Small, lopsided fruit that remain green at the stylar end and taste bitter"
            ],
            "hi": [
                "पत्ती पर असमान पीले धब्बे (धब्बेदार पीलापन)",
                "संक्रमित टहनियों पर पत्तियों की नसें मोटी और उभरी हुई हो जाती हैं",
                "छोटे, टेढ़े-मेढ़े फल जो नीचे से हरे रहते हैं और कड़वे स्वाद के होते हैं"
            ]
        },
        "do_now": {
            "en": [
                "Inspect citrus trees for the presence of Asian citrus psyllid vectors",
                "Report suspected greening infections immediately to local agriculture authorities",
                "Safely rogue and eradicate severely infected trees to protect surrounding orchards"
            ],
            "hi": [
                "सिट्रस साइला कीट की उपस्थिति के लिए पेड़ों की जांच करें",
                "संक्रमण का संदेह होने पर तुरंत स्थानीय कृषि अधिकारी को सूचित करें",
                "आसपास के पेड़ों को बचाने के लिए अत्यधिक संक्रमित पेड़ को उखाड़कर नष्ट करें"
            ]
        },
        "avoid_extra": {"en": [], "hi": []},
        "prevent": {
            "en": [
                "Plant only certified pathogen-tested citrus trees from approved nurseries",
                "Implement integrated psyllid vector monitoring and management programs",
                "Never transport uncertified citrus budwood or seedlings between districts"
            ],
            "hi": [
                "केवल प्रमाणित और रोगमुक्त नर्सरी पौधों का ही रोपण करें",
                "वाहक कीट साइला की रोकथाम के लिए अनुशंसित उपाय अपनाएं",
                "बिना प्रमाणन के एक जिले से दूसरे जिले में पौध सामग्री न ले जाएं"
            ]
        },
        "sources": [
            {"name": "USDA APHIS - Citrus Greening", "url": "https://www.aphis.usda.gov/"},
            {"name": "UC IPM - Citrus Greening and Asian Citrus Psyllid", "url": "https://ipm.ucanr.edu/"}
        ],
        "review": {"status": "draft", "note": "Draft entry for Citrus Greening (Huanglongbing)."}
    },
    {
        "id": "Peach___Bacterial_spot",
        "crop": {"en": "Peach", "hi": "आड़ू"},
        "disease": {"en": "Bacterial Spot", "hi": "जीवाणु धब्बा रोग"},
        "scientific_name": "Xanthomonas arboricola pv. pruni",
        "type": "bacterial",
        "healthy": False,
        "symptoms": {
            "en": [
                "Small, water-soaked, angular purple or brown spots on leaves",
                "Centres of spots dry up and drop out leaving a shot-hole appearance",
                "Infected leaves turn yellow at the tips and drop prematurely"
            ],
            "hi": [
                "पत्तियों पर छोटे, पानीदार, कोणीय बैंगनी या भूरे धब्बे",
                "धब्बों का केंद्र सूखकर गिर जाता है जिससे छलनी जैसे छेद बन जाते हैं",
                "संक्रमित पत्तियाँ सिरों से पीली होकर समय से पहले गिर जाती हैं"
            ]
        },
        "do_now": {
            "en": [
                "Prune diseased twigs displaying spring cankers to eliminate overwintering bacteria",
                "Avoid orchard operations when foliage is wet from rain or dew",
                "Apply a registered copper bactericide strictly in accordance with product label guidelines and agricultural officer advice"
            ],
            "hi": [
                "बैक्टीरिया को खत्म करने के लिए घाव वाली टहनियों को काटकर हटाएँ",
                "पत्तियों के गीले होने पर बगीचे में काम करने से बचें",
                "पंजीकृत कॉपर जीवाणुनाशक का उपयोग केवल लेबल और कृषि अधिकारी के निर्देशानुसार करें"
            ]
        },
        "avoid_extra": {"en": [], "hi": []},
        "prevent": {
            "en": [
                "Select peach varieties known to have resistance or tolerance to bacterial spot",
                "Establish windbreaks around sandy sites to decrease wind-driven sand abrasion",
                "Maintain balanced tree nutrition and avoid excessive spring nitrogen"
            ],
            "hi": [
                "जीवाणु धब्बा प्रतिरोधी आड़ू की किस्मों का चयन करें",
                "हवा से रगड़ को कम करने के लिए खेत के चारों ओर वायु-अवरोधक पेड़ लगाएँ",
                "संतुलित पोषण दें और वसंत में अत्यधिक नाइट्रोजन से बचें"
            ]
        },
        "sources": [
            {"name": "Penn State Extension - Peach Bacterial Spot", "url": "https://extension.psu.edu/"},
            {"name": "Clemson Cooperative Extension", "url": "https://hgic.clemson.edu/"}
        ],
        "review": {"status": "draft", "note": "Draft entry for Peach Bacterial Spot."}
    },
    {
        "id": "Squash___Powdery_mildew",
        "crop": {"en": "Squash", "hi": "स्क्वैश (कद्दू वर्ग)"},
        "disease": {"en": "Powdery Mildew", "hi": "चूर्णिल आसिता (पाउडरी मिल्ड्यू)"},
        "scientific_name": "Podosphaera xanthii",
        "type": "fungal",
        "healthy": False,
        "symptoms": {
            "en": [
                "Circular white powdery fungal patches on both leaf surfaces and stems",
                "Spots coalesce covering the entire leaf blade with talcum-powder growth",
                "Infected leaves turn yellow, brown, and wither prematurely"
            ],
            "hi": [
                "पत्तियों और तनों पर सफेद चूर्ण जैसे गोल फफूंद के धब्बे",
                "धब्बे फैलकर पूरी पत्ती को टेलकम पाउडर जैसी फफूंद से ढक देते हैं",
                "संक्रमित पत्तियाँ पीली और भूरी होकर समय से पहले सूख जाती हैं"
            ]
        },
        "do_now": {
            "en": [
                "Pick off and destroy the first few colonized leaves as soon as mildew appears",
                "Ensure plants have ample space for aeration and direct sunlight",
                "Apply an approved bio-fungicide strictly adhering to label specifications and extension advice"
            ],
            "hi": [
                "सफेद फफूंद दिखते ही शुरुआती कुछ संक्रमित पत्तियों को तोड़कर नष्ट करें",
                "पौधों के बीच पर्याप्त धूप और हवा सुनिश्चित करें",
                "अनुमोदित फफूंदनाशक का प्रयोग उत्पाद लेबल और कृषि विस्तार अधिकारी की सलाह पर करें"
            ]
        },
        "avoid_extra": {"en": [], "hi": []},
        "prevent": {
            "en": [
                "Plant powdery mildew resistant squash and pumpkin hybrids",
                "Avoid dense planting and maintain wide row spacing",
                "Water soil at the base using drip irrigation to avoid wet foliage"
            ],
            "hi": [
                "पाउडरी मिल्ड्यू प्रतिरोधी कद्दूवर्गीय किस्मों की बुवाई करें",
                "घने रोपण से बचें और पंक्तियों के बीच पर्याप्त दूरी रखें",
                "पत्तियों को गीला होने से बचाने के लिए ड्रिप सिंचाई का उपयोग करें"
            ]
        },
        "sources": [
            {"name": "Cornell Vegetable MD Online - Cucurbit Powdery Mildew", "url": "https://vegetablemdonline.ppath.cornell.edu/"},
            {"name": "UC IPM - Cucurbits Powdery Mildew", "url": "https://ipm.ucanr.edu/"}
        ],
        "review": {"status": "draft", "note": "Draft entry for Squash Powdery Mildew."}
    },
    {
        "id": "Strawberry___Leaf_scorch",
        "crop": {"en": "Strawberry", "hi": "स्ट्रॉबेरी"},
        "disease": {"en": "Leaf Scorch", "hi": "पत्ती झुलसा (लीफ स्कॉर्च)"},
        "scientific_name": "Diplocarpon earlianum",
        "type": "fungal",
        "healthy": False,
        "symptoms": {
            "en": [
                "Numerous small, irregular dark purple or brown spots on upper leaf surface",
                "Spots lack the white centre typical of common leaf spot",
                "Tissues between spots turn purple or brown, giving the foliage a scorched look"
            ],
            "hi": [
                "पत्ती की ऊपरी सतह पर अनेक छोटे, अनियमित गहरे बैंगनी या भूरे धब्बे",
                "धब्बों के बीच में सफेद केंद्र नहीं होता",
                "धब्बों के बीच की पत्ती सूखकर झुलसी हुई दिखाई देती है"
            ]
        },
        "do_now": {
            "en": [
                "Mow or clip off infected strawberry leaves after harvest and rake them away",
                "Improve row aeration by thinning overcrowded runner plants",
                "If infection is severe, apply an approved protective fungicide strictly per label instructions and local agricultural officer advice"
            ],
            "hi": [
                "कटाई के बाद संक्रमित पत्तियों को काटकर खेत से बाहर निकालें",
                "घने पौधों को छांटकर हवा का आवागमन सुधारें",
                "गंभीर स्थिति में अनुमोदित फफूंदनाशक का उपयोग केवल लेबल और कृषि अधिकारी की सलाह पर करें"
            ]
        },
        "avoid_extra": {"en": [], "hi": []},
        "prevent": {
            "en": [
                "Plant certified disease-free strawberry cultivars with scorch resistance",
                "Avoid excessive overhead irrigation that leaves foliage damp overnight",
                "Renew strawberry beds regularly and maintain clean mulch under plants"
            ],
            "hi": [
                "झुलसा-प्रतिरोधी प्रमाणित स्ट्रॉबेरी पौधों का उपयोग करें",
                "ऊपर से अधिक सिंचाई से बचें ताकि पत्तियाँ रात भर गीली न रहें",
                "स्ट्रॉबेरी की क्यारियों को नियमित रूप से बदलें और साफ़ मल्च रखें"
            ]
        },
        "sources": [
            {"name": "Penn State Extension - Strawberry Leaf Scorch", "url": "https://extension.psu.edu/"},
            {"name": "North Carolina State Extension - Strawberry Scorch", "url": "https://content.ces.ncsu.edu/"}
        ],
        "review": {"status": "draft", "note": "Draft entry for Strawberry Leaf Scorch."}
    }
]

def main():
    written = 0
    # 1. Healthy crops
    for cid, crop_en, crop_hi in HEALTHY_CROPS:
        data = make_healthy_entry(cid, crop_en, crop_hi)
        p = KB_DIR / f"{cid}.json"
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        written += 1
        print(f"Wrote {p.name}")

    # 2. Diseased crops
    for data in DISEASE_ENTRIES:
        cid = data["id"]
        p = KB_DIR / f"{cid}.json"
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        written += 1
        print(f"Wrote {p.name}")

    print(f"\nSuccessfully wrote {written} knowledge base entries to {KB_DIR}")

if __name__ == "__main__":
    main()
