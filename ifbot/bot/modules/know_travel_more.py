"""More travel knowledge: planning, saving money, food, stays, language, lost items,
missed connections, transport, luggage, children, weather, staying in touch.

Each rule is (spec, answer). Groups are separated by ' & ' and ALL must match; words inside
a group are alternatives separated by '|'. The most specific rule (most groups) wins."""

from __future__ import annotations

import math
import re
from typing import TYPE_CHECKING, Optional

from ..arbiter import Proposal

if TYPE_CHECKING:  # pragma: no cover
    from ..engine import Context

# Words that mark a question as being about travel.
T = ("travel|trip|abroad|holiday|vacation|visit|visiting|journey|overseas|foreign|destination|"
     "tourist|tourism|flight|airport|hotel|another&country")
T = T.replace("another&country", "country")

RULES = [
    # ---------- planning and first trips ----------
    ("prepare|ready|before|plan|planning|first & visit|visiting|go|going|another|foreign|abroad|overseas & country|countries|abroad|overseas", "Before visiting another country, check your passport and entry rules, book your transport and accommodation, arrange money and insurance, and learn a few local customs and phrases."),
    ("choose|pick|decide|deciding|select|where & destination|place|go|holiday|vacation|trip|travel|visit", "To choose a destination, think about your budget, the season, how long you have and what you enjoy, then compare a few places and read recent traveller reviews."),
    ("first & time|trip|abroad|traveller|traveler|travel|travelling|flying|flight|overseas", "For a first trip, keep the plan simple: check your passport and entry rules, book your flights and accommodation early, pack light and keep copies of your documents."),
    ("plan|planning|organise|organize|prepare & road & trip|journey", "To plan a road trip, map your route and stops, check the car and your insurance, carry water and snacks, and book accommodation ahead for busy nights."),
    ("road & trip|journey|travel|drive|driving & car|prepare|check|before|pack|bring|need", "Before a road trip, check your tyres, fuel, oil and lights, carry a spare tyre or repair kit, water, snacks, a charger and a map, and plan rest stops."),
    ("backpack|backpacking|backpacker|rucksack & travel|trip|budget|first|tips|how|plan|start", "For backpacking, pack light, keep your documents and valuables secure, stay in budget places such as hostels, and keep your plans flexible."),
    ("group|friends|family & trip|travel|holiday|vacation|plan|planning|organise|organize|together", "To plan a group trip, agree the dates, budget and main activities early, choose a person to organise bookings, and keep a shared list of costs."),
    ("weekend|short|city & break|getaway|trip|escape & plan|planning|tips|how|make", "For a short city break, pick a compact area, book a hotel near transport, list a few must-see places and book popular tickets ahead."),
    ("cruise|cruises|ship & first|tips|prepare|pack|what|should|beginner|plan", "For a cruise, check your documents and the dress code, pack for the weather, book shore trips early and know when to be back on board."),
    ("camp|camping|tent & trip|travel|prepare|pack|beginner|first|tips|what|bring|site", "For a camping trip, check the site rules, bring a tent, sleeping bag, torch, food, water and a first aid kit, and leave the place clean."),
    ("ski|skiing|snowboard|snowboarding & trip|holiday|vacation|plan|prepare|first|beginner|tips|resort", "For a ski trip, book early, learn the basics or take a lesson, wear warm layers and sunscreen, and check weather and snow conditions."),
    ("business|work|conference & trip|travel|travelling|abroad|prepare|pack|tips", "For a business trip, keep your documents and schedule handy, pack smart clothes and chargers, confirm your meetings and keep receipts for expenses."),
    ("honeymoon|romantic|anniversary & trip|holiday|plan|destination|choose|tips", "For a honeymoon or romantic trip, choose a destination you both like, book early, keep your schedule relaxed and tell the hotel about the occasion."),
    ("staycation|local|nearby|home & holiday|trip|break|ideas|plan|save|cheap", "For a trip close to home, look for local sights, parks and events, book short stays nearby and save on travel costs."),
    ("checklist|list|todo|things & before|travelling|traveling|travel|trip|holiday|leave|abroad|going", "Before you travel, check your passport and entry rules, confirm bookings, arrange money and insurance, pack, charge devices and tell someone your plans."),
    ("first|beginner|newbie|tips|advice & solo|alone|myself|travel|travelling|traveling|trip", "For your first solo trip, pick a safe and easy destination, book your first nights ahead, share your plans with someone and keep in touch."),
    ("itinerary|schedule|plan & day|days|week|weeks|two|three|five|short|trip|city|visit", "Plan the days by grouping sights by area, leave time for rest and meals, book key tickets ahead and keep a spare plan for bad weather."),
    ("research|read|find & destination|country|before|visiting|trip|travel", "Research your destination by reading official tourism sites, recent reviews and travel guides, and check entry rules, local customs and safety advice."),
    ("travel & agent|agency|package|packages|tour|operator|company", "A travel agent or package holiday can save planning time and bundle flights and hotels, but compare the price and read what is included before you book."),
    ("package|all-inclusive|inclusive & holiday|vacation|deal|trip|worth|include", "On a package or all-inclusive holiday, check exactly what is included, such as flights, transfers, meals and drinks, and compare it with booking separately."),
    ("last-minute|lastminute|last & minute|deal|deals|cheap|book|booking|trip|holiday|flight", "For last-minute deals, stay flexible with dates and destination, compare several sites and check the cancellation terms before you pay."),

    # ---------- booking and saving money ----------
    ("save|saving|cheaper|cheap|cheaply|reduce|cut|lower & money|cost|costs|spending|expensive|budget & travel|travelling|traveling|trip|holiday|vacation|abroad|visit|visiting", "To save money when travelling, book early, travel outside peak season, stay slightly outside the centre, eat where locals eat, use public transport and track your spending."),
    ("save|saving|cheaper|cheap|cheaply|find|get|book & flight|flights|plane|airfare|airline|ticket|tickets", "To find cheap flights, compare several sites, be flexible with your dates and nearby airports, book early, and travel on quieter days."),
    ("when|best|time|early|late & book|booking|buy|buying & flight|flights|plane|ticket|tickets", "Book flights well ahead for the best choice, compare prices on a few sites, and watch for price alerts and the cancellation rules before you buy."),
    ("direct|nonstop|non-stop|connecting|layover|stopover|stop & flight|flights|better|cheaper|choose|worth", "A direct flight is quicker and avoids missed connections, while a connecting flight is often cheaper; leave enough time between flights if you connect."),
    ("layover|stopover|connection|transfer|connecting & long|short|enough|how|time|long|airport|flight", "Allow enough time between connecting flights to change terminals, clear security and reach the next gate, especially if you must collect and recheck bags."),
    ("save|saving|cheap|cheaper|reduce|cut|find|get & hotel|hotels|accommodation|lodging|stay|room|rooms|hostel", "To save money on accommodation, book early, compare sites, stay slightly outside the centre, choose a place with free breakfast or a kitchen and check the cancellation terms."),
    ("save|saving|cheap|cheaper|reduce|cut|eat|eating & food|meals|restaurant|restaurants|eating|dining & travel|travelling|traveling|trip|holiday|abroad|visiting", "To save money on food when travelling, eat where locals eat, have your main meal at lunch, try markets and street food from busy stalls and carry a refillable water bottle."),
    ("save|saving|cheap|cheaper|reduce|cut & transport|transportation|getting|around|taxi|taxis|bus|train|public & travel|trip|abroad|holiday|city|visiting", "To save money on transport, use public transport or walk, buy a day or multi-day pass if it is cheaper, and avoid taxis from airports and tourist spots."),
    ("free|inexpensive|low-cost & things|activities|attractions|sights|sightseeing|entertainment|do & city|visit|visiting|travel|trip|abroad|destination|holiday", "To find free or cheap things to do, ask the tourist office, look for free museum days, parks, markets, walking tours and local events."),
    ("exchange|convert|change & currency|money|cash|rate|rates|dollars|euros|pounds & travel|trip|abroad|overseas|visiting|foreign|airport|best|rate|rates|cheap", "For the best exchange rate, avoid changing money at the airport, compare rates and fees, and consider a card or cash machine with low charges."),
    ("avoid|reduce|stop|cut|lower & fees|fee|charges|charge & card|cards|bank|abroad|overseas|foreign|travel|travelling|traveling|trip|international", "To avoid card fees abroad, check your bank's foreign charges, consider a travel card with low fees, pay in the local currency and withdraw larger amounts less often."),
    ("pay|paying|payment|currency|local|dollars|euros & card|cards|cash|abroad|overseas|local|foreign|travel", "When paying abroad, choose the local currency instead of your home currency when the card machine asks, since this usually gives a better rate."),
    ("notify|tell|inform|call|warn & bank|card|cards|provider & travel|travelling|traveling|trip|abroad|going|overseas|holiday", "Tell your bank you are travelling so your card is not blocked, and carry a backup card and a little cash in case one stops working."),
    ("emergency|spare|backup|extra & cash|money|card|cards & travel|travelling|traveling|trip|abroad|holiday|overseas", "Carry a backup card and a small amount of emergency cash, and keep them in a different place from your main wallet."),
    ("daily|per|each|how & budget|spend|spending|cost|money|afford & travel|trip|holiday|abroad|visit|visiting|day", "To set a daily travel budget, add up your accommodation, food, transport and activities for the destination, include a little extra for surprises and track what you spend."),
    ("points|miles|rewards|loyalty|frequent & flyer|flying|travel|flight|airline|hotel|card|use|earn|collect|save", "Loyalty programmes can give points or miles towards flights and hotels, so join the free ones for airlines and hotels you use often and check when points expire."),
    ("deposit|prepay|prepaid|refundable|non-refundable|nonrefundable|refund & hotel|booking|flight|trip|travel|ticket|accommodation|cancel", "Check whether a booking is refundable before you pay, and choose a flexible rate if your plans might change."),
    ("review|reviews|rating|ratings|trust|trustworthy|reliable|fake & hotel|accommodation|booking|site|website|airbnb|restaurant|travel", "Read recent reviews from several sites, look for repeated comments about cleanliness, location and safety, and be careful with reviews that seem too perfect."),
    ("booking|reservation|confirmation|ticket|tickets|itinerary|boarding & print|paper|offline|phone|save|keep|store|copy|copies|digital|travel|trip|abroad", "Save your booking confirmations and tickets on your phone and keep a printed copy as backup, in case your battery dies or you have no signal."),
    ("boarding & pass|passes|pass|mobile|phone|print|digital|get|where|how|airport|flight", "You can usually get your boarding pass by checking in online or in the airline app, and you can show it on your phone or print it."),
    ("online|web|app|mobile & check-in|checkin|check & flight|airline|airport|how|when|open|opens|work|works", "Most airlines let you check in online or in their app shortly before the flight, which saves time at the airport; check your airline's own rules."),
    ("check-in|checkin|check & hotel|accommodation|arrive|arriving|late|early|time|times|out|checkout", "Hotels set their own check-in and check-out times, so tell the hotel if you will arrive late or early and ask whether you can leave your bags."),
    ("arrive|arriving|arrival|get|getting|reach|reaching & hotel|accommodation|late|night|midnight|after", "If you will arrive late at your hotel, tell them in advance so your room is held, and have the address and phone number ready for your taxi."),
    ("overbooked|overbooking|bumped|denied|boarding|refused & flight|plane|airline|seat|what|do|happens|ask", "If your flight is overbooked, speak to the airline staff straight away, ask about the next flight and any help or compensation, and keep your documents."),
    ("overbooked|full|problem|dirty|noisy|wrong|broken|complain|complaint & hotel|room|accommodation|booking|what|do|stay", "If there is a problem with your hotel room, tell the reception straight away and politely ask for a fix or another room, and keep your booking details and photos."),
    ("complain|complaint|refund|compensation|claim & airline|flight|hotel|travel|holiday|trip|how|make|write|company", "To make a travel complaint, contact the company in writing, explain what went wrong, say what you want, and keep your booking, receipts and photos as evidence."),
    ("insurance & claim|cover|covers|include|includes|what|lost|stolen|cancel|cancellation|medical", "Travel insurance usually covers things like medical costs, cancellations and lost bags, but read the policy for exclusions and keep receipts and reports for any claim."),
    ("weather|storm|strike|delay|cancel|cancelled|cancelled & trip|holiday|flight|travel|plans|rebook|change|insurance|what|do", "If your trip is disrupted, contact the airline or provider first about rebooking or a refund, and keep receipts and any written notices for your insurance claim."),

    # ---------- food ----------
    ("find|finding|choose|choosing|pick|locate|look|looking|where & good|best|nice|decent|authentic|local & restaurant|restaurants|food|eat|eating|cafe|cafes|meal|meals|dining|place|spot & travel|travelling|traveling|abroad|trip|city|town|visit|visiting|holiday", "To find a good place to eat when travelling, ask local people for suggestions, choose busy places with a local crowd, read recent reviews and avoid restaurants right beside major tourist sights."),
    ("avoid|spot|escape|stay & tourist & trap|traps|restaurant|restaurants|rip-off", "To avoid tourist traps, walk a few streets away from the main sights, check menus with prices, read recent reviews and choose places where locals eat."),
    ("vegetarian|vegan|halal|kosher|gluten|gluten-free|dietary|diet|allergy|allergies|allergic & travel|abroad|trip|restaurant|restaurants|country|visit|visiting|eat|eating|holiday|food", "With dietary needs abroad, learn the local words for your food restrictions, carry a card that explains them, check menus ahead and ask staff about ingredients."),
    ("street|market|markets|stall|stalls & food|eat|eating|safe|safely|travel|abroad|try", "To eat street food safely, choose busy stalls with fresh food cooked in front of you, avoid food that has been sitting out, and wash your hands first."),
    ("local|traditional|regional|authentic & food|dish|dishes|cuisine|specialty|speciality|try|taste|eat|travel|visit|visiting|abroad|trip", "To try local food, ask residents for their favourites, visit markets and small family-run places, and look for dishes the region is known for."),
    ("breakfast|snack|snacks|water|picnic & travel|trip|journey|train|flight|road|sightseeing|day|carry|bring", "Carry water and a few snacks when travelling, since food on the way can be expensive or hard to find."),
    ("book|reserve|reservation|table & restaurant|dinner|popular|busy|travel|trip|holiday|visiting|ahead", "Book a table ahead at popular restaurants, especially at weekends and peak season, and check opening hours and meal times in the country you are visiting."),

    # ---------- places to stay and things to do ----------
    ("find|finding|choose|choosing|pick|book|booking|look|looking|where & good|best|nice|safe|right|suitable & hotel|accommodation|place|stay|lodging|room|hostel|apartment|airbnb|sleep & stay|sleep|accommodation|hotel|hostel|accomodation|lodging|room|apartment|airbnb & travel|trip|city|visit|visiting|holiday|vacation|abroad|stay", "To find a good place to stay, check recent reviews, the location and distance to transport, what is included and the cancellation policy, and compare a few options."),
    ("neighbourhood|neighborhood|area|district|part|where & stay|hotel|accommodation|city|town|choose|pick|best|safe", "To choose where to stay in a city, pick an area close to public transport and the sights you want to see, check that it feels safe at night and read recent reviews."),
    ("hotel|apartment|airbnb|rental|hostel & difference|versus|vs|pros|cons|compare|comparison|better", "A hotel offers services and flexibility, an apartment gives more space and a kitchen, and a hostel is cheapest and social; choose what fits your budget and needs."),
    ("safe|safety|secure|keep|protect & hotel|room|accommodation|valuables|belongings|stay|safe", "In your hotel, use the room safe for valuables and your passport, lock the door and windows, and do not share your room number."),
    ("find|finding|discover|look|what|where & attractions|sights|activities|things|events & do|see|city|visit|visiting|travel|destination|trip|abroad|local|town", "To find things to do in a new place, check the tourist office and official tourism website, read recent reviews, ask locals and look for local events."),
    ("hidden|secret|local|offbeat|off-beaten|lesser & gems|spots|places|attractions|travel|city|find|discover|visit", "To find hidden gems, ask locals, walk away from the main tourist areas, visit local markets and neighbourhoods, and check local blogs and community recommendations."),
    ("tour|tours|guide|guides & guided|walking|private|group|find|good|worth|book|choose|best|city|travel|trip|hire|hiring|local", "A guided tour is a good way to learn about a place quickly; read reviews, check what is included and the group size, and book through a trusted provider."),
    ("day & trip|trips|excursion|excursions|outing|outings & plan|find|book|from|city|nearby|travel|visit|holiday", "For a day trip, check travel time and transport options, start early, book popular tickets ahead and plan your return so you do not get stranded."),
    ("city|attraction|museum|sights & pass|card|discount|discounts|worth|tourist", "A city pass can save money if you plan to visit many paid attractions, so add up the entry costs and compare before you buy."),
    ("museum|museums|gallery|galleries & free|discount|cheap|visit|visiting|tips|travel|trip|open|opening|hours|close|closed|day", "Check museum opening days and hours before you go, look for free or discounted entry times, and book popular exhibitions ahead."),
    ("photograph|photograph|photo|photos|picture|pictures & people|locals|permission|respect|ask|travel|abroad|etiquette|strangers", "Ask for permission before taking photos of people, respect places where photography is not allowed, and be polite if someone says no."),
    ("eco|eco-friendly|sustainable|sustainably|environment|environmental|green|responsible|ethical & travel|travelling|traveling|tourism|trip|holiday|visit|tips", "To travel more sustainably, choose trains over short flights when you can, stay in local and eco-friendly places, use less plastic, respect nature and support local businesses."),
    ("accessible|accessibility|wheelchair|disabled|disability|mobility & travel|travelling|traveling|trip|holiday|flight|hotel|airport|plan|tips|assistance|help", "If you need accessibility support when travelling, contact the airline, hotel and attractions ahead of time to arrange assistance and check that facilities suit your needs."),
    ("nightlife|night|evening & out|safe|safety|city|travel|abroad|tips|visiting|tourist", "When going out at night abroad, stay in groups, keep an eye on your drink, share your location with a friend and plan a safe way back to your accommodation."),

    ("prepare|ready|plan|before|get|survive & long|overnight|international|long-haul & flight|plane|flying|haul", "To prepare for a long flight, wear comfortable clothes, charge your devices, bring water, snacks, a neck pillow and entertainment, and stretch and walk around during the flight."),
    ("short|quick|limited|few|one|two|three|little|only & time|hours|days|day|weekend & city|town|place & see|visit|explore|sightsee|sightseeing|tour", "To see a city in a short time, pick a few main sights close to each other, book key tickets ahead, use a walking or hop-on bus tour and leave time for a meal."),
    ("credit|debit|card|cards & abroad|overseas|foreign|travel|travelling|country & use|using|pay|paying|work|accepted|safe|take", "You can usually use a credit or debit card abroad, but check your bank's foreign charges, tell your bank you are travelling and carry some cash as a backup."),
    ("miss|missed|missing & flight|plane|flights", "If you miss your flight, go to the airline desk or customer service straight away, explain what happened and ask about the next available flight; keep your documents and receipts."),
    ("train|bus|coach|ferry|boat|tram|rail & delayed|delay|cancelled|canceled|cancel|late|strike|late", "If your train, bus or ferry is delayed or cancelled, check the operator's app or station staff for the next departure, ask about refunds or rebooking and keep your ticket and receipts."),
    ("taxi|taxis|cab|cabs & overpay|overpaying|overcharge|overcharged|ripoff|rip-off|scam|scams|price|prices|fare|fares|cheat|cheated", "To avoid overpaying for taxis abroad, use official taxi ranks or a trusted app, agree the price or insist on the meter before you set off and check the usual fare from the airport."),
    ("luggage|bag|suitcase|bags & identify|spot|recognise|recognize|distinguish|stand|tag|label|mark|bright|easy|ribbon|strap", "To make your luggage easy to spot, add a bright strap or tag, put your name and contact details inside and outside the bag and take a photo of it."),
    ("cheap|cheapest|cheaper|budget|inexpensive|affordable & way|ways|transport|travel|between|cities|city|towns|journey & train|bus|coach|flight|car|between|cities|towns", "The cheapest way to travel between cities is often a coach or bus, or a train booked early; compare options and book ahead, since prices can rise close to departure."),
    ("deal|deals|offer|offers|discount|discounts|bargain|bargains|sale & holiday|holidays|vacation|trip|flight|hotel|travel|package|break", "To find the best travel deals, compare several websites, be flexible with dates and destinations, sign up for price alerts and check the cancellation terms before you book."),
    ("pack|packing|bring|take|wear & beach|swimming|swim|seaside|sunny|coast|pool", "For a beach holiday, pack swimwear, sunscreen, a hat, sunglasses, a towel, light clothes, sandals and a reusable water bottle."),
    ("healthy|health|well|fit|illness|ill & travel|travelling|traveling|trip|holiday|abroad|while|stay|staying|keep", "To stay healthy when travelling, wash your hands often, drink safe water, eat balanced meals, get enough sleep, stay active and carry any medicines you need."),
    ("insurance & travel|trip|holiday|abroad|get|buy|need|worth|choose|cover|medical|overseas", "To get travel insurance, compare policies from reputable providers, check what is covered such as medical costs, cancellations and lost bags, and buy it when you book your trip."),
    # ---------- language, customs, culture ----------
    ("learn|learning|study|practise|practice|pick|speak|improve & language|phrases|words|local|basic|basics & before|visiting|travel|travelling|traveling|trip|abroad|country|going|holiday", "To learn the local language before travelling, start with basic phrases such as hello, please, thank you and where is, use a language app and listen to audio, and keep a translation app handy."),
    ("translation|translate|translator|communicate|communication|understand|barrier & language|speak|abroad|travel|country|foreign|app|apps|when", "If you do not speak the language, use a translation app, learn a few key phrases, carry the address of your hotel written down and use gestures and a friendly smile."),
    ("useful|key|important|essential|basic|common|must & phrases|words|expressions & travel|abroad|learn|know|trip|country|foreign|language", "Useful travel phrases include hello, goodbye, please, thank you, excuse me, how much, where is and do you speak English."),
    ("etiquette|manners|polite|respectful|respect|rude|offend|offensive|behave|behaviour|behavior|customs & travel|abroad|local|visit|visiting|country|tourist|culture|trip|foreign", "To be polite abroad, read about local customs before you go, greet people politely, dress sensibly and copy what locals do."),
    ("dress|dressing|clothes|clothing|wear|wearing|attire & modestly|conservative|modest|temple|church|mosque|religious|culture|country|local|abroad|travel|visit", "Dress modestly in religious places and conservative countries by covering shoulders and knees, and check the local dress customs before you go."),
    ("greet|greeting|greetings|hello|handshake|bow|bowing|kiss & country|local|abroad|culture|travel|customs|people", "Greeting customs differ between countries, so watch what locals do, start with a polite hello in the local language and follow their lead."),
    ("culture|cultural|shock|homesick|homesickness|lonely & travel|abroad|trip|cope|deal|overcome|new|country|moving", "To cope with culture shock or homesickness, keep a routine, stay in touch with home, stay open to new things, get enough sleep and explore at your own pace."),
    ("meet|meeting|make|making|find|finding|friends|people & travel|travelling|traveling|abroad|solo|trip|hostel|locals|alone", "To meet people when travelling, stay in social places like hostels, join walking tours, classes or local events and be friendly and open."),
    ("local|public|religious|national & holiday|holidays|festival|festivals|event|events & travel|visit|visiting|trip|plan|country|check|closed|closures", "Check local holidays and festivals before you book, since shops and attractions may close and prices and crowds may go up."),
    ("bargain|haggle|haggling|negotiate|negotiating|market|markets|price & travel|abroad|shopping|souvenirs|how|tips|vendor|vendors", "When bargaining at a market, ask the price first, offer lower with a smile, stay polite, and be ready to walk away if the price is not right."),

    # ---------- lost, stolen, delayed ----------
    ("lose|lost|losing|misplace|misplaced|stolen|stole|missing & passport|passports", "If you lose your passport, report it to the local police and contact your embassy or consulate, and keep copies of your documents to speed up a replacement."),
    ("lose|lost|losing|misplace|misplaced|stolen|stole|missing|forgot & wallet|purse|credit|debit|card|cards", "If you lose your wallet or cards while travelling, cancel your bank cards straight away, report the theft to the police if stolen, and contact your bank for a replacement."),
    ("lose|lost|losing|misplace|misplaced|stolen|stole|missing & phone|mobile|smartphone|iphone|android", "If you lose your phone while travelling, try to locate or lock it with your tracking service, contact your provider to block the SIM and change your important passwords."),
    ("lose|lost|losing|misplace|misplaced|forgot|missing & ticket|tickets|boarding|pass|booking|reservation|confirmation", "If you lose your ticket or boarding pass, go to the airline or ticket desk with your ID and booking reference and ask for a replacement."),
    ("lose|lost|losing|misplace|misplaced|stolen|stole|missing & id|identity|licence|license|driving|document|documents", "If your ID or documents are lost or stolen abroad, report it to the police, get a written report, and contact your embassy and issuing authority for replacements."),
    ("lose|lost|losing|misplace|misplaced|locked|forgot|missing & key|keys|room|hotel|accommodation", "If you lose your hotel key, tell the reception straight away so they can issue a new one and make sure the old key does not work."),
    ("lose|lost|losing|misplace|misplaced|separated|missing & child|kid|kids|family|group|friend|friends & travel|crowd|airport|trip|abroad|holiday|city", "If you lose someone in a crowd, stay calm, go to a pre-agreed meeting point, ask staff or police for help and keep your phone on."),
    ("lose|lost|losing|get|getting|stuck|stranded & way|route|directions|navigate|streets|city|town|foreign|unfamiliar", "If you get lost in a foreign city, stay calm, check your offline map, ask a shop, hotel or police officer for directions and keep your hotel address handy."),
    ("miss|missed|missing & connecting|connection|connect|transfer|onward & flight|plane|flights|airport|layover", "If you miss a connecting flight, go straight to the airline desk or transfer desk, explain what happened and ask to be rebooked on the next flight."),
    ("miss|missed|missing & train|bus|coach|ferry|boat|ship|cruise", "If you miss a train, bus or ferry, ask the station or ticket desk about the next departure and whether your ticket is still valid or can be changed."),
    ("miss|missed|missing & tour|excursion|activity|reservation|booking|show|event|check-in|checkin", "If you miss a tour or booking, contact the provider as soon as possible to ask about rebooking or a refund, and keep your confirmation."),
    ("flight & delay|delayed|late|cancelled|canceled|cancellation & what|do|happens|compensation|help|rights|meals|hotel|stuck|stranded", "If your flight is delayed or cancelled, check with the airline about rebooking, meals and hotel help, and keep your receipts in case you can claim compensation."),
    ("luggage|baggage|bag|suitcase|bags & delayed|late|arrive|arrived|not|missing|lost|lose|loses|damaged|broken|belt|carousel|didnt|did|never", "If your luggage is delayed, lost or damaged, report it to the airline at the airport before you leave, get a reference number and keep receipts for essentials you buy."),
    ("luggage|baggage|bag|suitcase|bags & damaged|broken|torn|ripped|damage|wheel|handle|zip|zipper", "If your luggage is damaged, report it to the airline at the airport right away, take photos, keep your baggage tag and file a written claim."),
    ("avoid|prevent|stop|reduce|chance|risk & lost|losing|lose|missing|delayed & luggage|baggage|bag|suitcase|bags", "To avoid losing luggage, put a tag with your contact details inside and outside the bag, take a photo of it, keep valuables in your hand luggage and check your bag is labelled correctly."),
    ("stolen|theft|robbed|mugged|robbery|victim|steal & travel|abroad|holiday|trip|tourist|city|country|what|do|report|police", "If you are robbed while travelling, stay safe, report it to the local police for a written report, cancel your cards and contact your insurer and embassy."),
    ("sick|ill|unwell|injured|hurt|accident|illness|injury & travel|travelling|traveling|abroad|trip|overseas|holiday|country|foreign|visiting|hospital|doctor|what|do", "If you get sick or injured abroad, get medical help, call the local emergency number if serious, contact your insurer and keep all medical receipts."),
    ("medicine|medication|medicines|prescription|pills|tablets & travel|travelling|traveling|abroad|trip|flight|carry|pack|bring|take|airport|overseas", "Carry your medicines in their original packaging in your hand luggage, bring a copy of your prescription, and check that they are allowed in your destination."),
    ("motion|travel|sea|car|air & sickness|sick|nausea|nauseous|nausea", "For motion or travel sickness, sit where the movement is least, look at the horizon, get fresh air, avoid reading and heavy meals and ask a pharmacist about remedies."),
    ("altitude|mountain|high|height & sickness|sick|acclimatise|acclimatize|acclimatisation|acclimatization|trip|trek|travel|ascend|climb", "To avoid altitude sickness, climb gradually, rest, drink water and avoid alcohol; go down and get help if you feel seriously unwell."),
    ("diarrhoea|diarrhea|stomach|upset|food|poisoning|tummy|belly & travel|travelling|traveling|abroad|trip|holiday|avoid|prevent|overseas|foreign", "To avoid stomach problems when travelling, wash your hands often, eat freshly cooked food, drink safe water and avoid raw or undercooked food."),
    ("first|aid|medical & kit|travel|trip|pack|bring|carry|holiday|abroad", "A travel first aid kit should hold plasters, antiseptic wipes, pain relief, any regular medicines, insect repellent, sunscreen and rehydration salts."),
    ("sunscreen|insect|mosquito|repellent|bug|bugs & travel|trip|holiday|abroad|tropical|pack|bring|protect", "Pack sunscreen and insect repellent, wear light long sleeves in the evening and sleep under a net where recommended to protect yourself on tropical trips."),
    ("embassy|consulate|emergency|consular & contact|details|number|find|save|carry|know|abroad|travel|trip|country|overseas", "Before you go, save the phone number of your country's embassy or consulate and the local emergency number somewhere easy to find."),

    # ---------- transport on arrival ----------
    ("get|getting|go|going|travel|transfer|reach|from|to & airport & city|centre|center|hotel|town|downtown|accommodation|centre", "To get from the airport to the city or your hotel, check the train, metro, bus or shuttle options, use official taxis or well-known apps, and have your hotel address ready."),
    ("public|metro|subway|tube|underground|bus|tram|train & transport|transit|card|pass|ticket|tickets|fare|fares & buy|get|use|how|work|works|city|tourist|travel|visitors|abroad", "To use public transport in a new city, look up routes with a map app, buy tickets or a travel card from official machines or offices, and check whether a day pass is cheaper."),
    ("find|get|hail|book|use|order|call|safe|trustworthy & taxi|taxis|cab|cabs|uber|rideshare|ride|ride-hailing|lift & abroad|travel|city|country|visit|visiting|foreign|airport|tourist", "To get a safe taxi abroad, use official ranks or a well-known app, check the car and driver details, agree the price or insist on the meter and avoid unmarked cars."),
    ("rent|rental|hire|hiring|renting & car|vehicle|scooter|moped|bike|bicycle|motorbike|motorcycle & abroad|travel|trip|holiday|visit|visiting|country|tips|first", "When renting a car or bike abroad, check your licence is accepted, compare the insurance, inspect and photograph the vehicle before you drive off and learn the local road rules."),
    ("parking|park & car|rental|city|abroad|travel|trip|tips|find", "In a new city, look up parking options and rules in advance, use official car parks, and do not leave valuables visible in the car."),
    ("night|overnight|sleeper & train|bus|coach|travel|journey|tips|safe|sleep", "For an overnight train or bus, bring a warm layer, earplugs, a lock for valuables, a snack and water, and keep your documents and money close."),
    ("ferry|boat|ship & travel|trip|ticket|tickets|book|tips|cross|crossing|sea", "For a ferry trip, check the timetable and booking rules, arrive early with your ticket and ID, and check the weather as sailings can be delayed."),
    ("rail|train|interrail|eurail & pass|passes|worth|ticket|tickets|cheap|cheaper|best|buy|travel|europe|country|multi", "A rail pass can save money if you plan several long journeys, so compare it with single tickets, and check whether seat reservations cost extra."),
    ("luggage|baggage|bags|bag|suitcase & storage|store|locker|lockers|left|leave|checkout|check-out|hotel|station|between", "If you have time before your flight or train after checking out, ask your hotel to hold your bags or use luggage lockers at the station or airport."),
    ("walk|walking|bike|cycling|bicycle & city|travel|explore|exploring|sightseeing|abroad|visit|tips", "Walking or cycling is a great way to explore a new city, so wear comfortable shoes, carry water and a map and follow local traffic rules."),
    ("tourist|travel|visitor|sim|local & card|pass|ticket & transport|city|buy|where", "Tourist travel cards are usually sold at airports, stations and tourist offices; compare the price with single tickets before buying."),
    ("scooter|moped|motorbike|motorcycle & rent|ride|travel|abroad|safe|safety|tips|helmet|licence|license", "If you rent a scooter or motorbike abroad, check you hold the right licence and insurance, always wear a helmet and be extra careful on unfamiliar roads."),

    # ---------- luggage and packing ----------
    ("backpack|suitcase|bag|case|rucksack|luggage & choose|pick|buy|which|better|right|best & travel|trip|holiday|wheels|carry-on", "Choose a suitcase or backpack by trip length and how you will move around: a wheeled case suits airports and hotels while a backpack suits uneven ground and many stops."),
    ("pack|packing|fold|store|protect|carry & fragile|breakable|glass|bottles|souvenirs|gifts|delicate & luggage|suitcase|bag|travel|trip|home|safely", "To pack fragile items, wrap them in clothes or bubble wrap, place them in the middle of the suitcase away from the edges, and carry the most delicate things in your hand luggage."),
    ("pack|packing|prevent|stop|avoid|carry|take & toiletries|shampoo|liquids|bottles|leak|leaking|spill|spilling & suitcase|luggage|bag|travel|flight", "To stop toiletries leaking, use travel-sized containers, seal them in a zip bag and keep them in a separate pocket or in your hand luggage."),
    ("pack|packing|fold|roll|prevent|stop|avoid & clothes|clothing|shirts|suits|suit|dress|wrinkles|creases|crease|crumpled|wrinkle|ironing", "To keep clothes from wrinkling in a suitcase, roll casual items, fold formal items flat or around tissue paper and hang them up as soon as you arrive."),
    ("pack|packing|fit|put|carry & shoes|shoe|boots|sandals|trainers", "When packing shoes, wear the bulkiest pair on the plane, put the others in bags at the edge of the suitcase and use the space inside them for small items."),
    ("pack|packing|bring|take|need & winter|cold|snow|snowy|freezing|chilly & trip|travel|holiday|clothes|weather|destination|visit", "For a cold-weather trip, pack warm layers, a waterproof coat, hat, gloves, scarf and sturdy shoes, since layers are easier to adjust than one thick coat."),
    ("pack|packing|bring|take|need|wear & hot|summer|tropical|warm|sunny|heat & trip|travel|holiday|clothes|weather|destination|visit", "For hot weather, pack light, breathable clothes, a hat, sunglasses, sunscreen and comfortable shoes, and carry a water bottle."),
    ("pack|packing|bring|take|need & rain|rainy|wet|monsoon|showers|umbrella & trip|travel|holiday|clothes|weather|destination|visit", "For a rainy destination, pack a waterproof jacket, a small umbrella, quick-drying clothes, shoes that can get wet and a waterproof cover for your bag."),
    ("pack|packing|bring|take|need & business|formal|work|meeting|suit & trip|travel|clothes|abroad|carry-on", "For a business trip, pack a few formal outfits that mix and match, wrinkle-resistant clothes, comfortable shoes and your chargers and documents in your hand luggage."),
    ("packing & cubes|organiser|organizer|organise|organize|organized|organised|tips|how|suitcase", "Packing cubes or zip bags help keep your suitcase organised, and putting heavy items near the wheels helps it stay balanced."),
    ("what|which|never|not|shouldn't|should|avoid & pack|packing|bring|take|carry & travel|trip|holiday|flight|abroad|luggage|suitcase|bag", "Avoid packing too much, valuables in checked luggage and anything banned by your airline or destination; keep documents, medicines, money and electronics in your hand luggage."),
    ("check|checked|hold|cabin|carry-on|carry & luggage|baggage|bag|bags|suitcase & difference|which|better|choose|or|versus|vs|should", "Cabin bags stay with you and avoid waiting at the carousel, while checked bags give more space; keep valuables, medicines and documents in your cabin bag."),
    ("packing|pack|pack & last|minute|quick|quickly|fast|late|hurry & trip|travel|holiday|how", "For quick packing, use a checklist, choose a few mix-and-match outfits, pack essentials like documents, chargers and medicines first and add the rest."),
    ("daypack|daybag|day & sightseeing|sightsee|tour|explore|exploring", "For a day of sightseeing, carry water, a charger, sunscreen, a small snack, a copy of your ID and a bag you can keep closed in front of you."),
    ("airline|flight|plane|airport & lost|baggage|luggage|tag|label|tags|identify|identify|suitcase & mark|identify|stand|recognise|recognize|distinguish", "Make your bag easy to identify with a bright strap or tag, and put your name and contact details inside and outside it."),

    # ---------- documents ----------
    ("keep|store|protect|secure|hide|carry|safe|safely|safekeeping & passport|documents|document|id|papers|cash|valuables & travel|travelling|traveling|abroad|trip|hotel|holiday|city", "Keep your passport and valuables in the hotel safe or a secure inside pocket, carry only what you need for the day and keep copies of your documents."),
    ("scan|copy|photo|photograph|digital|cloud|email|backup & passport|documents|document|id|tickets|booking & travel|abroad|trip|keep|save", "Take photos or scans of your passport, visa, tickets and insurance and save them to your email or cloud storage as well as keeping a paper copy."),
    ("renew|renewal|apply|applying|get|obtain|new|expired & passport|passports", "To get or renew a passport, apply through your government's official passport service well before your trip, since processing can take weeks."),
    ("entry|entry|requirements|rules|restrictions|allowed|admitted & country|destination|abroad|travel|visit|visiting|check|where|how|find|before", "To check entry requirements, use your government's official travel advice and the destination country's official website, and do this well before you book."),
    ("travel & advice|advisory|warning|warnings|alert|alerts|safe|safety & country|destination|abroad|check|government|official|where|how|find|before", "To check whether a country is safe to visit, read your government's official travel advice and any local news before you book and again before you leave."),
    ("declare|declaration|customs|import|bring|take|carry & food|gifts|goods|items|alcohol|cash|money|souvenirs|plants & through|into|across|border|airport|country|abroad|travel", "Check the customs rules of the country you are entering or leaving before you pack food, plants, gifts or large amounts of cash, and declare what is required."),
    ("immigration|border|passport & control|queue|line|questions|ask|asked|answer|what|expect|officer", "At immigration, have your passport, return ticket and address of your accommodation ready, answer the officer's questions politely and honestly and keep forms handy."),
    ("return|onward|ticket|proof & travel|entry|enter|country|need|required|asked|airport|abroad|flight", "Some countries ask for a return or onward ticket and proof of accommodation at the border, so check the entry rules and keep these documents handy."),

    # ---------- children, family ----------
    ("child|children|kid|kids|toddler|toddlers & flight|flying|plane|fly|airplane|airport|long|travel|entertain|entertaining|keep|calm|busy|bored", "To keep children happy on a flight, pack snacks, small toys, books, headphones and a tablet with downloaded shows, and let them move around when it is safe."),
    ("baby|babies|infant|newborn & flight|flying|plane|fly|airplane|travel|travelling|traveling|trip|pack|tips|bring|need", "When flying with a baby, bring nappies, wipes, spare clothes, feeding supplies and a comfort item, check your airline's rules for infants and feed during take-off and landing to help their ears."),
    ("car|child|kids|toddler|baby & seat|seats|safety|travel|rental|abroad|trip|taxi|car", "Children usually need an appropriate car seat or booster, so check local rules, ask the car rental company to provide one or bring your own."),
    ("pushchair|stroller|pram|buggy|carrier|sling & travel|flight|airport|trip|holiday|bring|take|pack|use|airline", "A lightweight stroller or baby carrier makes travel easier, and many airlines let you take a stroller to the gate; check your airline's rules."),
    ("teen|teens|teenager|teenagers|older & kids|children|family & travel|trip|holiday|vacation|plan|tips|involve|activities", "On a family trip with teenagers, let them help plan some activities, allow some free time and keep a balance between sightseeing and relaxing."),
    ("kids|children|child|family & trip|holiday|vacation|destination|travel|activities|plan|planning|choose|best|friendly|tips|ideas|things|visit|visiting", "On a family trip, choose child-friendly places, keep the schedule relaxed with breaks, pack snacks and entertainment and book family rooms or apartments."),
    ("kids|children|child|family & consent|letter|permission|documents|passport|travel|alone|one|parent|abroad", "When travelling abroad with children, bring their passports and check whether you need extra documents such as a letter of permission, especially if only one parent travels."),
    ("kids|children|child & lost|safe|safety|keep|track|crowd|airport|abroad|trip|holiday|travel|busy|stay|together", "To keep children safe in crowds, agree on a meeting point, give them a card with your phone number, dress them in bright clothes and hold hands in busy places."),
    ("kids|children|child|baby & jet|lag|time|zone|adjust|sleep|travel|trip|flight|long", "To help children with jet lag, shift bedtimes gradually, get daylight at your destination and keep meal and sleep times regular."),

    # ---------- weather and seasons ----------
    ("best|good|right|ideal|when|time & time|season|month|months|period & visit|go|travel|travelling|traveling|trip|destination|holiday|vacation|weather", "The best time to visit depends on the weather and crowds you want to avoid, so check the climate and busy seasons for your destination before you book."),
    ("avoid|escape|beat|skip|fewer|less|crowd|crowds|crowded|busy|peak|tourists|quiet|quieter & travel|visit|visiting|trip|destination|season|city|attraction|attractions|holiday|sights", "To avoid crowds when travelling, visit outside peak season, go early in the morning or late afternoon, book tickets in advance and try less famous places."),
    ("shoulder|off|low|peak|high|season|seasons & travel|trip|holiday|cheap|cheaper|visit|good|worth|time|mean|means|what", "Travelling in the off-season or shoulder season often means lower prices and fewer crowds, but check the weather and whether attractions and services are open."),
    ("weather|forecast|climate|temperature & check|know|find|look|before|trip|travel|destination|visit|pack", "Check the weather forecast for your destination before you travel and again just before you pack, so you can bring the right clothes."),
    ("rainy|monsoon|wet|hurricane|cyclone|typhoon|storm|storms|season & travel|trip|visit|visiting|holiday|go|should|safe|avoid|plan", "Before travelling in a rainy or storm season, check the forecast and local advice, have flexible bookings and insurance and plan indoor options."),
    ("winter|cold|snow & travel|trip|holiday|drive|driving|road|journey|prepare|safe", "For winter travel, check the weather and road or flight conditions, allow extra time, dress in warm layers and carry water and a charger."),
    ("heat|hot|summer|sun & travel|trip|holiday|sightseeing|visit|visiting|stay|cool|beat|cope|tips|city", "In hot weather, plan sightseeing for the morning and evening, rest indoors at midday, drink water often and wear a hat, sunscreen and light clothing."),
    ("hurricane|earthquake|flood|disaster|storm|emergency|volcano & travel|travelling|traveling|abroad|trip|tourist|what|do|prepare|safe|holiday", "In a natural disaster while travelling, follow local authorities' instructions, contact your embassy and family, keep your phone charged and your documents with you."),

    # ---------- staying in touch ----------
    ("stay|staying|keep|keeping|get|call|calling|contact|contacting|phone|message|messaging|talk & touch|home|family|friends|connected|abroad|travel|travelling|traveling|trip|overseas", "To stay in touch with home when travelling, use free messaging and video call apps over Wi-Fi, and agree a regular time to check in with family."),
    ("call|calling|phone|ring|dial & home|family|abroad|overseas|international|cheap|cheaper|free|travel|from", "To call home cheaply from abroad, use a messaging or video call app over Wi-Fi or data, since international phone calls can be expensive."),
    ("sim|esim|e-sim|data|plan|plans|phone|mobile|roaming|bills|bill|internet|cell & travel|abroad|overseas|trip|country|holiday|buy|get|local|visit|visiting|how|best|tourist", "For data abroad, buy a local SIM or an eSIM data plan, or check your provider's roaming bundles, and make sure your phone is unlocked."),
    ("wifi|wi-fi|internet|online|signal|connected|data & hotel|abroad|travel|trip|find|get|stay|free|country|airport", "To get internet while travelling, look for free Wi-Fi in hotels, cafes and airports, but use mobile data or a trusted secure connection for banking and passwords."),
    ("share|sharing|tell|inform|send & location|itinerary|plans|whereabouts|plan & family|friends|someone|home|safe|safety|trip|travel|abroad|solo|alone", "Share your itinerary and your live location with a trusted friend or family member and check in regularly so someone knows where you are."),
    ("phone|battery|power|charge|charging|powerbank|charger & travel|trip|day|out|sightseeing|dies|dead|run|running", "Carry a power bank and charge your phone before you go out, and lower the screen brightness to save battery when sightseeing."),
    ("app|apps|useful|best|essential|download|helpful & travel|travelling|traveling|trip|abroad|holiday|phone|before|need|recommend|smartphone|tourist", "Useful travel apps include offline maps, a translation app, your airline and hotel apps, a currency converter and a transport app for your destination."),
    ("offline|download|downloaded & map|maps|translation|guide|guides|travel|abroad|trip|city|signal|data|use|app", "Download offline maps, translations and your bookings before you leave so you can use them without a signal or data."),
    ("work|working|remote|laptop & travel|abroad|trip|travelling|traveling|while|digital|nomad|holiday|connect|wifi", "To work remotely while travelling, check your Wi-Fi and time zone ahead, carry a charger and adapter, back up your files and keep your laptop secure."),

    # ---------- safety ----------
    ("safe|safety|secure|protect|avoid|danger|dangerous|crime|trouble|risk & woman|women|female|girl|girls|lone|alone|solo|myself & travel|travelling|traveling|abroad|trip|alone|solo|night|city", "To stay safe when travelling alone, share your plans, stay in well-reviewed places, avoid empty areas at night, trust your instincts and keep your phone charged."),
    ("safe|safety|secure|protect & atm|cash|money|machine|machines|withdraw|withdrawing & abroad|travel|trip|city|foreign|tips|use|using", "To use cash machines safely abroad, use ones inside banks or well-lit busy places, cover the keypad, check for anything unusual on the machine and take your card and cash straight away."),
    ("safe|safety|secure|protect|avoid & pickpocket|pickpockets|pickpocketing|thief|thieves|theft|bag|wallet|phone & abroad|travel|trip|tourist|city|crowd|crowds|busy|tips", "To avoid pickpockets, keep your bag closed and in front of you, use inside pockets, be extra careful in crowds and on public transport and do not display valuables."),
    ("safe|safety|secure|protect & rental|hire|hired|car|vehicle & abroad|travel|trip|tips|driving|visit", "In a rental car abroad, lock the doors, keep valuables out of sight, park in well-lit places and keep the rental company's contact number with you."),
    ("local|emergency & number|numbers|call|dial|know|find|police|ambulance|fire|help & abroad|travel|trip|country|overseas|foreign|visit|visiting", "Emergency numbers vary by country, so look up the local emergency number for your destination before you go and save it in your phone."),
    ("safe|safety|trustworthy|reliable|legitimate|legit|fake|scam & booking|accommodation|website|site|rental|apartment|tickets|listing|travel|online|how", "To avoid fake travel bookings, use well-known sites, read recent reviews, never pay outside the booking platform or by bank transfer to strangers and be wary of prices that seem too good."),
    ("drink|drinks|spiked|alcohol|bar|bars|party|clubs & safe|safety|abroad|travel|trip|tourist|tips|watch|city", "When drinking out abroad, watch your drink, stay with friends, know your limits and have a safe plan for getting back to your accommodation."),
    ("safe|safety|swim|swimming|water|sea|beach|ocean|surf|waves & abroad|travel|trip|holiday|tips|tourist|visiting|rip|current", "When swimming abroad, swim at beaches with lifeguards, follow flag and warning signs, never swim alone or after drinking alcohol and ask locals about currents."),

    # ---------- return and misc ----------
    ("return|returning|coming|come|after|back & home|trip|travel|travelling|traveling|holiday|abroad|jet|lag|adjust|cope|tips", "After a trip, give yourself a day or two to rest, unpack and get back into your normal sleep schedule, and spend some time outdoors in daylight."),
    ("bring|take|carry|buy|transport|get & gifts|souvenirs|presents|duty-free|duty|free|shopping|home & travel|flight|airport|abroad|trip|customs", "Check your airline's and your home country's rules on what you can carry home before you buy gifts or duty-free items, and keep your receipts."),
    ("tax|refund|vat & shopping|tourist|travel|abroad|claim|get|how|purchases", "Some countries refund sales tax to visitors on purchases, so ask the shop for the paperwork, keep your receipts and check the airport refund process before you leave."),
    ("tips|advice|ideas|hacks|tricks|secrets|rules & travel|travelling|traveling|trip|holiday|abroad|better|smarter|easier|beginner", "General travel tips: pack light, keep copies of your documents, tell your bank, carry a power bank, learn a few local phrases and stay flexible."),
    ("mistakes|mistake|avoid|common|wrong|regret|worst & travel|travelling|traveling|trip|holiday|abroad|first|tourist|tourists|beginners", "Common travel mistakes include overpacking, overscheduling, not checking passport validity and entry rules, not having travel insurance and not keeping copies of your documents."),
    ("pet|pets|dog|dogs|cat|cats & hotel|accommodation|stay|travel|friendly|find|book|trip|holiday|where", "To find pet-friendly places to stay, search for pet-friendly filters on booking sites, confirm the pet policy and any fees with the hotel before you book and check the local rules."),
    ("overweight|extra|baggage|excess|fees & luggage|bag|suitcase|pay|airport|how|avoid|cost", "To avoid overweight baggage fees, weigh your bag at home, check your airline's allowance, wear your bulkiest items and move heavy things to your cabin bag if allowed."),
    ("jet|lag & prevent|avoid|reduce|beat|fight|cope|minimise|minimize|cure|help|tips|flying|flight|travel|trip", "To reduce jet lag, shift your sleep schedule a little before you leave, drink water, avoid too much alcohol and caffeine, and get daylight at your destination."),
    ("sleep|sleeping|rest|nap & plane|flight|flying|long|night|travel|airport|train|overnight|how|better|tips", "To sleep on a flight, bring a neck pillow, eye mask and earplugs, wear comfortable clothes, avoid caffeine and heavy meals and choose a seat where you can rest."),
    ("airport|airports & time|kill|wait|waiting|bored|boredom|layover|long|stopover|do|what|spend|spending", "During a long wait at the airport, find a quiet seat near a charging point, explore the terminal, walk around, read or download shows, and check if there are lounges you can use."),
    ("red-eye|redeye|overnight & flight|flights|plane & booking|book|choose|cheap|cheaper", "Early morning flights tend to be less delayed and quieter, while late flights can save a hotel night; choose by how you will get to the airport."),
    ("airport|security & faster|quicker|speed|skip|avoid|queue|queues|line|lines|get|through|tips|go|clear|ready", "To get through airport security faster, have your documents ready, put liquids and electronics where they are easy to take out, wear slip-on shoes and arrive early."),
    ("seat|seats|choose|pick|reserve|select|select & flight|plane|airline|book|booking|extra|legroom|exit|free", "You can usually choose your seat when you book or check in; extra legroom or exit row seats may cost more, and an aisle seat makes it easier to stretch."),
    ("food|meal|meals|special|vegetarian|vegan|halal|kosher|allergy|dietary & flight|plane|airline|order|request|book|inflight|in-flight", "To request a special meal on a flight, order it when you book or contact the airline at least a day or two before departure, and bring snacks as a backup."),
    ("water|bottle|drink|refill|hydrate & flight|plane|airport|airline|security|empty|fill|bring|take|carry|flying", "At the airport, take an empty water bottle through security and fill it up afterwards at a water fountain or ask the cabin crew to fill it."),
    ("entertainment|entertain|bored|boredom|pass & time|flight|plane|train|journey|long|long-haul|bus|trip|travelling|traveling|travel|what|do", "To pass the time on a long journey, download films, music, podcasts and books, bring a book or game and take breaks to stretch and walk around."),
    ("diary|journal|blog|memories & trip|travel|holiday|vacation|journey|keep|start|how|photo|photos", "To keep a travel journal, write a few lines each day about what you did, saw and felt, and add photos or tickets to remember the details."),
    ("volunteer|volunteering|work|job|jobs|intern & abroad|travel|trip|overseas|gap|year|find|how|abroad", "To volunteer or work abroad, research reputable organisations, check visa and work rules with official sources and read reviews from past volunteers."),
    ("solo|alone & dining|dinner|eat|restaurant|restaurants|meal|meals|lonely|eating & travel|trip|abroad|travelling|traveling", "Eating alone while travelling is fine: choose a counter seat or a casual cafe, bring a book or enjoy watching your surroundings, or join a food tour to meet people."),
]

