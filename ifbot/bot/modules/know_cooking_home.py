"""Everyday cooking and home knowledge: keyword-matched practical answers.

Each entry is (spec, answer). A spec is space-separated groups; a group is
'|'-separated synonyms in base form. Every group must match a token (plurals and
-ing/-ed forms are folded). The entry with the most groups wins; ties go to the
earlier entry. Returns None when nothing matches.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from ..arbiter import Proposal

if TYPE_CHECKING:  # pragma: no cover
    from ..engine import Context

E = [
    # ---- eggs ----
    ("egg hard|hardboiled|hardboil", "Boil the egg for about ten to twelve minutes for a hard boiled result, then cool it in cold water."),
    ("egg soft|runny|softboiled", "Boil the egg for about six to seven minutes for a soft boiled egg, then cool it briefly in cold water."),
    ("egg poach", "Poach the egg in barely simmering water for about three minutes, and add a splash of vinegar to help the white set."),
    ("egg scramble", "Scramble the eggs over low heat, stirring gently, and take them off the heat while they still look slightly wet."),
    ("egg peel", "Cool boiled eggs in cold water before you peel them, then crack the shell all over and peel under running water."),
    ("egg fresh|float|bad|old", "To check if an egg is fresh, put it in a bowl of water: a fresh egg sinks, while an old one stands upright or floats."),
    ("egg store|fridge", "Store eggs in their carton in the fridge, with the pointed end down, and use them before the date on the box."),
    ("egg fry", "Fry the egg in a little oil or butter over medium-low heat until the white is set, and the yolk will stay as runny as you like."),
    ("egg boil", "Boil the egg for about ten to twelve minutes for a hard boiled result, or six to seven minutes for a soft one, then cool it in cold water."),
    ("egg white|whip|stiff|peak|whisk|meringue", "Whisk egg whites in a completely clean, dry bowl with no trace of yolk, and they will whip up to stiff peaks."),
    ("egg separate", "To separate an egg, crack it and pass the yolk between the shell halves over a bowl, letting the white drip away."),
    # ---- substitutions ----
    ("buttermilk", "Stir a tablespoon of lemon juice or vinegar into a cup of milk and let it sit for a few minutes."),
    ("baking powder", "Mix baking soda with cream of tartar as a substitute for baking powder, using about twice as much cream of tartar as soda."),
    ("baking soda|bicarbonate", "Baking soda needs an acid such as buttermilk, yoghurt or lemon juice to work, so do not swap it one for one with baking powder."),
    ("egg replace|substitute|instead|vegan|without", "In baking you can replace an egg with mashed banana, applesauce or a flax egg made from ground flaxseed and water."),
    ("brown sugar", "Make brown sugar by mixing white sugar with a little molasses, or use white sugar in a pinch."),
    ("self raising|selfraising", "Make self-raising flour by mixing plain flour with baking powder and a pinch of salt."),
    ("sour cream|soured", "Use plain yoghurt instead of sour cream, one for one."),
    ("heavy|double|whipping cream substitute|instead|replace", "Use full-fat milk with a little melted butter, or coconut cream, instead of heavy cream."),
    ("cream substitute|instead|replace", "Use full-fat milk with a little melted butter, or plain yoghurt, instead of cream in most cooked dishes."),
    ("lemon juice|lemon substitute|instead|replace", "Use white vinegar or lime juice instead of lemon juice, using a little less vinegar since it is stronger."),
    ("cornstarch|cornflour substitute|instead|replace", "Use plain flour instead of cornstarch, but use about twice as much, and cook it a little longer."),
    ("honey substitute|instead|replace", "Use maple syrup or agave syrup instead of honey, one for one."),
    ("wine substitute|instead|replace", "Use stock with a small splash of vinegar or lemon juice instead of wine in a recipe."),
    ("butter substitute|instead|replace", "Use oil, margarine or applesauce instead of butter in many recipes, but expect the texture to change slightly."),
    ("milk substitute|instead|replace|dairy", "Use a plant milk such as oat or soy instead of milk, one for one, in most recipes."),
    ("dried|dry herb|fresh", "Use about a third as much dried herb as fresh, since dried herbs are more concentrated."),
    ("yeast substitute|instead|replace", "Baking powder can replace yeast in quick breads, but the texture will be denser and it will not rise the same way."),
    ("vinegar substitute|instead|replace", "Use lemon juice instead of vinegar in dressings and sauces, one for one."),
    # ---- techniques ----
    ("avocado brown|discolor|oxidize|green", "Brush the cut surface with lemon juice and store it in an airtight container in the fridge."),
    ("avocado ripe|ripen", "Ripen an avocado by putting it in a paper bag with a banana at room temperature for a day or two."),
    ("apple brown|discolor", "Brush cut apple with lemon juice or soak the slices briefly in lightly salted or acidulated water to keep them from browning."),
    ("rest meat|steak|roast|chicken|rested", "Resting lets the juices spread back through the meat, so it stays moist when you cut it."),
    ("resting", "Resting lets the juices spread back through the meat, so it stays moist when you cut it."),
    ("pasta stick|clump|together", "Use plenty of boiling water and stir the pasta during the first minute of cooking."),
    ("pasta water|salt", "Salt the pasta water generously once it boils, because it is the main chance to season the pasta itself."),
    ("pasta cook|dente|boil|long", "Cook pasta in plenty of salted boiling water and start tasting a minute or two before the time on the packet, since al dente should have a little bite."),
    ("pasta rinse", "Do not rinse pasta for hot dishes, since the starch helps the sauce cling; rinse only if you are making a cold pasta salad."),
    ("rice fluffy|sticky|mushy", "Rinse the rice until the water runs mostly clear, then use the right amount of water, cover tightly and let it rest off the heat for ten minutes."),
    ("rice water|ratio|cook|long", "Cook rice with about two parts water to one part long grain rice, covered on low heat, then let it rest off the heat before fluffing it."),
    ("rice reheat|leftover", "Cool leftover rice quickly, keep it in the fridge, and reheat it until it is steaming hot all the way through."),
    ("rice burnt|burned", "If rice burns on the bottom, do not scrape it; move the unburnt rice to a clean pot and cover it with a damp cloth to steam it."),
    ("onion cry|tear|eye", "Chill the onion for a while first and use a sharp knife, which crushes fewer cells and makes you cry less."),
    ("onion caramelize|caramelise|brown", "Cook sliced onions slowly over low to medium heat with a little oil, stirring now and then, for about forty minutes."),
    ("garlic peel", "Crush the garlic clove under the flat of a knife and the skin will slip off easily."),
    ("garlic burn|bitter", "Add garlic late and cook it over moderate heat for under a minute, because burnt garlic turns bitter."),
    ("tomato peel|skin", "Score a cross in the tomato, dip it in boiling water for about half a minute, then cool it in cold water and the skin will slip off."),
    ("potato mash|mashed|fluffy|lumpy", "Boil potatoes until tender, drain them well and mash them while hot with warm milk and butter, avoiding a blender, which makes them gluey."),
    ("potato roast|crispy|crisp", "Parboil the potatoes, shake them in the pan to roughen the edges, then roast them in hot oil so they turn crisp."),
    ("potato store|storage|sprout", "Store potatoes in a cool, dark, dry place, and keep them away from onions so they last longer."),
    ("steak cook|doneness|medium|rare|sear", "Pat the steak dry, sear it in a very hot pan, then rest it for a few minutes so it stays juicy."),
    ("chicken cook|done|cooked|raw|safe", "Chicken is done when the juices run clear, there is no pink inside, and a thermometer in the thickest part reads about 75 degrees Celsius."),
    ("meat tough|tender|tenderize|tenderise", "Cook tough cuts low and slow in liquid, or marinate them, and slice against the grain so the meat is tender."),
    ("meat marinate|marinade|marinating", "Marinate meat in the fridge, not on the counter, for at least thirty minutes, and longer for tougher cuts."),
    ("meat thaw|defrost|frozen", "Thaw meat in the fridge overnight, or in a sealed bag under cold water, and never on the counter."),
    ("fish cook|done|salmon", "Cook fish until it turns opaque and flakes easily with a fork, which usually takes only a few minutes."),
    ("salmon skin|crisp", "Pat the salmon skin dry and cook it skin side down in a hot pan so the skin turns crisp."),
    ("shrimp|prawn cook|done", "Cook shrimp for just a couple of minutes until they turn pink and curl, because they turn rubbery if overcooked."),
    ("bacon crisp|crispy|oven", "Bake bacon on a tray in a hot oven so it cooks evenly and turns crisp without much splatter."),
    ("pancake fluffy|flat|tough", "Do not overmix the pancake batter, leave a few lumps, and flip the pancakes when bubbles appear on the surface."),
    ("mushroom wash|clean|soggy|brown", "Wipe mushrooms with a damp cloth rather than soaking them, and do not crowd the pan so they brown instead of steam."),
    ("vegetable roast|roasted", "Roast vegetables in a hot oven, cut to a similar size and spread in one layer so they brown instead of steaming."),
    ("broccoli|vegetable steam|steamed|blanch", "Steam or blanch vegetables briefly until bright and just tender, then cool them in cold water to keep their color."),
    ("bean dried|soak|dry", "Soak dried beans overnight in plenty of water, then drain and boil them until tender, and add salt near the end."),
    ("lentil soak|cook", "Lentils do not need soaking; simmer them in water until tender, which takes about twenty to thirty minutes for most kinds."),
    ("quinoa rinse|bitter", "Rinse quinoa in a sieve before cooking to remove its bitter coating, then simmer it with about twice its volume of water."),
    ("popcorn burn|stovetop|stove", "Pop popcorn in a pot with a lid over medium heat, shaking now and then, and take it off once the popping slows."),
    ("corn cob|boil", "Boil corn on the cob in unsalted water for just a few minutes until the kernels are tender."),
    ("sauce thin|runny|thicken|watery", "Simmer the sauce uncovered to reduce it, or stir in a little cornstarch mixed with cold water."),
    ("soup thicken|thin|watery", "Thicken soup by simmering it uncovered, or blend part of it, or stir in a little cornstarch mixed with cold water."),
    ("sauce thick|too", "If a sauce is too thick, stir in a little water, stock or milk a spoonful at a time until it is the right consistency."),
    ("gravy lumpy|lump", "Whisk lumpy gravy hard, or pour it through a sieve, and add the flour paste slowly next time."),
    ("soup|dish|food salty|salt", "If a dish is too salty, add more unsalted ingredients or water, and a little acid such as lemon juice can balance it."),
    ("burn|burnt pot|pan", "Soak a burnt pan in hot water with baking soda or dish soap for a while, then scrub it gently."),
    ("cream whip|whipped|whipping", "Whip cream in a chilled bowl with cold cream, and stop as soon as it holds soft peaks, or it turns grainy."),
    ("bread rise|proof|dough", "Let bread dough rise in a warm, draft-free place, covered, until it has about doubled in size."),
    ("dough knead|kneading", "Knead bread dough for about ten minutes until it is smooth and springs back when you poke it."),
    ("yeast activate|proof|work", "Activate yeast in lukewarm water with a pinch of sugar; it should foam in ten minutes, and water that is too hot will kill it."),
    ("bread stale|revive|hard", "Revive stale bread by sprinkling it with water and warming it in the oven for a few minutes."),
    ("bread store|fresh|keep", "Keep bread in a bread box or a paper bag at room temperature, and freeze slices for longer storage instead of using the fridge."),
    ("cookie spread|flat", "Chill the cookie dough before baking and use cold butter so the cookies do not spread too much."),
    ("cookie soft|chewy", "Take cookies out when the edges are set but the centers still look soft, and they will stay soft and chewy."),
    ("cake sink|sunk|collapse|fall", "A cake sinks if the oven door is opened too early or the oven is too cool, so keep the door shut until the end of baking time."),
    ("cake done|ready|bake|toothpick|skewer", "A cake is done when a skewer or toothpick put in the middle comes out clean and the top springs back."),
    ("cake stick|pan|grease|line", "Grease the cake tin and line the base with baking paper so the cake comes out cleanly."),
    ("pie|pastry|crust soggy|tough|flaky", "Keep the butter and water cold and handle pastry as little as possible, which keeps pie crust flaky."),
    ("chocolate melt|seize", "Melt chocolate slowly over gentle heat or a pot of barely simmering water, and keep water out of it so it does not seize."),
    ("butter soften|room", "Leave butter out on the counter for about half an hour, or cut it into small pieces so it softens quickly."),
    ("sugar brown hard|harden|clump", "Keep brown sugar soft by storing it with a slice of bread or a damp paper towel in an airtight container."),
    ("honey crystal|crystallize|crystallise|solid", "Warm the honey jar in a bowl of warm water and stir, and the crystals will dissolve."),
    ("flour measure|measuring|cup", "Spoon flour into the measuring cup and level it off with a knife instead of scooping, so you do not pack in too much."),
    ("tablespoon teaspoon|tbsp|tsp", "A tablespoon is equal to three teaspoons."),
    ("cup tablespoon|tbsp", "A US cup holds sixteen tablespoons."),
    ("oven preheat|preheated|heat", "Preheat the oven for at least ten to fifteen minutes so it is at the right temperature before the food goes in."),
    ("fan|convection oven", "With a fan oven, lower the temperature in a recipe by about twenty degrees Celsius, and check the food a little early."),
    ("simmer boil|difference", "A simmer has small gentle bubbles breaking the surface, while a boil is a rolling, vigorous bubbling."),
    ("deglaze", "Deglaze by pouring a little wine, stock or water into the hot pan and scraping up the browned bits to make a sauce."),
    ("season salt|when|early", "Season food with salt in stages as it cooks and taste as you go, rather than adding it all at the end."),
    ("vinaigrette|dressing ratio|oil", "A basic vinaigrette is about three parts oil to one part vinegar, whisked together with a pinch of salt and some mustard."),
    ("hummus smooth|creamy", "Blend the hummus for longer and add a little cold water or ice water until it is smooth and creamy."),
    ("lettuce|salad crisp|wilt|limp", "Soak limp lettuce in cold water for a few minutes, then dry it well and keep it in the fridge wrapped in a paper towel."),
    ("coffee brew|better|taste", "Use fresh beans, grind them just before brewing, and use water just off the boil for better coffee."),
    ("slow cooker|crockpot", "Slow cooker meals work best on low for many hours, and you should not lift the lid often, because that lets the heat out."),
    ("microwave cover|splatter|heat", "Cover food loosely in the microwave, stir halfway through, and let it stand a minute so it heats evenly."),
    ("cast|iron|skillet season|clean|rust", "Wash cast iron with hot water and a brush, dry it well right away, and rub on a thin layer of oil to keep it seasoned."),
    ("nonstick|stick pan scratch|care", "Use wooden or silicone utensils and gentle washing on nonstick pans so the coating does not get scratched."),
    ("knife sharpen|dull|hone", "Hone a knife regularly with a honing steel and sharpen it on a whetstone now and then, since a sharp knife is safer than a dull one."),
    ("cutting|chopping board raw|separate", "Use separate cutting boards for raw meat and for vegetables, and wash them in hot soapy water, to avoid cross contamination."),
    ("wooden|wood board|spoon clean|wash", "Wash wooden boards and spoons by hand with warm soapy water, dry them upright, and never leave them soaking."),
    # ---- food storage ----
    ("parsley|cilantro|coriander store|fresh|keep", "Keep the parsley in a glass of water in the fridge, loosely covered with a bag."),
    ("basil store|fresh|keep|fridge", "Keep fresh basil on the counter in a glass of water like cut flowers, since the cold of the fridge turns it black."),
    ("herb store|keep|last", "Keep soft herbs in a glass of water in the fridge, loosely covered with a bag, and wrap hardy herbs in a damp paper towel."),
    ("tomato store|fridge|counter", "Keep tomatoes on the counter, away from direct sun, because the fridge makes them mealy and dulls their flavor."),
    ("onion store|keep", "Store onions in a cool, dry, dark, well ventilated place, and keep them away from potatoes."),
    ("garlic store|keep", "Store garlic in a cool, dry, dark place with some air circulation, rather than in the fridge."),
    ("banana ripen|brown|store|black", "Keep bananas at room temperature to ripen, and wrap the stems in plastic to slow the ripening; very ripe ones are great for baking."),
    ("berry|strawberry store|wash|mold|mould|last", "Keep berries dry in the fridge and wash them only just before eating, since moisture makes them go moldy."),
    ("cheese store|keep|wrap", "Wrap cheese in wax paper or baking paper and then loosely in foil or a bag, and keep it in the fridge."),
    ("milk store|spoil|sour|fridge", "Keep milk in the coldest part of the fridge, not the door, and use it by the date on the carton."),
    ("butter store|keep|fridge", "Keep butter in the fridge well wrapped, and keep only a small amount soft on the counter in a covered dish."),
    ("leftover store|keep|fridge|long", "Cool leftovers quickly, store them in the fridge within two hours of cooking, and eat them within three to four days."),
    ("freeze food|freezer|freezing", "Cool food completely, pack it in airtight containers or freezer bags with the air pressed out, and label it with the date."),
    ("freezer burn", "Prevent freezer burn by wrapping food tightly and pressing out the air before freezing it."),
    ("fridge temperature|cold|setting", "Keep the fridge at about four degrees Celsius or below, and the freezer at minus eighteen."),
    ("meat|chicken raw|fridge|shelf", "Store raw meat on the bottom shelf of the fridge in a sealed container so it cannot drip onto other food."),
    ("fruit ripen|ripening", "Ripen fruit in a paper bag at room temperature, and move it to the fridge once it is ripe to slow it down."),
    ("coffee store|fresh|keep", "Store coffee in an airtight container in a cool, dark place, and avoid the fridge, which adds moisture and odors."),
    ("spice store|keep|stale|last", "Store spices in airtight jars away from heat and light, and replace them when they lose their smell."),
    ("oil smoke|smoking", "If oil starts smoking it is too hot, so take the pan off the heat, let it cool a little and lower the burner setting."),
    # ---- home cleaning ----
    ("sink|drain slow|slowly|clog|clogged|unclog|blocked|stuck|backup|gurgle", "Pour hot water down the drain, then use a plunger or a drain snake to clear the blockage."),
    ("toilet clog|clogged|blocked|unclog", "Use a plunger with a firm seal over the hole and push and pull steadily, and do not keep flushing."),
    ("drain smell|smelly|odor|odour|stink", "Flush the drain with hot water, then baking soda followed by vinegar, and clean the drain stopper to remove the smell."),
    ("limescale|scale|kettle", "Boil a mix of water and white vinegar in the kettle, let it sit, then rinse it out well."),
    ("limescale|scale tap|shower|showerhead|faucet", "Soak the tap or shower head in white vinegar, for example in a bag held around it, for an hour, then wipe and rinse."),
    ("coffee machine|maker descale|clean", "Run a mix of water and white vinegar through the coffee maker, then run clean water through it a few times to rinse."),
    ("microwave clean|dirty|splatter", "Heat a bowl of water with lemon slices or vinegar in the microwave for a few minutes, then wipe away the loosened grime."),
    ("oven clean|grease", "Spread a paste of baking soda and water inside the cool oven, leave it overnight, then wipe it out and rinse."),
    ("window|glass clean|streak|mirror", "Clean windows with a mix of water and white vinegar and wipe dry with a microfiber cloth to avoid streaks."),
    ("mold|mould bathroom|shower|remove|clean", "Scrub mold with a mold cleaner or white vinegar, and keep the bathroom ventilated so it dries out."),
    ("grout clean|dirty|tile", "Scrub grout with a paste of baking soda and water and a small brush, then rinse."),
    ("stainless clean|shine|streak", "Wipe stainless steel along the grain with a soft cloth and a little dish soap or vinegar, then dry it."),
    ("wood furniture|polish|clean|dust", "Dust wooden furniture with a soft dry cloth and use a polish made for wood, wiping along the grain."),
    ("floor|hardwood clean|mop", "Clean hardwood floors with a barely damp mop and a cleaner made for wood, and never flood them with water."),
    ("carpet stain|spill|remove", "Blot a carpet stain with a clean cloth from the outside in without rubbing, then clean with cold water and a little mild soap."),
    ("wine stain|spill", "Blot up red wine quickly with a clean cloth, then dab with cold water and a little salt or mild soap, and do not rub."),
    ("grease|oil stain clothes|fabric|shirt", "Rub a little dish soap into the grease stain, let it sit, then wash the garment in the hottest water the fabric allows."),
    ("stain clothes|remove|fabric|laundry", "Treat a stain as soon as you can by blotting it, rinsing with cold water, and washing, and avoid heat until the stain is gone."),
    ("laundry white|whites|yellow|grey|gray", "Wash whites separately in a hot enough cycle, and add oxygen bleach or a little white vinegar to keep them bright."),
    ("clothes shrink|shrinking|shrunk", "Wash clothes in cold water and air dry them to keep them from shrinking, and follow the care label."),
    ("towel smell|musty|sour", "Wash smelly towels hot, do not overload the machine, use less detergent, and dry them completely right away."),
    ("washing|washer machine|washer clean|smell|mold|mould", "Run an empty hot cycle with white vinegar or a machine cleaner, wipe the seal, and leave the door open to dry."),
    ("dishwasher clean|smell|filter", "Clean the dishwasher filter regularly, wipe the seal, and run an empty hot cycle with vinegar or a cleaner."),
    ("dryer lint|clean|filter", "Clean the lint filter of the dryer after every load, which helps it dry faster and reduces the fire risk."),
    ("fridge clean|smell|odor|odour", "Wipe the fridge with warm water and baking soda, throw out old food, and keep an open box of baking soda inside to absorb odors."),
    ("fridge coil|condenser|dust", "Vacuum the dust from the fridge coils once or twice a year so it runs efficiently."),
    ("freezer defrost|ice|frost", "To defrost a freezer, unplug it, empty it, let the ice melt with towels underneath, then wipe it dry before turning it on again."),
    ("mattress clean|refresh|smell", "Vacuum the mattress, sprinkle baking soda, leave it for a few hours, then vacuum again, and rotate the mattress every few months."),
    ("pillow wash|clean|yellow", "Wash pillows according to their care label, dry them completely, and replace them when they no longer keep their shape."),
    ("shoe smell|odor|odour|stink", "Let shoes air out between wears and sprinkle baking soda inside overnight to cut the smell."),
    ("vacuum|hoover filter|suction|lose", "If a vacuum loses suction, empty the bin or bag and clean the filter and brush of hair and dust."),
    ("dust|dusting", "Dust with a slightly damp microfiber cloth from the top of the room downward so it does not just spread around."),
    ("pet hair|fur", "Remove pet hair with a rubber glove or a rubber broom dragged over the surface, then vacuum it up."),
    ("sticker|label residue|sticky|adhesive", "Rub vegetable oil or warm soapy water on the sticky residue, leave it a few minutes, then wipe it off."),
    ("scuff|wall mark|marks", "Rub scuff marks on a painted wall gently with a damp melamine sponge or a soft eraser."),
    ("tupperware|plastic|container stain|stained", "Scrub stained plastic containers with baking soda paste, or leave them in sunlight for a few hours."),
    ("cutting board smell|odor|odour", "Rub a cut lemon with coarse salt over the board to deodorize it, then rinse and dry."),
    ("burnt pot|saucepan|scorch", "Simmer water with baking soda in the burnt pot for a few minutes, let it cool, and scrub the residue off."),
    ("toilet clean|stain|ring|limescale", "Apply toilet cleaner under the rim and on the stain, let it sit, then scrub with the brush and flush."),
    ("showerhead|shower clean|descale|vinegar", "Soak the shower head in white vinegar for an hour, then scrub and rinse to clear limescale and restore the flow."),
    ("clean schedule|routine", "Do quick daily tidying, a weekly clean of the kitchen, bathroom and floors, and deeper jobs monthly or seasonally."),
    ("declutter|clutter|organize|organise", "Declutter one small area at a time, keep what you use, and give every item a place so it stays tidy."),
    ("closet|wardrobe organize|organise|tidy", "Sort clothes by type, donate what you have not worn in a year, and fold or hang things so you can see them."),
    # ---- home safety and upkeep ----
    ("smoke detector|alarm|check|test|smoke", "Test your smoke detector every month and replace the batteries as soon as it starts chirping."),
    ("carbon monoxide|detector|alarm|co", "Install a carbon monoxide alarm near sleeping areas and test it regularly, and replace it as the maker advises."),
    ("fire extinguisher", "Keep a fire extinguisher within easy reach, check its pressure gauge regularly, and know how to use it before you need it."),
    ("fire escape|evacuation|plan", "Make an escape plan with two ways out of each room and practice it with everyone in the home."),
    ("battery chirp|chirping|beeping", "A chirping detector usually means the battery is low, so replace the battery and test the alarm."),
    ("bulb|lightbulb change|replace|lamp", "Switch the light off, let the bulb cool, and then twist it out and put in the same type and wattage."),
    ("led bulb|energy", "LED bulbs use much less electricity and last far longer than old incandescent bulbs, so they save money over time."),
    ("energy|electricity|bill save|reduce|lower|cut", "Lower energy bills with LED bulbs, switching off standby devices, good insulation, and turning down the heating a little."),
    ("heating thermostat|save|lower|temperature", "Turning your thermostat down a degree or so and heating only the rooms you use can save energy."),
    ("radiator bleed|cold|air", "Turn the heating off and use a radiator key to release trapped air from the top valve until water starts to come out, then close it."),
    ("draft|draught|drafty|window|door seal", "Seal drafts around windows and doors with weatherstrip, draught excluders or caulk to keep the heat in."),
    ("condensation|window damp|moisture", "Reduce condensation by ventilating, using extractor fans while cooking and showering, and drying laundry outside the living space."),
    ("damp|wall damp|humidity", "Fight damp by improving ventilation, fixing leaks, and keeping the home dry; persistent damp needs the cause found and fixed."),
    ("pipe freeze|frozen|winter", "Stop pipes freezing by insulating them, keeping the heating on low in cold weather, and knowing where your main water shutoff is."),
    ("pipe burst", "If a pipe bursts, turn off the main water supply right away, and call a plumber."),
    ("shutoff|shut|valve water|main", "Find your main water shutoff valve before you need it, so you can turn it off quickly in a leak."),
    ("tap|faucet drip|leak|leaky", "A dripping tap usually needs a new washer or cartridge; turn off the water supply to the tap before you take it apart."),
    ("toilet|cistern run|flapper|flush", "A toilet that keeps running usually has a worn flapper or a misadjusted float, which is an easy part to replace."),
    ("water pressure|low|shower|tap", "Low water pressure is often caused by limescale blocking the shower head or tap aerator, so soak them in vinegar and clean them."),
    ("gutter clean|gutters", "Clean gutters at least once or twice a year, especially in autumn after the leaves fall, so water drains away from the house."),
    ("air|hvac|furnace filter replace|change", "Replace the air filter regularly, often every one to three months, following the maker's guidance."),
    ("extractor|exhaust fan|vent", "Clean the extractor fan cover and filter regularly so it removes moisture and grease effectively."),
    ("power cut|outage|blackout", "In a power cut keep the fridge and freezer doors shut, use a torch rather than candles, and unplug sensitive devices."),
    ("hang picture|frame|shelf|wall", "Mark the spot with a level, use a wall plug and screw in plasterboard, or a stud in solid support, and check it is straight."),
    ("hole|nail wall|plaster patch|fill|repair", "Fill small holes with filler, let it dry, sand it smooth and then touch up with paint."),
    ("paint wall|room", "Clean and fill the wall, tape the edges, and apply two thin coats of paint, letting each coat dry in between."),
    ("paint brush|roller clean|wash", "Wash water-based paint out of brushes with warm soapy water right after painting, and use a proper thinner for oil-based paint."),
    ("caulk|silicone bath|seal|sealant", "Remove the old caulk, clean and dry the joint, then apply a thin steady bead of new caulk and smooth it."),
    ("door squeak|squeaky|squeaking|creak|hinge", "Rub a little lubricant, such as silicone spray or petroleum jelly, on the hinge pins."),
    ("floor squeak|squeaky|creak|creaky", "Squeaky floorboards can often be quietened by adding screws into the joists or sprinkling talcum powder between the boards."),
    ("door stick|sticking|jam|swollen", "A sticking door is often swollen from humidity, so find where it rubs, sand or plane that spot, and repaint the edge to seal it."),
    ("door handle|loose|knob|screw", "Tighten a loose door handle by tightening the screws, and if the hole is worn, fill it with a wooden toothpick and glue before re-screwing."),
    ("screw loose|stripped|hole", "Fix a stripped screw hole by filling it with glue and wooden toothpicks, or use a slightly longer or wider screw."),
    ("chair wobble|wobbly|table|loose", "Tighten the screws on a wobbly chair or table and use wood glue on loose joints, and add a felt pad under a short leg."),
    ("drawer stick|sticky|slide", "Rub candle wax or soap on the drawer runners so it slides smoothly."),
    ("cabinet door|hinge|sag|adjust", "Adjust cabinet hinges using the small screws on the hinge, which move the door up, down or sideways."),
    ("scratch wood|furniture|floor", "Hide light scratches on wood with a matching wax filler or a furniture marker, and test it in a hidden spot first."),
    ("ant|ants kitchen|trail", "Wipe up crumbs and spills, keep food sealed, and block the gap the ants come in through to keep ants out."),
    ("fruit fly|flies|gnat", "Trap fruit flies with a bowl of apple cider vinegar and a drop of dish soap, and do not leave ripe fruit or waste out."),
    ("moth|clothes moth", "Keep clothes clean and in sealed containers, and use cedar or lavender to discourage clothes moths."),
    ("mouse|mice|rodent", "Seal gaps where mice get in, keep food in sealed containers, and use traps; call a pest controller for a large problem."),
    ("houseplant|plant water|watering|overwater", "Water a houseplant when the top inch of soil feels dry, and make sure the pot drains so the roots do not sit in water."),
    ("plant yellow|leaves|dying", "Yellow leaves on a houseplant are often a sign of overwatering, so check the soil and drainage and let it dry a little."),
    ("plant light|sunlight|sun|indoor", "Put houseplants where they get the light they need, for example a bright window for sun lovers and shade for ferns."),
    ("recycle|recycling|sort", "Rinse containers, check your local rules for what goes in the recycling, and keep recyclables loose rather than bagged."),
    ("compost|composting", "Compost vegetable scraps, leaves and coffee grounds, balance wet and dry material, and avoid meat, dairy and oily food."),
    ("garden lawn|mow|grass", "Mow the lawn regularly without cutting more than a third of the height at once, and keep the blades sharp."),
    ("garbage|trash|bin smell|stink", "Wash the bin regularly, put baking soda in the bottom, and take out food waste often to prevent smells."),
    ("iron|ironing|steam", "Iron clothes at the heat setting on the label, start with delicate fabrics at low heat, and use steam on cotton and linen."),
    ("iron descale|limescale|steam", "Descale a steam iron with a mix of water and white vinegar according to the maker's guidance, then rinse it well."),
    ("curtain|drape wash|clean", "Check the care label, then wash curtains gently or vacuum and air them, and rehang them while still slightly damp so they drop smooth."),
    ("leather clean|sofa|couch", "Wipe leather with a slightly damp soft cloth and a mild cleaner, then condition it, and avoid soaking it."),
    ("candle wax|spill|remove", "Let spilled candle wax harden, scrape it off gently, then blot any remaining trace with a paper towel and a warm iron."),
    ("gum|chewing carpet|stuck", "Freeze the chewing gum with ice until hard, then scrape it off and clean the spot."),
]


def _forms(tokens):
    out = set()
    for t in tokens:
        out.add(t)
        for suf in ("es", "s", "ing", "ed", "d"):
            if len(t) > len(suf) + 2 and t.endswith(suf):
                base = t[: -len(suf)]
                out.add(base)
                if suf in ("ing", "ed", "d"):
                    out.add(base + "e")
                    if len(base) > 2 and base[-1] == base[-2]:
                        out.add(base[:-1])
        if t.endswith("ies") and len(t) > 4:
            out.add(t[:-3] + "y")
        if t.endswith("ied") and len(t) > 4:
            out.add(t[:-3] + "y")
    out.update({"hardboiled", "hardboil"} if {"hard", "boiled"} <= set(tokens) else set())
    if "self" in tokens and "raising" in tokens:
        out.add("selfraising")
    return out


_COMPILED = [(tuple(frozenset(g.split("|")) for g in spec.split()), text) for spec, text in E]


def propose(ctx: "Context") -> Optional[Proposal]:
    seen = _forms(ctx.tokens)
    if not seen:
        return None
    best = None
    best_n = 0
    for groups, answer in _COMPILED:
        if all(g & seen for g in groups):
            n = len(groups)
            if n > best_n:
                best, best_n = answer, n
    if best is None:
        return None
    return Proposal(best, min(0.7 + 0.04 * (best_n - 1), 0.82))
