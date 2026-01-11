# GM Kit Development Journal.md

## 11-12-2025 Spec-kit, mcps and next steps. 

One thing I’m seeing with spec-kit is the rigor that the process and the agent use to produce the proper output. There is a large list of checks that are created for each stage of the process to ensure the AI stays focused on the feature and delivers the proper artifacts.  From this writeup:

[https://github.com/github/spec-kit/blob/main/spec-driven.md](https://github.com/github/spec-kit/blob/main/spec-driven.md)

The spec is now the new code and the checklists are the “unit tests” that ensure there is no regression in the spec.  

But what are these checklists and how are they designed?  To really understand how to use spec-kit, we need to look under the covers. So I've added a new todo list (listed under "Spec-kit Archetecture Analysis") for this step.

## 11-23-2025 New thoughts on gm-kit (gm-assist) 

As per my 11-12 journal, I’ve been thinking  a lot about gm-kit from my work working through the “No Matter How Small” scenario for Werewolf: The Apocalypse.  Right now I’ve created a series of prompts to create the specs.  But as I’m prepping the W5 scenario, there are a few things I realize I need to consider/change for my prompts and specs to work:

* Once the distilled document is created and validated by the AI, Linking or referencing the original md/pdf is kind of a devils bargain and is ultimately limiting.  The AI can track all of that for you, so why keep it?  When using GM-KIT, the gm should decide completely what the final structure will be. Like surge-bench, the gm-kit is more of a work bench where you can take a scenario, tear it down and rebuil it to your liking.  What does that look like, a bunch of input/output schemas as context/specs as per Kelsey Dionne's approach in her Arcane Library DnD modules.  

* Output is markdown and only markdown, but it doesn’t have to be.  Just update the schemas to the format you prefer.  As long as it’s an open standard, you are good to go.

Also, what is the goal of project:

* To allow GM’s to quickly and thoroughly generate their prep elements/artifacts into a cohesive structure that provides complete confidence at the table.   
  * At a minimum, the prep materials should look like the published DnD  scenarios from Arcane Library (So Skyhorn Lighthouse, Temple of the Basilisk Cult, etc).  Here is a quick analysis of the format and output: [https://chatgpt.com/share/6923836e-20c0-8010-862f-8b96fba99799](https://chatgpt.com/share/6923836e-20c0-8010-862f-8b96fba99799)  
    * Looking at Kelsey’s approach it’s so much better than mine and more minimal.  She combines my social encounter and my character details into a single artifact: the character detail.   The reason she does this is because she doesn’t have to worry about what the character has to say or do outside of the single encounter the character has been placed in.  She keeps the description simple with three:  Appearance, Does, Secret.  The secret gives just enough detail to infer objections and motivations.  
      * What this means is that there is a distinct difference between translating/transforming a published dungeon and generating one from scratch.  The generated one doesn’t necessarily have a clue-flow plot structure defined. You can’t just randomly generate a clue flow can you?  I imagine if you prompted right (so using the 100 plot hook list and the 5 scene grid, you could).  This makes me realize we need to build the tools that perform the transformation and then build out any tools that will fill in the gaps for anything the source material usually provides (so a basic plot structure, rewards, characters or events that tie each structure together, and a way to to   
    * A few  more notes:    
      * For each page she uses a simple three part pattern to break down the elements of a scene.  A scene  is basically:   
        * **Approaching the…**: Arriving at a location and orientation   
        * **Developments (the problem):** Research/Investigation and then the change or twist that introduces a problem to solve.    
        * **(The solution):**  The solultion is broken down into two basic choices: a **COMBAT**  or **SKILL CHALLENGE**     
          * **COMBAT:** Includes, triggers, developments and exit ramps for villains.  
          * **SKILL CHALLENGE:**  usually contains a skill ladder(this can be called TALK IT OUT/DISCUSSION for socials, or  “THE TRAP”, or “ESCAPE\!”, “CHASE\!”, etc or similar. But it’s basically  a skill challenge.  
            * For socials any dialog is provided via the included character details ON THE SAME  PAGE.  So every character get’s only a single starring moment, but we don’t have to be religious about that.  
      * If there are details added that distract from story prep (prep notes, additional rules, guidelines for how to roleplay), then add a hyperlink called “Errata” or Non-Essential with any details.  The AI or GM can decide if it’s needed or not.  But since we are going to completely remap the adventure, better to just jettison.  But there may be some edge cases where additional information may sit on the fence between necessity or noise.  Anything like that goes here.  
      * For the “No Matter How Small” scenario, there are a lot of gaps due to handwaving.  But using Kelsey’s approach with transitions and also the clue route diagram get you most of the way there. The gaps are more in the detail layer.  So this version may fit better with Kelsey’s format which definitely has specifics but not at the detail level of my own stuff.    
      * We may need to provide a second pass effort where every detail can be locked down and/or generated. But I think this is version 2 stuff.   
      * Looking at Kelsey’s plots,  they aren’t that complex, so we may have to evolve our level of detail for complex plots.  
      * Interestingly she ~~doesn’t~~ include wandering monsters, but she deals with surprises in the Developments section.  (UPDATE: She does in Temple of the Baslisk Cult but it’s a anomaly),  
      * One final note:  Unless completely empty, I think we should treat every room in a dungeon as its own location or scene, skipping the Dramatic Question if it’s obvious but always providing transition(s) to joining rooms.  
    * Consider an option that anonymizes the details of the story:   
      * So Borlandia becomes “THE KINGDOM”,  Chiltony is “THE CAPITAL”, etc.   This seems a bit too tweaky to me.  Something to think about.  
  * You can create a basic template that allows this level of detail and then add additional elements based on how detailed you want to go.  So for the big boss fight you may want the most thorough encounter available.  Maybe instead of small, medium, large you have min, med, and max?   
  * For ensuring the story moves forward she adds the “Dramatic Question” and the Transition (which points to the next scene). We could combine this with the plot flowchart and would be golden.  
* To allow generation via AI or via transformation from a published scenario using AI.

A few more things to keep in mind:;

* The GM should not have to read an entire module to begin the translation. Ideally they read the background details, previous events and the synopsis (if available, if not: have the AI generate a synopsis).  Then the AI should generate the clue-flow-diagram to ensure they know how the original story is arranged.  At that point (and as a first pass),  he can restructure the plot, fix any clue-flow blockages as he needs.  Then on the second pass, start drilling down into specifics (so translating or creating elements).

## 12-20-2025 Spec-kit Architecture Analysis  

I've begun the architecture analysis documentation.  For now I've placed in the subfolder spec-kit-analysis under this folder.  I may move  it later but that's good for now. 

##  01-09-2026 Great video that explains in detail the two ends of the spectrum dungeon prep format and approach  

[Is Goodman Games Cooked?](https://youtu.be/KwhuwpFAlcg)

This channel understands the problem most DMs face with prepping a published scenario or dungeon.  He compares two different dungeons: 

- The revised "Caverns of Thracia" mega dungeon (authored by Janelle Jaquays and re-published by Goodman Games)
- "The Devoured Labrinth" a mega dungeon for Shadowdark.

According to the vlogger, both have their pros and cons but both are missing specific details that would make it easier for a DM to run the game. 

- Most glaringly is with Caverns of Thracia, which chose to present the entire dungoen in the original 1979(!!!) format.  The density of the information on the page is unbelievablely difficult to manage at the table.  Your definitely better off highlighting the details you need or converting the entire dungeon into abbreviated notes in a format that is readable (I think you can see where this is going). 
- But Devoured Labrinth has it's own issues, specifically the reduced (51 words!!!) backstory for the dungeon and stripped down prep notes that don't provide enough detail to make the dungeon compelling.  He also complains about the generic random encounter tables that don't reflect the factions or the ecosystem of the dungeon in a particularlly compelling fashion. Again, these are the kind of complaints I'm hoping gm-kit will address.

So I think it makes sense to consider using both of these dungeons as test modules for appllying to gmkit.  If everything goes right, gmkit should be able to convert the dungeon into a bullet pointed outline of keyed pages, one for each room in the dugeon for COT. On the other hand, it should be able to analyze TDL to create a meaningful backstory, analyze the factions, establish their goals and rivalries, increase the vividness of the encounters, maybe provide boss tactics and fix the random encounter tables.  

One reduces the prep notes significantly, while the other increases the size a bit but also adds needed context. 

## 01-09-2025 Creating a prep preference wizard for gmkit 

I saw this video:  [Shadow Dark's City Sandbox is INCREIBLE!](https://youtu.be/mi8a-l-nY9Y).  

It looks like the schema for some of the stats (npc descriptions in particular) have changed in this zine from the work Kelsey Dionne was doing with her Arcane Library 5e adventures on DMs guild.  This makes me think there is no obvious standard for these schemas, it just depends on what the publisher wants vs what the gm prefers.  So I think it may be a good idea to create a "Prep Schema Wizard" that the GM can walk through to establish formats. Since all of the scripts are powershell or bash, as long at the AI is capable, we should be able to have the AI show differernt prep formats/schemas, allow the user to select and/or refine and then that format will be used when generating the prep artifacts.   

## 01-09-2025 The Black Wyrm of Brandonsford: Another great example of a lighweight sandbox/dungeon scenario for OSR games 

- Here's the youtube review (note how he describes the clue path at the end of the video, this is gold for verifying gm-kit's clue path analysis)
  - https://tenfootpole.org/ironspike/?p=7349
- Here's where to buy the pdf
  - https://www.dmsguild.com/en/product/327744/the-black-wyrm-of-brandonsford
- Another rave review from Ten Foot Pole
  - https://tenfootpole.org/ironspike/?p=7349

  A few thoughts:
    - Instead of using AI to generate his artwork, he's using images from the public domain.  Another reason to investigate the images from here:
      - https://www.youtube.com/@petebeard
      - Particularly : GUSTAF TENGGREN
        - Here is one of his books at he library  of congress: https://tile.loc.gov/storage-services/public/gdcmassbookdig/redfairybook00lang_1/redfairybook00lang_1.pdf
    - The scenario's layout is excellent.  Location and Characters descriptions are terse but descriptive, The structure of the encounters, the stat blocks, etc. Everyhing is there but with no wasted text.
    - Interesting how the clues, the secrets, the allies and the magic items prepare the party for battling the dragon.  This could be another aspect of our clue path analysis that needs to be considered for gm-kit's design.  
      - GOLDMINE: Maybe another analysis is in order?:  The **Party Success Path Analysis**, ensuring they have everything they need to avoid a TPK or critical failure.  ADDITIONALLY: What if the party needs a specific class/archetype to complete the quest and they don't have one?  How to revise the story so it works (so adding magic items to fill in the missing cleric feats, adding npc's to fill in for the missing class, changing the monster or the monster's weaknesses to something manageable)? 
    - GOLDMINE: Ooh another one:  The **Emotional Investment Path Analysis**?  What elements in the story increase the PC's motivation to complete the quest?  How do the encounters that take place before reaching the dragon scare them, anger them, or motivate them to complete the quest? These can include the carrots (treasure/magic items), the sticks (survival, revenge), aligned goals (as defined by the players for their characters) and aligned values (what will they not abide or endure -- for themselves and for others?.  Sometime all of them want treasure, magic items, etc. But usually each player has a different motivation.
    - ADDITIONALLY: Determining if the module's tone fits the PCs expectations.  Do they want old school high fantasy (Tolkien, etc), gonzo scifi (so OSE), deadly baleful worlds full of desperate elements (so Howard, Leiber), or demonic/cosmic horror and existential dread (Lovecraft, Stoker).  Trying to customize or modify a module to those elements requires a writing partner to help manage the details.
    - GOLDMINE:  **Monster Prepifier**: inspired by Matt Colville's Action Oriented Monsters discussion and also RUnehammer's "Build AI for your Monsters":
      - [Action Oriented Monsters](https://youtu.be/y_zl8WWaSyI)
      - [Build an AI for your Monters](https://www.youtube.com/watch?v=jc9OBmy8Sag)
      - What does it do?
        - It takes a weak statblock and description and makes it effortlessly playable at the table.
        - It gives a tactic AI mechanic to follow at the table for the emonster.
        - It embeds elegant descriptions into each monster stat.
          - First Look, Actions as descriptions.
      - Looking at Colville and Runehammer's discussion this tool should really be considered for bosses.  But a 5th level boss looks like a mook to a 10th level party.  So it may be a moot point.
    -Also, **Symbiotic Monsters** (or as Rune Hammer indicates:  [Monster Sets](https://youtu.be/SnXuQmZNKus)
      - How to make the combination of two monsters compelling?  I remember how the Otyugh and Mimic combination worked so well.
      - How to create advantages/disadvantages when monster set members work together?
        - If you notice, Matt Colville's Goblin Boss (Action Oriented Monsters link) has a lot of similarities with Runehammer's Oath Readers (from the "Monster Sets" link above). Both empower there minions, both are the weak point for defeating the minions.
 
## 01-09-2026 Another feature to consider - Vision impared pdf conversion 

- So providing guidance on how to print the zine in a larger format?  Probably a good idea. 

## 01-11-2026 Challenge of the Frog Idol: Another well structured/well formatted dungeon 

https://tenfootpole.org/ironspike/?p=1121

24 pages, with a hex crawl and two dungeons.  Tenfoot pole liked the structure, the scale and scope and evocative but succinct descriptions.  Since it's free, this could be a great candidate as an example of a good scenario/adventure.

ALSO:  Just search in this list for "free": https://tenfootpole.org/ironspike/?page_id=844.  Don't forget to search the contents, a few gems in their as well.

Ideally, we need a classic module that is short but way too verbose that we can convert into a bullet point outline as a prime example on how to improve/convert/revise it.  Maybe I can ask around on tenfootpole.org for an adventure that is free, creative commons, legendary, but rough around the edges (too verbose, incorrectly structured?  I could as if anyone has actually fixed a dungeon that has these issues before as well.  I joined the forum today.

## 01-11-2026 Another attempt at a shorthand/statblock reduction approach 

From this video: https://youtu.be/khgQ5q1sfNI

As with a lot of the modules ten foot pole, likes, this guy is on the right track, but who has time to convert 256 pages?  The one thing I kind of liked was his shorthand mechanism for poison saving throws.  I'll need to revisit it and see if it's of actual value.

## 01-11-2025 A few more things to add to the backlog:

1. A documentation portal on github with proper user documentation.  This should align with and replace what is in docs/user/user_guide and we should use this as our cononical source of project truth.  But it should also meet the actual needs of the user. Any code related documentation found in the user_guide.md file should be moved to the docs/team folder.