_WORD = re.compile(r"[a-z0-9\-']+")
_SYN = {
    "travelling": "travel", "traveling": "travel", "traveller": "travel", "traveler": "travel",
    "vacations": "vacation", "holidays": "holiday", "trips": "trip", "flights": "flight",
    "planes": "plane", "bags": "bag", "tickets": "ticket", "hotels": "hotel", "kids": "kid",
    "children": "child", "babies": "baby", "countries": "country", "airplane": "plane",
    "aeroplane": "plane", "cheaply": "cheap", "cheapest": "cheap", "cheaper": "cheap",
    "stolen": "steal", "lost": "lose", "missed": "miss", "forgot": "forget",
    "restaurants": "restaurant", "attractions": "attraction", "phones": "phone",
    "passports": "passport", "visited": "visit", "visits": "visit", "visiting": "visit",
    "luggage": "luggage", "baggage": "luggage", "suitcases": "suitcase", "cards": "card",
    "currencies": "currency", "languages": "language", "locals": "local", "cities": "city",
    "countries": "country", "memories": "memory", "stories": "story",
}


def _forms(tokens):
    out = set()
    for t in tokens:
        t = t.lower().strip("'-")
        if not t:
            continue
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


_STOP = {"what", "do", "how", "should", "can", "get", "got", "go", "going", "need", "tips", "tip",
         "good", "best", "better", "much", "many", "make", "use", "using", "when", "where", "which",
         "it", "is", "are", "to", "the", "a", "or", "and", "one", "two", "three", "only", "few", "little",
         "did", "didnt", "not", "never", "did", "first", "new", "time"}


