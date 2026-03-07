"""
Generates properly quoted CSV datasets for the AI Tourism System.
Run once: python generate_data.py
"""
import csv
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# ── Destinations ─────────────────────────────────────────────────────────────
DESTINATIONS = [
    (1,"Bali","Indonesia","Asia","beach tropical culture wellness",1200,4.7,"tropical","true","April-October","A magical island paradise blending lush rice terraces with vibrant Hindu culture and world-class surf breaks.",-8.4095,115.1889,"W213011"),
    (2,"Patagonia","Argentina","South America","adventure trekking nature wilderness",2800,4.9,"cold","false","November-March","One of the world's last great wildernesses — glaciers, jagged peaks, and endless wind-swept steppes.",-51.623,-69.2168,"W222423"),
    (3,"Santorini","Greece","Europe","romance luxury beach island",3200,4.8,"mediterranean","true","May-October","Iconic blue-domed churches and cliffside white buildings cascading above the volcanic caldera.",36.3932,25.4615,"W168177"),
    (4,"Kyoto","Japan","Asia","culture history temples zen",1800,4.8,"temperate","true","March-May","Japan's cultural heart — home to over 1000 Buddhist temples, lush bamboo forests, and the timeless tea ceremony.",35.0116,135.7681,"W208648"),
    (5,"Machu Picchu","Peru","South America","history adventure trekking ancient",1600,4.9,"highland","false","May-September","The legendary Incan citadel floating above the clouds in the Andes — a UNESCO World Heritage wonder.",-13.1631,-72.545,"W216491"),
    (6,"Reykjavik","Iceland","Europe","northern_lights adventure nature geothermal",2500,4.6,"subarctic","true","September-March","Gateway to Iceland's surreal landscapes — geysers, black sand beaches, and the Aurora Borealis.",64.147,-21.9426,"W104920"),
    (7,"Safari Kenya","Kenya","Africa","wildlife safari nature photography",3500,4.9,"tropical","false","July-October","Witness the Great Wildebeest Migration across the Masai Mara — nature's greatest spectacle.",-1.5061,35.1432,"W207825"),
    (8,"Amalfi Coast","Italy","Europe","romance scenic luxury coastal",2800,4.7,"mediterranean","true","May-September","A UNESCO coastline of dazzling villages perched on dramatic cliffs above the turquoise Tyrrhenian Sea.",40.634,14.6027,"W217148"),
    (9,"Queenstown","New Zealand","Oceania","adventure bungee skiing extreme_sports",2200,4.7,"temperate","true","June-August","The adventure capital of the world — bungee jumping, skydiving, and skiing against stunning alpine backdrops.",-45.0312,168.6626,"W184473"),
    (10,"Marrakech","Morocco","Africa","culture souks history budget",900,4.6,"arid","true","March-May","A sensory feast of winding medina alleys, vibrant souks, aromatic spices, and ornate palaces.",31.6295,-7.9811,"W205518"),
    (11,"Maldives","Maldives","Asia","beach luxury diving wellness",4500,4.9,"tropical","true","November-April","Crystal-clear turquoise lagoons and pristine coral reefs in the ultimate barefoot-luxury paradise.",3.2028,73.2207,"W188609"),
    (12,"Prague","Czech Republic","Europe","culture history architecture budget",800,4.7,"temperate","true","May-September","A fairy-tale city of Gothic spires, Baroque palaces, and cobblestone streets spanning the Vltava River.",50.0755,14.4378,"W111899"),
    (13,"Banff","Canada","North America","nature skiing hiking mountain",1800,4.8,"cold","true","June-August","Turquoise glacial lakes and soaring Rocky Mountain peaks in Canada's oldest national park.",51.4968,-115.9281,"W29462"),
    (14,"Dubrovnik","Croatia","Europe","coastal history romance island_hopping",2000,4.7,"mediterranean","true","May-September","The Pearl of the Adriatic — a perfectly preserved medieval walled city on the Dalmatian Coast.",42.6507,18.0944,"W184476"),
    (15,"Tokyo","Japan","Asia","culture food technology urban",2500,4.8,"temperate","true","March-May","A relentless electrifying megacity where ancient shrines and neon-lit streets coexist in harmony.",35.6762,139.6503,"W208617"),
    (16,"Petra","Jordan","Asia","history ancient adventure desert",1200,4.8,"arid","false","March-May","The legendary Rose City — a 2000-year-old Nabataean marvel carved directly into rose-red sandstone cliffs.",30.3285,35.4444,"W207940"),
    (17,"Cape Town","South Africa","Africa","nature culture wine coastal",1500,4.7,"mediterranean","true","November-March","Where two oceans meet — Table Mountain, the Cape Winelands, and the vibrant V&A Waterfront.",-33.9249,18.4241,"W223263"),
    (18,"Phuket","Thailand","Asia","beach budget nightlife diving",700,4.5,"tropical","true","November-April","Thailand's largest island — stunning Andaman beaches, emerald sea, and legendary Thai street food.",7.8804,98.3923,"W194804"),
    (19,"Amsterdam","Netherlands","Europe","culture canals art cycling",1800,4.6,"temperate","true","April-October","A city of masterpiece museums, charming canal houses, and a liberal vibrant arts scene.",52.3676,4.9041,"W127497"),
    (20,"Havana","Cuba","Caribbean","culture music history colonial",1000,4.6,"tropical","false","December-April","A living time capsule of vintage Cadillacs, crumbling colonial grandeur, and irresistible salsa rhythms.",23.1136,-82.3666,"W189518"),
    (21,"Swiss Alps","Switzerland","Europe","skiing mountain hiking luxury",4000,4.9,"cold","true","December-March","Pristine ski slopes and dramatic alpine scenery in the heart of Swiss skiing culture.",46.8182,8.2275,"W158185"),
    (22,"Angkor Wat","Cambodia","Asia","history temples culture ancient",600,4.8,"tropical","false","November-February","The world's largest religious monument — a breathtaking 12th-century Khmer empire temple complex.",13.4125,103.867,"W187484"),
    (23,"Barcelona","Spain","Europe","culture architecture beach food",1800,4.7,"mediterranean","true","May-October","Gaudi's organic masterpieces, La Rambla's buzz, and the sun-drenched Barceloneta beach in one city.",41.3851,2.1734,"W126874"),
    (24,"Rio de Janeiro","Brazil","South America","beach carnival culture urban",1200,4.6,"tropical","true","December-February","The Marvelous City — Copacabana, Christ the Redeemer, and the world's greatest Carnival.",-22.9068,-43.1729,"W214396"),
    (25,"Zanzibar","Tanzania","Africa","beach culture diving history",1000,4.7,"tropical","false","June-October","A spice island paradise blending white-sand beaches, turquoise Indian Ocean waters, and Swahili culture.",-6.1659,39.2026,"W218749"),
    (26,"Lisbon","Portugal","Europe","culture food coastal budget",1000,4.7,"mediterranean","true","April-October","Seven hilly neighborhoods of colorful azulejo tiles, vintage trams, and the melancholic sound of Fado.",38.7223,-9.1393,"W128285"),
    (27,"Galapagos Islands","Ecuador","South America","wildlife nature diving adventure",4000,4.9,"tropical","false","June-December","A living museum of extraordinary wildlife — giant tortoises, marine iguanas, and Darwin's finches.",-0.9538,-90.9656,"W211853"),
    (28,"Istanbul","Turkey","Asia","culture history food bridge",900,4.7,"mediterranean","true","April-June","Where East meets West — Hagia Sophia, the Grand Bazaar, and the shimmering Bosphorus Strait.",41.0082,28.9784,"W172085"),
    (29,"Hallstatt","Austria","Europe","scenic nature lake romantic",1500,4.8,"temperate","true","May-September","A jaw-dropping Alpine lakeside village — often called the most beautiful village in the world.",47.5622,13.6493,"W104617"),
    (30,"New Orleans","USA","North America","food music culture festivals",1200,4.6,"subtropical","true","February-May","The soulful birthplace of Jazz — Mardi Gras, beignets, and Bourbon Street's electric nightlife.",29.9511,-90.0715,"W27517"),
    (31,"Mount Cook","New Zealand","Oceania","mountain hiking stargazing nature",2000,4.8,"cold","false","December-March","New Zealand's highest peak surrounded by glaciers — a certified Dark Sky Reserve for breathtaking stargazing.",-43.595,170.1418,"W193026"),
    (32,"Chiang Mai","Thailand","Asia","culture temples trekking budget",400,4.7,"tropical","true","November-February","Northern Thailand's cultural crown jewel — hundreds of ornate temples and elephant sanctuaries.",18.7883,98.9853,"W195234"),
    (33,"Torres del Paine","Chile","South America","trekking nature wilderness adventure",2500,4.9,"cold","false","November-March","The crown jewel of Chilean Patagonia — iconic granite towers, glaciers, and pristine lakes.",-51.0341,-72.9904,"W219052"),
    (34,"Cinque Terre","Italy","Europe","coastal hiking scenic budget",1200,4.8,"mediterranean","true","May-September","Five candy-colored fishing villages clinging to dramatic Ligurian cliffs above the Italian Riviera.",44.1,9.72,"W212043"),
    (35,"Norwegian Fjords","Norway","Europe","scenic nature hiking kayaking",3000,4.9,"cold","true","June-August","UNESCO-listed fjords of staggering beauty — steep cliffs, mirror-like waters, and remote mountain villages.",60.472,8.4689,"W109285"),
    (36,"Varanasi","India","Asia","culture spirituality history ancient",300,4.6,"subtropical","false","October-March","The world's oldest living city — sacred ghats along the Ganges and the eternal cycle of life and death.",25.3176,82.9739,"W202432"),
    (37,"Phi Phi Islands","Thailand","Asia","beach diving snorkeling island",800,4.7,"tropical","false","November-April","Emerald waters, towering limestone karsts, and the world-famous Maya Bay.",7.7407,98.7784,"W196128"),
    (38,"Bhutan","Bhutan","Asia","culture spirituality himalaya trekking",3000,4.9,"mountain","false","March-May","The Last Shangri-La — a Buddhist kingdom measuring happiness in the pristine Himalayas.",27.5142,90.4336,"W183234"),
    (39,"Tuscany","Italy","Europe","wine food scenic cycling",2000,4.8,"mediterranean","true","April-October","Rolling hills dotted with vineyards, cypress trees, and medieval hilltop towns.",43.7711,11.2486,"W212345"),
    (40,"Oludeniz","Turkey","Asia","paragliding beach adventure coastal",800,4.7,"mediterranean","true","May-October","Home to Turkey's most photographed beach — the Blue Lagoon and the world's premier paragliding site.",36.5498,29.1143,"W192012"),
    (41,"Scottish Highlands","United Kingdom","Europe","nature hiking castles whisky",1200,4.7,"cold","true","May-September","Ancient lochs, rugged moorland, and medieval castles in Britain's last great wilderness.",57.0,-4.0,"W105912"),
    (42,"Siem Reap","Cambodia","Asia","history temples culture budget",500,4.7,"tropical","true","November-February","Gateway to the ancient temples of Angkor — the greatest archaeological marvel in Southeast Asia.",13.3671,103.8448,"W188012"),
    (43,"Palawan","Philippines","Oceania","beach diving nature island",1000,4.9,"tropical","false","November-May","An untouched paradise of turquoise lagoons, white beaches, and the UNESCO Puerto Princesa river.",9.8349,118.7384,"W193408"),
    (44,"Iceland Ring Road","Iceland","Europe","adventure nature northern_lights road_trip",3200,4.8,"subarctic","false","June-August","Drive the epic 1400km Route 1 circumnavigating the island — waterfalls, glaciers, and volcanic landscapes.",64.9631,-19.0208,"W104930"),
    (45,"Sahara Morocco","Morocco","Africa","adventure desert camping culture",1100,4.7,"arid","false","October-April","Journey to the edge of the Sahara — camel treks to towering sand dunes and nights in desert camps.",31.0,-4.0,"W206098"),
    (46,"Oaxaca","Mexico","North America","culture food indigenous art",700,4.7,"subtropical","true","October-May","Mexico's cultural and culinary capital — mezcal, vibrant markets, and Dia de Muertos.",17.0732,-96.7266,"W22934"),
    (47,"Ha Long Bay","Vietnam","Asia","scenic cruise nature kayaking",900,4.8,"tropical","true","October-April","A UNESCO World Heritage seascape of 1600 emerald limestone islands rising from the Gulf of Tonkin.",20.9101,107.1839,"W197845"),
    (48,"Serengeti","Tanzania","Africa","wildlife safari photography nature",4000,4.9,"tropical","false","June-October","Africa's most iconic safari destination — endless plains teeming with the Big Five and the Great Migration.",-2.3333,34.8333,"W220498"),
    (49,"Bruges","Belgium","Europe","history canals chocolate romantic",1200,4.7,"temperate","true","April-September","A perfectly preserved medieval gem of cobblestone streets and world-class Belgian chocolate.",51.2093,3.2247,"W104289"),
    (50,"Hoi An","Vietnam","Asia","culture lanterns food history",600,4.8,"tropical","true","February-August","A magical ancient trading port of colorful lanterns and some of Vietnam's finest cuisine.",15.8758,108.337,"W198072"),
    (51,"Meteora","Greece","Europe","spiritual hiking scenery history",900,4.9,"mediterranean","true","April-October","Monasteries perched impossibly atop towering rock pillars — one of the most astonishing sights on Earth.",39.7217,21.6306,"W169254"),
    (52,"Costa Rica","Costa Rica","Central America","wildlife adventure eco_tourism nature",1500,4.7,"tropical","false","December-April","A biodiversity hotspot of cloud forests, active volcanoes, and pristine Pacific and Caribbean beaches.",9.7489,-83.7534,"W208419"),
    (53,"Antelope Canyon","USA","North America","photography canyon nature scenic",1400,4.9,"arid","false","March-October","The photographer's holy grail — swirling sandstone slot canyons in Arizona that glow with ethereal light.",36.8619,-111.3743,"W23048"),
    (54,"Blue Lagoon Iceland","Iceland","Europe","wellness geothermal luxury unique",2000,4.7,"subarctic","true","Year-round","A milky-blue geothermal spa in a prehistoric lava field.",63.8804,-22.4495,"W104945"),
    (55,"Kruger Park","South Africa","Africa","wildlife safari photography nature",2500,4.8,"subtropical","false","May-September","South Africa's flagship safari — the Big Five in their most accessible and iconic setting.",-23.9884,31.5547,"W223481"),
    (56,"Kathmandu","Nepal","Asia","culture trekking himalaya spirituality",400,4.6,"mountain","false","October-November","The gateway to the Himalayas — chaotic spiritual and bursting with ancient temples.",27.7172,85.324,"W201982"),
    (57,"Positano","Italy","Europe","luxury romantic coastal scenic",3000,4.8,"mediterranean","true","May-September","The jewel of the Amalfi Coast — pastel-hued houses tumbling down a cliff into the sea.",40.628,14.485,"W216392"),
    (58,"Tulum","Mexico","North America","beach wellness Mayan cenotes",1200,4.7,"tropical","true","November-April","A boho paradise of Mayan ruins on clifftops, crystal cenotes, and Caribbean beaches.",20.2115,-87.4653,"W22742"),
    (59,"Taipei","Taiwan","Asia","food technology culture budget",800,4.6,"subtropical","true","October-December","A vibrant city of night markets and some of Asia's most spectacular street food.",25.033,121.5654,"W208902"),
    (60,"Cappadocia","Turkey","Asia","hot_air_balloon adventure scenic unique",1500,4.9,"arid","true","April-June","A dreamlike landscape of fairy chimneys and cave dwellings — best from a hot air balloon.",38.6431,34.8289,"W172432"),
    (61,"Lake Bled","Slovenia","Europe","scenic lake romantic hiking",1200,4.8,"temperate","true","April-October","A fairy-tale emerald lake with a tiny island church and a clifftop castle in the Julian Alps.",46.3683,14.1146,"W122589"),
    (62,"Lofoten Islands","Norway","Europe","northern_lights scenic fishing photography",2500,4.9,"cold","false","January-March","Dramatic Arctic archipelago of jagged peaks and some of the Northern Lights' best displays.",68.1576,13.9994,"W110423"),
    (63,"Ubud","Indonesia","Asia","culture wellness art nature",900,4.7,"tropical","true","April-October","Bali's spiritual and artistic heart — rice terraces, yoga retreats, and the Sacred Monkey Forest.",-8.5069,115.2625,"W213102"),
    (64,"Great Barrier Reef","Australia","Oceania","diving snorkeling wildlife nature",2500,4.8,"tropical","true","June-October","The world's largest coral reef system — an underwater paradise of extraordinary marine biodiversity.",-18.2871,147.6992,"W183192"),
    (65,"Jiuzhaigou","China","Asia","scenery nature lakes colorful",1100,4.9,"mountain","false","April-November","A magical valley of multi-colored lakes, waterfalls, and snow-capped peaks in Sichuan Province.",33.26,103.92,"W186432"),
    (66,"Salar de Uyuni","Bolivia","South America","unique photography nature adventure",800,4.8,"highland","false","November-April","The world's largest salt flat — a mirror-like expanse that perfectly reflects the sky.",-20.1338,-67.4891,"W215723"),
    (67,"El Nido","Philippines","Oceania","beach diving island nature",1000,4.9,"tropical","false","November-May","Hidden lagoons, secret beaches, and dramatic karst cliffs in Palawan's most pristine island paradise.",11.1784,119.4068,"W193218"),
    (68,"Chefchaouen","Morocco","Africa","photography culture scenic budget",500,4.8,"mountain","true","April-June","The Blue City — a labyrinth of strikingly blue-washed streets tucked into the Rif Mountains.",35.1688,-5.2636,"W205218"),
    (69,"Wadi Rum","Jordan","Asia","adventure desert camping scenic",800,4.8,"arid","false","March-May","The Valley of the Moon — a vast desert of soaring sandstone mountains and ancient petroglyphs.",29.576,35.4228,"W208019"),
    (70,"Plitvice Lakes","Croatia","Europe","nature lakes waterfalls hiking",1100,4.9,"temperate","true","April-October","A UNESCO cascade of 16 terraced turquoise lakes connected by thundering waterfalls in dense forest.",44.8654,15.582,"W184198"),
    (71,"Inca Trail","Peru","South America","trekking adventure history highland",1800,4.8,"highland","false","May-September","The world's most iconic trek — four days through cloud forest and Andean passes to Machu Picchu.",-13.52,-72.08,"W216621"),
    (72,"Socotra","Yemen","Asia","unique nature endemic beach",2200,4.9,"tropical","false","October-April","Earth's most alien-looking island — Dragon Blood Trees and endemic species found nowhere else.",12.4634,53.8237,"W207219"),
    (73,"Faroe Islands","Denmark","Europe","scenic nature hiking unique",2800,4.8,"cold","false","June-August","Remote Atlantic archipelago of emerald cliffs and roaring waterfalls in swirling mist.",61.8926,-6.9118,"W106219"),
    (74,"Bagan","Myanmar","Asia","history temples sunrise ancient",700,4.8,"tropical","false","November-February","A vast plain of over 2000 ancient Buddhist temples — best seen from a hot air balloon.",21.1717,94.8585,"W187091"),
    (75,"Sossusvlei","Namibia","Africa","desert photography nature scenic",2000,4.8,"arid","false","May-September","The world's tallest sand dunes — towering red-orange giants rising from the ancient Namib Desert.",-24.7281,15.3381,"W221183"),
    (76,"Kotor","Montenegro","Europe","coastal history medieval scenic",1000,4.8,"mediterranean","true","May-September","One of Europe's best-preserved medieval towns — a UNESCO bay of stunning natural beauty.",42.4247,18.7712,"W177289"),
    (77,"Yellowstone","USA","North America","nature geothermal wildlife geysers",2000,4.8,"temperate","true","June-September","America's first national park — Old Faithful, prismatic hot springs, grizzly bears, and wolf packs.",44.428,-110.5885,"W24482"),
    (78,"Darjeeling","India","Asia","tea mountain train himalaya",400,4.6,"mountain","true","October-November","The Queen of the Hills — emerald tea gardens, the Toy Train, and panoramic Himalayan views.",27.036,88.2627,"W201498"),
    (79,"Guilin","China","Asia","scenery river karst photography",800,4.8,"subtropical","true","April-October","Legendary alien karst peaks rising from the Li River — arguably China's most iconic landscape.",25.2736,110.29,"W186109"),
    (80,"Dolomites","Italy","Europe","mountain hiking skiing scenic",2200,4.9,"cold","true","June-September","A UNESCO mountain range of impossibly dramatic pinnacles glowing pink at sunset.",46.4102,11.844,"W212891"),
    (81,"Pamukkale","Turkey","Asia","thermal unique history wellness",700,4.7,"mediterranean","true","April-October","Snow-white travertine terraces of warm mineral pools — Turkey's surreal Cotton Castle.",37.9213,29.1199,"W172819"),
    (82,"Easter Island","Chile","South America","mystery history unique culture",2500,4.9,"subtropical","false","November-March","A remote volcanic island of over 1000 colossal stone Moai statues carved by the ancient Rapa Nui.",-27.1127,-109.3497,"W214209"),
    (83,"Similan Islands","Thailand","Asia","diving beach underwater nature",900,4.8,"tropical","false","November-April","Thailand's finest diving destination — pristine coral reefs in the Andaman Sea.",8.6367,97.6419,"W196483"),
    (84,"Munnar","India","Asia","tea nature mountain scenic",300,4.6,"highland","true","September-March","Kerala's glorious hill station — an emerald sea of rolling tea plantations in the Western Ghats.",10.0889,77.0595,"W201823"),
    (85,"Valletta","Malta","Europe","history culture coastal architecture",900,4.6,"mediterranean","true","April-June","Europe's smallest capital — a UNESCO Baroque city of grandmasters palaces and fortress walls.",35.8989,14.5146,"W167892"),
    (86,"Zhangjiajie","China","Asia","scenery nature unique forest",700,4.9,"subtropical","false","April-October","The real-life Avatar mountains — towering sandstone pillar columns wrapped in mist in Hunan Province.",29.1175,110.479,"W186892"),
    (87,"Big Island Hawaii","USA","North America","volcano lava beaches diving",2500,4.8,"tropical","true","Year-round","Witness live lava flows at Hawaii Volcanoes National Park and snorkel alongside manta rays.",19.8968,-155.5828,"W23891"),
    (88,"Jaisalmer","India","Asia","desert fort culture camel",300,4.6,"arid","false","October-March","The Golden City — a living desert fortress of sandstone rising from the Thar Desert.",26.9157,70.9083,"W201783"),
    (89,"Yosemite","USA","North America","nature hiking rock_climbing waterfalls",1800,4.9,"temperate","true","May-September","America's most beloved valley — El Capitan, Half Dome, and thundering waterfalls.",37.8651,-119.5383,"W24561"),
    (90,"Penang","Malaysia","Asia","food culture art budget",500,4.7,"tropical","true","December-February","Asia's food capital — a UNESCO heritage city of street food, colonial shophouses, and street art.",5.4141,100.3288,"W189412"),
    (91,"Skeleton Coast","Namibia","Africa","wilderness unique photography nature",3000,4.8,"arid","false","May-October","One of the world's most desolate and hauntingly beautiful coastlines — shipwrecks and desert lions.",-21.0,13.5,"W221634"),
    (92,"Rotorua","New Zealand","Oceania","geothermal Maori nature unique",1400,4.6,"temperate","true","Year-round","New Zealand's geothermal wonderland — boiling mud pools, geysers, and immersive Maori culture.",-38.1368,176.2497,"W184621"),
    (93,"Siwa Oasis","Egypt","Africa","desert unique history oasis",600,4.7,"arid","false","October-March","A remote oasis of date palms in Egypt's Western Desert — oracle temple of Alexander the Great.",29.2031,25.5194,"W203819"),
    (94,"Hvar","Croatia","Europe","beach nightlife island lavender",1500,4.7,"mediterranean","true","June-September","Croatia's sunniest island of lavender fields, Renaissance piazzas, and glamorous beach clubs.",43.1729,16.4412,"W185219"),
    (95,"Alberobello","Italy","Europe","unique culture history architecture",1000,4.7,"mediterranean","true","April-October","A surreal UNESCO village of whitewashed trulli cone-roofed houses.",40.7879,17.2414,"W214982"),
    (96,"Kuala Lumpur","Malaysia","Asia","urban food culture budget",600,4.5,"tropical","true","Year-round","A dynamic multicultural metropolis with Petronas Towers, vibrant street food markets, and rich Malay culture.",3.139,101.6869,"W187234"),
    (97,"Cinque Terre Alt","Italy","Europe","coastal hiking scenic food",1300,4.8,"mediterranean","true","May-September","Dramatic coastal villages with colorful buildings and excellent Ligurian seafood cuisine.",44.127,9.715,"W212044"),
    (98,"Koh Samui","Thailand","Asia","beach luxury resort tropical",1100,4.6,"tropical","true","December-April","Thailand's tropical resort island with palm-fringed beaches, luxury spas, and vibrant beach clubs.",9.5120,100.0136,"W196521"),
    (99,"Hampi","India","Asia","history ruins architecture ancient",250,4.7,"arid","false","October-February","A UNESCO World Heritage site of 14th-century Vijayanagara Empire ruins scattered across a boulder-strewn landscape.",15.335,76.4619,"W201456"),
    (100,"Fjordland NP","New Zealand","Oceania","nature fjords hiking scenic",2200,4.9,"cold","true","December-March","New Zealand's most spectacular national park — Milford Sound, Doubtful Sound, and Sutherland Falls.",-45.4136,167.7197,"W184782"),
]

