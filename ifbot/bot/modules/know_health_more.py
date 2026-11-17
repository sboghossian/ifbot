"""More everyday wellbeing knowledge (round 2). Each rule: groups joined by ' & ' must ALL match;
words inside a group separated by '|' are alternatives (prefix match for words of 4+ letters).
General wellbeing only: no diagnosis, no medicines."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Optional

from ..arbiter import Proposal

if TYPE_CHECKING:  # pragma: no cover
    from ..engine import Context

D = " See a doctor if it is serious or does not get better."

RULES = [
    # ---- benefits of foods ----
    ("vegetable & good|healthy|benefit|why|important|eat", "Vegetables are good for you because they give you vitamins, minerals and fibre while being low in calories, so eat a variety every day."),
    ("fruit & good|healthy|benefit|why|important|eat", "Fruit is good for you because it provides vitamins, fibre and natural energy; eat a variety of fruit every day."),
    ("leafy|spinach|greens|broccoli & good|healthy|benefit|why|eat", "Leafy green vegetables are good for you because they are full of vitamins, minerals and fibre."),
    ("whole & grain|grains|wheat|bread|rice & good|healthy|benefit|why|better|white|eat|choose", "Whole grains are better than refined grains because they keep their fibre, which helps digestion and keeps you feeling full."),
    ("oat|oats|porridge|oatmeal & good|healthy|benefit|why|eat|breakfast", "Oats are a healthy breakfast because they are a whole grain with fibre that keeps you full for longer."),
    ("bean|beans|lentil|lentils|legume|legumes|chickpea|chickpeas & good|healthy|benefit|why|eat", "Beans and lentils are healthy because they provide protein and fibre and are filling and low in fat."),
    ("nut|nuts|almond|almonds|walnut|walnuts & good|healthy|benefit|why|eat", "Nuts are healthy in small handfuls because they provide protein, fibre and healthy fats, but they are high in calories so keep portions modest."),
    ("fish|salmon|seafood & good|healthy|benefit|why|eat|often|week", "Eating fish is good for you because it is a source of protein and healthy fats; try to include some fish in your weekly meals."),
    ("egg|eggs & good|healthy|benefit|why|eat|protein", "Eggs are a healthy food because they provide protein and vitamins; they suit most people as part of a balanced diet."),
    ("milk|dairy|cheese|yoghurt|yogurt|calcium & good|healthy|benefit|why|bones|need|important", "Dairy foods such as milk and yoghurt provide calcium and protein, which help keep your bones and teeth strong."),
    ("calcium & bones|bone|strong|why|important|need|sources", "Calcium helps keep your bones and teeth strong; good sources are dairy foods, leafy greens and fortified foods."),
    ("iron & why|important|need|food|foods|sources|tired|blood", "Iron helps your blood carry oxygen around your body; it is found in meat, beans, lentils and leafy greens. See a doctor if you think you lack it."),
    ("fat|fats & healthy|good|bad|why|need|eat|unsaturated", "Your body needs some fat, and unsaturated fats from fish, nuts and olive oil are healthier than too much saturated fat from fatty and fried foods."),
    ("fried|fry|fast|junk|processed & food|foods|eat|bad|unhealthy|why|often", "Fried, fast and processed foods are best kept occasional because they are often high in salt, sugar and fat and low in nutrients."),
    ("breakfast & why|important|skip|good|eat|benefit", "Breakfast gives you energy to start the day and can help you concentrate, so eat something balanced in the morning if you can."),
    ("fibre|fiber & why|important|need|good|benefit|eat", "Fibre is important because it helps digestion, keeps you feeling full and supports a healthy gut; get it from fruit, vegetables, beans and whole grains."),
    ("vitamin & c|d & why|important|need|good|benefit|get|sources", "Vitamin C supports your immune system and skin and comes from fruit and vegetables, while vitamin D supports your bones and comes mainly from sunlight and some foods."),
    ("sunlight|daylight|sun & good|healthy|benefit|why|need|outside|outdoors|vitamin", "A little sunlight helps your body make vitamin D and can lift your mood, but protect your skin from too much sun."),
    ("breakfast|lunch|dinner|meal|meals & regular|skip|skipping|why|important|time", "Regular meals help keep your energy steady, so try not to skip meals and eat at similar times each day."),
    ("portion|portions & size|control|why|important|big|eat|how|much", "Portion size matters because eating more than you need can lead to weight gain; use a smaller plate and eat slowly until you feel full."),
    ("slowly|chew|chewing & eat|eating|food|why|good|important|digestion", "Eating slowly and chewing your food well helps digestion and lets you notice when you are full."),
    ("water & before|with|during & meal|meals|food|eat", "Drinking water with meals is fine and helps digestion; water is the best drink to have alongside food."),
    ("water & good|why|important|benefit|body|drink", "Water is important because your body needs it to keep your temperature steady, move nutrients and keep your skin and organs working well."),
    ("fizzy|soda|energy|sugary|sweetened & drink|drinks|soft|cola|bad|why|unhealthy|avoid", "Sugary and fizzy drinks are not good for you because they add sugar without nutrients and can harm your teeth, so choose water most of the time."),
    ("wash & fruit|vegetables|vegetable|produce|salad & why|before|eat|should", "Wash fruit and vegetables before eating them to remove dirt and germs from the surface."),
    ("leftovers|leftover|reheat|reheating & safe|food|rice|how|chill|store|fridge", "Cool leftovers quickly, keep them in the fridge, eat them within a day or two and reheat them until they are steaming hot all the way through."),
    ("raw|undercooked & chicken|meat|egg|eggs|food|why|risk|bad", "Raw or undercooked meat and eggs can carry germs that cause food poisoning, so cook them thoroughly and keep raw meat away from other food."),
    ("vegetarian|vegan|plant|plant-based & healthy|diet|good|eat|protein", "A vegetarian or plant-based diet can be healthy if it is varied, with beans, lentils, nuts, grains, fruit and vegetables; a doctor or dietitian can advise on any nutrients you may miss."),
    ("diet|dieting|crash|fad & bad|healthy|work|why|avoid|good", "Crash and fad diets are not a healthy long-term way to manage weight; balanced meals, sensible portions and regular activity work better."),
    ("snack|snacking & between|meals|healthy|late|night|bad|why", "Healthy snacks between meals such as fruit, nuts or yoghurt can keep your energy up, but frequent sugary snacks can harm your health and teeth."),
    ("sweet|craving|cravings|chocolate|dessert & what|how|do|control|reduce|stop|healthy", "To handle sugar cravings, eat regular balanced meals, drink water, choose fruit when you want something sweet and keep sweets for occasional treats."),
    ("late|night|midnight & eating|eat|food|snack|dinner|bad|why", "Eating a large meal just before bed can disturb your sleep, so try to have dinner a few hours before bedtime."),
    # ---- exercise and being active ----
    ("exercise|physical|activity|active|workout & good|benefit|benefits|why|important|healthy|help", "Exercise is good for you because it strengthens your heart and muscles, boosts your mood and energy, helps you sleep and supports a healthy weight."),
    ("exercise|physical|activity|active|workout & mood|happy|stress|mental|feel", "Exercise improves your mood and eases stress because moving your body helps you feel more relaxed and energised."),
    ("exercise|physical|activity|active|workout & sleep", "Regular exercise helps you fall asleep more easily and sleep better, but try not to do hard exercise right before bed."),
    ("exercise|physical|activity|active|workout & heart", "Regular exercise strengthens your heart and helps keep your blood vessels healthy."),
    ("exercise|physical|activity|active|workout & bone|bones", "Weight-bearing exercise such as walking, running and strength training helps keep your bones strong."),
    ("exercise|physical|activity|active|workout & energy|tired", "Regular exercise can actually raise your energy levels over time, even though you may feel tired when you start."),
    ("exercise|active|activity|workout & busy|time|no|work|fit|schedule|excuse|daily|routine", "You can fit activity into a busy day with short bursts, such as a brisk walk, taking the stairs or a few minutes of stretching, since small amounts add up."),
    ("active|activity|move|moving|movement & more|day|daily|everyday|office|work|desk|how|can|stay", "To be more active during the day, walk or cycle when you can, take the stairs, stand up and move every hour and take short walking breaks."),
    ("stairs|stair|escalator|elevator|lift & why|good|take|healthy|benefit", "Taking the stairs is a simple way to be more active during the day, and it is good for your heart and legs."),
    ("sitting|sedentary|desk|sit & bad|why|risk|too|long|health|unhealthy", "Sitting for long periods is bad for your health because it slows circulation and strains your back, so stand up, stretch and walk around regularly."),
    ("stand|standing|walk|walking & break|hour|every|work|desk|office|meeting|why|often", "Standing up and walking for a few minutes every hour keeps your blood flowing, eases stiffness and helps you concentrate."),
    ("cycle|cycling|bike|biking|swim|swimming & good|healthy|benefit|why|exercise", "Cycling and swimming are good exercise because they work your heart and muscles and are gentle on your joints."),
    ("walk|walking & lunch|break|work|after|meal|dinner|short|day", "A short walk during the day or after a meal is a simple way to stay active, clear your head and give you more energy."),
    ("walk|walking & fast|brisk|pace|speed|how|quickly|intensity", "Brisk walking means a pace that raises your heart rate and breathing a little but still lets you talk."),
    ("strength|resistance|weights|muscle|muscles & training|exercise|why|important|good|benefit|older|age", "Strength exercise is important because it keeps your muscles and bones strong, supports your joints and helps you stay independent as you age."),
    ("exercise|workout|gym|training & motivated|motivation|lazy|laziness|stick|consistent|keep|going|routine|habit|bored", "To stay motivated, pick activities you enjoy, set small goals, schedule your exercise like an appointment and exercise with a friend."),
    ("exercise|workout|gym|run|running|training & morning|evening|night|best|time|when", "The best time to exercise is whenever you can do it regularly; pick a time that suits your routine and energy."),
    ("exercise|workout & eat|eating|food|before|after|meal|empty|stomach", "Have a light snack an hour or two before exercise if you need energy, and eat a balanced meal with some protein afterwards to help recovery."),
    ("exercise|workout|train|training & water|drink|hydrated|during|thirsty", "Drink water before, during and after exercise, especially when it is hot, to replace the fluid you lose when you sweat."),
    ("exercise|workout|training & cool|cooldown|cool-down|after|finish|end", "After exercise, cool down with a few minutes of slow movement and gentle stretching so your heart rate comes down gradually."),
    ("exercise|workout|training & injury|injured|prevent|avoid|safe|safely", "To avoid injury, warm up first, increase intensity gradually, use good form, wear proper shoes and rest when you feel pain."),
    ("exercise|workout|gym|train|training & sick|ill|cold|unwell|flu|fever", "If you have a mild cold you can do light activity if you feel up to it, but rest if you have a fever or feel very unwell, and return gradually."),
    ("pain|painful|hurt|hurts & exercise|workout|training|during|sharp", "Mild muscle soreness is normal, but sharp pain during exercise is a sign to stop and rest; see a doctor if it continues."),
    ("breathless|breathing|breath & exercise|workout|run|running|out|short", "Getting a little out of breath during exercise is normal, but slow down if you cannot speak or feel dizzy, and see a doctor if it worries you."),
    ("kid|kids|child|children & exercise|active|activity|play|outside|why|good|importance|important", "Active play is important for children because it builds strong bones and muscles, supports healthy growth and helps them sleep and concentrate."),
    ("older|elderly|senior|aging|ageing & exercise|active|activity|walk|why|good|important", "Staying active as you get older helps keep your muscles, balance and mood strong and supports independence; start gently and check with a doctor if you have concerns."),
    ("balance|falls|falling & older|elderly|exercise|prevent|improve|age", "Gentle exercise such as walking and balance practice helps prevent falls by keeping your legs and balance strong."),
    ("home|indoors|indoor|inside & exercise|workout|exercises|no|gym|without|equipment", "You can exercise at home with bodyweight moves such as squats, lunges, push-ups and planks, or by walking, dancing or following a video."),
    # ---- rest and recovery ----
    ("sick|ill|unwell|cold|flu & rest|sleep|bed|recover|recovery|why|important|better", "Rest is important when you are sick because your body uses its energy to fight the illness, so sleep, drink fluids and take things easy."),
    ("sick|ill|unwell|cold|flu & drink|fluids|water|why|should|plenty|help", "Drinking plenty of fluids when you are ill helps replace water lost through fever and sweating and keeps you from becoming dehydrated."),
    ("sick|ill|unwell|cold|flu|fever & eat|food|eating|appetite|what|should", "When you are ill, eat light, simple food when you feel able and keep drinking fluids; do not worry if your appetite is small for a day or two."),
    ("sick|ill|unwell|cold|flu & work|school|stay|home|go|back|return|when|should", "Stay home while you are unwell so you can recover and avoid spreading germs, and go back when you feel better and have no fever."),
    ("sick|ill|unwell|flu|fever|cold & how|long|recover|last|take|days|better", "Recovery time varies, but most common colds improve within a week or so; see a doctor if you are not improving or feel worse."),
    ("fever|temperature & what|do|reduce|lower|handle|help|child|high|when|doctor", "With a fever, rest, drink plenty of fluids and wear light clothing; see a doctor if the fever is high, lasts more than a few days or comes with other worrying symptoms."),
    ("sleep & why|important|need|good|benefit|enough|lack|not", "Sleep is important because it lets your body and brain rest and repair, and not getting enough can affect your mood, memory and health."),
    ("sleep|tired|rested|rest & more|how|can|improve|get|feel|better|well", "To feel more rested, keep a regular sleep schedule, get daylight and exercise in the day, limit caffeine late in the day and keep your bedroom dark, quiet and cool."),
    ("sleep|asleep|bed & fall|falling|cannot|cant|trouble|difficulty|quickly|faster|insomnia", "To fall asleep more easily, keep a regular bedtime, avoid screens and caffeine before bed, wind down with something calm and keep your room dark and cool."),
    ("wake|waking|awake & night|middle|early|keep|keeps|often", "If you wake in the night, stay calm, avoid looking at your phone, try slow breathing and go back to bed when you feel sleepy; see a doctor if it continues."),
    ("morning|wake|waking|rise|alarm & easier|energy|tired|how|get|up|early|routine|feel", "To wake up more easily, go to bed and get up at similar times, get daylight soon after waking and avoid screens late at night."),
    ("sleep & lack|deprived|enough|not|too|little|effects|happens|miss", "Too little sleep can leave you tired, irritable and unable to concentrate, and over time it can affect your health, so aim for regular, enough sleep."),
    ("bedroom|bed|mattress|pillow & sleep|better|good|environment|ideal|temperature|dark|quiet", "A good sleep environment is dark, quiet and cool, with a comfortable bed, so keep your bedroom free of bright light and noise."),
    ("break|breaks|pause|downtime|relax|relaxing & why|important|good|need|work|working|day|benefit", "Short breaks are important because they let your mind and body recover, which helps you stay focused and reduces stress and tiredness."),
    ("holiday|vacation|day|days & off|rest|why|important|burnout|good|need", "Time off is important because it lets you rest and recharge, which protects you from burnout and stress."),
    ("burnout|exhausted|overworked|overwork & prevent|avoid|what|do|signs|help|cope", "To avoid burnout, take regular breaks, set limits on work, sleep well, stay active and talk to someone you trust; speak to a doctor if you feel overwhelmed."),
    # ---- posture and body ----
    ("posture & good|why|important|bad|poor|improve|better|how|benefit", "Good posture is important because it reduces strain on your back, neck and shoulders; sit and stand tall, keep your shoulders relaxed and move regularly."),
    ("neck|shoulder|shoulders & pain|stiff|sore|ache|tension|relieve|ease|desk|work|phone", "To ease neck and shoulder tension, take breaks from your screen, check your posture, stretch gently and keep your screen at eye level. See a doctor if the pain continues."),
    ("phone|screen|laptop|computer|tablet|mobile & neck|posture|hold|looking|down|text", "Hold your phone up closer to eye level and take breaks, since looking down for long can strain your neck."),
    ("chair|desk|workstation|monitor & set|up|ergonomic|ergonomics|height|position|good|right|comfortable|work", "Set your chair so your feet are flat, your back is supported, your screen is at eye level and your arms are relaxed, and take regular movement breaks."),
    ("back & pain|ache|sore|hurt|prevent|avoid|help|ease|what|do|stop|relieve", "To prevent or ease back pain, stay active, avoid sitting for long periods, lift with your knees and keep good posture; see a doctor if it is severe or does not improve."),
    ("shoes|footwear|feet|foot & comfortable|good|support|wear|choose|why|important|pain|sore|healthy", "Wear comfortable, well-fitting shoes with good support because poor footwear can cause foot, knee and back pain."),
    # ---- stress and mind ----
    ("stress & why|bad|harm|effects|body|affect|health|happens|long|term", "Long-term stress is bad for you because it can affect your sleep, mood and body, so find ways to relax and ask for help when you need it."),
    ("stress|stressed|pressure|exam|exams|deadline|deadlines|work & cope|manage|handle|reduce|deal|how|relieve|tips", "To manage stress, break tasks into small steps, take breaks, move your body, get enough sleep, breathe slowly and talk to someone you trust."),
    ("relax|relaxed|calm|calmer|unwind|wind & how|can|be|more|feel|quickly|ways|help|evening", "To feel more relaxed, breathe slowly, take a walk, listen to calming music, stretch gently and set aside time each day for something you enjoy."),
    ("panic|anxious|anxiety|nervous|worried|worry & what|do|feel|attack|calm|help|cope|manage", "If you feel anxious, breathe in slowly through your nose and out gently, focus on what you can see and hear around you and talk to someone you trust. See a doctor if it is frequent."),
    ("overthink|overthinking|racing|thoughts|mind & stop|calm|quiet|how|help|sleep", "To calm racing thoughts, try slow breathing, write your worries down, go for a walk and keep a regular sleep routine."),
    ("friends|friend|social|company|connection|people|loneliness|lonely & health|good|why|important|wellbeing|benefit|mental", "Staying connected with friends and family is good for your wellbeing because it reduces loneliness and stress and supports your mood."),
    ("laugh|laughter|fun|hobby|hobbies|music|enjoy & health|good|why|important|wellbeing|benefit|relax|mood", "Laughing and doing things you enjoy are good for you because they lift your mood and help reduce stress."),
    ("gratitude|journal|journaling|diary|write|writing & health|good|why|benefit|wellbeing|mental|mood", "Writing down your thoughts or things you are grateful for can help you feel calmer and more positive."),
    ("talk|talking|ask|seek & help|therapist|counsellor|counselor|professional|mental|when|should|why", "Ask for help from a doctor or counsellor when low mood, worry or stress lasts for weeks or gets in the way of daily life; talking to someone is a sign of strength."),
    ("worry|stress|anxiety|screen|phone|news|social & media|scrolling|doomscrolling|news|too|much|limit|bad", "Spending too much time on social media or news can raise stress and worry, so set limits, take breaks and spend time offline."),
    ("self-care|selfcare|care & what|how|good|why|important|yourself|look", "Self-care means looking after your body and mind with enough sleep, healthy food, movement, rest and time for things you enjoy."),
    # ---- sun, heat, cold ----
    ("sun|sunlight|sunburn|sunscreen|uv|tan|tanning & why|important|use|wear|need|protect|should|bad|harm|skin", "Sun protection is important because too much sun can burn and damage your skin, so use sunscreen, wear a hat and seek shade, especially in the middle of the day."),
    ("sunscreen|sun & how|often|apply|reapply|use|put|when|much", "Put on sunscreen before going out, apply enough to cover all exposed skin and reapply regularly, especially after swimming or sweating."),
    ("sunburn|sunburnt|burnt & what|do|treat|help|ease|got|get|have|skin", "For sunburn, get out of the sun, cool your skin with cool water, drink plenty of fluids and apply a soothing moisturiser; see a doctor if it blisters badly or you feel unwell."),
    ("heat|hot|summer|heatwave & stroke|exhaustion|sick|dizzy|signs|symptoms|overheat|overheated|what|do", "If you are overheating, move to a cool place, rest, drink water and cool your skin with a damp cloth. Get urgent help if you feel confused, faint or stop sweating."),
    ("hot|heat|summer|heatwave & weather|day|days|stay|cool|how|keep|tips|sleep|home", "To stay cool in hot weather, drink plenty of water, stay in the shade, wear light loose clothing, keep your home shaded and avoid hard activity in the hottest hours."),
    ("cold|winter|freezing|chilly & weather|outside|keep|stay|warm|how|tips|dress|clothes|wear", "To keep warm in cold weather, wear several thin layers, a hat, gloves and a scarf, keep your feet dry and have warm food and drinks."),
    ("cold|winter|freezing & hypothermia|frostbite|danger|signs|risk|too|long|outside", "Staying out in the cold for too long can be dangerous, so cover up, keep dry and go inside to warm up if you start shivering badly or feel numb."),
    ("winter|dark|darker|gloomy|short & mood|blues|sad|low|tired|days|help|energy|cope", "In the darker winter months, get outside in daylight, stay active, keep a regular routine and talk to a doctor if your low mood lasts."),
    ("fresh|outdoor|outdoors & air|open|window|windows|ventilate|ventilation|indoor|indoors|why|good|healthy", "Fresh air is good for you; opening windows regularly improves the air indoors and spending time outside lifts your mood."),
    # ---- minor complaints ----
    ("headache|head & what|do|get|got|have|ease|relieve|help|stop|cure|treat|if|mild", "For a mild headache, rest in a quiet place, drink water, relax and avoid screens for a while. See a doctor if it is severe, sudden or keeps coming back."),
    ("headache|headaches & prevent|avoid|stop|often|frequent|why|cause|causes|reduce", "To avoid headaches, drink enough water, sleep regularly, eat regular meals, take screen breaks and manage stress; see a doctor if they are frequent."),
    ("cold|sniffle|sniffles|blocked|stuffy|runny|congestion & nose|what|do|ease|help|relieve|get|have", "For a blocked or runny nose, rest, drink fluids, breathe warm steamy air and use tissues, then wash your hands. See a doctor if it lasts more than a couple of weeks."),
    ("sore|throat|scratchy & what|do|ease|relieve|help|get|got|have|soothe|if", "For a sore throat, drink plenty of warm fluids, rest your voice and keep the air moist. See a doctor if it is severe or lasts more than a few days."),
    ("cough|coughing & what|do|ease|relieve|help|get|got|have|stop|if|soothe|night", "For a cough, rest, drink plenty of fluids and warm drinks and keep your head slightly raised at night. See a doctor if it lasts more than a few weeks or you have trouble breathing."),
    ("stomach|tummy|belly|nausea|nauseous|vomiting|diarrhoea|diarrhea|sick & what|do|get|got|have|ease|help|relieve|if|upset", "For an upset stomach, rest, sip water or other fluids often and eat plain food once you feel better. See a doctor if it is severe, lasts more than a couple of days or you cannot keep fluids down."),
    ("constipated|constipation|bowel|toilet & what|do|help|ease|relieve|get|have|if|more|fibre|fiber", "For constipation, eat more fibre such as fruit, vegetables and whole grains, drink plenty of water and be more active. See a doctor if it continues."),
    ("heartburn|indigestion|acid|reflux & what|do|help|ease|relieve|get|have|if|avoid|cause", "For indigestion or heartburn, eat smaller meals, eat slowly, avoid very spicy or fatty food late at night and avoid lying down right after eating. See a doctor if it keeps happening."),
    ("bloated|bloating|gas|wind|trapped & what|do|help|ease|relieve|get|have|if|why|avoid", "To ease bloating, eat slowly, avoid gulping air, have smaller meals and move around gently. See a doctor if it is frequent or painful."),
    ("dry|chapped|cracked|itchy|flaky & skin|lips|hands|what|do|help|ease|treat|prevent|moisturise|moisturize", "For dry skin or lips, use a gentle moisturiser or lip balm regularly, avoid very hot washing and drink water."),
    ("acne|spots|spot|pimple|pimples|breakout|breakouts & what|do|help|treat|prevent|reduce|skin|face", "For spots, wash your face gently twice a day, avoid squeezing them and keep hair and hands away from your face. See a doctor or pharmacist if they are severe."),
    ("rash|itchy|itch|itching|hives & what|do|help|ease|relieve|get|have|if|skin", "For a mild itchy rash, keep the skin cool and clean, avoid scratching and avoid anything that seems to trigger it. See a doctor if it spreads, blisters or comes with fever."),
    ("eye|eyes & dry|tired|strain|sore|red|screen|what|do|help|ease|relieve|prevent|computer", "To rest tired eyes, take regular screen breaks, look at something far away, blink often and make sure the room is well lit. See an optician if problems continue."),
    ("eye|eyes & something|foreign|dust|object|got|in|splash", "If you get something in your eye, do not rub it; rinse it gently with clean water and see a doctor if it is painful or your sight changes."),
    ("ear|ears & ache|pain|blocked|wax|what|do|help|ease|get|have|clean", "Do not push anything into your ear; see a doctor if you have ear pain, a blocked ear or hearing loss that does not clear up."),
    ("toothache|tooth|teeth|gum|gums & hurt|pain|ache|what|do|help|ease|bleeding|sensitive|get|have", "For tooth pain or bleeding gums, brush gently, avoid very hot, cold or sugary things and see a dentist soon."),
    ("muscle|muscles|sore|soreness|stiff|stiffness & after|what|do|help|ease|relieve|get|have|reduce", "For sore muscles, rest, move gently, stretch lightly, drink water and be patient, since soreness usually fades within a few days."),
    ("ankle|knee|joint|joints|wrist|twisted|sprain & what|do|help|first|get|have|treat|if|hurt", "For a minor sprain or sore joint, rest it, apply a cold pack wrapped in cloth, keep it raised and see a doctor if you cannot put weight on it or it is very swollen."),
    ("cut|scrape|graze|wound|bleeding & infection|infected|signs|clean|care|prevent|avoid|when", "Keep a cut clean and covered, and see a doctor if it becomes red, swollen, hot, very painful or leaks pus."),
    ("burn|scald & first|aid|what|do|treat|help|ease|get|got|have|kitchen|hot", "For a minor burn, cool it under cool running water for several minutes, do not use ice or butter and cover it loosely with a clean dressing. See a doctor for a large or deep burn."),
    ("bite|bites|sting|stings|mosquito|insect|bee|wasp & what|do|help|ease|relieve|get|got|have|itch|treat|if", "For an insect bite or sting, wash it with soap and water, apply a cold pack and avoid scratching. Get urgent help if you have trouble breathing or swelling of the face."),
    ("nose|nosebleed|nosebleeds & what|do|stop|help|get|have|how|bleeding|if", "For a nosebleed, sit up, lean slightly forward and pinch the soft part of your nose firmly for about ten minutes. See a doctor if it will not stop."),
    ("hiccup|hiccups & stop|cure|get|rid|how|what|do|help", "Hiccups usually pass by themselves; breathing slowly or sipping water can help."),
    ("dizzy|dizziness|faint|fainting|lightheaded|light-headed & what|do|feel|get|have|help|if|stand|standing", "If you feel dizzy or faint, sit or lie down straight away, drink some water and get up slowly. See a doctor if it keeps happening."),
    ("tired|tiredness|fatigue|exhausted|sluggish|drained & why|always|feel|feeling|constantly|all|time|cause|causes|reasons", "Common reasons for feeling tired include too little sleep, stress, poor diet, too little activity or not drinking enough water. See a doctor if you are tired all the time."),
    ("tired|tiredness|fatigue|exhausted|sluggish|energy & afternoon|slump|midday|after|lunch|work|what|do|help|beat|fight", "To beat an afternoon slump, drink water, take a short walk, get some daylight and eat a balanced lunch rather than a heavy or sugary one."),
    ("concentrate|concentration|focus|focusing|attention|distracted & why|cannot|cant|difficulty|trouble|improve|help|better|how|study|work", "To concentrate better, sleep well, take short breaks, drink water, reduce distractions such as your phone and work in focused blocks of time."),
    ("memory|remember|forget|forgetful|forgetting & improve|better|help|boost|how|why|tips", "To help your memory, get enough sleep, stay active, eat well, stay mentally active and use notes and routines to support you. See a doctor if you are worried."),
    ("cramp|cramps|stitch & what|do|help|ease|get|have|if|why|leg|night|run|running", "For a muscle cramp, stop, gently stretch and massage the muscle and drink some water; warming up and staying hydrated help prevent cramps."),
    # ---- habits ----
    ("habit|habits & healthy|good|build|form|start|how|new|stick|keep|make|develop|tips", "To build a healthy habit, start small, do it at the same time each day, link it to something you already do and be patient with yourself."),
    ("routine|habits|habit & daily|morning|day|healthy|good|stay|healthy|simple|tips|what", "Simple healthy daily habits include regular sleep, balanced meals, drinking water, moving your body, washing your hands and making time to relax."),
    ("healthy|health|wellbeing & stay|keep|being|live|living|lifestyle|how|tips|ways|simple|can|i", "To stay healthy, eat a balanced diet, move daily, sleep well, drink water, manage stress, avoid smoking and have regular check-ups."),
    ("smoking|smoke|cigarettes|cigarette|tobacco|vaping|vape & why|bad|harm|health|quit|stop|effects|risks|unhealthy", "Smoking is bad for your health because it damages your lungs and heart and raises the risk of serious illness; quitting is one of the best things you can do, and a doctor or pharmacist can help."),
    ("alcohol & why|bad|harm|health|effects|too|much|risks|limit|sleep", "Too much alcohol is bad for your health and can disturb your sleep, so keep to moderate amounts, have alcohol-free days and ask a doctor for personal advice."),
    ("check-up|checkup|checkups|check-ups|screening|screenings|doctor & why|regular|important|need|go|visit|often", "Regular check-ups are important because a doctor can spot problems early and give you advice, even when you feel well."),
    ("vaccine|vaccines|vaccination|vaccinations|immunisation|immunization|jab|jabs & why|important|need|good|benefit|get|protect|work|how", "Vaccines are important because they help your body protect itself against serious illnesses and help protect others around you; ask your doctor which are recommended for you."),
    ("hand|hands & wash|washing|clean|sanitiser|sanitizer|gel & why|important|when|should|how|often|good|germs", "Washing your hands is important because it removes germs and helps prevent infections; wash with soap and water before eating, after the toilet and after coughing or sneezing."),
    ("hygiene|clean|cleanliness & why|important|good|personal|daily|keep|how|tips", "Good personal hygiene is important because it helps stop germs spreading and keeps you healthy, so wash regularly, keep your hands, nails and teeth clean and wear clean clothes."),
    ("teeth|tooth|brush|brushing & why|important|twice|daily|good|dentist|need|visit", "Brushing your teeth twice a day is important because it removes plaque and helps prevent tooth decay and gum disease; visit the dentist regularly too."),
    ("urine|thirsty|dehydrated & enough|know|tell|signs|sign|water|drink", "A good sign that you are drinking enough is pale yellow urine; if it is dark, you feel thirsty, tired or have a dry mouth, drink more water."),
    ("water|drink|drinking & forget|remember|more|how|can|get|enough|habit|tips|make", "To drink more water, keep a bottle with you, sip regularly through the day, have a glass with each meal and use reminders if you forget."),
    ("weight|overweight|obese|obesity & why|bad|health|risk|important|healthy|affect", "Carrying a lot of extra weight can raise the risk of health problems, so balanced meals, regular activity and enough sleep help; a doctor can give personal advice."),
    ("weight|healthy|body & maintain|keep|stay|manage|how|control|lose|losing|safely|tips|slowly", "To manage your weight in a healthy way, eat balanced meals with sensible portions, be active every day, sleep well and make changes gradually."),
    ("posture|exercise|stretch|stretching & why|good|important|benefit|flexibility|daily|morning|how|often", "Stretching regularly is good for you because it eases stiffness and helps keep you flexible; stretch gently, hold each stretch and never bounce."),
    ("breathing|breathe|breath & why|deep|slow|good|helps|calm|benefit|important|how", "Slow deep breathing helps because it calms your nervous system and lowers stress; breathe in through your nose, then out slowly."),
    ("meditation|mindfulness|yoga & why|good|benefit|help|healthy|important|work|how|start|beginner", "Meditation and yoga are good for you because they help you relax, ease stress and improve focus; start with a few quiet minutes of slow breathing each day."),
    ("first|aid & kit|home|have|why|keep|need|what", "Keep a first aid kit at home with plasters, dressings, bandages, antiseptic wipes, scissors, tweezers and a thermometer so you can treat minor injuries quickly."),
]

_WORD = re.compile(r"[a-z0-9\-']+")
_SYN = {
    "tummy": "stomach", "belly": "stomach", "kids": "children", "kid": "child",
    "ill": "sick", "unwell": "sick", "cannot": "cant", "keeps": "keep",
}


def _norm(t):
    t = t.lower().strip("'-")
    return t[:-2] if t.endswith("'s") else t


def _compile():
    out = []
    for spec, answer in RULES:
        groups = []
        for part in spec.split(" & "):
            words = [w.strip() for w in part.split("|") if w.strip()]
            if words:
                groups.append(words)
        out.append((groups, answer))
    return out


_RULES = _compile()


def _hit(word, tokens):
    for t in tokens:
        if t == word:
            return True
        if len(word) >= 4 and t.startswith(word):
            return True
        if len(t) >= 4 and word.startswith(t) and len(word) - len(t) <= 2:
            return True
    return False


def propose(ctx: "Context") -> Optional[Proposal]:
    raw = getattr(ctx, "tokens", None)
    if raw is None:
        raw = _WORD.findall(str(getattr(ctx, "text", "")).lower())
    toks = {_norm(t) for t in raw}
    toks |= {_SYN[t] for t in list(toks) if t in _SYN}
    toks = {t for t in toks if t}
    if not toks:
        return None
    best = None
    best_score = 0.0
    for groups, answer in _RULES:
        # The first group is the topic and must match; of the rest, at least one must.
        if not _hit_any(groups[0], toks):
            continue
        support = sum(1 for g in groups[1:] if _hit_any(g, toks))
        if len(groups) > 1 and support == 0:
            continue
        score = 1.0 + 1.5 * support + 0.1 * len(groups)
        if score > best_score:
            best_score, best = score, answer
    if best is None:
        return None
    return Proposal(best, min(0.85, 0.76 + 0.025 * best_score))


def _hit_any(words, toks):
    return any(_hit(w, toks) for w in words)
