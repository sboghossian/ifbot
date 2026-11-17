"""Everyday health and travel knowledge. Each rule: groups joined by '&' must all match;
words inside a group separated by '|' are alternatives. General wellbeing only."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Optional

from ..arbiter import Proposal

if TYPE_CHECKING:  # pragma: no cover
    from ..engine import Context

D = "See a doctor if it is serious or does not improve."

RULES = [
    # ---------------- HEALTH ----------------
    ("water|hydrat|fluid & drink|much|enough|day|daily|thirst", "Needs vary from person to person, but drinking water regularly through the day and when you feel thirsty is a good habit."),
    ("hydrat|dehydrat|thirst", "To stay hydrated, drink water regularly through the day, drink more when it is hot or you exercise, and drink when you feel thirsty."),
    ("hand|hands & wash|clean|soap|germ", "Washing your hands with soap removes germs and helps stop infections from spreading."),
    ("wash|clean & hand|hands & how|long|properly|when", "Wash your hands with soap and water, rubbing all surfaces for about twenty seconds, then rinse and dry them well, especially before eating and after the toilet."),
    ("sleep|bed|bedtime|insomnia|rest & habit|better|good|tip|improve|well|help|trouble|hard|cannot|cant", "Keep a regular bedtime, avoid screens just before bed, and keep your bedroom dark and quiet."),
    ("sleep & hour|much|enough|need", "Most adults do best with around seven to nine hours of sleep a night, though needs vary by person and age."),
    ("nap|napping", "A short nap earlier in the day can refresh you, but a long nap late in the day may make it harder to sleep at night."),
    ("caffeine|coffee & sleep|night|evening|late", "Caffeine late in the day can keep you awake, so try to avoid coffee and strong tea in the evening."),
    ("eye|eyes|eyestrain|vision & computer|screen|work|working|tired|strain|look", "Take regular breaks to look at something far away, and make sure your screen is not too bright."),
    ("cut|cuts|scrape|graze|wound & small|minor|get|got|what|do|treat|clean|bleeding", "Wash the cut with clean water, press on it with a clean cloth to stop the bleeding, and cover it with a bandage."),
    ("burn|burns|burnt|scald & minor|small|first|treat|do|what|cool|aid|kitchen", "Cool a minor burn under cool running water for several minutes, do not use ice or butter, and cover it loosely with a clean dressing. " + D),
    ("nosebleed|nose & bleed|bleeding|blood", "Sit up, lean slightly forward, and pinch the soft part of your nose for about ten minutes. " + D),
    ("sprain|sprained|twist|twisted|ankle & what|do|treat|first|help", "For a minor sprain, rest the joint, apply a cold pack wrapped in cloth, keep it raised, and see a doctor if you cannot put weight on it or it is very swollen."),
    ("bruise|bruises|bruised", "For a bruise, apply a cold pack wrapped in cloth for a short while and rest the area; it usually fades by itself over a couple of weeks."),
    ("blister|blisters", "Keep a blister clean and covered with a plaster, and try not to pop it, since the skin protects it while it heals."),
    ("insect|bug|mosquito|bee|wasp & bite|bites|sting|stings|stung|itch", "Wash an insect bite or sting with soap and water, apply a cold pack to ease swelling, and avoid scratching. Get urgent help if you have trouble breathing or your face swells."),
    ("splinter", "Wash your hands and the area, then gently remove the splinter with clean tweezers and wash the skin again."),
    ("sunburn|sunscreen|sun & protect|skin|burn|prevent|avoid|lotion|cream", "Protect your skin from the sun with sunscreen, a hat, loose clothing and shade, especially in the middle of the day, and reapply sunscreen regularly."),
    ("cold|flu|sniffle|sniffles & recover|rest|help|treat|better|what|do|common|catch|have", "For a common cold, rest, drink plenty of fluids and keep warm; most colds pass in about a week. See a doctor if symptoms are severe or last longer."),
    ("sore & throat", "For a sore throat, rest, drink plenty of fluids and warm drinks, and see a doctor if it is severe or lasts more than a few days."),
    ("cough|coughing", "For a cough, rest and drink plenty of fluids, and see a doctor if it lasts for several weeks or you have trouble breathing."),
    ("fever", "With a fever, rest and drink plenty of fluids, and contact a doctor if it is high, lasts more than a few days, or comes with other worrying symptoms."),
    ("headache|headaches|migraine", "For a mild headache, rest in a quiet place, drink water and avoid screens for a while. See a doctor if headaches are severe, frequent or sudden."),
    ("stomach|upset|nausea|nauseous|diarrhoea|diarrhea|vomit|vomiting & ache|what|do|help|food|poisoning|tummy|sick", "For an upset stomach, rest and sip water or other fluids often, and eat plain food once you feel able. See a doctor if it is severe or lasts more than a couple of days."),
    ("constipation|digestion|digest|bloating", "Fibre from fruit, vegetables and whole grains, plenty of water and regular movement help digestion. See a doctor if problems continue."),
    ("back & pain|ache|posture|sore|hurt|care", "Keep moving gently, avoid sitting for long stretches, and check your posture and chair. See a doctor if back pain is severe or does not improve."),
    ("posture|sitting|sit|desk & back|neck|good|healthy|long|stand|ergonomic|work", "Sit with your feet flat, back supported and screen at eye level, and stand up and move around regularly."),
    ("stretch|stretching|stretches", "Stretch gently after warming up, hold each stretch without bouncing, and stop if you feel sharp pain."),
    ("warm & up|exercise|workout|before", "Warm up before exercise with a few minutes of light movement to get your muscles ready and lower the risk of injury."),
    ("exercise|workout|physical|activity|active & much|often|week|need|should|recommend|how", "Regular movement most days is good for your health; even a brisk daily walk helps. Build up gradually and check with a doctor if you have health concerns."),
    ("exercise|workout|fitness|gym|active & start|begin|beginner|getting|motivated|motivation|habit", "Start small with something you enjoy, such as walking, and build up gradually. Regular, achievable sessions work better than doing too much too soon."),
    ("walk|walking|steps & benefit|good|healthy|daily", "Walking regularly is a simple way to stay fit; it is good for your heart, mood and energy, and you can build up the time slowly."),
    ("muscle|muscles|soreness & sore|ache|after|recover|recovery", "For sore muscles after exercise, rest, gentle movement, light stretching and plenty of water help recovery."),
    ("rest|recover|recovery & day|days|after|exercise|workout", "Rest days let your body recover and get stronger, so include them between harder workouts."),
    ("diet|eat|eating|food|nutrition|meal|meals & healthy|healthily|balanced|good|better|tips|well", "A healthy diet includes plenty of vegetables and fruit, whole grains, some protein, and not too much sugar, salt and processed food."),
    ("vegetable|vegetables|fruit|fruits & portion|portions|daily|day|much|many|eat|should", "Aim to eat a variety of fruit and vegetables every day; they provide vitamins, minerals and fibre."),
    ("breakfast & important|skip|skipping|eat|healthy|good", "Breakfast can give you energy for the morning, but what matters most is eating regular, balanced meals that suit you."),
    ("sugar|sugary|sweet|sweets|soda|snack|snacks & much|less|cut|reduce|avoid|healthy|bad", "Too much sugar can harm your teeth and health, so choose water or unsweetened drinks and eat sweet foods only occasionally."),
    ("salt|sodium & much|less|cut|reduce|bad|eat", "Too much salt is not good for your health, so go easy on salty processed food and taste before you add more."),
    ("fibre|fiber", "Fibre from whole grains, beans, fruit and vegetables supports healthy digestion and keeps you feeling full."),
    ("protein", "Protein from sources such as beans, eggs, fish, meat and dairy helps your body build and repair itself, and most people get enough from a varied diet."),
    ("vitamin|vitamins|supplement|supplements & need|take|should|necessary", "Most people can get the vitamins they need from a varied, balanced diet; ask a doctor or pharmacist before taking supplements."),
    ("weight|lose|losing|slim|overweight & healthy|how|safely|tips|loss", "For healthy weight management, eat balanced meals with sensible portions, move more and sleep well, and avoid crash diets. A doctor can give personal advice."),
    ("snack|snacking & healthy|good|better|choose", "Healthy snacks include fruit, vegetables with a dip, yoghurt, or a handful of nuts."),
    ("tooth|teeth|dental|brush|brushing|toothbrush & how|often|twice|clean|care|good|healthy|long", "Brush your teeth for about two minutes twice a day with fluoride toothpaste, clean between them daily, and visit the dentist regularly."),
    ("floss|flossing|gum|gums", "Cleaning between your teeth daily with floss or small brushes helps keep your gums healthy; see a dentist if gums keep bleeding."),
    ("toothache|dentist|cavity|cavities", "Limit sugary food and drinks, brush twice a day and see a dentist regularly; see one soon if you have a toothache."),
    ("shower|bath|bathe|hygiene|hygienic & daily|often|how|good|personal", "Wash regularly with soap and water, especially after sweating, and keep your clothes, nails and hair clean for good hygiene."),
    ("nail|nails|fingernail & trim|cut|clean|care|bitten|bite", "Keep your nails short and clean, since dirt and germs can collect under them."),
    ("skin & care|dry|healthy|moisturise|moisturize|routine", "For healthy skin, wash gently, moisturise if it feels dry, drink water, and protect it from the sun."),
    ("hair & wash|care|healthy|often|dandruff", "Wash your hair as often as feels comfortable for you with a gentle shampoo, and avoid harsh treatments and too much heat."),
    ("stress|stressed|anxiety|anxious|worry|worried|overwhelmed|relax|relaxation|calm", "To ease stress, take slow deep breaths, go for a walk, get enough sleep and talk to someone you trust. If it feels overwhelming, speak to a doctor or counsellor."),
    ("mental & health|wellbeing|wellness|healthy|care|look", "To look after your mental health, stay connected with people, keep active, sleep well, take breaks and ask for help from a professional if you are struggling."),
    ("mood|sad|sadness|low|down|depressed|lonely|loneliness", "If you feel low, talk to someone you trust, get some daylight and gentle exercise, and speak to a doctor or counsellor if it continues."),
    ("breathing|breathe|breath & deep|exercise|calm|technique|relax", "Slow deep breathing, in through the nose and out gently, can help you feel calmer."),
    ("meditation|mindfulness|meditate", "Mindfulness or meditation can be as simple as sitting quietly for a few minutes and paying attention to your breathing."),
    ("energy|tired|tiredness|fatigue|fatigued|exhausted|sluggish & boost|more|feel|always|why|low|increase", "To keep your energy up, get regular sleep, eat balanced meals, drink water and move daily. See a doctor if you are tired all the time."),
    ("focus|concentrate|concentration|study|studying|productive|productivity & better|improve|help|tips|how", "To focus better, sleep well, take short breaks, reduce distractions, and drink water."),
    ("screen|screens|phone|phones|device & time|too|much|limit|bed|night|before", "Limit screen time, take breaks, and avoid screens just before bed so that your sleep is not disturbed."),
    ("smoke|smoking|cigarette|cigarettes|quit|vape|vaping|tobacco", "Not smoking is one of the best things you can do for your health. A doctor or pharmacist can offer support if you want to quit."),
    ("alcohol|drinking|drink & healthy|limit|much|safe|moderation|moderate", "If you drink alcohol, keep it moderate, have alcohol-free days, and drink water alongside it. Ask a doctor for personal advice."),
    ("first & aid & kit|contents|have|home|what|should|include", "A basic first aid kit holds plasters, sterile dressings, bandages, antiseptic wipes, tweezers, scissors, gloves and a thermometer."),
    ("emergency|urgent|choking|unconscious|stroke|heart|attack|severe|bleeding & call|number|what|do|help|doctor", "In a serious emergency, call your local emergency number straight away and follow the operator's instructions."),
    ("doctor|gp|physician|check|checkup|appointment & when|see|should|go|visit|often|regular", "See a doctor if symptoms are severe, sudden, unusual or do not improve, and have regular check-ups to keep an eye on your health."),
    ("allergy|allergies|allergic|hayfever", "If you think you have an allergy, try to avoid the trigger and see a doctor or pharmacist for advice. Get urgent help for any trouble breathing or swelling of the face."),
    ("pharmacist|pharmacy|medicine|medicines|medication|tablets|pills & safe|safely|take|store|how|use|child|children", "Read the label and follow the instructions, keep medicines out of reach of children, and ask a pharmacist or doctor if you are unsure."),
    ("wear|wearing|sunglasses|glasses|contact|lenses & eyes|eye|protect|care|clean", "Keep your glasses and lenses clean, follow your optician's advice, and have regular eye tests."),
    ("ear|ears|hearing|headphones|loud|volume|noise & protect|damage|care|safe", "Keep headphone volume moderate, take breaks from loud sounds and protect your ears at loud events to help protect your hearing."),
    ("cold & weather|winter|keep|warm|stay|dress|layers", "In cold weather, dress in warm layers, keep your head, hands and feet covered, and stay dry."),
    ("heat|hot|heatwave|summer|sunstroke|overheating & stay|cool|safe|avoid|tips|weather", "In hot weather, drink plenty of water, stay in the shade or somewhere cool in the hottest hours, wear light clothing and a hat, and rest."),
    ("lifting|lift|heavy|carry & safely|back|how|properly", "To lift safely, bend your knees, keep your back straight and the load close to your body, and avoid twisting."),
    ("routine|habit|habits|healthy|lifestyle|wellbeing|wellness & daily|build|good|tips|stay|live|living", "Healthy habits include regular sleep, balanced meals, plenty of water, daily movement and time to relax."),
    ("immune|immunity|immune system & boost|strengthen|support|improve|healthy|stronger", "To support your immune system, sleep well, eat a balanced diet, stay active, manage stress and wash your hands regularly."),
    ("vaccine|vaccines|vaccination|vaccinations|immunisation|immunization|jab|jabs", "Vaccines help protect you and others from serious illness; ask your doctor which ones are recommended for you."),
    ("germs|infection|infections|spread|prevent|illness & stop|avoid|catching|stay|healthy|prevent|cough|sneeze", "To stop germs spreading, wash your hands often, cover coughs and sneezes with a tissue or your elbow, and stay home when you are unwell."),
    ("sneeze|sneezing|tissue", "Cover your mouth and nose with a tissue or your elbow when you cough or sneeze, then throw the tissue away and wash your hands."),
    ("posture|stand|standing|sitting|sit|desk|breaks|sedentary|long & hours|too|much|move|break", "If you sit for long periods, stand up, stretch and walk around every so often."),
    ("mask|masks", "Wearing a mask in crowded or high-risk settings can help reduce the spread of germs, and following local health guidance is sensible."),
    ("kitchen|food & hygiene|safe|safety|poisoning|storing|fridge|raw|meat|chicken", "For food safety, wash your hands, keep raw meat away from other food, cook food thoroughly, and chill leftovers promptly."),
    ("baby|toddler|child|children|kid|kids & sleep|bedtime|routine", "Children do best with a regular bedtime routine and enough sleep; ask a doctor or health visitor for advice about your child."),
    ("elderly|older|senior|aging|ageing & healthy|stay|active|tips|care", "Staying active, eating well, keeping in touch with others and having regular check-ups all help older people stay healthy."),
    ("period|pregnancy|pregnant & healthy|care|tips|advice", "For anything to do with pregnancy or periods, a doctor or midwife can give you advice that fits you."),
    ("eyes|eye & dry|tired|rub|itchy|sore|red", "Rest your eyes with regular breaks, blink often, and see a doctor or optician if they stay red, painful or your sight changes."),
    ("muscle|muscles|strength|strong|weights & build|gain|train|training|start", "Build strength gradually with bodyweight exercises or light weights, use good form, rest between sessions and eat enough protein."),
    ("run|running|jogging|jog|cardio|marathon|5k & start|begin|beginner|tips|train|training|how", "To start running, begin with a mix of short runs and walking, build up slowly, wear proper shoes and rest between sessions."),
    ("posture|yoga|pilates|flexibility|flexible", "Gentle stretching, yoga or pilates can improve flexibility and posture; go at your own pace and stop if anything hurts."),
    ("cramp|cramps|stitch", "For a muscle cramp, stop and gently stretch and massage the muscle, and drink some water; warming up helps prevent cramps."),
    ("hangover", "Drink water, rest, and eat something light; time is the main cure. Drinking less in the first place is the best prevention."),
    ("hiccup|hiccups", "Hiccups usually pass by themselves; breathing slowly or sipping water can help."),
    ("dizzy|dizziness|faint|fainting|light-headed|lightheaded", "If you feel dizzy, sit or lie down, and drink some water. See a doctor if it happens often or comes with other symptoms."),
    ("water|drinks|drink & plain|tap|safe|good|healthy|best", "Water is the best everyday drink; choose it over sugary drinks most of the time."),
    ("coffee|tea|caffeine & healthy|many|cups|bad|safe", "Moderate amounts of coffee or tea are fine for most people, but too much caffeine can affect sleep, so keep it to the morning and early afternoon."),
    ("break|breaks & work|working|desk|office|screen", "Take a short break from your desk every hour or so to stand, stretch and rest your eyes."),
    # ---------------- TRAVEL ----------------
    ("pack|packing|carry-on|carryon|carry|hand|luggage|bag|suitcase & short|trip|weekend|what|should|essentials|cabin|need|bring", "Pack a change of clothes, small containers of toiletries, your charger, and your travel documents."),
    ("pack|packing|suitcase|luggage & tips|better|smart|light|efficient|how|fit|space|rolling|roll", "Pack light by choosing versatile clothes that mix and match, rolling them to save space, and keeping heavy items near the wheels. Check your airline's baggage rules."),
    ("packing|pack|bring|list|checklist & holiday|vacation|trip|travel|beach|week", "Pack clothes for the weather, toiletries, chargers, a few essential medicines, and your documents, and keep valuables in your carry-on."),
    ("airport|flight|plane|airline & early|arrive|get|there|before|how|long|time|when", "Check your airline's advice, but arriving a couple of hours before an international flight is common."),
    ("airport|check|checkin|check-in|security|boarding & process|work|how|first|time|what|expect|tips", "Check in with your passport or ID, drop any hold luggage, go through security with liquids and electronics ready, then head to your gate in good time."),
    ("liquids|liquid|toiletries|shampoo|carry & airport|security|flight|plane|bag|allowed|rules", "Liquids in hand luggage are usually limited to small containers placed in a clear bag, but rules differ, so check with your airline and airport."),
    ("jet|lag|jetlag", "Shift your sleep schedule a little before you leave, drink water, and get daylight at your destination."),
    ("document|documents|passport|visa|id & need|abroad|overseas|travelling|traveling|international|required|bring|take", "You usually need a valid passport, and some countries also ask for a visa, so check the entry rules before you go."),
    ("passport & valid|expire|expiry|expires|validity|renew|months|how|check", "Many countries require your passport to be valid for some time beyond your trip, so check the expiry date and the destination's entry rules well before you go."),
    ("passport|lost|lose|stolen|stole|missing & what|do|abroad|replace|replacement|report", "If you lose your passport abroad, report it to the local police and contact your country's embassy or consulate for a replacement or emergency travel document."),
    ("visa|visas & need|apply|required|how|do|get", "Visa rules depend on your nationality and destination, so check the official government website of the country you are visiting well before you travel."),
    ("belongings|valuables|pickpocket|pickpockets|theft|thief|steal|stolen|bag|wallet|safe & crowd|crowded|keep|protect|safety|place|city|tourist", "Keep your bag closed and in front of you, and put valuables in an inside pocket."),
    ("safe|safety|secure|security & travel|travelling|traveling|abroad|solo|tips|stay|alone|tourist|city|night", "Stay safe by keeping valuables hidden, staying aware of your surroundings, sharing your plans with someone, and avoiding unlit, empty areas at night."),
    ("solo|alone|woman|female & travel|travelling|traveling|safe|tips|trip", "When travelling alone, share your itinerary with someone you trust, stay in well-reviewed places, keep in touch regularly and trust your instincts."),
    ("insurance & travel|trip|holiday|need|worth|should|get|medical", "Travel insurance can cover medical costs, cancellations and lost belongings, so it is worth considering and reading what it covers before you buy."),
    ("money|cash|currency|exchange|cards|card & abroad|overseas|travel|travelling|traveling|foreign|best|use|take|carry|bring|trip", "Carry a mix of a card and a little local cash, tell your bank you are travelling, and compare exchange rates and fees instead of changing money at the last moment."),
    ("atm|withdraw|withdrawal|fees|fee & abroad|overseas|travel|foreign|cash|card", "Cash machine and card fees abroad can add up, so check your bank's charges and withdraw larger amounts less often rather than many small ones."),
    ("tip|tips|tipping & abroad|country|restaurant|local|custom|travel", "Tipping customs differ between countries, so check local practice before you go and look at the bill to see whether service is already included."),
    ("language|translate|translation|speak|phrases|phrasebook|communicate|communication & abroad|foreign|travel|learn|trip|country", "Learn a few basic phrases such as hello, please, thank you and where is, and keep a translation app handy; locals usually appreciate the effort."),
    ("food|eat|eating|water|street & abroad|travel|safe|safely|stomach|sick|tummy|foreign|local|tips", "Eat at busy places where food is freshly cooked, wash your hands often, and check whether the tap water is safe to drink where you are."),
    ("book|booking|reserve|reservation|hotel|flight|flights|ticket|tickets|accommodation & cheap|cheaper|best|when|tips|how|early|deal|deals|save|saving", "Book early when you can, compare prices on a few sites, and be flexible with dates; check the cancellation terms before you pay."),
    ("hotel|accommodation|hostel|airbnb|stay & choose|pick|book|find|good|how|where|tips|location", "Check recent reviews, location, what is included and the cancellation terms, and choose somewhere close to transport links."),
    ("cancel|cancelled|canceled|cancellation|delayed|delay|flight & what|do|rights|help|airline|compensation", "If your flight is delayed or cancelled, speak to the airline staff or check its app for rebooking options, and keep your receipts and documents in case you can claim."),
    ("miss|missed|missing & flight|plane|connection|connecting", "If you miss a flight, go to the airline desk as soon as you can and ask about the next available flight."),
    ("lost|lose|missing|left|forgot|forgotten & luggage|baggage|suitcase|bag|airport|belongings", "If your luggage is lost, report it to the airline at the airport before you leave, get a reference number, and keep your receipts for essentials you have to buy."),
    ("lost|lose|missing|forgot|left|stolen|stole & phone|wallet|card|cards|bank|belongings|item|items|trip|abroad", "If something is lost or stolen, report it to the local police, cancel any bank cards straight away, and contact your insurer and embassy if needed."),
    ("copy|copies|backup|scan|photo & documents|passport|travel", "Keep copies of your passport and key documents, such as photos on your phone and a paper copy kept separately from the originals."),
    ("phone|mobile|sim|roaming|data|wifi|wi-fi|internet|esim & abroad|overseas|travel|travelling|traveling|use|foreign|cheap|trip|country", "Check your provider's roaming charges before you go; a local SIM or eSIM, or Wi-Fi, can be cheaper. Download maps and key information beforehand."),
    ("adapter|adaptor|plug|plugs|socket|sockets|voltage|charger & travel|abroad|need|country|travelling|traveling", "Plug sockets differ between countries, so bring a travel adapter and check that your chargers support the local voltage."),
    ("charger|battery|powerbank|power & travel|flight|airport|phone|long", "Charge your devices before travelling and carry a power bank in your hand luggage along with your chargers."),
    ("map|maps|navigate|navigation|directions|lost|getting|around & city|abroad|travel|offline|find", "Download offline maps before you go, note your hotel's address, and ask staff or the tourist office if you need directions."),
    ("transport|public|metro|bus|train|subway|taxi|rideshare & city|abroad|travel|get|around|use|how|tips|local", "Look up public transport options in advance, buy tickets from official machines or offices, and use licensed or well-known taxi services."),
    ("taxi|taxis|cab & safe|abroad|scam|ripoff|overcharge|airport", "Use official taxi ranks or well-known apps, agree the price or check the meter, and note the licence details if you feel uneasy."),
    ("scam|scams|tourist|ripoff|rip-off|overcharged|fraud & avoid|travel|abroad|tips|common|spot|protect", "To avoid tourist scams, be wary of unsolicited offers, agree prices beforehand, use official ticket sellers and never hand over your passport to strangers."),
    ("train|rail|railway|interrail & travel|ticket|tickets|book|tips|journey", "Check the timetable and booking rules in advance, since buying early can be cheaper, and keep your ticket handy and valid for the whole journey."),
    ("road|driving|drive|car|rental|rent|hire & abroad|trip|travel|abroad|tips|licence|license|foreign", "Check that your driving licence is accepted in the country, learn the local road rules, and read the insurance terms before renting a car."),
    ("itinerary|plan|planning|organise|organize & trip|travel|holiday|vacation|how|tips|first|schedule", "Pick your main sights, group them by area, leave free time, and book key tickets and transport ahead; do not overpack your days."),
    ("budget|cheap|cheaply|save|saving|afford & travel|travelling|traveling|trip|holiday|vacation", "Travel on a budget by being flexible with dates, booking early, staying outside the busiest areas, eating where locals eat and tracking your spending."),
    ("weather|season|climate|when|best & visit|time|travel|go|trip|destination|check", "Check the weather and busy seasons for your destination before you book, since the best time to go depends on what you want to do."),
    ("beach|swim|swimming|sea|ocean|sun & travel|trip|holiday|safe|safety|tips|pack", "At the beach, use sunscreen, drink water, swim where it is safe and supervised, and follow local flag and safety warnings."),
    ("hiking|hike|trek|trekking|walk|camp|camping|outdoors|mountain & trip|travel|tips|safe|safety|prepare|pack|beginner", "For hiking, tell someone your plan, wear proper shoes, carry water, food and a map, check the weather and turn back early if conditions change."),
    ("child|children|kid|kids|baby|family|toddler & travel|travelling|traveling|flight|trip|tips|plane|long", "When travelling with children, pack snacks, entertainment and a change of clothes, keep documents handy and allow extra time for everything."),
    ("pet|pets|dog|cat & travel|travelling|traveling|abroad|flight|trip|rules|need", "Rules for travelling with pets vary by country and airline, so check entry requirements, paperwork and carrier rules well in advance with your vet and airline."),
    ("health|medical|medicine|medicines|vaccine|vaccines|vaccination|vaccinations|doctor & travel|travelling|traveling|abroad|before|trip|holiday|need", "Before you go, check whether your destination recommends vaccines or health precautions, carry any regular medicines in their original packaging and see a doctor or travel clinic early."),
    ("customs|declare|border|immigration & airport|abroad|rules|what|forms|allowed|bring|carry|arrival", "At the border, have your passport and any entry forms ready, answer questions honestly, and check what you are allowed to bring into the country."),
    ("arrival|arrive|arrived|landing|landed & airport|first|what|do|new|country|tips|destination", "On arrival, follow signs for immigration, collect your bags, and have your accommodation address and a way to reach it ready."),
    ("long|haul & flight|flights|travel|comfortable|comfort|tips|survive|sleep|plane", "On a long flight, wear comfortable clothes, drink water, walk around and stretch now and then, and bring a neck pillow, headphones and snacks."),
    ("seat|seats|window|aisle & flight|plane|choose|pick|best", "An aisle seat makes it easier to stand and stretch, while a window seat is better for resting, so pick what suits you when you check in or book."),
    ("ears|ear|pop|pressure & flight|plane|landing|takeoff|take-off", "Swallowing, yawning or chewing gum during take-off and landing can help your ears with the pressure change."),
    ("fear|afraid|nervous|scared|anxious|anxiety|phobia & flying|fly|flight|plane|flights", "If you are nervous about flying, breathe slowly, bring something to distract you, and tell the cabin crew; learning how planes work can help too."),
    ("culture|customs|etiquette|respect|dress|dress-code|manners & travel|abroad|local|visit|country|tips|temple|religious", "Read up on local customs before you go, dress modestly where needed, and follow local etiquette such as removing shoes or covering shoulders at religious sites."),
    ("souvenir|souvenirs|gift|gifts|shopping|shop|bargain|haggle & travel|abroad|trip|tips|buy", "Buy souvenirs from reputable local sellers, check the price before you pay, and make sure you are allowed to take them through customs."),
    ("sightseeing|attractions|tourist|tour|tours|museum|museums & queue|queues|lines|avoid|crowd|crowds|tickets|skip", "Book tickets online ahead of time, go early in the day or outside peak season, and check opening hours to avoid long queues."),
    ("overpacking|overpack|baggage|luggage|weight|overweight|limit|allowance|fees|fee & airline|airport|flight|bag|suitcase|how|much|avoid", "Check your airline's baggage allowance before you travel, weigh your bag at home, and wear your bulkiest items to avoid extra fees."),
    ("lock|locks|padlock|luggage & suitcase|bag|safe|secure", "A small luggage lock or tag with your contact details helps keep your bag secure and easy to identify."),
    ("hostel|dorm|shared & stay|safe|tips|budget", "In a hostel, use the lockers for valuables, keep your things organised, and be considerate of others who may be sleeping."),
    ("tap|drinking|water & safe|abroad|travel|drink|bottle|bottled|country", "Tap water is not safe to drink everywhere, so check locally and use bottled or treated water where advised."),
    ("emergency|embassy|consulate|help|trouble|police & abroad|travel|travelling|traveling|need|contact|what|do", "In an emergency abroad, call the local emergency number and contact your embassy or consulate; keep their details and your insurer's number with you."),
    ("jetlag|jet-lag|time|zone|timezone & adjust|adapt|sleep|cope|new|recover|fast|travel|abroad", "To adjust to a new time zone, get daylight at your destination, eat and sleep on local time as soon as you can, and drink water."),
    ("carry|hand|cabin & bag|baggage|luggage|size|allowed|weight|limit|rules|dimensions", "Cabin bag size and weight limits differ by airline, so check yours before you travel."),
    ("restaurant|restaurants|eat|food|local|cuisine|dining & abroad|travel|find|where|choose|good|best|tips", "To find good local food, ask residents for suggestions, look for busy places with a local crowd, and check recent reviews."),
    ("vacation|holiday|holidays|trip|trips & first|time|abroad|plan|prepare|tips|checklist|before|go|leaving", "Before you leave, check your passport and entry rules, book your transport and accommodation, arrange money and insurance, pack, and share your plans with someone at home."),
    ("home|house|leave|leaving|away & trip|holiday|vacation|secure|safe|before|tips|lock|empty", "Before a trip, lock doors and windows, unplug unnecessary appliances, ask a neighbour to keep an eye on your home and avoid sharing your travel dates widely online."),
    ("photos|photo|camera|photography & travel|trip|tips|backup|safe|protect|memories", "Back up your photos regularly while you travel, either online or on a second device, and keep your camera or phone secure."),
    ("wifi|wi-fi|public|network|vpn|hotspot & safe|security|travel|abroad|airport|cafe|use|banking", "Avoid doing banking or entering passwords on public Wi-Fi; use your mobile data or a trusted secure connection instead."),
]

_WORD = re.compile(r"[a-z0-9\-']+")
_SYN = {
    "travelling": "travel", "traveling": "travel", "vacations": "vacation", "holidays": "holiday",
    "trips": "trip", "flights": "flight", "planes": "plane", "bags": "bag", "tablets": "tablet",
}


def _forms(tokens):
    out = set()
    for t in tokens:
        t = t.lower().strip("'-")
        out.add(t)
        if t.endswith("'s"):
            out.add(t[:-2])
        if len(t) > 3 and t.endswith("s"):
            out.add(t[:-1])
        if len(t) > 4 and t.endswith("es"):
            out.add(t[:-2])
        if len(t) > 5 and t.endswith("ing"):
            out.add(t[:-3])
            out.add(t[:-3] + "e")
        if len(t) > 4 and t.endswith("ed"):
            out.add(t[:-2])
            out.add(t[:-1])
        if t in _SYN:
            out.add(_SYN[t])
    return out


def _compile():
    rules = []
    for spec, answer in RULES:
        groups = [set(g.strip() for g in part.split("|")) for part in spec.split(" & ")]
        # Re-split: ' & ' separates groups. Keep only non-empty ones.
        groups = [g for g in groups if g]
        rules.append((groups, answer))
    return rules


_RULES = _compile()


def propose(ctx: "Context") -> Optional[Proposal]:
    seen = _forms(ctx.tokens)
    if not seen:
        return None
    best = None
    best_score = 0.0
    for groups, answer in _RULES:
        if not groups:
            continue
        # The first group is the topic and must match; the rest add support.
        if not (groups[0] & seen):
            continue
        support = sum(1 for g in groups[1:] if g & seen)
        topic_hits = 1
        # Rules with required context groups (3+ groups): need at least one support word.
        if len(groups) > 1 and support == 0:
            continue
        score = topic_hits + 2.0 * support + (0.5 if len(groups) > 2 and support == len(groups) - 1 else 0)
        if score > best_score:
            best_score, best = score, answer
    if best is None:
        return None
    return Proposal(best, min(0.85, 0.7 + 0.03 * best_score))