dest_fields = ["id","name","country","continent","tags","avg_cost_usd","avg_rating","climate","accessibility","best_season","description","latitude","longitude","xid"]

with open(os.path.join(DATA_DIR, "destinations.csv"), "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f, quoting=csv.QUOTE_ALL)
    writer.writerow(dest_fields)
    writer.writerows(DESTINATIONS)

print(f"Generated destinations.csv — {len(DESTINATIONS)} rows")

# ── Users ─────────────────────────────────────────────────────────────────────
USERS = [
    ("U001","Arjun Sharma","medium","adventure trekking mountain himalaya","5 57 71","false","adventurer"),
    ("U002","Priya Nair","high","beach luxury wellness diving","1 11 3","true","luxury"),
    ("U003","Carlos Rivera","low","budget culture food history","12 32 50","true","backpacker"),
    ("U004","Emma Johnson","high","romance luxury coastal wine","8 39 57","true","romantic"),
    ("U005","Liam OBrien","medium","adventure nature hiking wildlife","7 9 27","false","eco_traveler"),
    ("U006","Yuki Tanaka","medium","culture temples history food","4 15 22","true","cultural"),
    ("U007","Fatima Al-Rashid","medium","culture history desert ancient","16 28 69","false","cultural"),
    ("U008","Sofia Andersen","high","scenic northern_lights nature geothermal","6 35 62","true","explorer"),
    ("U009","Raj Patel","low","budget food culture temples","32 42 50","true","backpacker"),
    ("U010","Marie Dubois","high","romance wine food art","39 57 3","true","romantic"),
    ("U011","Noah Williams","medium","adventure extreme_sports skiing mountain","9 21 80","false","adventurer"),
    ("U012","Aisha Mbeki","low","wildlife safari nature photography","7 48 55","false","eco_traveler"),
    ("U013","Lucas Santos","medium","beach carnival food music","24 19 10","true","cultural"),
    ("U014","Hana Kim","high","culture temples zen food","4 15 38","true","cultural"),
    ("U015","Oliver Brown","medium","hiking nature waterfalls national_park","89 77 70","true","eco_traveler"),
    ("U016","Amara Diallo","low","culture indigenous art food","46 10 36","false","cultural"),
    ("U017","Ivan Petrov","medium","skiing mountain adventure cold","21 80 2","false","adventurer"),
    ("U018","Isabella Rossi","high","coastal scenic luxury romantic","57 8 3","true","romantic"),
    ("U019","James Wilson","medium","history ancient culture temples","22 4 16","true","cultural"),
    ("U020","Mei Chen","high","luxury beach diving wellness","11 43 64","true","luxury"),
    ("U021","Andre Moreau","medium","food wine culture cycling","39 23 26","true","cultural"),
    ("U022","Zara Ahmed","low","budget culture food backpacker","32 12 50","true","backpacker"),
    ("U023","Thomas Mueller","high","skiing mountain luxury adventure","21 80 35","false","luxury"),
    ("U024","Valentina Cruz","medium","beach culture Mayan cenotes","58 46 24","true","explorer"),
    ("U025","Ben Taylor","medium","wildlife nature photography safari","7 48 27","false","eco_traveler"),
    ("U026","Nadia Svensson","high","northern_lights scenic nature cold","6 62 44","false","explorer"),
    ("U027","Kwame Asante","low","culture history music food","10 28 36","true","cultural"),
    ("U028","Elena Volkov","medium","culture history architecture canals","19 49 61","true","cultural"),
    ("U029","Sam Park","medium","technology food urban culture","15 59 90","true","cultural"),
    ("U030","Leila Hassan","medium","desert adventure camping scenic","69 45 88","false","adventurer"),
    ("U031","Max Schreiber","medium","adventure bungee extreme_sports","9 40 83","false","adventurer"),
    ("U032","Chloe Martin","high","wellness thermal romantic luxury","54 81 11","true","luxury"),
    ("U033","Diego Fernandez","low","budget beach diving island","37 43 83","false","backpacker"),
    ("U034","Aiko Yamamoto","medium","culture art temples photography","4 74 22","true","cultural"),
    ("U035","Patrick OConnor","medium","hiking castles nature whisky","41 35 6","false","eco_traveler"),
    ("U036","Ling Wei","medium","scenery lakes colorful photography","65 70 61","true","explorer"),
    ("U037","Olga Kimova","high","luxury coastal island romance","11 3 94","true","luxury"),
    ("U038","Marcus Johnson","low","budget culture temples history","42 74 86","true","backpacker"),
    ("U039","Sari Korhonen","medium","nature hiking northern_lights cold","35 62 6","false","eco_traveler"),
    ("U040","Camille Bernard","high","wine food art romance","39 21 49","true","luxury"),
    ("U041","Phan Duc","low","food culture history budget","50 47 42","true","backpacker"),
    ("U042","Rashida Thomas","medium","wildlife safari photography nature","48 55 7","false","eco_traveler"),
    ("U043","Felix Bauer","medium","adventure trekking mountain nature","2 33 71","false","adventurer"),
    ("U044","Yara Saleh","medium","history ancient culture temples","16 28 22","true","cultural"),
    ("U045","Ethan Clark","medium","beach diving snorkeling island","43 83 64","false","eco_traveler"),
    ("U046","Nour Ben Ali","high","luxury beach wellness spa","11 32 54","true","luxury"),
    ("U047","Luisa Gomez","low","culture food indigenous art","46 10 50","true","backpacker"),
    ("U048","Bjorn Larsson","medium","hiking nature fjords cold","35 73 41","false","eco_traveler"),
    ("U049","Maya Gupta","medium","culture spirituality ancient temples","36 4 22","false","cultural"),
    ("U050","Aaron Mitchell","high","adventure photography unique scenic","60 66 72","false","explorer"),
]

user_fields = ["user_id","name","budget_bracket","preferred_tags","visited_destinations","accessibility_needs","travel_style"]

with open(os.path.join(DATA_DIR, "users.csv"), "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f, quoting=csv.QUOTE_ALL)
    writer.writerow(user_fields)
    writer.writerows(USERS)

print(f"Generated users.csv — {len(USERS)} rows")

# ── Ratings ───────────────────────────────────────────────────────────────────
RATINGS = [
    ("U001",5,5.0),("U001",2,4.5),("U001",71,5.0),("U001",56,4.0),("U001",38,4.5),("U001",80,4.0),("U001",33,3.5),("U001",13,4.5),
    ("U002",1,5.0),("U002",11,5.0),("U002",3,4.5),("U002",57,4.5),("U002",54,4.0),("U002",39,4.0),("U002",94,4.5),
    ("U003",12,5.0),("U003",32,4.5),("U003",50,4.5),("U003",42,4.0),("U003",26,4.5),("U003",90,4.0),("U003",22,4.5),
    ("U004",8,5.0),("U004",39,5.0),("U004",57,4.5),("U004",3,4.5),("U004",49,4.0),("U004",29,4.5),("U004",61,4.0),
    ("U005",7,5.0),("U005",9,4.5),("U005",27,5.0),("U005",55,4.0),("U005",35,4.5),("U005",52,4.5),("U005",15,3.5),
    ("U006",4,5.0),("U006",15,4.5),("U006",22,5.0),("U006",38,4.5),("U006",74,4.0),("U006",42,4.5),("U006",34,3.5),
    ("U007",16,5.0),("U007",28,4.5),("U007",69,5.0),("U007",10,4.0),("U007",45,4.5),("U007",88,4.0),("U007",81,4.5),
    ("U008",6,5.0),("U008",35,5.0),("U008",62,4.5),("U008",44,4.0),("U008",73,4.5),("U008",29,4.0),("U008",54,4.5),
    ("U009",32,5.0),("U009",42,4.5),("U009",50,4.5),("U009",22,4.0),("U009",12,4.0),("U009",26,3.5),("U009",86,4.0),
    ("U010",39,5.0),("U010",57,5.0),("U010",3,4.5),("U010",49,4.5),("U010",21,4.0),("U010",19,4.0),("U010",20,4.5),
    ("U011",9,5.0),("U011",21,4.5),("U011",80,5.0),("U011",40,4.0),("U011",44,4.5),("U011",31,4.0),("U011",2,4.5),
    ("U012",7,5.0),("U012",48,5.0),("U012",55,4.5),("U012",25,4.5),("U012",42,4.0),("U012",91,4.0),("U012",75,4.5),
    ("U013",24,5.0),("U013",19,4.0),("U013",10,4.0),("U013",23,4.5),("U013",30,4.5),("U013",26,3.5),("U013",58,4.0),
    ("U014",4,5.0),("U014",15,4.5),("U014",38,5.0),("U014",22,4.5),("U014",74,4.0),("U014",34,4.0),("U014",86,4.0),
    ("U015",89,5.0),("U015",77,4.5),("U015",70,5.0),("U015",35,4.0),("U015",9,4.5),("U015",80,4.5),("U015",13,4.0),
    ("U016",46,5.0),("U016",10,4.5),("U016",36,4.5),("U016",27,4.0),("U016",88,4.0),("U016",28,3.5),("U016",84,4.0),
    ("U017",21,5.0),("U017",80,5.0),("U017",2,4.5),("U017",35,4.0),("U017",9,4.5),("U017",33,4.0),("U017",73,4.0),
    ("U018",57,5.0),("U018",8,5.0),("U018",3,4.5),("U018",29,4.5),("U018",61,4.0),("U018",94,4.5),("U018",14,4.0),
    ("U019",22,5.0),("U019",4,4.5),("U019",16,5.0),("U019",28,4.0),("U019",74,4.0),("U019",42,4.5),("U019",19,3.5),
    ("U020",11,5.0),("U020",43,5.0),("U020",64,4.5),("U020",1,4.5),("U020",37,4.0),("U020",54,4.0),("U020",18,3.5),
    ("U021",39,5.0),("U021",21,4.5),("U021",49,4.5),("U021",23,4.0),("U021",26,4.0),("U021",34,4.5),("U021",19,4.0),
    ("U022",32,5.0),("U022",12,4.5),("U022",50,4.5),("U022",26,4.0),("U022",42,4.0),("U022",22,4.5),("U022",90,3.5),
    ("U023",21,5.0),("U023",80,5.0),("U023",35,4.5),("U023",9,4.0),("U023",29,4.5),("U023",54,4.0),("U023",73,4.5),
    ("U024",58,5.0),("U024",46,4.5),("U024",24,4.5),("U024",19,4.0),("U024",1,4.0),("U024",37,4.0),("U024",28,3.5),
    ("U025",7,5.0),("U025",48,5.0),("U025",27,4.5),("U025",55,4.0),("U025",52,4.5),("U025",5,4.0),("U025",77,4.0),
    ("U026",6,5.0),("U026",62,5.0),("U026",44,4.5),("U026",35,4.5),("U026",73,4.0),("U026",31,4.0),("U026",54,4.5),
    ("U027",10,5.0),("U027",28,4.5),("U027",36,4.0),("U027",27,4.5),("U027",46,4.0),("U027",30,4.5),("U027",88,3.5),
    ("U028",19,5.0),("U028",49,4.5),("U028",61,4.5),("U028",29,4.0),("U028",14,4.5),("U028",70,4.0),("U028",50,4.0),
    ("U029",15,5.0),("U029",59,5.0),("U029",90,4.5),("U029",19,4.0),("U029",29,4.0),("U029",23,4.5),("U029",4,3.5),
    ("U030",69,5.0),("U030",45,5.0),("U030",88,4.5),("U030",10,4.0),("U030",81,4.5),("U030",16,4.0),("U030",28,4.5),
    ("U031",9,5.0),("U031",40,5.0),("U031",83,4.5),("U031",44,4.5),("U031",2,4.0),("U031",31,4.0),("U031",33,4.5),
    ("U032",54,5.0),("U032",81,4.5),("U032",11,5.0),("U032",3,4.5),("U032",29,4.0),("U032",32,4.0),("U032",61,4.5),
    ("U033",37,5.0),("U033",43,4.5),("U033",83,4.5),("U033",1,4.0),("U033",33,4.5),("U033",18,4.0),("U033",90,3.5),
    ("U034",4,5.0),("U034",74,4.5),("U034",22,4.5),("U034",63,4.0),("U034",15,4.5),("U034",34,4.0),("U034",19,3.5),
    ("U035",41,5.0),("U035",35,4.5),("U035",6,4.5),("U035",13,4.0),("U035",77,4.0),("U035",73,4.5),("U035",80,3.5),
    ("U036",65,5.0),("U036",70,5.0),("U036",61,4.5),("U036",36,4.0),("U036",29,4.5),("U036",79,4.5),("U036",47,4.0),
    ("U037",11,5.0),("U037",3,4.5),("U037",94,5.0),("U037",43,4.0),("U037",57,4.5),("U037",18,4.0),("U037",1,4.5),
    ("U038",42,5.0),("U038",74,4.5),("U038",86,4.0),("U038",22,4.5),("U038",32,4.0),("U038",36,4.0),("U038",50,3.5),
    ("U039",35,5.0),("U039",62,5.0),("U039",6,4.5),("U039",73,4.0),("U039",41,4.5),("U039",13,4.0),("U039",77,4.0),
    ("U040",39,5.0),("U040",21,5.0),("U040",49,4.5),("U040",23,4.0),("U040",57,4.5),("U040",19,4.0),("U040",3,4.5),
    ("U041",50,5.0),("U041",47,4.5),("U041",42,4.5),("U041",90,4.0),("U041",32,3.5),("U041",86,4.0),("U041",18,4.0),
    ("U042",48,5.0),("U042",55,5.0),("U042",7,4.5),("U042",25,4.0),("U042",41,4.5),("U042",75,4.5),("U042",27,4.0),
    ("U043",2,5.0),("U043",33,4.5),("U043",71,5.0),("U043",80,4.5),("U043",9,4.0),("U043",35,4.5),("U043",56,4.0),
    ("U044",16,5.0),("U044",28,4.5),("U044",22,4.5),("U044",42,4.0),("U044",81,4.0),("U044",74,4.5),("U044",69,4.0),
    ("U045",43,5.0),("U045",83,5.0),("U045",64,4.5),("U045",37,4.0),("U045",1,4.5),("U045",18,4.0),("U045",33,4.0),
    ("U046",11,5.0),("U046",32,4.0),("U046",54,5.0),("U046",3,4.5),("U046",18,4.0),("U046",94,4.5),("U046",1,4.0),
    ("U047",46,5.0),("U047",10,4.5),("U047",50,4.5),("U047",32,4.0),("U047",26,4.0),("U047",22,4.5),("U047",42,3.5),
    ("U048",35,5.0),("U048",73,5.0),("U048",41,4.5),("U048",6,4.0),("U048",13,4.5),("U048",62,4.5),("U048",70,4.0),
    ("U049",36,5.0),("U049",4,4.5),("U049",22,4.5),("U049",38,4.5),("U049",56,4.0),("U049",74,4.0),("U049",16,4.0),
    ("U050",60,5.0),("U050",66,5.0),("U050",72,4.5),("U050",82,4.5),("U050",51,4.5),("U050",86,4.5),("U050",62,4.0),
]

ratings_data = [(f"U{str(uid).zfill(3)}" if not str(uid).startswith("U") else uid, dest_id, rating) for uid, dest_id, rating in RATINGS]

with open(os.path.join(DATA_DIR, "ratings.csv"), "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f, quoting=csv.QUOTE_ALL)
    writer.writerow(["user_id","destination_id","rating"])
    for row in RATINGS:
        writer.writerow(list(row))

print(f"Generated ratings.csv — {len(RATINGS)} rows")
print("All datasets generated successfully!")
