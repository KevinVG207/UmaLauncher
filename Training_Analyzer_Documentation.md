# Uma Launcher - Training Analyzer CSV Documentation
Many thanks to Kawaii Shadowii for writing this up.
## <span style="text-decoration:underline;">Columns:</span>

* **Run:**
    * _Only exists when multiple runs get generated in one CSV._
    * Differentiates all the runs included in the CSV by numbering them sequentially.
* **Scenario:**
    * Shows the scenario that the run was done in
* **Chara:**
    * Shows the character used in the run.
    * The name in square brackets corresponds to the outfit name.
* **Support 1-6:**
    * Shows the support cards in your deck.
    * The number before the name of the support card is the game's internal ID of the support card.
* **Turn:**
    * Show what turn of the run the action took place on.
* **Action:**
    * Shows you the type of action.
    * The following actions currently exists:
        * Start
        * End
        * Training
        * Event
        * Race
        * SkillHint
        * BuySkill
        * Rest
        * Outing
        * Infirmary
        * GoddessWisdom (Grand Master only)
        * BuyItem (MANT only)
        * UseItem (MANT only)
        * Lesson (Grand Live only)
        * AfterRace
        * Continue
        * AoharuRaces (Aoharu Cup only)
        * SSMatch (Project L'Arc only)
    * _If an action shows up as "Unknown", please let us know on the [Discord server](https://discord.gg/wvGHW65C6A) and provide us with your training run's gzip file._
* **Text:**
    * Contains additional text-based info about the action type:
        * <span style="text-decoration:underline;">Action Type "Start":</span>
            * [GameTora Training Event Helper](https://gametora.com/umamusume/training-event-helper) link with the pre-selected character and support cards
        * <span style="text-decoration:underline;">Action Type "Training":</span>
            * Selected training facility
        * <span style="text-decoration:underline;">Action Type "Event":</span>
            * Event name
        * <span style="text-decoration:underline;">Action Type "Race":</span>
            * Race name
        * <span style="text-decoration:underline;">Action Type "SkillHint":</span>
            * Name of the character whose skill hint event triggered
        * <span style="text-decoration:underline;">Action Type "Outing":</span>
            * Name of the character/support card you went on an outing with
        * <span style="text-decoration:underline;">Action Type "GoddessWisdom":</span>
            * Name of the goddess whose wisdom was activated
        * <span style="text-decoration:underline;">Action Type "BuyItem":</span>
            * Names of the bought items
            * Separated by | (pipe symbol)
        * <span style="text-decoration:underline;">Action Type "UseItem":</span>
            * Names of the used items
            * Separated by | (pipe symbol)
        * <span style="text-decoration:underline;">Action Type "AfterRace":</span>
            * Race name
        * <span style="text-decoration:underline;">Action Type "AoharuRaces":</span>
            * Amount of wins, losses and draws
* **Value:**
    * Contains additional value-based info about the action type:
        * <span style="text-decoration:underline;">Action Type "Training":</span>
            * Fail percentage on the selected training facility
        * <span style="text-decoration:underline;">Action Type "Event":</span>
            * _Only for event with multiple choices_
            * Shows which choice you picked
                * 1 = first option
                * 2 = second option
                * etc.
        * <span style="text-decoration:underline;">Action Type "Race":</span>
            * Position that you finished in
        * <span style="text-decoration:underline;">Action Type "GoddessWisdom":</span>
            * Level of the selected goddess wisdom
        * <span style="text-decoration:underline;">Action Type "AfterRace":</span>
            * Final position that you finished in after continues
        * <span style="text-decoration:underline;">Action Type "Continue":</span>
            * Type of continue
                * 1 = daily free continue
                * 2 = normal continue which uses a clock
        * Action Type "SSMatch"
            * Type of SS Match
                * 1 = SS Match
                * 2 = SSS Match
* **SPD:**
    * Shows your speed stat at that moment.
* **STA:**
    * Shows your stamina stat at that moment.
* **POW:**
    * Shows your power stat at that moment.
* **GUT:**
    * Shows your guts stat at that moment.
* **INT:**
    * Shows your wisdom stat at that moment.
* **SKLPT:**
    * Shows your amount of skill points at that moment.
* **ERG:**
    * Shows your amount of energy left at that moment.
* **MOT:**
    * Shows your motivation at that moment.
* **FAN:**
    * Shows your amount of fans at that moment.
* **ΔSPD:**
    * Shows the change of the speed stat from this action.
* **ΔSTA:**
    * Shows the change of the stamina stat from this action.
* **ΔPOW:**
    * Shows the change of the power stat from this action.
* **ΔGUT:**
    * Shows the change of the guts stat from this action.
* **ΔINT:**
    * Shows the change of the wisdom stat from this action.
* **ΔSKLPT:**
    * Shows the change of the amount of skill points from this action.
* **ΔERG:**
    * Shows the change of the amount of energy left from this action.
* **ΔMOT:**
    * Shows the change of the motivation from this action.
* **ΔFAN:**
    * Shows the change of the amount of fans from this action.
* **Skills Added:**
    * Shows all skills that were added from this action
    * Separated by | (pipe symbol)
* **Skills Removed:**
    * Shows all skills that were removed from this action
    * Separated by | (pipe symbol)
* **Skill Hints Added:**
    * Shows all skill hints that were added from this action
    * Separated by | (pipe symbol)
* **Statuses Added:**
    * Shows all status effects that were added from this action
    * Separated by | (pipe symbol)
* **Statuses Removed:**
    * Shows all status effects that were removed from this action
    * Separated by | (pipe symbol)