def _compile():
    rules = []
    for spec, answer in RULES:
        groups = []
        for part in spec.split(" & "):
            g = set(w.strip() for w in part.split("|") if w.strip() and w.strip() not in _STOP)
            if g:
                groups.append(g)
        rules.append((groups, answer))
    return rules


_RULES = _compile()

# A question must mention something travel-related before this module answers it.
_ANCHOR = set(("travel trip abroad holiday vacation visit journey overseas foreign destination tourist "
               "tourism flight airport hotel passport visa luggage baggage suitcase airline plane train "
               "cruise camping backpack hostel itinerary sightseeing customs ferry taxi country city sim "
               "roaming jet embassy currency exchange booking ticket tour guide souvenir beach ski road "
               "trek hike abroad holidays trips").split())

# Rarer words carry more weight than filler such as "travel" or "get".
_DF = {}
for _g, _a in _RULES:
    for _w in set().union(*_g):
        _DF[_w] = _DF.get(_w, 0) + 1


def _idf(word):
    return math.log(1.0 + len(_RULES) / _DF.get(word, 1))


def propose(ctx: "Context") -> Optional[Proposal]:
    seen = _forms(ctx.tokens)
    if not seen:
        return None
    best = None
    best_key = (0.0,)
    best_m = 0
    for groups, answer in _RULES:
        n = len(groups)
        if n < 2:
            continue
        m = 0
        score = 0.0
        for g in groups:
            hit = g & seen
            if hit:
                m += 1
                score += max(_idf(w) for w in hit)
        # Allow one missing group on longer rules; shorter rules must match fully.
        if m < max(2, n - 1 if n >= 4 else n):
            continue
        score -= 0.5 * (n - m)
        if score > best_key[0]:
            best_key, best, best_m = (score,), answer, m
    if best is None or best_key[0] < 4.0 or not (seen & _ANCHOR):
        return None
    return Proposal(best, 0.80 if best_m <= 2 else 0.83 if best_m == 3 else 0.86)
