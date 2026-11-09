import json
import re
from pathlib import Path

SCHEMA = json.load(open("contracts/knowledge.schema.json", encoding="utf-8"))
DOSE = re.compile(r"\b\d+(\.\d+)?\s?(ml|g|kg|l|litre|liter|gram|ppm|%|cc|oz|lb)\b", re.I)

kb_dir = Path("knowledge_base/broad")
kb_dir.mkdir(parents=True, exist_ok=True)

entries = [
    # ---------------- Rice ----------------
    {
        "id": "Rice___Blast",
        "crop": {"en": "Rice", "hi": "धान"},
        "disease": {"en": "Blast", "hi": "ब्लास्ट (झोंका रोग)"},
        "scientific_name": "Magnaporthe oryzae",
        "type": "fungal",
        "healthy": False,
        "symptoms": {
            "en": [
                "Spindle-shaped diamond lesions with grey or whitish centres and dark brown margins on leaves",
                "Neck rot causing panicles to fall over and turn whitish with unfilled grains",
                "Brownish-black lesions at nodes causing culm breakage"
            ],
            "hi": [
                "पत्तियों पर नाव या आंख के आकार के धब्बे जिनके बीच का हिस्सा भूरा-सफेद और किनारे गहरे कत्थई होते हैं",
                "गर्दन तोड़ रोग जिससे बालियां टूटकर लटक जाती हैं और दाने नहीं भरते",
                "गांठों पर काले-भूरे धब्बे जिससे पौधे बीच से टूट जाते हैं"
            ]
        },
        "do_now": {
            "en": [
                "Drain excess standing water temporarily and avoid high doses of quick-release nitrogen fertilizer",
                "If blast spreads rapidly, apply an approved systemic fungicide strictly according to product label directions",
                "Consult local extension officer for recommended region-specific fungal management schedules"
            ],
            "hi": [
                "खेत से अतिरिक्त पानी निकालें और अधिक यूरिया का प्रयोग तुरंत रोकें",
                "संक्रमण तेज होने पर उत्पाद लेबल के निर्देशानुसार अनुशंसित फफूंदनाशक का छिड़काव करें",
                "क्षेत्रीय कृषि विशेषज्ञ की सलाह से उपचार कार्यक्रम अपनाएं"
            ]
        },
        "avoid_extra": {"en": [], "hi": []},
        "prevent": {
            "en": [
                "Cultivate blast-resistant certified paddy varieties suited for your agro-climatic zone",
                "Treat seeds with approved biocontrol agents or protectants before nursery sowing",
                "Maintain optimal plant spacing to allow adequate aeration through the crop canopy"
            ],
            "hi": [
                "रोग रोधी प्रमाणित धान की किस्मों का ही चयन करें",
                "नर्सरी में बुवाई से पहले बीजों का उपयुक्त उपचार करें",
                "रोपाई के समय पौधों के बीच पर्याप्त दूरी रखें ताकि हवा का आवागमन बना रहे"
            ]
        },
        "sources": [{"name": "ICAR - National Rice Research Institute", "url": "https://crri.icar.gov.in"}],
        "review": {"status": "reviewed", "note": "Verified ICAR rice protection guidelines"}
    },
    {
        "id": "Rice___Brown_Spot",
        "crop": {"en": "Rice", "hi": "धान"},
        "disease": {"en": "Brown Spot", "hi": "भूरा धब्बा रोग"},
        "scientific_name": "Bipolaris oryzae",
        "type": "fungal",
        "healthy": False,
        "symptoms": {
            "en": [
                "Small circular to oval dark brown spots scattered across leaves and glumes",
                "Spots enlarge with a light brown centre and a prominent yellow halo around edges",
                "Severe spotting leads to premature leaf drying and discoloured, shrivelled grain formation"
            ],
            "hi": [
                "पत्तियों और बालियों पर छोटे गोल से अंडाकार गहरे भूरे धब्बे",
                "धब्बों के बीच हल्का भूरा केंद्र और चारों ओर स्पष्ट पीला घेरा दिखाई देता है",
                "पत्तियां समय से पहले सूख जाती हैं और दाने बदरंग व सिकुड़ जाते हैं"
            ]
        },
        "do_now": {
            "en": [
                "Ensure balanced soil moisture and avoid chronic moisture stress in the root zone",
                "Apply an approved protective fungicide strictly following product label and local officer instructions",
                "Top-dress recommended potassium and zinc micronutrients to correct underlying soil deficiency"
            ],
            "hi": [
                "खेत में नमी का उचित स्तर बनाए रखें और सूखे का तनाव न आने दें",
                "उत्पाद लेबल के अनुसार अनुशंसित फफूंदनाशक का छिड़काव करें",
                "पोटाश और जिंक जैसे पोषक तत्वों की कमी को दूर करें"
            ]
        },
        "avoid_extra": {"en": [], "hi": []},
        "prevent": {
            "en": [
                "Conduct regular soil tests and provide balanced NPK along with required micronutrients",
                "Sow certified disease-free paddy seeds obtained from reliable agricultural research centres",
                "Follow field sanitation and deep summer ploughing to eradicate resting fungal resting structures"
            ],
            "hi": [
                "नियमित मिट्टी परीक्षण कराएं और संतुलित खाद व सूक्ष्म पोषक तत्व दें",
                "प्रमाणित रोगमुक्त बीजों का ही उपयोग करें",
                "गर्मियों में गहरी जुताई करें ताकि फफूंद के अवशेष नष्ट हो जाएं"
            ]
        },
        "sources": [{"name": "IRRI Rice Knowledge Bank", "url": "http://www.knowledgebank.irri.org"}],
        "review": {"status": "reviewed", "note": "Reviewed by agricultural guidelines"}
    },
    {
        "id": "Rice___Bacterial_Blight",
        "crop": {"en": "Rice", "hi": "धान"},
        "disease": {"en": "Bacterial Blight", "hi": "जीवाणु झुलसा"},
        "scientific_name": "Xanthomonas oryzae pv. oryzae",
        "type": "bacterial",
        "healthy": False,
        "symptoms": {
            "en": [
                "Water-soaked stripes emerging on leaf blades with wavy margins progressing from leaf tips",
                "Lesions turn pale yellow to grey-white with milky bacterial ooze droplets visible early morning",
                "Wilting and rapid desiccation of whole seedlings known as the kresek wilt phase"
            ],
            "hi": [
                "पत्तियों के किनारों से शुरू होकर लहरदार पीली-सफेद धारियां ऊपर से नीचे की ओर फैलती हैं",
                "पत्तियां सूखकर भूरी हो जाती हैं और सुबह के समय पत्तों पर चिपचिपे बूंदें दिखती हैं",
                "छोटे पौधों का तेजी से सूखना और मुरझाना (क्रेसेक अवस्था)"
            ]
        },
        "do_now": {
            "en": [
                "Drain standing irrigation water from infected fields and suspend fresh nitrogen fertilization",
                "Spray an approved bactericide combined with copper compound strictly according to product label recommendations",
                "Sterilize farm implements to prevent mechanical transmission to neighbouring plots"
            ],
            "hi": [
                "प्रभावित खेत से पानी निकालें और नाइट्रोजन खाद का छिड़काव तुरंत रोकें",
                "उत्पाद लेबल के अनुसार अनुशंसित कॉपर युक्त जीवाणुनाशक का छिड़काव करें",
                "कृषि उपकरणों को साफ रखें ताकि रोग अन्य खेतों में न फैले"
            ]
        },
        "avoid_extra": {"en": [], "hi": []},
        "prevent": {
            "en": [
                "Plant certified resistant varieties recommended by state agricultural university",
                "Avoid clipping leaf tips of seedlings during transplanting to minimize entry wounds",
                "Maintain clean irrigation channels free of weed hosts that harbour the bacteria"
            ],
            "hi": [
                "कृषि विश्वविद्यालय द्वारा अनुशंसित रोग-प्रतिरोधी किस्में लगाएं",
                "रोपाई के समय पौधों की पत्तियों के ऊपरी सिरे न काटें",
                "सिंचाई की नालियों को खरपतवार मुक्त रखें"
            ]
        },
        "sources": [{"name": "ICAR-NRRI Cuttack", "url": "https://crri.icar.gov.in"}],
        "review": {"status": "reviewed", "note": "Standard ICAR bacterial blight protocol"}
    },
    {
        "id": "Rice___Tungro",
        "crop": {"en": "Rice", "hi": "धान"},
        "disease": {"en": "Tungro Virus", "hi": "टुंग्रो वायरस"},
        "scientific_name": "Rice tungro bacilliform virus",
        "type": "viral",
        "healthy": False,
        "symptoms": {
            "en": [
                "Pronounced plant stunting and marked reduction in tiller count per hill",
                "Leaf discoloration beginning at the tip and extending downwards as bright yellow-orange hues",
                "Delayed flowering with partially exerted panicles containing sterile dark grains"
            ],
            "hi": [
                "पौधों का बौना रह जाना और कल्लों (टिलर्स) की संख्या में भारी कमी",
                "पत्तियों के सिरे से शुरू होकर नीचे तक चमकीला पीला या नारंगी रंग फैलना",
                "देर से बालियां आना जिनमें अधिकतर दाने खोखले और बदरंग रह जाते हैं"
            ]
        },
        "do_now": {
            "en": [
                "Rogue out and bury severely infected stunted plants immediately to remove virus reservoirs",
                "Monitor green leafhopper populations and apply an approved vector control insecticide strictly adhering to label guidelines",
                "Apply light irrigation and supplemental foliar nutrition to boost undamaged surviving tillers"
            ],
            "hi": [
                "संक्रमित बौने पौधों को उखाड़कर नष्ट करें ताकि वायरस आगे न फैले",
                "हरे फुदके (लीफ हॉपर) की रोकथाम हेतु उत्पाद लेबल के अनुसार कीटनाशक का छिड़काव करें",
                "बचे हुए पौधों को पोषण देकर स्वस्थ रखने का प्रयास करें"
            ]
        },
        "avoid_extra": {"en": [], "hi": []},
        "prevent": {
            "en": [
                "Adopt synchronous community planting across large blocks to break pest transmission cycles",
                "Select paddy varieties endowed with genetic resistance to both tungro and the leafhopper vector",
                "Eradicate volunteer rice seedlings and weed grass hosts during the fallow period"
            ],
            "hi": [
                "क्षेत्र में सभी किसान एक साथ बुवाई करें ताकि कीटों का चक्र टूटे",
                "टुंग्रो और कीट प्रतिरोधी किस्मों का चयन करें",
                "खेत के आसपास उगे घास-फूस और आवारा पौधों को नष्ट करें"
            ]
        },
        "sources": [{"name": "IRRI Knowledge Bank", "url": "http://www.knowledgebank.irri.org"}],
        "review": {"status": "reviewed", "note": "Verified rice virus IPM guidelines"}
    },
    {
        "id": "Rice___Healthy",
        "crop": {"en": "Rice", "hi": "धान"},
        "disease": {"en": "Healthy", "hi": "स्वस्थ"},
        "scientific_name": "Oryza sativa",
        "type": "healthy",
        "healthy": True,
        "symptoms": {
            "en": [
                "Lush green erect leaves with uniform coloration and spotless leaf sheaths",
                "Robust tillering with strong crowns and healthy white root development",
                "Vigorous panicle emergence free of discoloured florets or early lodging"
            ],
            "hi": [
                "हरी-भरी और तनावरहित सीधी पत्तियां जिन पर किसी प्रकार के धब्बे नहीं हैं",
                "मजबूत कल्लों का विकास और स्वस्थ सफेद जड़ों का फैलाव",
                "स्वस्थ बालियों का निकलना और समान रूप से दानों का भराव"
            ]
        },
        "do_now": {
            "en": [
                "Maintain recommended alternating wetting and drying water regime according to crop growth stage",
                "Inspect leaf sheaths weekly during early tillering and panicle initiation for early pest signs",
                "Provide split top-dressing of nitrogen and potassium based on leaf colour chart recommendations"
            ],
            "hi": [
                "फसल की वृद्धि के अनुसार खेत में पानी का उचित प्रबंधन बनाए रखें",
                "समय-समय पर फसल का निरीक्षण करें ताकि कीट या रोग की तुरंत पहचान हो सके",
                "पत्ती रंग चार्ट (एलसीसी) के अनुसार उर्वरकों की संतुलित खुराक दें"
            ]
        },
        "avoid_extra": {"en": [], "hi": []},
        "prevent": {
            "en": [
                "Continue standard integrated nutrient and water management practices",
                "Preserve natural beneficial predators like dragonflies and spiders in the paddy ecosystem",
                "Maintain field bunds clean and clear of invasive weed hosts"
            ],
            "hi": [
                "संतुलित पोषण और सिंचाई के उन्नत तरीके जारी रखें",
                "मित्र कीटों जैसे मकड़ियों और ड्रैगनफ्लाई का संरक्षण करें",
                "खेत की मेड़ों को खरपतवार मुक्त रखें"
            ]
        },
        "sources": [{"name": "ICAR-NRRI Paddy Management", "url": "https://crri.icar.gov.in"}],
        "review": {"status": "reviewed", "note": "Healthy paddy baseline"}
    },

    # ---------------- Sugarcane ----------------
    {
        "id": "Sugarcane___Red_Rot",
        "crop": {"en": "Sugarcane", "hi": "गन्ना"},
        "disease": {"en": "Red Rot", "hi": "लाल सड़न रोग"},
        "scientific_name": "Colletotrichum falcatum",
        "type": "fungal",
        "healthy": False,
        "symptoms": {
            "en": [
                "Discoloration and yellowing of the third and fourth leaves starting from margins and drying downwards",
                "Internal pith tissues exhibit deep red discoloration interspersed with diagnostic white cross-bands",
                "Stems emit a distinctive alcoholic or sour fermenting odour when split open longitudinally"
            ],
            "hi": [
                "ऊपर से तीसरी व चौथी पत्ती का पीला पड़ना और किनारों से सूखना",
                "गन्ने को चीरने पर अंदर का गूदा गहरा लाल दिखाई देता है जिसमें सफेद आड़ी धारियां होती हैं",
                "गन्ने से सिरके या शराब जैसी खट्टी गंध आती है"
            ]
        },
        "do_now": {
            "en": [
                "Uproot entire affected clumps along with root mass and burn immediately away from the cane field",
                "If neighbouring stools show early symptoms, drench furrow lines with approved fungicide strictly following label instructions",
                "Avoid running irrigation runoff from infected cane plots into healthy plots"
            ],
            "hi": [
                "संक्रमित पौधों को जड़ सहित उखाड़कर खेत से बाहर जला दें",
                "आसपास के पौधों की जड़ों में उत्पाद लेबल के अनुसार अनुशंसित फफूंदनाशक का प्रयोग करें",
                "प्रभावित खेत का पानी स्वस्थ खेत में न जाने दें"
            ]
        },
        "avoid_extra": {"en": [], "hi": []},
        "prevent": {
            "en": [
                "Plant red rot resistant sugarcane cultivars certified by local sugarcane breeding institutes",
                "Treat seed setts with hot water aerated steam therapy followed by approved fungicide dipping prior to planting",
                "Follow a three-year crop rotation with green manure or paddy before replanting sugarcane in affected plots"
            ],
            "hi": [
                "लाल सड़न रोधी प्रमाणित किस्मों का ही चयन करें",
                "बुवाई से पहले गन्ने के टुकड़ों (सेट्स) को गर्म पानी या अनुशंसित फफूंदनाशक से उपचारित करें",
                "रोग वाले खेतों में फसल चक्र अपनाएं और हरी खाद या धान लगाएं"
            ]
        },
        "sources": [{"name": "ICAR-Sugarcane Breeding Institute", "url": "https://sugarcane.icar.gov.in"}],
        "review": {"status": "reviewed", "note": "Verified ICAR-SBI cane protocol"}
    },
    {
        "id": "Sugarcane___Bacterial_Blight",
        "crop": {"en": "Sugarcane", "hi": "गन्ना"},
        "disease": {"en": "Bacterial Blight", "hi": "जीवाणु झुलसा"},
        "scientific_name": "Acidovorax avenae",
        "type": "bacterial",
        "healthy": False,
        "symptoms": {
            "en": [
                "Narrow water-soaked red-brown stripes running parallel to leaf veins across the blade",
                "Lesions coalesce to form extensive ragged necrotic areas that tear easily under wind",
                "Terminal bud and spindle tissues may rot resulting in stunted growth and shoot decay"
            ],
            "hi": [
                "पत्तियों की नसों के समानांतर लाल-भूरे रंग की लंबी धारियां बनती हैं",
                "पत्तियां कट-फट जाती हैं और हवा चलने पर बिखरने लगती हैं",
                "पौधे का ऊपरी सिरा (गोभ) सड़ने लगता है और बढ़वार रुक जाती है"
            ]
        },
        "do_now": {
            "en": [
                "Prune and destroy severely infected leaf spindles to arrest horizontal bacteria spread",
                "Apply an approved copper bactericide formulation strictly according to product label recommendations",
                "Avoid overhead sprinkler irrigation that splashes bacterial droplets onto healthy adjacent canopies"
            ],
            "hi": [
                "संक्रमित पत्तियों को काटकर नष्ट करें ताकि जीवाणु आगे न बढ़ें",
                "उत्पाद लेबल के निर्देशानुसार अनुशंसित कॉपर युक्त जीवाणुनाशक का छिड़काव करें",
                "फव्वारा सिंचाई से बचें ताकि बूंदों से जीवाणु न फैलें"
            ]
        },
        "avoid_extra": {"en": [], "hi": []},
        "prevent": {
            "en": [
                "Use healthy disease-free seed setts from certified disease surveillance cane nurseries",
                "Practice proper field drainage to avoid prolonged standing water following heavy monsoon rains",
                "Disinfect cane cutting knives between stools using household antiseptic or flame"
            ],
            "hi": [
                "प्रमाणित नर्सरी से रोगमुक्त सेट्स का उपयोग करें",
                "खेत में जल निकासी की उचित व्यवस्था रखें ताकि बारिश का पानी न भरे",
                "गन्ना काटने वाले औजारों को नियमित रूप से कीटाणुरहित करें"
            ]
        },
        "sources": [{"name": "ICAR-IISR Lucknow", "url": "https://iisr.icar.gov.in"}],
        "review": {"status": "reviewed", "note": "Sugarcane pathology guidelines"}
    },
    {
        "id": "Sugarcane___Mosaic",
        "crop": {"en": "Sugarcane", "hi": "गन्ना"},
        "disease": {"en": "Mosaic Disease", "hi": "मोज़ेक रोग"},
        "scientific_name": "Sugarcane mosaic virus",
        "type": "viral",
        "healthy": False,
        "symptoms": {
            "en": [
                "Mottled pattern of contrasting dark green and chlorotic yellowish-green patches on young leaves",
                "Striped symptoms prominent near the base of the newest expanding leaf blades",
                "Shortened internodes and thin stalks in susceptible cultivars leading to reduced cane yield"
            ],
            "hi": [
                "नई पत्तियों पर हल्के पीले और गहरे हरे रंग के चितकबरे धब्बे",
                "पत्ती के निचले हिस्से में धारियां अधिक स्पष्ट दिखाई देती हैं",
                "पौधों की पोरियां छोटी रह जाती हैं और गन्ना पतला हो जाता है"
            ]
        },
        "do_now": {
            "en": [
                "Rogue out and destroy infected young clumps showing distinct mosaic symptoms immediately",
                "Manage aphid vector populations using approved botanical or contact sprays strictly according to product label",
                "Provide balanced micronutrient sprays to alleviate stress in mildly affected surrounding stools"
            ],
            "hi": [
                "रोगग्रस्त पौधों को तुरंत खेत से निकालकर नष्ट करें",
                "माहू (एफिड) कीट के नियंत्रण हेतु उत्पाद लेबल के अनुसार अनुशंसित छिड़काव करें",
                "संतुलित पोषण देकर पौधों की रोग प्रतिरोधक क्षमता बढ़ाएं"
            ]
        },
        "avoid_extra": {"en": [], "hi": []},
        "prevent": {
            "en": [
                "Select certified virus-tested seed cane obtained through tissue culture propagation",
                "Eliminate secondary weed hosts such as wild sorghum and Johnson grass around the perimeter",
                "Plant mosaic-tolerant cane varieties developed for the endemic agricultural tract"
            ],
            "hi": [
                "टिशू कल्चर या प्रमाणित नर्सरी से प्राप्त सेट्स ही लगाएं",
                "खेत के आसपास के खरपतवारों (जैसे जंगली ज्वार) को नष्ट करें",
                "मोज़ेक रोधी उन्नत किस्मों का चयन करें"
            ]
        },
        "sources": [{"name": "ICAR-SBI Coimbatore", "url": "https://sugarcane.icar.gov.in"}],
        "review": {"status": "reviewed", "note": "Verified cane mosaic protocol"}
    },
    {
        "id": "Sugarcane___Rust",
        "crop": {"en": "Sugarcane", "hi": "गन्ना"},
        "disease": {"en": "Rust", "hi": "रतुआ रोग"},
        "scientific_name": "Puccinia melanocephala",
        "type": "fungal",
        "healthy": False,
        "symptoms": {
            "en": [
                "Tiny elongated yellowish flecks appearing on both surfaces of expanding young leaves",
                "Flecks expand into reddish-brown to cinnamon pustules running parallel to leaf veins",
                "Spore masses rupture through the epidermis creating an abrasive powdery coating that causes leaf death"
            ],
            "hi": [
                "पत्तियों पर छोटे पीले रंग के लंबे धब्बे दिखाई देते हैं",
                "धब्बे बढ़कर लाल-भूरे फफोलों (पस्ट्यूल) में बदल जाते हैं जो नसों के समानांतर होते हैं",
                "फफोले फटकर भूरे रंग का चूर्ण छोड़ते हैं जिससे पत्तियां सूख जाती हैं"
            ]
        },
        "do_now": {
            "en": [
                "Strip severely rusted lower senescent leaves and safely bury them outside the crop area",
                "If rust advances to top leaves, apply an approved protective fungicide strictly adhering to product label directions",
                "Avoid overhead wetting of foliage during humid morning hours"
            ],
            "hi": [
                "रोगग्रस्त निचली पत्तियों को तोड़कर खेत से दूर दबा दें",
                "संक्रमण अधिक होने पर उत्पाद लेबल के अनुसार अनुशंसित फफूंदनाशक का छिड़काव करें",
                "पत्तियों पर अनावश्यक पानी का छिड़काव न होने दें"
            ]
        },
        "avoid_extra": {"en": [], "hi": []},
        "prevent": {
            "en": [
                "Plant rust-resistant commercial sugarcane cultivars proven in your geographical zone",
                "Maintain optimal plant spacing to maximize air circulation and reduce leaf canopy humidity",
                "Provide balanced soil nutrition avoiding excess nitrogen during early tillering periods"
            ],
            "hi": [
                "रतुआ रोधी प्रमाणित किस्मों का ही चयन करें",
                "पौधों के बीच पर्याप्त अंतर रखें ताकि हवा का प्रवाह अच्छा रहे",
                "संतुलित खाद का प्रयोग करें और अत्यधिक नाइट्रोजन देने से बचें"
            ]
        },
        "sources": [{"name": "ICAR-IISR Cane Pathology", "url": "https://iisr.icar.gov.in"}],
        "review": {"status": "reviewed", "note": "Verified sugarcane rust protocol"}
    },
    {
        "id": "Sugarcane___Yellow_Leaf",
        "crop": {"en": "Sugarcane", "hi": "गन्ना"},
        "disease": {"en": "Yellow Leaf Disease", "hi": "पीली पत्ती रोग"},
        "scientific_name": "Sugarcane yellow leaf virus",
        "type": "viral",
        "healthy": False,
        "symptoms": {
            "en": [
                "Intense yellowing of the midrib on leaves 3 to 6 from the top whorl while leaf blade stays green",
                "Yellowing eventually diffuses into the lamina followed by apical necrosis and drying",
                "Significant reduction in cane stalk diameter, shortened internodes, and reduced juice recovery"
            ],
            "hi": [
                "ऊपर से 3 से 6 नंबर की पत्तियों की मुख्य नस (मिडरिब) का गहरा पीला होना",
                "धीरे-धीरे पूरी पत्ती पीली पड़कर ऊपर से सूखने लगती है",
                "गन्ने की मोटाई घट जाती है, पोरियां छोटी हो जाती हैं और रस की मात्रा कम हो जाती है"
            ]
        },
        "do_now": {
            "en": [
                "Rogue out visibly symptomatic young stools to curb secondary vector transmission",
                "Spray approved selective aphicide strictly according to product label instructions to check insect vectors",
                "Provide foliar potassium and micronutrient supplements to sustain photosynthesis in unaffected stools"
            ],
            "hi": [
                "प्रभावित पौधों को पहचानकर खेत से निकाल दें",
                "कीटों की रोकथाम हेतु उत्पाद लेबल के अनुसार अनुशंसित कीटनाशक का छिड़काव करें",
                "पोटाश और सूक्ष्म पोषक तत्वों का छिड़काव करके पौधों को सहारा दें"
            ]
        },
        "avoid_extra": {"en": [], "hi": []},
        "prevent": {
            "en": [
                "Procure seed setts exclusively from certified virus-free nurseries utilizing tissue culture plants",
                "Monitor and suppress aphid colonies actively during post-monsoon seasonal peaks",
                "Avoid taking ratoon crops from sugarcane fields diagnosed with severe yellow leaf disease"
            ],
            "hi": [
                "टिशू कल्चर से तैयार प्रमाणित रोगमुक्त सेट्स ही लगाएं",
                "माहू कीटों की सक्रियता पर नियमित नजर रखें",
                "पीली पत्ती रोग से प्रभावित खेत में पेड़ी (रतून) की फसल न लें"
            ]
        },
        "sources": [{"name": "ICAR-SBI Coimbatore YLD Guide", "url": "https://sugarcane.icar.gov.in"}],
        "review": {"status": "reviewed", "note": "Verified yellow leaf protocol"}
    },
    {
        "id": "Sugarcane___Healthy",
        "crop": {"en": "Sugarcane", "hi": "गन्ना"},
        "disease": {"en": "Healthy", "hi": "स्वस्थ"},
        "scientific_name": "Saccharum officinarum",
        "type": "healthy",
        "healthy": True,
        "symptoms": {
            "en": [
                "Deep green erect foliage with robust wide leaf blades free from stripes or pustules",
                "Stout solid stalks exhibiting uniform internode length and healthy intact leaf sheaths",
                "Vigorous stool formation with clean moist root crown free of decay or red pith"
            ],
            "hi": [
                "गहरी हरी चौड़ी पत्तियां जिन पर किसी प्रकार के धब्बे या धारियां नहीं हैं",
                "मजबूत और मोटा तना जिसमें पोरियों की लंबाई एक समान है",
                "पौधों का स्वस्थ गुच्छा और जड़ों का अच्छा विकास"
            ]
        },
        "do_now": {
            "en": [
                "Maintain scheduled irrigation cycles based on soil moisture and ambient seasonal requirements",
                "Perform earthing up around the base of cane clumps to support upright growth and suppress weeds",
                "Conduct routine crop monitoring for early detection of stem borers or foliar pests"
            ],
            "hi": [
                "मौसम और मिट्टी की आवश्यकतानुसार नियमित सिंचाई करते रहें",
                "पौधों की जड़ों पर मिट्टी चढ़ाएं ताकि गन्ना गिरे नहीं और खरपतवार दब जाएं",
                "कीटों और रोगों की निगरानी हेतु नियमित निरीक्षण जारी रखें"
            ]
        },
        "avoid_extra": {"en": [], "hi": []},
        "prevent": {
            "en": [
                "Follow balanced integrated nutrient management combining organic manure with recommended fertilizers",
                "Conserve beneficial predators and parasitoids like Trichogramma for natural pest suppression",
                "Maintain clean field borders and clear drainage furrows before the onset of monsoon"
            ],
            "hi": [
                "गोबर की खाद और संतुलित उर्वरकों का सही अनुपात में प्रयोग करें",
                "मित्र कीटों (जैसे ट्राइकोग्रामा) का संरक्षण करें",
                "खेत की नालियों को साफ रखें ताकि बारिश में जलभराव न हो"
            ]
        },
        "sources": [{"name": "ICAR-IISR Sugarcane Production Manual", "url": "https://iisr.icar.gov.in"}],
        "review": {"status": "reviewed", "note": "Healthy sugarcane baseline"}
    },

    # ---------------- Cotton ----------------
    {
        "id": "Cotton___Bacterial_Blight",
        "crop": {"en": "Cotton", "hi": "कपास"},
        "disease": {"en": "Bacterial Blight", "hi": "जीवाणु झुलसा"},
        "scientific_name": "Xanthomonas citri pv. malvacearum",
        "type": "bacterial",
        "healthy": False,
        "symptoms": {
            "en": [
                "Angular water-soaked leaf lesions constrained by leaf veinlets (angular leaf spot phase)",
                "Blackish-brown elongated lesions girdling main stems and branches (black arm phase)",
                "Water-soaked circular dark lesions on developing bolls leading to boll rot and lint staining"
            ],
            "hi": [
                "पत्तियों की नसों के बीच कोणीय (कोनेदार) पानीदार धब्बे बनते हैं",
                "तने और टहनियों पर काले-भूरे लंबे धब्बे बनते हैं जिसे ब्लैक आर्म कहते हैं",
                "कपास के टिंडों (बॉल्स) पर काले गोल धब्बे जिससे रुई सड़ जाती है और दागदार हो जाती है"
            ]
        },
        "do_now": {
            "en": [
                "Prune and destroy severely blighted vegetative branches to lower bacterial inoculum",
                "Spray an approved copper bactericide formulation strictly adhering to product label instructions",
                "Avoid inter-row movement when crop foliage is wet with morning dew to prevent spread"
            ],
            "hi": [
                "संक्रमित शाखाओं को काटकर नष्ट करें ताकि जीवाणु आगे न फैलें",
                "उत्पाद लेबल के अनुसार अनुशंसित कॉपर युक्त जीवाणुनाशक का छिड़काव करें",
                "ओस या गीले पत्तों के समय खेत में काम करने से बचें"
            ]
        },
        "avoid_extra": {"en": [], "hi": []},
        "prevent": {
            "en": [
                "Delint and treat certified cotton seeds with approved acid and seed protectants prior to sowing",
                "Grow bacterial blight resistant cotton hybrids recommended by state agricultural university",
                "Incorporate crop residues deeply into soil using mouldboard plough after final picking"
            ],
            "hi": [
                "बुवाई से पहले प्रमाणित बीजों का उचित उपचार करें",
                "जीवाणु झुलसा रोधी संकर कपास की किस्मों का चयन करें",
                "फसल कटाई के बाद खेत की गहरी जुताई करके अवशेषों को मिट्टी में दबा दें"
            ]
        },
        "sources": [{"name": "ICAR-Central Institute for Cotton Research", "url": "https://cicr.icar.gov.in"}],
        "review": {"status": "reviewed", "note": "Verified ICAR-CICR cotton protocol"}
    },
    {
        "id": "Cotton___Healthy",
        "crop": {"en": "Cotton", "hi": "कपास"},
        "disease": {"en": "Healthy", "hi": "स्वस्थ"},
        "scientific_name": "Gossypium hirsutum",
        "type": "healthy",
        "healthy": True,
        "symptoms": {
            "en": [
                "Broad dark green lobed leaves free of angular spots, puckering, or yellow vein networks",
                "Erect sturdy main stem with balanced sympodial branch development and vigorous squaring",
                "Clean green developing bolls with intact bracts free from feeding punctures or water spots"
            ],
            "hi": [
                "गहरी हरी चौड़ी पत्तियां जिन पर किसी प्रकार के कोणीय धब्बे या मरोड़ नहीं हैं",
                "मजबूत तना और फलों वाली शाखाओं का अच्छा विकास",
                "स्वस्थ और हरे टिंडे (बॉल्स) जिन पर किसी कीट या सड़न का निशान नहीं है"
            ]
        },
        "do_now": {
            "en": [
                "Maintain scheduled irrigation avoiding excess waterlogging during critical squaring and boll stages",
                "Scout fields twice weekly using yellow sticky traps and pheromone traps for early sucking pests",
                "Provide foliar potassium nitrate and magnesium sprays to support high boll retention"
            ],
            "hi": [
                "फूल और टिंडे बनते समय खेत में नमी का उचित स्तर रखें और पानी न भरने दें",
                "रस चूसक कीटों की निगरानी के लिए ट्रैप लगाएं और नियमित जांच करें",
                "टिंडों के अच्छे विकास हेतु पोटाश और मैग्नीशियम का संतुलित छिड़काव करें"
            ]
        },
        "avoid_extra": {"en": [], "hi": []},
        "prevent": {
            "en": [
                "Practice integrated pest and nutrient management to maintain natural agro-ecosystem resilience",
                "Conserve beneficial generalist predators like green lacewings, ladybird beetles, and predatory spiders",
                "Maintain weed-free inter-rows and clear field margins of alternate malvaceous weed hosts"
            ],
            "hi": [
                "उन्नत कीट एवं पोषण प्रबंधन का पालन करें",
                "मित्र कीटों जैसे लेडीबर्ड बीटल और क्राइसोपा का संरक्षण करें",
                "खेत के आसपास के खरपतवारों को नियमित रूप से हटाएं"
            ]
        },
        "sources": [{"name": "ICAR-CICR Cotton Production Guide", "url": "https://cicr.icar.gov.in"}],
        "review": {"status": "reviewed", "note": "Healthy cotton baseline"}
    },

    # ---------------- Groundnut ----------------
    {
        "id": "Groundnut___Early_Leaf_Spot",
        "crop": {"en": "Groundnut", "hi": "मूंगफली"},
        "disease": {"en": "Early Leaf Spot (Tikka)", "hi": "अगेती टिक्का रोग"},
        "scientific_name": "Cercospora arachidicola",
        "type": "fungal",
        "healthy": False,
        "symptoms": {
            "en": [
                "Circular reddish-brown to dark brown leaf spots appearing on the upper leaf surface early in the season",
                "Characteristic bright yellow chlorotic halo prominent around every necrotic spot",
                "Severe spotting induces premature leaf yellowing and heavy defoliation of lower canopy"
            ],
            "hi": [
                "पत्तियों की ऊपरी सतह पर गोल लाल-भूरे से गहरे कत्थई रंग के धब्बे",
                "धब्बों के चारों ओर स्पष्ट पीला घेरा (हेलो) दिखाई देता है",
                "पत्तियां पीली पड़कर तेजी से गिरने लगती हैं जिससे पौधे गंजे दिखने लगते हैं"
            ]
        },
        "do_now": {
            "en": [
                "Remove and bury heavily infected fallen leaves to restrict air-borne conidial dispersal",
                "Apply an approved protective or systemic fungicide strictly according to product label recommendations",
                "Ensure proper field drainage to avoid prolonged high humidity within the crop canopy"
            ],
            "hi": [
                "रोगग्रस्त गिरी हुई पत्तियों को इकट्ठा करके मिट्टी में दबा दें",
                "उत्पाद लेबल के निर्देशानुसार अनुशंसित फफूंदनाशक का छिड़काव करें",
                "खेत में पानी का भराव न होने दें ताकि नमी नियंत्रित रहे"
            ]
        },
        "avoid_extra": {"en": [], "hi": []},
        "prevent": {
            "en": [
                "Sow certified Tikka-tolerant groundnut varieties recommended by your regional research station",
                "Treat seed kernels with approved biocontrol formulation or protectants prior to sowing",
                "Rotate groundnut with non-host graminaceous crops such as pearl millet or sorghum"
            ],
            "hi": [
                "टिक्का रोग रोधी प्रमाणित बीजों का ही चयन करें",
                "बुवाई से पहले बीजों का उपयुक्त फफूंदनाशक से उपचार करें",
                "बाजरा या ज्वार जैसी फसलों के साथ फसल चक्र अपनाएं"
            ]
        },
        "sources": [{"name": "ICAR-Directorate of Groundnut Research", "url": "https://dgr.icar.gov.in"}],
        "review": {"status": "reviewed", "note": "Verified ICAR-DGR groundnut protocol"}
    },
    {
        "id": "Groundnut___Late_Leaf_Spot",
        "crop": {"en": "Groundnut", "hi": "मूंगफली"},
        "disease": {"en": "Late Leaf Spot (Tikka)", "hi": "पछेती टिक्का रोग"},
        "scientific_name": "Cercosporidium personatum",
        "type": "fungal",
        "healthy": False,
        "symptoms": {
            "en": [
                "Nearly circular small dark brown to black spots developing late in the growing season",
                "Lower leaf surface displays carbon-black cushions of fungal spore fruiting bodies",
                "Halo is usually absent or minimal; rapid leaf drop leads to severe yield and haulm reduction"
            ],
            "hi": [
                "फसल पकने के समय पत्तियों पर छोटे काले-भूरे गोल धब्बे बनते हैं",
                "पत्ती की निचली सतह पर काले रंग के फफूंद के उभार साफ दिखते हैं",
                "धब्बों के चारों ओर पीला घेरा प्रायः नहीं होता और पत्तियां बहुत तेजी से झड़ती हैं"
            ]
        },
        "do_now": {
            "en": [
                "Spray an approved broad-spectrum fungicide strictly according to product label instructions",
                "Avoid overhead sprinkler irrigation during late afternoon hours to keep foliage dry overnight",
                "Harvest crop promptly once pods reach physiological maturity to avoid pod shedding in soil"
            ],
            "hi": [
                "उत्पाद लेबल के अनुसार अनुशंसित फफूंदनाशक का तत्काल छिड़काव करें",
                "शाम के समय सिंचाई न करें ताकि रात में पत्ते गीले न रहें",
                "फसल पकते ही समय पर खुदाई करें ताकि फलियां मिट्टी में न छूटें"
            ]
        },
        "avoid_extra": {"en": [], "hi": []},
        "prevent": {
            "en": [
                "Select certified disease-tolerant cultivars developed by state agricultural universities",
                "Carry out deep summer ploughing to bury fungal overwintering debris into soil depths",
                "Maintain balanced fertilization with required gypsum top-dressing at flowering"
            ],
            "hi": [
                "रोग-सहनशील प्रमाणित किस्मों की ही बुवाई करें",
                "गर्मियों में गहरी जुताई करें ताकि फफूंद के अवशेष नष्ट हो जाएं",
                "फूल आते समय जिप्सम का संतुलित प्रयोग करें"
            ]
        },
        "sources": [{"name": "ICAR-DGR Groundnut Pathology", "url": "https://dgr.icar.gov.in"}],
        "review": {"status": "reviewed", "note": "Verified groundnut late leaf spot protocol"}
    },
    {
        "id": "Groundnut___Rust",
        "crop": {"en": "Groundnut", "hi": "मूंगफली"},
        "disease": {"en": "Rust", "hi": "रतुआ रोग"},
        "scientific_name": "Puccinia arachidis",
        "type": "fungal",
        "healthy": False,
        "symptoms": {
            "en": [
                "Pustules appear primarily on lower surface of leaves as round orange-brown powdery blisters",
                "Pustules rupture discharging masses of reddish-brown urediniospores leaving leaves ragged",
                "Infected leaves curl, become necrotic and dry out, but often remain attached to the stems"
            ],
            "hi": [
                "पत्तियों की निचली सतह पर नारंगी-भूरे रंग के छोटे-छोटे उभरे हुए फफोले",
                "फफोले फटकर लाल-भूरे रंग का चूर्ण छोड़ते हैं जिससे पत्तियां खुरदरी हो जाती हैं",
                "पत्तियां सूखकर मुड़ जाती हैं लेकिन तने से लटकी रहती हैं"
            ]
        },
        "do_now": {
            "en": [
                "Apply an approved systemic fungicide strictly according to product label recommendations",
                "Avoid sprinkler irrigation that disperses fungal spores across adjacent healthy rows",
                "Inspect lower foliage regularly during periods of overcast, humid monsoon weather"
            ],
            "hi": [
                "उत्पाद लेबल के निर्देशानुसार अनुशंसित फफूंदनाशक का छिड़काव करें",
                "फव्वारा सिंचाई से बचें ताकि बीजाणु अन्य पौधों पर न फैलें",
                "बादल वाले और नम मौसम में निचली पत्तियों की नियमित जांच करें"
            ]
        },
        "avoid_extra": {"en": [], "hi": []},
        "prevent": {
            "en": [
                "Grow dual-resistant cultivars that resist both rust and leaf spot complexes",
                "Intercrop with cereal crops such as pearl millet or maize to act as physical spore barriers",
                "Eradicate self-sown volunteer groundnut plants that carry rust spores between seasons"
            ],
            "hi": [
                "रतुआ और टिक्का दोनों से सुरक्षित उन्नत किस्में लगाएं",
                "बाजरा या मक्का के साथ अंतःफसल (इंटरक्रॉपिंग) करें",
                "खेत के आसपास उगे आवारा मूंगफली के पौधों को नष्ट करें"
            ]
        },
        "sources": [{"name": "ICAR-DGR Junagadh", "url": "https://dgr.icar.gov.in"}],
        "review": {"status": "reviewed", "note": "Groundnut rust protocol"}
    },
    {
        "id": "Groundnut___Rosette",
        "crop": {"en": "Groundnut", "hi": "मूंगफली"},
        "disease": {"en": "Rosette Disease", "hi": "रोज़ेट (गुच्छा) रोग"},
        "scientific_name": "Groundnut rosette virus",
        "type": "viral",
        "healthy": False,
        "symptoms": {
            "en": [
                "Extreme stunting with severely shortened internodes producing a dense rosette cushion of foliage",
                "Leaves show chlorotic yellowing, mottling, or dark green mosaic curling",
                "Plants fail to flower or produce small, distorted pods resulting in near total yield loss"
            ],
            "hi": [
                "पौधे अत्यधिक बौने रह जाते हैं और पत्तियां एक जगह गुच्छे की तरह सिमट जाती हैं",
                "पत्तियों का रंग पीला पड़ जाता है या वे मुड़कर विकृत हो जाती हैं",
                "पौधों में फूल नहीं आते और फलियां नहीं बनतीं जिससे भारी नुकसान होता है"
            ]
        },
        "do_now": {
            "en": [
                "Uproot and destroy stunted rosette-affected plants early before aphid vector colonisation",
                "Spray an approved aphicide strictly adhering to product label directions to suppress vector insects",
                "Ensure dense plant population to minimize bare ground patches that attract aphids"
            ],
            "hi": [
                "संक्रमित गुच्छेदार पौधों को तुरंत उखाड़कर नष्ट करें",
                "माहू (एफिड) कीट के नियंत्रण हेतु उत्पाद लेबल के अनुसार कीटनाशक का छिड़काव करें",
                "पौधों की उचित संख्या बनाए रखें ताकि खाली जमीन न दिखे जो कीटों को आकर्षित करती है"
            ]
        },
        "avoid_extra": {"en": [], "hi": []},
        "prevent": {
            "en": [
                "Plant certified rosette-resistant seed varieties recommended for your region",
                "Sow early with the onset of monsoon at optimum plant density to achieve rapid ground cover",
                "Preserve natural aphid predators such as coccinellid beetles and hoverfly larvae"
            ],
            "hi": [
                "रोग रोधी प्रमाणित किस्मों का ही उपयोग करें",
                "मानसून आते ही समय पर घनी बुवाई करें ताकि जमीन जल्दी ढक जाए",
                "माहू खाने वाले मित्र कीटों का संरक्षण करें"
            ]
        },
        "sources": [{"name": "ICRISAT Groundnut Information Guide", "url": "https://www.icrisat.org"}],
        "review": {"status": "reviewed", "note": "ICRISAT groundnut rosette guide"}
    },
    {
        "id": "Groundnut___Healthy",
        "crop": {"en": "Groundnut", "hi": "मूंगफली"},
        "disease": {"en": "Healthy", "hi": "स्वस्थ"},
        "scientific_name": "Arachis hypogaea",
        "type": "healthy",
        "healthy": True,
        "symptoms": {
            "en": [
                "Vibrant green pinnate foliage with smooth clean leaf surfaces free of spots or halos",
                "Symmetrical compact spreading bush with vigorous flowering and peg penetration into soil",
                "Healthy root system displaying abundant active pinkish Rhizobium nitrogen-fixing nodules"
            ],
            "hi": [
                "हरी-भरी स्वस्थ पत्तियां जिन पर किसी प्रकार के धब्बे या पीलापन नहीं है",
                "पौधे का अच्छा फैलाव, प्रचुर मात्रा में फूल और खूंटियों (पेग्स) का जमीन में प्रवेश",
                "जड़ों में सक्रिय गुलाबी रंग की राइजोबियम ग्रंथियों का उत्तम विकास"
            ]
        },
        "do_now": {
            "en": [
                "Keep soil loose and weed-free around the pegging zone to facilitate smooth pod penetration",
                "Maintain adequate moisture during the critical flowering, pegging, and pod filling phases",
                "Apply recommended dose of gypsum around flowering time to supply essential calcium for pod formation"
            ],
            "hi": [
                "खूंटियां बनते समय खेत को खरपतवार मुक्त और मिट्टी को भुरभुरी रखें",
                "फूल और फलियां बनते समय खेत में पर्याप्त नमी बनाए रखें",
                "फलियों के अच्छे भराव के लिए फूल आने पर जिप्सम की आवश्यक मात्रा दें"
            ]
        },
        "avoid_extra": {"en": [], "hi": []},
        "prevent": {
            "en": [
                "Follow balanced integrated nutrient practices with required micronutrients like boron and zinc",
                "Maintain optimal plant spacing to promote uniform aeration through the canopy",
                "Rotate with cereal crops to sustain soil biological vitality"
            ],
            "hi": [
                "जिंक और बोरॉन जैसे सूक्ष्म पोषक तत्वों का संतुलित प्रयोग करें",
                "पौधों के बीच उचित दूरी रखें ताकि धूप और हवा मिलती रहे",
                "अनाज वाली फसलों के साथ नियमित फसल चक्र अपनाएं"
            ]
        },
        "sources": [{"name": "ICAR-DGR Groundnut Production Package", "url": "https://dgr.icar.gov.in"}],
        "review": {"status": "reviewed", "note": "Healthy groundnut baseline"}
    },

    # ---------------- Mango ----------------
    {
        "id": "Mango___Anthracnose",
        "crop": {"en": "Mango", "hi": "आम"},
        "disease": {"en": "Anthracnose", "hi": "एंथ्रेक्नोज़ (श्याम वर्ण)"},
        "scientific_name": "Colletotrichum gloeosporioides",
        "type": "fungal",
        "healthy": False,
        "symptoms": {
            "en": [
                "Dark brown to black angular necrotic spots on young tender leaves that coalesce and drop out",
                "Black sunken lesions on flower panicles resulting in blossom blight and severe fruit drop",
                "Tear-stain patterns and sunken rotting spots with pinkish spore crusts on developing fruits"
            ],
            "hi": [
                "नई कोमल पत्तियों पर काले-भूरे धब्बे जो बाद में फटकर छेद बना देते हैं",
                "बौर (फूलों) पर काले धब्बे जिससे बौर झुलस जाता है और फूल गिर जाते हैं",
                "फलों पर काले धंसे हुए धब्बे और आंसुओं जैसी धारियां बनती हैं जिससे फल सड़ जाते हैं"
            ]
        },
        "do_now": {
            "en": [
                "Prune dead twigs and dried panicles post-harvest and safely burn them outside the orchard",
                "Apply an approved copper-based or protective fungicide strictly according to product label directions",
                "Avoid overhead irrigation during flowering and fruit setting intervals"
            ],
            "hi": [
                "सूखी टहनियों और पुराने बौर को काटकर खेत से बाहर जला दें",
                "उत्पाद लेबल के निर्देशानुसार अनुशंसित कॉपर युक्त फफूंदनाशक का छिड़काव करें",
                "बौर और फल आते समय फव्वारा सिंचाई से बचें"
            ]
        },
        "avoid_extra": {"en": [], "hi": []},
        "prevent": {
            "en": [
                "Maintain proper canopy pruning after harvest to permit ample sunlight and airflow through trees",
                "Follow scheduled preventive sprays prior to flower bud opening and after fruit set",
                "Dip harvested mango fruits in approved hot water bath before packing to prevent latent post-harvest rot"
            ],
            "hi": [
                "कटाई के बाद पेड़ों की छंटाई करें ताकि धूप और हवा अंदर तक पहुंचे",
                "बौर खिलने से पहले और फल बनने के बाद अनुशंसित सुरक्षात्मक छिड़काव करें",
                "तुड़ाई के बाद फलों को गर्म पानी के उपचार से सुरक्षित करें"
            ]
        },
        "sources": [{"name": "ICAR-Central Institute for Subtropical Horticulture", "url": "https://cish.icar.gov.in"}],
        "review": {"status": "reviewed", "note": "Verified ICAR-CISH mango protocol"}
    },
    {
        "id": "Mango___Bacterial_Canker",
        "crop": {"en": "Mango", "hi": "आम"},
        "disease": {"en": "Bacterial Canker", "hi": "जीवाणु कैंकर"},
        "scientific_name": "Xanthomonas campestris pv. mangiferaeindicae",
        "type": "bacterial",
        "healthy": False,
        "symptoms": {
            "en": [
                "Water-soaked angular dark brown to black raised lesions on leaves surrounded by yellow halos",
                "Cankerous cracked lesions on branches with dark gummy exudates running down the bark",
                "Stelliform star-shaped deep cracks with gum oozing on green developing mango fruits"
            ],
            "hi": [
                "पत्तियों पर काले-भूरे उभरे हुए कोणीय धब्बे जिनके चारों ओर पीला घेरा होता है",
                "टहनियों पर दरारें और कत्थई रंग का गोंद जैसा रिसाव निकलता दिखाई देता है",
                "फलों पर तारे के आकार की गहरी दरारें बनती हैं और चिपचिपा गोंद निकलता है"
            ]
        },
        "do_now": {
            "en": [
                "Prune infected twigs and cankered branches cleanly and seal cut ends with approved paste",
                "Apply an approved copper bactericide formulation strictly following product label recommendations",
                "Collect and burn all infected fallen leaves and dropped fruits from orchard floor"
            ],
            "hi": [
                "संक्रमित टहनियों को काटकर हटा दें और कटे हुए भाग पर सुरक्षात्मक लेप लगाएं",
                "उत्पाद लेबल के अनुसार अनुशंसित कॉपर युक्त जीवाणुनाशक का छिड़काव करें",
                "जमीन पर गिरे रोगग्रस्त पत्तों और फलों को इकट्ठा करके नष्ट करें"
            ]
        },
        "avoid_extra": {"en": [], "hi": []},
        "prevent": {
            "en": [
                "Establish tall windbreak trees around orchard borders to minimize wind-induced leaf abrasion wounds",
                "Plant certified disease-free grafted saplings obtained from accredited horticultural nurseries",
                "Disinfect pruning secateurs and saws between tree treatments using antiseptic solution"
            ],
            "hi": [
                "बाग के चारों ओर वायुरोधी पेड़ लगाएं ताकि तेज हवा से पत्तियों पर चोट न लगे",
                "प्रमाणित नर्सरी से रोगमुक्त कलमी पौधे ही लगाएं",
                "छंटाई के औजारों को नियमित रूप से कीटाणुरहित रखें"
            ]
        },
        "sources": [{"name": "ICAR-CISH Lucknow", "url": "https://cish.icar.gov.in"}],
        "review": {"status": "reviewed", "note": "Verified mango bacterial canker protocol"}
    },
    {
        "id": "Mango___Powdery_Mildew",
        "crop": {"en": "Mango", "hi": "आम"},
        "disease": {"en": "Powdery Mildew", "hi": "चूर्णिल आसिता (पाउडरी मिल्ड्यू)"},
        "scientific_name": "Oidium mangiferae",
        "type": "fungal",
        "healthy": False,
        "symptoms": {
            "en": [
                "White powdery superficial fungal growth spreading across flower panicles and flower stalks",
                "Infected blossom petals drop prematurely leaving blackened bare panicle skeletons",
                "Young leaves curl, distort, and show purplish-brown blotches underneath white powdery patches"
            ],
            "hi": [
                "बौर और फूलों की डंडियों पर सफेद चूर्ण जैसी फफूंद की परत जम जाती है",
                "फूल समय से पहले झड़ जाते हैं और बौर सूखा व काला दिखने लगता है",
                "नई पत्तियां मुड़ जाती हैं और सफेद पाउडर के नीचे बैंगनी-भूरे धब्बे बनते हैं"
            ]
        },
        "do_now": {
            "en": [
                "Apply an approved protective or systemic fungicide strictly according to product label directions",
                "Time spray applications early in the morning when calm air ensures optimal blossom coverage",
                "Remove heavily blanketed flower clusters to check spore spread across adjacent canopies"
            ],
            "hi": [
                "उत्पाद लेबल के निर्देशानुसार अनुशंसित फफूंदनाशक का तुरंत छिड़काव करें",
                "सुबह के शांत मौसम में छिड़काव करें ताकि बौर पर दवा अच्छी तरह पहुंचे",
                "अत्यधिक प्रभावित बौर को हटाकर नष्ट कर दें"
            ]
        },
        "avoid_extra": {"en": [], "hi": []},
        "prevent": {
            "en": [
                "Maintain open tree structure with annual post-harvest pruning to discourage humid microclimates",
                "Initiate scheduled preventive sprays when flower panicles are expanding prior to blossom opening",
                "Monitor weather forecast during February-March for sudden cloudy spells and cool morning dews"
            ],
            "hi": [
                "कटाई के बाद पेड़ों की कटाई-छंटाई करें ताकि बौर में हवा और धूप बनी रहे",
                "बौर खिलने से पहले अनुशंसित सुरक्षात्मक छिड़काव करें",
                "बसंत ऋतु में मौसम में नमी और बादलों पर नजर रखें"
            ]
        },
        "sources": [{"name": "ICAR-CISH Mango Protection Guide", "url": "https://cish.icar.gov.in"}],
        "review": {"status": "reviewed", "note": "Verified mango powdery mildew protocol"}
    },
    {
        "id": "Mango___Die_Back",
        "crop": {"en": "Mango", "hi": "आम"},
        "disease": {"en": "Die Back", "hi": "डाई बैक (उल्टा सूखा रोग)"},
        "scientific_name": "Lasiodiplodia theobromae",
        "type": "fungal",
        "healthy": False,
        "symptoms": {
            "en": [
                "Drying and withering of branches starting from the tip downwards giving a scorched appearance",
                "Leaves turn brown, dry up completely, and remain firmly attached to dead branches for months",
                "Internal wood displays dark brown discoloration with discoloured vascular streaks when split"
            ],
            "hi": [
                "टहनियों का ऊपरी सिरे से नीचे की ओर सूखना शुरू होना",
                "पत्तियां भूरी होकर सूख जाती हैं लेकिन सूखी टहनी से चिपकी रहती हैं",
                "टहनी को काटने पर अंदर की लकड़ी में भूरी या काली धारियां दिखती हैं"
            ]
        },
        "do_now": {
            "en": [
                "Prune dried branches three inches below the healthy green transition line and safely burn them",
                "Paint all pruned branch stubs with an approved copper paste formulation strictly according to label",
                "Spray the entire tree canopy with an approved fungicide following label instructions"
            ],
            "hi": [
                "सूखी टहनी को स्वस्थ भाग से कुछ इंच नीचे से काटें और जला दें",
                "कटे हुए भाग पर तुरंत उत्पाद लेबल के अनुसार कॉपर युक्त लेप लगाएं",
                "पेड़ के पूरे घेरे पर लेबल निर्देशानुसार अनुशंसित फफूंदनाशक का छिड़काव करें"
            ]
        },
        "avoid_extra": {"en": [], "hi": []},
        "prevent": {
            "en": [
                "Manage stem borers and bark-eating caterpillars whose tunnels serve as fungal entry pathways",
                "Avoid root damage during intercultural ploughing and avoid severe drought stress in summer",
                "Apply balanced organic manure combined with zinc and copper micronutrient supplements"
            ],
            "hi": [
                "तना छेदक कीटों की रोकथाम करें ताकि फफूंद के प्रवेश के रास्ते न बनें",
                "जुताई के समय मुख्य जड़ों को कटने से बचाएं और गर्मियों में पानी की कमी न होने दें",
                "संतुलित खाद के साथ जिंक और कॉपर जैसे सूक्ष्म पोषक तत्व दें"
            ]
        },
        "sources": [{"name": "ICAR-CISH Lucknow Die Back Advisory", "url": "https://cish.icar.gov.in"}],
        "review": {"status": "reviewed", "note": "Verified die back protocol"}
    },
    {
        "id": "Mango___Healthy",
        "crop": {"en": "Mango", "hi": "आम"},
        "disease": {"en": "Healthy", "hi": "स्वस्थ"},
        "scientific_name": "Mangifera indica",
        "type": "healthy",
        "healthy": True,
        "symptoms": {
            "en": [
                "Lustrous deep green leathery mature leaves with clean margins free of blemishes or curling",
                "Vigorous emerging copper-red flushes developing into healthy spotless dark green canopies",
                "Strong clean trunk with smooth bark free of gum exudation, borers, or cankerous fissures"
            ],
            "hi": [
                "चमकदार गहरी हरी चमड़े जैसी मजबूत पत्तियां जिन पर कोई धब्बे या कट-फट नहीं है",
                "नई तांबे जैसी लाल कोपलों का स्वस्थ विकास और गहरा हरा होना",
                "साफ और मजबूत तना जिस पर किसी गोंद या कीट का निशान नहीं है"
            ]
        },
        "do_now": {
            "en": [
                "Maintain scheduled drip or basin irrigation aligned with crop phenological stage",
                "Apply recommended organic compost and balanced fertilizers around the tree drip-line perimeter",
                "Inspect tree crowns weekly during flowering and early fruit development for pest incursions"
            ],
            "hi": [
                "फसल की अवस्था के अनुसार पेड़ के थाले में उचित सिंचाई बनाए रखें",
                "पेड़ की छाया के घेरे में गोबर की खाद और संतुलित उर्वरक दें",
                "फूल और फल आते समय बौर व फलों का नियमित निरीक्षण करें"
            ]
        },
        "avoid_extra": {"en": [], "hi": []},
        "prevent": {
            "en": [
                "Conduct annual post-harvest canopy thinning to allow sun penetration into inner scaffolds",
                "Paint the main lower trunk with lime-copper wash prior to monsoon to deter bark pathogens",
                "Maintain clean orchard basin free of wild brush and weed hosts"
            ],
            "hi": [
                "फल तुड़ाई के बाद पेड़ों की हल्की छंटाई करें ताकि अंदर तक धूप पहुंचे",
                "मानसून से पहले तने पर चूने और कॉपर का लेप लगाएं",
                "पेड़ों के आसपास खरपतवार न उगने दें"
            ]
        },
        "sources": [{"name": "ICAR-CISH Mango Cultivation Manual", "url": "https://cish.icar.gov.in"}],
        "review": {"status": "reviewed", "note": "Healthy mango baseline"}
    },

    # ---------------- Wheat ----------------
    {
        "id": "Wheat___Yellow_Rust",
        "crop": {"en": "Wheat", "hi": "गेहूं"},
        "disease": {"en": "Yellow Rust", "hi": "पीला रतुआ (स्ट्राइप रस्ट)"},
        "scientific_name": "Puccinia striiformis",
        "type": "fungal",
        "healthy": False,
        "symptoms": {
            "en": [
                "Bright lemon-yellow powdery pustules arranged in narrow distinct linear stripes along leaf veins",
                "Pustules erupt releasing powdery yellow spores that adhere readily to clothing and fingers",
                "Severe stripe infection causes rapid leaf desiccation, premature drying, and shrivelled grain filling"
            ],
            "hi": [
                "पत्तियों की नसों के समानांतर चमकीले पीले रंग के फफोले लंबी कतारों (धारियों) में दिखाई देते हैं",
                "फफोले फटकर पीले रंग का चूर्ण छोड़ते हैं जो हाथ या कपड़ों पर हल्दी की तरह लग जाता है",
                "पत्तियां तेजी से सूख जाती हैं और बालियों में दाने सिकुड़कर बहुत हल्के रह जाते हैं"
            ]
        },
        "do_now": {
            "en": [
                "Scout wheat fields regularly during cool winter mornings for isolated yellow rust focal foci",
                "On initial focal detection, spray an approved systemic triazole fungicide strictly following label instructions",
                "Alert regional agricultural extension authorities to track community-level spore movement"
            ],
            "hi": [
                "सर्दियों में सुबह के समय खेत का नियमित निरीक्षण करें और पीले धब्बों की पहचान करें",
                "शुरुआती लक्षण दिखते ही उत्पाद लेबल के निर्देशानुसार अनुशंसित फफूंदनाशक का छिड़काव करें",
                "क्षेत्रीय कृषि अधिकारियों को सूचना दें ताकि सामूहिक रोकथाम हो सके"
            ]
        },
        "avoid_extra": {"en": [], "hi": []},
        "prevent": {
            "en": [
                "Sow certified rust-resistant wheat varieties recommended for your specific agro-climatic zone",
                "Avoid excessively late sowing which exposes the crop to high temperature rust sporulation peaks",
                "Maintain balanced soil nutrition avoiding excess nitrogen applications that accelerate rust spread"
            ],
            "hi": [
                "अपने क्षेत्र के लिए अनुशंसित रतुआ रोधी प्रमाणित किस्मों की ही बुवाई करें",
                "देर से बुवाई करने से बचें ताकि फसल रतुआ के प्रकोप से बच सके",
                "संतुलित खाद दें और अधिक यूरिया डालने से बचें"
            ]
        },
        "sources": [{"name": "ICAR-Indian Institute of Wheat and Barley Research", "url": "https://iiwbr.icar.gov.in"}],
        "review": {"status": "reviewed", "note": "Verified ICAR-IIWBR wheat rust protocol"}
    },
    {
        "id": "Wheat___Brown_Rust",
        "crop": {"en": "Wheat", "hi": "गेहूं"},
        "disease": {"en": "Brown Rust", "hi": "भूरा रतुआ (लीफ रस्ट)"},
        "scientific_name": "Puccinia triticina",
        "type": "fungal",
        "healthy": False,
        "symptoms": {
            "en": [
                "Small round to oval orange-brown powdery pustules scattered randomly across upper leaf surfaces",
                "Unlike yellow rust, pustules do not form stripes but appear as isolated dots across the blade",
                "Pustules turn dark brown to black towards maturity as teliospores form underneath epidermis"
            ],
            "hi": [
                "पत्तियों की ऊपरी सतह पर गोल से अंडाकार नारंगी-भूरे रंग के फफोले बिखरे हुए दिखते हैं",
                "पीले रतुआ की तरह धारियां नहीं बनतीं बल्कि धब्बे अलग-अलग बिखरे रहते हैं",
                "मौसम गर्म होने पर फफोले काले-भूरे रंग में बदल जाते हैं"
            ]
        },
        "do_now": {
            "en": [
                "Inspect the flag leaf and top two canopy leaves when spring temperatures begin rising",
                "If brown pustules appear on flag leaves, apply an approved protective fungicide strictly adhering to product label",
                "Avoid unnecessary waterlogging in irrigation furrows"
            ],
            "hi": [
                "तापमान बढ़ने पर झंडा पत्ती (फ्लैग लीफ) और ऊपरी पत्तियों की नियमित जांच करें",
                "फ्लैग लीफ पर धब्बे दिखते ही उत्पाद लेबल के अनुसार अनुशंसित फफूंदनाशक का छिड़काव करें",
                "खेत में पानी का भराव न होने दें"
            ]
        },
        "avoid_extra": {"en": [], "hi": []},
        "prevent": {
            "en": [
                "Plant certified resistant wheat cultivars proven against prevailing pathotypes",
                "Complete timely sowing within the recommended November planting window",
                "Follow balanced integrated nutrient management combining zinc with recommended fertilizer doses"
            ],
            "hi": [
                "प्रमाणित रोग रोधी किस्मों की ही बुवाई करें",
                "नवंबर के महीने में समय पर बुवाई संपन्न करें",
                "संतुलित खाद और जिंक का उचित प्रयोग करें"
            ]
        },
        "sources": [{"name": "ICAR-IIWBR Karnal", "url": "https://iiwbr.icar.gov.in"}],
        "review": {"status": "reviewed", "note": "Verified wheat brown rust protocol"}
    },
    {
        "id": "Wheat___Stem_Rust",
        "crop": {"en": "Wheat", "hi": "गेहूं"},
        "disease": {"en": "Stem Rust", "hi": "तना रतुआ (ब्लैक रस्ट)"},
        "scientific_name": "Puccinia graminis",
        "type": "fungal",
        "healthy": False,
        "symptoms": {
            "en": [
                "Large reddish-brown elongated pustules appearing prominently on stems, leaf sheaths, and glumes",
                "Pustules rupture epidermal tissues giving stems a rough torn appearance",
                "Stalks become fragile and lodge heavily under wind with severely pinched, lightweight grains"
            ],
            "hi": [
                "तनों, पत्ती के आवरण और बालियों पर बड़े लाल-भूरे रंग के उभरे हुए फफोले",
                "फफोले फटने से तने की ऊपरी छाल फट जाती है और तना खुरदरा हो जाता है",
                "पौधे कमजोर होकर गिर जाते हैं और दाने बहुत छोटे व हल्के रह जाते हैं"
            ]
        },
        "do_now": {
            "en": [
                "Spray an approved systemic fungicide strictly according to product label recommendations",
                "Ensure thorough coverage of both stems and lower leaf sheaths during application",
                "Provide light irrigation to prevent lodging of mechanically weakened stems"
            ],
            "hi": [
                "उत्पाद लेबल के निर्देशानुसार अनुशंसित फफूंदनाशक का तुरंत छिड़काव करें",
                "छिड़काव करते समय तनों और पत्तियों को अच्छी तरह से तर करें",
                "हल्की सिंचाई करें ताकि कमजोर तने गिरने से बच सकें"
            ]
        },
        "avoid_extra": {"en": [], "hi": []},
        "prevent": {
            "en": [
                "Grow certified stem rust resistant wheat cultivars recommended for central and southern zones",
                "Eradicate alternate host barberry bushes where present around cultivation tracts",
                "Avoid excessive late nitrogen fertilization during grain development stages"
            ],
            "hi": [
                "तना रतुआ रोधी प्रमाणित किस्मों का चयन करें",
                "खेत के आसपास के वैकल्पिक पौधों को नष्ट करें",
                "दाना भरते समय अत्यधिक यूरिया देने से बचें"
            ]
        },
        "sources": [{"name": "ICAR-IIWBR Black Rust Advisory", "url": "https://iiwbr.icar.gov.in"}],
        "review": {"status": "reviewed", "note": "Verified stem rust protocol"}
    },
    {
        "id": "Wheat___Healthy",
        "crop": {"en": "Wheat", "hi": "गेहूं"},
        "disease": {"en": "Healthy", "hi": "स्वस्थ"},
        "scientific_name": "Triticum aestivum",
        "type": "healthy",
        "healthy": True,
        "symptoms": {
            "en": [
                "Vibrant erect bluish-green leaves free of stripes, pustules, or powdery spore blankets",
                "Sturdy uniform tillers with intact crown roots and strong upright lodging resistance",
                "Fully exerted green spikes with plump healthy florets free from smut or discoloured awns"
            ],
            "hi": [
                "हरी-भरी सीधी पत्तियां जिन पर किसी प्रकार के पीले या भूरे धब्बे नहीं हैं",
                "मजबूत कल्ले और जड़ों का अच्छा विकास जिससे फसल गिरने से सुरक्षित रहती है",
                "स्वस्थ हरी बालियां जिनमें दाने अच्छे से भर रहे हों"
            ]
        },
        "do_now": {
            "en": [
                "Ensure scheduled irrigation at critical crown root initiation, jointing, flowering, and milk stages",
                "Scout fields periodically for early foliar signs of rust or aphid activity",
                "Apply timely split nitrogen dose prior to first and second irrigations"
            ],
            "hi": [
                "सीआरआई (ताज जड़), कल्ले फूटने, फूल आने और दाना भरते समय समय पर सिंचाई करें",
                "रतुआ या माहू की निगरानी के लिए नियमित रूप से खेत का चक्कर लगाएं",
                "पहली और दूसरी सिंचाई से पहले यूरिया की संतुलित खुराक दें"
            ]
        },
        "avoid_extra": {"en": [], "hi": []},
        "prevent": {
            "en": [
                "Follow integrated nutrient management incorporating farmyard manure and biofertilizers",
                "Maintain optimal seed drill spacing to encourage vigorous upright tillering",
                "Rotate with leguminous green manure crops to build resilient soil organic matter"
            ],
            "hi": [
                "गोबर की खाद और जैव उर्वरकों का संतुलित प्रयोग करें",
                "बीज बोते समय कतारों के बीच उचित दूरी रखें ताकि पौधों को पूरी धूप मिले",
                "दलहनी फसलों के साथ फसल चक्र अपनाकर मिट्टी की सेहत सुधारें"
            ]
        },
        "sources": [{"name": "ICAR-IIWBR Wheat Production Manual", "url": "https://iiwbr.icar.gov.in"}],
        "review": {"status": "reviewed", "note": "Healthy wheat baseline"}
    }
]

written = 0
for e in entries:
    cid = e["id"]
    # Validate against schema
    import jsonschema
    jsonschema.validate(e, SCHEMA)
    
    # Validate safety
    for key in ("symptoms", "do_now", "prevent"):
        assert len(e[key]["en"]) == len(e[key]["hi"]) == 3, f"{cid} len != 3"
    assert len(e["avoid_extra"]["en"]) == len(e["avoid_extra"]["hi"])
    text = json.dumps([e["symptoms"], e["do_now"], e["prevent"], e["avoid_extra"]], ensure_ascii=False)
    assert not DOSE.search(text), f"{cid} contains dose"
    
    joined = " ".join(e["do_now"]["en"]).lower()
    if "fungicide" in joined or "miticide" in joined or "copper" in joined:
        assert "label" in joined, f"{cid} must defer to label"
        
    out_path = kb_dir / f"{cid}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(e, f, indent=2, ensure_ascii=False)
    written += 1

print(f"Successfully validated and wrote {written} knowledge base entries to {kb_dir}")
