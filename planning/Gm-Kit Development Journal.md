**11-12-2025 Spec-kit, mcps and next steps.**

One thing I’m seeing with spec-kit is the rigor that the process and the agent use to produce the proper output. There is a large list of checks that are created for each stage of the process to ensure the AI stays focused on the feature and delivers the proper artifacts.  From this writeup:

[https://github.com/github/spec-kit/blob/main/spec-driven.md](https://github.com/github/spec-kit/blob/main/spec-driven.md)

The spec is now the new code and the checklists are the “unit tests” that ensure there is no regression in the spec.  

But what are these checklists and how are they designed?  To really understand how to use spec-kit, we need to look under the covers. So I've added a new todo list (listed under "Spec-kit Archetecture Analysis") for this step.

**11-23-2025 New thoughts on gm-kit (gm-assist)**

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
        * ***“Approaching the…”***: Arriving at a location and orientation   
        * ***Developments (the problem):*** Research/Investigation and then the change or twist that introduces a problem to solve.    
        * **(The solution):** The solultion is broken down into two basic choices: a **COMBAT** or **SKILL CHALLENGE**    
          * ***COMBAT:*** Includes, triggers, developments and exit ramps for villains.  
          * **SKILL CHALLENGE:  usually contains a skill ladder(this can be called TALK IT OUT/DISCUSSION**  for socials, or  “THE TRAP”, or “ESCAPE\!”, “CHASE\!”, etc or similar. But it’s basically  a skill challenge.  
            * For socials any dialog is provided via the included character details ON THE SAME  PAGE.  So every character get’s only a single starring moment, but we don’t have to be religious about that.  
      * if there are details added that distract from story prep (prep notes, additional rules, guidelines for how to roleplay), then add a hyperlink called “Errata” or Non-Essential with any details.  The AI or GM can decide if it’s needed or not.  But since we are going to completely remap the adventure, better to just jettison.  But there may be some edge cases where additional information may sit on the fence between necessity or noise.  Anything like that goes here.  
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
