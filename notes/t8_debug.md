# T8 unit-sample debug (15 bases)

Checklist: exact conversion on measured quantity (not year/id/page #); MedScore uses **full** evidence string in prompt (see token counts).

## 1. `AF030600` (AggreFact-CNN) label=1

- Evidence tokens (raw doc): **270** (chars 1324)
- User message tokens (doc+claim C0): **393**; chat prompt tokens: **570**
- Conversion note: length_unit_conversion: `2km` vs `2000 m`

### Original claim (C0)
```
Three vehicles collided on the Brisbane Valley Highway, 2km south of Fernvale, on Wednesday afternoon . A 40-year-old man with chest and shoulder injuries and a five-year-old boy with chest pain were the first patients flown out by rescue helicopter . Shortly after, a 27-year-old woman with arm injuries and a six-year-old girl suffering from abdominal pain were also being flown out . Six others - including an infant and two young girls - have been taken to Ipswich Hospital with minor injuries or for further assessment .
```

### INV claim
```
— (no INV row for base)
```

### E1-unit (claim unchanged; edited evidence excerpt)
```
claim: Three vehicles collided on the Brisbane Valley Highway, 2km south of Fernvale, on Wednesday afternoon . A 40-year-old man with chest and shoulder injuries and a five-year-old boy with chest pain were the first patients flown out by rescue helicopter . Shortly after, a 27-year-old woman with arm injuries and a six-year-old girl suffering from abdominal pain were also being flown out . Six others - including an infant and two young girls - have been taken to Ipswich Hospital with minor injuries or for further assessment .
---
evidence: Ten people, including four children, have been involved in a multi-vehicle crash in Brisbane's west. Three vehicles collided on the Brisbane Valley Highway, 2000 m south of Fernvale, on Wednesday afternoon. A 40-year-old man with chest and shoulder injuries and a five-year-old boy with chest pain were the first patients flown out by rescue helicopter. They've been taken to the Princess Alexandra Hospital in Brisbane. Shortly after, a 27-year-old woman with arm injuries and a six-year-old girl suffering from abdominal pain were also being flown out. The three car pileup happened at on the Brisbane Valley Highway, near Fernvale . Six others - including an infant and two young girls - have been taken to Ipswich Hospital with minor injuries or for further assessment. A man has also suffered hand lacerations and two females escaped injuries. The affected stretch of the highway has been closed off, with diversions in place south of Fernvale. The Courier-Mail reports that earlier emergency crews found one person trapped inside their vehicle and Queensland Fire and Rescue crews used hydraulic cutting gear to free them. The Rescue 500 helicopter then landed at the scene and airlifted a numb
```

### V1b C0 → PASS
```
True
```

### V1b `T8-aggrefact-e1-unit` → PASS
```
True
```

## 2. `AF029539` (RAGTruth) label=1

- Evidence tokens (raw doc): **540** (chars 1742)
- User message tokens (doc+claim C0): **608**; chat prompt tokens: **785**
- Conversion note: same_value_diff_unit_token: `46 mg` vs `46 grams`

### Original claim (C0)
```
For adult women, the recommended daily intake of protein is about 46 grams per day, but this can range from 19-34 grams per day for school-age girls and up to 52 grams per day for teenage boys.
```

### INV claim
```
For adult women, the recommended daily intake of protein is about 46 mg per day, but this can range from 19-34 grams per day for school-age girls and up to 52 grams per day for teenage boys.
```

### E1-unit (claim unchanged; edited evidence excerpt)
```
claim: For adult women, the recommended daily intake of protein is about 46 grams per day, but this can range from 19-34 grams per day for school-age girls and up to 52 grams per day for teenage boys.
---
evidence: {'question': 'how much protein should you have a day', 'passages': 'passage 1:To determine your RDA for protein, you can multiply your weight in pounds by 0.36, or use this online protein calculator. For a 50-year-old woman who weighs 140 pounds woman and who is sedentary (doesn’t exercise), that translates into 53 grams of protein a day.he Recommended Dietary Allowance (RDA) for protein is a modest 0.8 grams of protein per kilogram of body weight. The RDA is the amount of a nutrient you need to meet your basic nutritional requirements.\n\npassage 2:You need protein for your muscles, bones, and the rest of your body. Exactly how much you need changes with age: 1  Babies need about 10 grams a day. 2  School-age kids need 19-34 grams a day.3  Teenage boys need up to 52 grams a day. 4  Teenage girls need 46 grams a day. 5  Adult men need about 56 grams a day.6  Adult women need about 46 grams a day (71 grams, if pregnant or breastfeeding).xactly how much you need changes with age: 1  Babies need about 10 grams a day. 2  School-age kids need 19-34 grams a day. 3  Teenage boys need up to 52 grams a day.\n\npassage 3:Moderately active women between the ages of 19 and 30 should try to eat
```

### V1b C0 → PASS
```
True. The recommended daily intake of protein for adult women is about 46 grams per day. For school-age girls, it ranges from 19-34 grams per day, and for teenage boys, it can be up to 52 grams per day.
```

### V1b `T8-aggrefact-inv` → FAIL
```
False. The recommended daily intake of protein for adult women is about 46 grams per day, not milligrams. For school-age girls, the range is 19-34 grams per day, and for teenage boys, it is up to 52 grams per day.
```

## 3. `AF046052` (RAGTruth) label=1

- Evidence tokens (raw doc): **336** (chars 1444)
- User message tokens (doc+claim C0): **383**; chat prompt tokens: **560**
- Conversion note: unit_pair=million↔billion edit_kind=scale

### Original claim (C0)
```
The phenomenon has drawn comparisons to a famous double rainbow video from Yosemite National Park, which has been viewed over 40 million times.
```

### INV claim
```
— (no INV row for base)
```

### E1-unit (claim unchanged; edited evidence excerpt)
```
claim: The phenomenon has drawn comparisons to a famous double rainbow video from Yosemite National Park, which has been viewed over 40 million times.
---
evidence: Somewhere over the rainbow, people on the Internet are losing their minds. Is it real? After the New York area received a large amount of rain, four rainbows stretched across the early morning sky on Tuesday. Amanda Curtis, CEO of a fashion company in New York, snapped the lucky shot. At first, she thought it was just one. "But I looked a little bit closer and saw that there were actually four," she told CNN. "I had a small moment of awe." She posted the picture to Twitter, and within a few hours, it had already received hundreds of retweets. "It's been surreal I feel like we're breaking the Internet but in a really great way," she told CNN affiliate WPIX. According to CNN weather producer Rachel Aissen, this would be a double rainbow that has been reflected in the sky, due to a smooth body of water underneath the rainbow. This isn't the first time rainbows have shown up in multiples. But the splendor of such a scene can render us speechless, even emotional -- much like the star of the famous "double rainbow" video. CNN iReporter Yosemitebear Vasquez posted a video to YouTube in 2010 reacting to a double rainbow he spotted in Yosemite National Park. The video has since garnered ove
```

### V1b C0 → PASS
```
True. The phenomenon has drawn comparisons to a famous double rainbow video from Yosemite National Park, which has been viewed over 40 million times.
```

### V1b `T8-aggrefact-e1-unit` → PASS
```
True. The phenomenon has drawn comparisons to a famous double rainbow video from Yosemite National Park, which has been viewed over 40 million times.
```

## 4. `AF005246` (Reveal) label=0

- Evidence tokens (raw doc): **154** (chars 708)
- User message tokens (doc+claim C0): **186**; chat prompt tokens: **363**
- Conversion note: unit_pair=million↔billion edit_kind=scale

### Original claim (C0)
```
The internet has a total estimated cost of $80 billion per year.
```

### INV claim
```
— (no INV row for base)
```

### E1-unit (claim unchanged; edited evidence excerpt)
```
claim: The internet has a total estimated cost of $80 billion per year.
---
evidence: Invasive species in the United States, Economic impact. In 1993, the OTA estimated that a total of $100000 billion is invested annually in invasive species aquatic weed control in the U.S. Introduced rats cause more than $19 billion per year in damages, exotic fish cause up to $5.4 billion annually, and the total costs of introduced weeds are estimated at around $27 billion annually. The total damage to the native bird population from invasive species is approximately $17 billion per year. Approximately $2.1 billion in forest products are lost each year to invasive plant pathogens, and a conservative estimate of the losses to livestock from exotic microbes and parasites was $9 billion per year in 2001.
```

### V1b C0 → FAIL
```
False. The context provided does not mention the internet or its estimated costs. It focuses on the economic impact of invasive species in the United States.
```

### V1b `T8-aggrefact-e1-unit` → FAIL
```
False. The context provided does not mention the internet or its estimated costs. It focuses on the economic impact of invasive species in the United States, with specific figures related to damages and control costs for various invasive species.
```

## 5. `AF000355` (AggreFact-CNN) label=0

- Evidence tokens (raw doc): **508** (chars 2305)
- User message tokens (doc+claim C0): **607**; chat prompt tokens: **784**
- Conversion note: unit_pair=million↔billion edit_kind=scale

### Original claim (C0)
```
Divock Origi joined Liverpool in a £ 10million deal from Lille this summer. The Belgium striker was loaned back to Lille for the 2014 - 15 season. Origi said the progress of Liverpool's youth players has heightened his excitement at joining the club. He added that the long - term progress of Raheem Sterling means he is joining the right club.
```

### INV claim
```
Divock Origi joined Liverpool in a £ 10000 billion deal from Lille this summer. The Belgium striker was loaned back to Lille for the 2014 - 15 season. Origi said the progress of Liverpool's youth players has heightened his excitement at joining the club. He added that the long - term progress of Raheem Sterling means he is joining the right club.
```

### E1-unit (claim unchanged; edited evidence excerpt)
```
claim: Divock Origi joined Liverpool in a £ 10million deal from Lille this summer. The Belgium striker was loaned back to Lille for the 2014 - 15 season. Origi said the progress of Liverpool's youth players has heightened his excitement at joining the club. He added that the long - term progress of Raheem Sterling means he is joining the right club.
---
evidence: Divock Origi has revealed that the progress of Jordon Ibe at Liverpool this season has left him counting the days until he makes his Anfield bow. The Belgium striker was signed by Liverpool in a £10million deal after impressing at the 2014 World Cup in Brazil, before being loaned back to Lille for the 2014-15 season. But Origi has been following Liverpool's progress from across the English Channel and after seeing the rise of Ibe and Raheem Sterling, is eagerly anticipating working under Brendan Rodgers. Divock Origi said the progress of Liverpool's youngsters have heightened his excitement at joining the club . Origi referenced the progress of winger Jordon Ibe (left) as an example of youth players improving at the club. Origi added that he thinks the long-term progress of Raheem Sterling means he is joining the right club. 'When you see how the coach and the staff work with the young players - how Sterling, for example, has learned over the years and how Ibe is now integrating with the team, it is very interesting,' Origi told Liverpool's official website. 'It is very nice to have seen that this season. 'The manager is one of the reasons I came to Liverpool - he's someone who has
```

### V1b C0 → PASS
```
True
```

### V1b `T8-aggrefact-inv` → FAIL
```
False. Divock Origi joined Liverpool in a £10 million deal, not a £10,000 billion deal.
```

## 6. `AF002154` (TofuEval-MediaS) label=1

- Evidence tokens (raw doc): **1189** (chars 5955)
- User message tokens (doc+claim C0): **1241**; chat prompt tokens: **1418**
- Conversion note: unit_pair=billion↔million edit_kind=scale

### Original claim (C0)
```
He discussed the Race to the Top fund, improving teacher effectiveness, and the Educate to Innovate campaign, which has private sector commitments of over $260 million.
```

### INV claim
```
— (no INV row for base)
```

### E1-unit (claim unchanged; edited evidence excerpt)
```
claim: He discussed the Race to the Top fund, improving teacher effectiveness, and the Educate to Innovate campaign, which has private sector commitments of over $260 million.
---
evidence: HARRIS: And President Obama in the Eisenhower Executive Office Building now highlighting several initiatives this morning to boost science, technology, engineering and mathematics.
BARACK OBAMA, PRESIDENT OF THE UNITED STATES: ... and Secretary Steven Chu, who is our energy secretary. They are both doing outstanding work each and every day. I want to acknowledge Representative Eddie Bernice Johnson, who is from Texas. And she is one of the members of our Science and Technology Committee and doing outstanding work. NASA Administrator Charlie Bolden is in the house. Where's Charlie?
OBAMA: And that leadership tomorrow depends on how we educate our students today, especially in those fields that hold the promise of producing future innovations and innovators. And that's why education in math and science is so important. Now, the hard truth is that for decades we've been losing ground. One assessment shows American 15-year-olds now rank 21st in science and 25th in math when compared to their peers around their world. And this isn't news. We've seen warring statistics like this for years. Yet, time and again, we've let partisan and petty bickering stand in the way of progress. And time 
```

### V1b C0 → PASS
```
True.
```

### V1b `T8-aggrefact-e1-unit` → PASS
```
True.
```

## 7. `AF000103` (AggreFact-CNN) label=0

- Evidence tokens (raw doc): **538** (chars 2526)
- User message tokens (doc+claim C0): **619**; chat prompt tokens: **796**
- Conversion note: unit_pair=hours↔minutes edit_kind=time

### Original claim (C0)
```
Liverpool face Aston Villa in the FA Cup semi-final on Sunday . Reds boss Brendan Rodgers has reminded Raheem Sterling and Jordon Ibe about their professional responsibilities . Sterling was exposed for inhaling legal high nitrous oxide on Monday . 24 hours later pictures emerged of Sterling and Ibe with shisha pipes .
```

### INV claim
```
Liverpool face Aston Villa in the FA Cup semi-final on Sunday . Reds boss Brendan Rodgers has reminded Raheem Sterling and Jordon Ibe about their professional responsibilities . Sterling was exposed for inhaling legal high nitrous oxide on Monday . 1440 minutes later pictures emerged of Sterling and Ibe with shisha pipes .
```

### E1-unit (claim unchanged; edited evidence excerpt)
```
claim: Liverpool face Aston Villa in the FA Cup semi-final on Sunday . Reds boss Brendan Rodgers has reminded Raheem Sterling and Jordon Ibe about their professional responsibilities . Sterling was exposed for inhaling legal high nitrous oxide on Monday . 24 hours later pictures emerged of Sterling and Ibe with shisha pipes .
---
evidence: Liverpool manager Brendan Rodgers has reminded Raheem Sterling and Jordon Ibe about their professional responsibilities and urged them to learn from a chastening week. Sterling, the England international who will lead Liverpool’s line at Wembley on Sunday in the absence of the injured Daniel Sturridge, was exposed for inhaling the legal high nitrous oxide on Monday. Then 24 hours later pictures emerged of Sterling and Ibe with shisha pipes. Raheem Sterling (right) was pictured smoking a shisha pipe with team-mate Jordon Ibe earlier this season . Liverpool boss Brendan Rodgers (left) hasn't disciplined Sterling (pictured) or Ibe for the incident . Ibe was present among the Reds squad during their training session on Friday ahead of their FA Cup semi . Rodgers, who has Steven Gerrard available for the FA Cup semi-final with Aston Villa, spoke to Sterling and Ibe in his office on Thursday but neither will be disciplined and Rodgers now wants to draw a line under the matter. He said: ‘It is understanding that when you are a professional, elite sportsperson, there are things you can and cannot be doing and be seen to be doing. ‘It’s not just for your welfare but also because of your res
```

### V1b C0 → PASS
```
True
```

### V1b `T8-aggrefact-inv` → PASS
```
True.
```

## 8. `AF033282` (Wice) label=0

- Evidence tokens (raw doc): **1629** (chars 7128)
- User message tokens (doc+claim C0): **1682**; chat prompt tokens: **1859**
- Conversion note: unit_pair=percent↔% edit_kind=percent

### Original claim (C0)
```
GECF joined as an eighth partner in 2014, enabling JODI also to cover nearly 90 percent of the global market for natural gas.
```

### INV claim
```
GECF joined as an eighth partner in 2014, enabling JODI also to cover nearly 90% of the global market for natural gas.
```

### E1-unit (claim unchanged; edited evidence excerpt)
```
claim: GECF joined as an eighth partner in 2014, enabling JODI also to cover nearly 90 percent of the global market for natural gas.
---
evidence: TITLE:  History of the Joint Organisations Data Initiative | JODI   PUBLISHED DATETIME: 2019-05-29 About JODI Jodi World Databases Worldwide Support For JODI JODI FAQs Capacity Building JODI Manuals JODI-Oil Participating Economies Participation Assessment JODI-Oil Support JODI-Oil User Guide JODI-Oil Manual Update Calendar JODI-Oil FAQs History of JODI-Oil Customisable Charts Country By Country Review Data Downloads JODI-Oil Questionnaire JODI-Gas Participating Economies Participation Assessment JODI-Gas Support JODI-Gas User Guide JODI-Gas Manual JODI-Gas FAQs History of JODI-Gas Data Dashboards Data Downloads JODI-Gas Questionnaire JODI Forum News & Events JODI in the Media Events & Conferences Papers & Reports JODI Logos Image Gallery JODI TV JODI Manuals # History ## Historical Background: JODI and Oil Data Back in the late 1990s, Energy Ministers identified the lack of transparent and reliable oil statistics as a key contributor to oil price volatility. Producers and consumers alike stepped up efforts to improve the availability and reliability of oil data, and Ministers at the 7th International Energy Forum in Riyadh urged a global response to the challenge of greater transp
```

### V1b C0 → PASS
```
True. The Gas Exporting Countries Forum (GECF) joined as a JODI partner in 2014, which helped JODI-Gas cover nearly 90% of the global natural gas supply and demand.
```

### V1b `T8-aggrefact-inv` → PASS
```
True. The Gas Exporting Countries Forum (GECF) joined as a JODI partner in 2014, which helped JODI-Gas cover nearly 90% of the global natural gas supply and demand.
```

## 9. `AF034028` (Reveal) label=0

- Evidence tokens (raw doc): **109** (chars 345)
- User message tokens (doc+claim C0): **144**; chat prompt tokens: **321**
- Conversion note: unit_pair=million↔billion edit_kind=scale

### Original claim (C0)
```
The Netherlands had a population of 1.9 million in 1581.
```

### INV claim
```
The Netherlands had a population of 1900 billion in 1581.
```

### E1-unit (claim unchanged; edited evidence excerpt)
```
claim: The Netherlands had a population of 1.9 million in 1581.
---
evidence: Van Gogh Museum, Visitors. Since 2000, the museum had between 1.2 and 1.9 million visitors per year. From 2010 to 2012, it was the most visited museum in the Netherlands. In 2015, the museum had 1.9 million visitors, it was the 2nd most visited museum in the Netherlands, after the Rijksmuseum, and the 31st most visited art museum in the world.
```

### V1b C0 → PASS
```
True. The Netherlands had a population of approximately 1.9 million in 1581.
```

### V1b `T8-aggrefact-inv` → FAIL
```
False. The population of the Netherlands in 1581 was not 1900 billion. Such a number is far beyond any historical population figures for that time period.
```

## 10. `AF033625` (Reveal) label=1

- Evidence tokens (raw doc): **115** (chars 432)
- User message tokens (doc+claim C0): **147**; chat prompt tokens: **324**
- Conversion note: unit_pair=km↔m edit_kind=length

### Original claim (C0)
```
The radius of the Moon is 1737.4 km.
```

### INV claim
```
— (no INV row for base)
```

### E1-unit (claim unchanged; edited evidence excerpt)
```
claim: The radius of the Moon is 1737.4 km.
---
evidence: Topography of the Moon, Reference elevation: The Moon obviously lacks any mean sea level to be used as vertical datum. The USGS's Lunar Orbiter Laser Altimeter (LOLA), an instrument on NASA's Lunar Reconnaissance Orbiter (LRO), employs a digital elevation model (DEM) that uses the nominal lunar radius of 1,737400 m (1,079.6 mi). The selenoid (the geoid for the Moon) has been measured gravimetrically by the GRAIL twin satellites.
```

### V1b C0 → PASS
```
True. The radius of the Moon is 1,737.4 km.
```

### V1b `T8-aggrefact-e1-unit` → PASS
```
True. The radius of the Moon is 1,737.4 km.
```

## 11. `AF030660` (AggreFact-CNN) label=1

- Evidence tokens (raw doc): **861** (chars 3786)
- User message tokens (doc+claim C0): **939**; chat prompt tokens: **1116**
- Conversion note: unit_pair=hours↔minutes edit_kind=time

### Original claim (C0)
```
`` it seems he survived by sheer willpower , '' says a doctor who treated rishi khanal . khanal , 27 , suffered a crushed foot and was too weak to talk about his traumatic experience . a 4-month-old baby was rescued 22 hours after the quake struck .
```

### INV claim
```
`` it seems he survived by sheer willpower , '' says a doctor who treated rishi khanal . khanal , 27 , suffered a crushed foot and was too weak to talk about his traumatic experience . a 4-month-old baby was rescued 1320 minutes after the quake struck .
```

### E1-unit (claim unchanged; edited evidence excerpt)
```
claim: `` it seems he survived by sheer willpower , '' says a doctor who treated rishi khanal . khanal , 27 , suffered a crushed foot and was too weak to talk about his traumatic experience . a 4-month-old baby was rescued 22 hours after the quake struck .
---
evidence: Kathmandu, Nepal (CNN)Rescuers in Nepal have pulled a man from the wreckage of a building where he was stuck for a staggering 82 hours after the devastating earthquake that hit the country Saturday. His survival is unusual, as experts say it's rare for injured people who are trapped to hold out for longer than 72 hours after a disaster. The man, Rishi Khanal, was saved after a French search and rescue team found him under the rubble on the outskirts of Kathmandu, the capital, around noon Tuesday, said Pushparam K.C., a spokesman for the Armed Police Force of Nepal. The team used specialized gear that detects signs of life, he said. But it took about 10 more hours for the French team and police officers to dig him out, the spokesman said. A police video of the rescue showed the teams drilling through concrete to reach Khanal's location and then hauling him up through the hole. They then carried him out of the ruined building on a stretcher. On Wednesday afternoon, Khanal, 27, had just undergone surgery and was resting, surrounded by family and friends. He had suffered a crushed foot and was too weak and distraught to talk about his traumatic experience. "It seems he survived by shee
```

### V1b C0 → PASS
```
True. The statement accurately reflects the information provided in the context. Rishi Khanal, who is 27 years old, survived with a crushed foot and was too weak to talk about his experience. Additionally, a 4-month-old baby was indeed rescued 22 hours after the earthquake struck.
```

### V1b `T8-aggrefact-inv` → PASS
```
True. A 4-month-old baby was rescued 1,320 minutes (which is 22 hours) after the quake struck, as mentioned in the context.
```

## 12. `AF030204` (RAGTruth) label=1

- Evidence tokens (raw doc): **467** (chars 2026)
- User message tokens (doc+claim C0): **521**; chat prompt tokens: **698**
- Conversion note: unit_pair=hours↔minutes edit_kind=time

### Original claim (C0)
```
After the adhesive has been given 24 hours to dry, the extensions can last up to six weeks or more, depending on the growth cycle and speed of your lashes.
```

### INV claim
```
After the adhesive has been given 1440 minutes to dry, the extensions can last up to six weeks or more, depending on the growth cycle and speed of your lashes.
```

### E1-unit (claim unchanged; edited evidence excerpt)
```
claim: After the adhesive has been given 24 hours to dry, the extensions can last up to six weeks or more, depending on the growth cycle and speed of your lashes.
---
evidence: {'question': 'how to eyelash extensions work', 'passages': "passage 1:Avoid touching your lashes, picking, pulling or rubbing your lashes can potentially damage not only your lash extensions, but your natural lashes as well. Avoid extensive exercise the day of application. Avoid saunas and steam rooms 48 hours after application. The heat will cause the bond to weaken.void getting your lashes wet for 24 hours after application allowing the adhesive bond to fully dry. Use only OIL –FREE products on and around the eyelashes(including make-up remover, mascara and eyeliner). Use special care around the eye area applying gentle and light pressure when washing or drying the face.\n\npassage 2:What To Know Before You Get Eyelash Extensions. Women spend millions of dollars each year trying to get longer, lusher, fuller lashes. While mascara may be enough for many, some women just didn't score the genetic jackpot when it comes to long lashes.hat are the downsides? While this process is generally considered safe, there are some things you should be aware of before you decide to commit to lash extensions. 1  Cost – This process is not cheap! 2  You can spend anywhere from $120 to $500 for a se
```

### V1b C0 → PASS
```
True. After the adhesive has been given 24 hours to dry, eyelash extensions can last up to six weeks or more, depending on the growth cycle and speed of your lashes.
```

### V1b `T8-aggrefact-inv` → PASS
```
True. After the adhesive has been given 1440 minutes (which is 24 hours) to dry, the extensions can last up to six weeks or more, depending on the growth cycle and speed of your lashes.
```

## 13. `AF030881` (AggreFact-CNN) label=0

- Evidence tokens (raw doc): **1207** (chars 4930)
- User message tokens (doc+claim C0): **1296**; chat prompt tokens: **1473**
- Conversion note: same_value_diff_unit_token: `300 g` vs `300g`

### Original claim (C0)
```
Fortnum & Mason's Chotch Egg is the world ’s first gourmet chocolate Scotch egg. The Wyke Farms Cheaster Egg is two feet tall and made with 300 g of award winning cheddar. Godiva's Alter Eggo can be made at stores or customised with hair, eyes and a smile.
```

### INV claim
```
— (no INV row for base)
```

### E1-unit (claim unchanged; edited evidence excerpt)
```
claim: Fortnum & Mason's Chotch Egg is the world ’s first gourmet chocolate Scotch egg. The Wyke Farms Cheaster Egg is two feet tall and made with 300 g of award winning cheddar. Godiva's Alter Eggo can be made at stores or customised with hair, eyes and a smile.
---
evidence: They are the chocolate treats we most look forward to at Easter, and in Britain alone more than 90 million of them are consumed every year. But this year traditional Easter eggs have undergone a dramatic makeover, appearing on supermarket shelves and restaurant menus made of meat, Marmite - and a giant block of cheese. Grab your egg-cups as we take a look at the most bonkers eggs in Britain... Fortnum & Mason's Chotch Egg is the world’s first gourmet chocolate Scotch egg. Would you eat this? The Marmite chocolate egg has a strong, rather beefy aftertaste . From yeast-flavoured chocolate (we're looking at you, Marmite) to an egg made from 300g of Cheddar, here is FEMAIL's selection of the most unusual eggs you can try this Easter. Love me, Hate me, Break Me -  the Marmite Easter Egg, £5. A Marmite chocolate egg made with the love-it-or-hate it spread accompanied with Marmite Cashew nuts makes for a fun Yeaster treat. This beefy-tasting egg divided the FEMAIL team with some enjoying the depth of flavour from the savour extract that flavours the chocolate while others couldn't stomach the strange tangy-sweet combination. . Chocolate Egg and Soldiers, £7.99 . Choc n Choc's ingenious in
```

### V1b C0 → PASS
```
True.
```

### V1b `T8-aggrefact-e1-unit` → PASS
```
True.
```

## 14. `AF005419` (Reveal) label=1

- Evidence tokens (raw doc): **257** (chars 943)
- User message tokens (doc+claim C0): **288**; chat prompt tokens: **465**
- Conversion note: scale_or_plain_format: `7000 million` vs `7.4 billion`

### Original claim (C0)
```
The human race can reach a population of 7 billion people.
```

### INV claim
```
The human race can reach a population of 7000 million people.
```

### E1-unit (claim unchanged; edited evidence excerpt)
```
claim: The human race can reach a population of 7 billion people.
---
evidence: World population milestones: It is estimated that the population of the world reached one billion for the first time in 1804. It would be more than 100 years before it reached two billion in 1927, but it took only 33 years to reach three billion in 1960. Thereafter, the global population reached four billion in 1974, five billion in 1987, six billion in 1999 and, by some estimates, seven billion in October 2011 with other estimates being in March 2012. It is projected to reach eight billion by 2023–2027, nine billion by 2037–2046, and ten billion by 2054-2071, with alternative scenarios ranging from a low of 7.4 billion to a high of more than 10.6 billion by the 2050s and beyond. Projected figures vary depending on underlying statistical assumptions and which variables are manipulated in projection calculations, especially the fertility variable. Long-range predictions to 2150 range from a population decline to 3.2 billion in the
```

### V1b C0 → PASS
```
True. The human race reached a population of 7 billion people around October 2011, with some estimates placing it in March 2012.
```

### V1b `T8-aggrefact-inv` → PASS
```
True. The human race reached a population of 7,000 million (or 7 billion) people around October 2011, with some estimates placing it in March 2012.
```

## 15. `AF024852` (RAGTruth) label=1

- Evidence tokens (raw doc): **460** (chars 2044)
- User message tokens (doc+claim C0): **497**; chat prompt tokens: **674**
- Conversion note: unit_pair=hours↔minutes edit_kind=time

### Original claim (C0)
```
Over the course of more than two years, they shot over 50 hours of footage.
```

### INV claim
```
Over the course of more than two years, they shot over 3000 minutes of footage.
```

### E1-unit (claim unchanged; edited evidence excerpt)
```
claim: Over the course of more than two years, they shot over 50 hours of footage.
---
evidence: David Beckham: The Victoria Documentary on Netflix was a "Hell" and an "Emotional Roller Coaster."
The completion of filming his Netflix documentary with his wife Victoria Beckham has delighted David Beckham.
During the David Beckham Fragrances Launch Party at the popular restaurant Torrisi in New York City, the former soccer player shared details about the project.
David said to People on Wednesday, "It was a series that took me a while to come to terms with filming, and talking about my life." "And when I decided to retire from playing soccer ten years ago, I wasn't really prepared to look back and talk about my career and my life," the speaker said.
Over the course of more than two years, the athlete and former Spice Girl shot more than 50 hours for "Beckham," which David described as a "hell of a journey."
Over the past 2.5 years, he said, "it wasn't easy and it was an emotional roller coaster, but I think we've produced something that my team can be very proud of."
Ahead of his retirement's tenth anniversary, he felt it was "the right time" to share his tale, even though he stated that he "was ready to move on straight away" after retirement to concentrate on his business ende
```

### V1b C0 → PASS
```
True. Over the course of more than two years, they shot more than 50 hours of footage for the documentary "Beckham."
```

### V1b `T8-aggrefact-inv` → PASS
```
True. Over the course of more than two years, they shot more than 50 hours of footage, which is equivalent to over 3000 minutes.
```
