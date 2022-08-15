# The Command Line Murders Machine

Script for generating a new/customized set of "Command Line Murders" evidence and environment files.

## How `clmystery` Works

The steps in solving Noah Veltman's original `clmystery` case are as follows:

1. use `grep CLUE mystery/crimescene` to indentify the clues scattered among random Alice in Wonderland quotes
    
    ```
    CLUE: Footage from an ATM security camera is blurry but shows that the perpetrator is a tall male, at least 6'.
    CLUE: Found a wallet believed to belong to the killer: no ID, just loose change, and membership cards for AAA, Delta SkyMiles, the local library, and the Museum of Bash History. The cards are totally untraceable and have no name, for some reason.
    CLUE: Questioned the barista at the local coffee shop. He said a woman left right before they heard the shots. The name on her latte was Annabel, she had blond spiky hair and a New Zealand accent.
    ```

2. use `grep Annabel mystery/people` to discover address information for all "Annabel"-named people:

    ```
    Annabel Sun     F       26      Hart Place, line 40
    Oluwasegun Annabel      M       37      Mattapan Street, line 173
    Annabel Church  F       38      Buckingham Place, line 179
    Annabel Fuglsang        M       40      Haley Street, line 176
    ```

    Note two males, leaving two females to investigate.

3. use `head -n LINE_NUMBER mystery/streets/STREET_NAME | tail -n 1` to "go visit" these persons of interest

    ```
    SEE INTERVIEW #47246024
    SEE INTERVIEW #699607
    ```

4. use `cat mystery/interviews/interview-INTERVIEW_NUMBER` to follow up on those two interviews

    ```
    # interview 47246024
    Ms. Sun has brown hair and is not from New Zealand.  Not the witness from the cafe.

    # inteview 699607
    Interviewed Ms. Church at 2:04 pm.  Witness stated that she did not see anyone she could identify as the shooter, that she ran away as soon as the shots were fired.

    However, she reports seeing the car that fled the scene.  Describes it as a blue Honda, with a license plate that starts with "L337" and ends with "9"
    ```

5. use `grep -A 4 "L337.*9$" vehicles | grep -A3 "Honda" | grep -A2 "Blue"` to find suspects driving such cars

    ```
    Color: Blue
    Owner: Erika Owens
    Height: 6'5"
    --
    Color: Blue
    Owner: Aron Pilhofer
    Height: 5'3"
    --
    Color: Blue
    Owner: Heather Billings
    Height: 5'2"
    --
    Color: Blue
    Owner: Joe Germuska
    Height: 6'2"
    --
    Color: Blue
    Owner: Jeremy Bowers
    Height: 6'1"
    --
    Color: Blue
    Owner: Jacqui Maher
    Height: 6'2"
    ```

    Females (cross-ref from `people`) and/or too-short people are out, leaving Joe Germuska and Jeremy Bowers as suspects.

6. use `cat mystery/memberships/AAA mystery/memberships/Delta_SkyMiles mystery/memberships/Terminal_City_Library mystery/memberships/Museum_of_Bash_History | grep -c "SUSPECT_NAME"` to see which of the suspects has all 4 memberships (remember the wallet found?)

    only Jeremy Bowers has all 4


## Constructing a New Mystery

By "new mystery" we mean simply a different perpetrator; i.e., the solving process remains the same, but the answer differs.
This limitation in novelty is intentional: the original is well-designed to teach a progression in CLI skills, but we don't want each student to end up with a unique answer/suspect (both for the gratification of actually _solving_ something and to minimize cheating).

### Seed Files

We cannot use the existing `people`, `vehicles`, and `memberships/` files as-is (as-are?).
The data is too well randomized: the only license-plate numbers that could provide ambiguity and require membership matching appear to be specially-crafted for the "Jeremy Bowers" perpetrator from the original mystery.

Instead, we will harvest the following data from the original seed files:

* first names (male), with popularity count
* first names (female), with popularity count
* last names (unified), with popularity count
* car make
* car color
* street names (the actual street files; not all the street names in `people` actually had street files)
* member organization names

We will use actual male/female average height/weight stats from WolframAlpha to generate heights/weights.

Ages can be simply randomly generated uniformly from 18 - 80 (not realistic, but whatever).

### World Generation Problems

The fundamental problem is generating a set of people, vehicle registrations, and memberships that requires the user to perform _all of_ but _no more than_ the original steps (get clues, find and interview witness, sort through vehicle registrations, cross-reference membership lists) to unambiguously identify a murderer.

To recap the clues given the player:

* perp _sex_ (2 possibilies)
* perp relative _height_ (3 possibilities: tall, short, medium-height)
* perp memberships; given the 11 organizations in the original game, there are
    * 2048 possible combinations of membership (from no memberships at all, to membership in all 11)
    * 55 possible combinations of simple dual-membership (all citizens are members of exactly 2)
    * 165 combinations of exactly-3-orgs
    * 330 combinations of exactly-4-orgs
* perp car make (16 possibilies)
* perp car color (11 possiblities)
* perp's license plate prefix (3 characters) and suffix (1 character)
    * this was where the original author doctored the data---only a small set of license plate numbers manually constructed around the perp had cardinality over 1
    * I first thought of generating license plates in a 4-letter/3-digit scheme where the first 2 letters are deterministically generated from the make, the next 2 from the color, and the 3 digits are generated randomly but with restrictions (e.g., the last digit must be odd) as needed to tune the expected cardinality of the vehicle-registration-search output set; an odd-even-odd digit policy would allow 125 distinct license plates for each make/color combination. following the 3-pre/1-post pattern of clue, this would mean only 5 possibilities beyond the fixed make/color portion. This worked great in terms of easily generating a consistent population/mystery, but ended up destroying the challenge of grepping for multi-line-record matches (one of the key breakthroughs in CLI skills).
    * Take 2: go to a 3-alpha/4-digit tag generation scheme, but artificially limit things by having the 3-alpha prefix drawn from a pool of 5 prefixes randomly generated at the start of world-generation and keep the even/odd/even/odd digit distribution. This would produce only 25 possibilities beyond sex/height/car-color/car-make and could keep the population size sane.

We would like the vehicle registration search step to generate a list of at least 2 and no more than 5 candidates (which the player must disambiguate by cross-referencing membership lists).
At the same time, the membership policies and population size must be such that simply having the perp's membership cards (and sex/height) is not sufficient for identification.

To make sure the user should get 2-5 people of the right sex/height/car-color/car-make/prefix-cluster/final-tag-digit, we need `N *(2 * 3 * 11 * 16 * 5 * 5)`, where `N` is our safety factor, which must be greater than 2.

With `N = 3`, this means a population size of **79,200** (about 16 times the original CLM world), and 3 expected candidate perps after the vehicle registration search.  *Any* number of memberships would be sufficient to resolve this ambiguity, probably (and we should do a sanity check to make sure the generated case does not disappoint).

**Unfortunately**, all of the above math starts to founder when _names_ enter the picture and we need to select a witness whose first name gives a nice number of first/last name hits.  So I am fudging the population size back down to **15840**, which seems to work well with our database.

But we need to make sure that we don't allow an advanced user to bypass the witness hunt/vehicle search entirely by simply identifying all, e.g., tall males who are members of exactly AAA, Delta SkyMiles, Terminal City Library, and the Museum of Bash History (the original mystery does in fact ensure this property).

To keep things simple, lets go with `M = 3` memberships (randomly selected from the 11 orgs; that's 165 possible combinations of membership) for all citizens.

### World Generation Procedure

* load the seed data from the files listed above
* compute the population size using the `N` formula above (using the cardinality of the car make/color sets)
* generate that many "persons" (with registered vehicles) using the seed/stat data
* pick the murderer (see below)
* pick the witness (see below)
* generate the world files and clue files (see below)

### Perp Selection

There shouldn't be any special steps for perp selection given our carefully-parameterized population size and world generation.  Just pick someone.  Anyone.

We do, however, cover our bases and double-check that we get non-empty (and non-huge) sets of near-match candidates based on membership sets and tag matches.
If we don't, just try generating/picking again...

### Witness Selection

For an ideal experience, we want the witness to have a first name that generates 4-ish hits in `people`, at least 2 of whom are the correct sex and thus must both be looked up/interviewed.

### Clue Generation

We then generate a number of files to fill out the experience:

* templated CLUEs in the `crimescene` file (interspersed with random excerpts of Alice in Wonderland)
* templated INTERVIEW files for the witness and any "red herring" ambiguous matches; random gibberish interview files to make the true interviews hard to find automagically
* street files for each person in `people`, with dictionary word salad on each line except for the witness/red-herring lines, which reference the appropriate interview files

## Generation Details

### The `crimescene` File

The format of the file is a sequence of 1000 "Crime Scene Report" blocks in the following format:

```
*******
Crime Scene Report #<RANDOM_DIGITS>
********

<TEXT BODY>


```

where `<TEXT BODY>` is _either_ a random selection from a seed text (Alice in Wonderland in the original mystery) _or_ a line starting with `CLUE: ` and containing one of the preseeded clues given the player to start the investigation.

### CLUE formats

The player is given 3 clues in `crimescene`:

* CLUE 1: `Footage from an ATM security camera is blurry but shows that the perpetrator is a <MURDERER_HEIGHT_CLASS> <MURDER_SEX_FORMAL>, <HEIGHT_CLASS_DESCRIPTION>.`
* CLUE 2: `Found a wallet believed to belong to the killer: no ID, just loose change and membership cards for <COMMA_SEPARATED_LIST_OF_MEMBERSHIP_ORG_NAMES>.  The cards are totally untraceable and have no name, for some reason.`
* CLUE 3: `Questioned the barista at the local coffee shop. He said a <WITNESS_SEX_INFORMAL> left right before they heard the shots.  The name on <WITNESS_POS_PRONOUN> latte was <WITNESS_FIRST_NAME>; <WITNESS_SUB_PROJOUN> had <WITNESS_HAIR_COLOR> <WITNESS_HAIR_STYLE> and a <WITNESS_NATIONALITY> accent.`

### Interview Files

The following interview files must be generated:

* one for the murderer, saying:
    ```
    Home appears to be empty, no answer at the door.

    After questioning neighbors, appears that the occupant may have left for a trip recently.

    Considered a suspect until proven otherwise, but would have to eliminate other suspects to confirm.
    ```

* one for the cafe witness, saying:
    ```
    Interviewed <WITNESS_TITLE> at 2:04pm.  Witness stated that <WITNESS_SUB_PRONOUN> did not see anyone <WSP> could identify as the shooter, that <WSP> ran away as soon as the shots were fired.

    However, <WSP> reports seeing the car that fled the scene.  Describes it as a <PERP_CAR_COLOR> <PERP_CAR_MAKE>, with a license plate that starts with "<PERP_TAG_PREFIX>" and ends with "<PERP_TAG_SUFFIX>."
    ```

* one for each cafe witness red herring, saying either:
    ```
    <PERSON_TITLE> is clearly not a <WITNESS_SEX_INFORMAL>.  Not the witness from the cafe.
    ```

    or

    ```
    <PERSON_TITLE> has <PERSON_HAIR_COLOR> and a <PERSON_NATIONALITY> accent.  Not the witness from the cafe.
    ```

    depending on if the red-herring's sex matches or mismatches the witness.  Note that we don't actually establish hair color/nationality for all the red herrings in advance: we just generate one that _doesn't_ match the witness's on the fly.

* one for each tag-match murderer-candidate (NOT including the actual murderer) saying
    ```
    <PERSON_TITLE> <COINCIDENCE>, but has never been a member of <ORG_NAME> and has a solid alibi for the morning in question. Not considered a suspect.
    ```
    where `ORG_NAME` is one of the perp's memberships that the candidate does not share and
    where `COINCIDENCE` is a phrase randomly selected from a list of plausible and/or humorous false-flag suspicions (e.g., "knew the victim", "lives nearby", "looks as shady as a rack of sunglasses", etc.)

* one for each membership-match murderer-candidate (NOT including the actual murderer) saying
    ```
    <PERSON_TITLE> <COINCIDENCE>, but has never owned a car matching the witness's description and has a solid alibi for the morning in question. Not considered a suspect.
    ```

* and as many gibberish/filler-stuffed fake interviews as it takes to make 500 total files

### Street Files

Each person in the population is assigned a street address (a street name and line number).
The street name is simply picked from the seed list when we generate the person.
We can then group the people by street and generate their line numbers while generating that street file by:

* writing 50-100 (randomly selected) lines of junk at the start of the street file
* writing either (a) random junk or (b) and interview reference, if available, for each person on that street
* padding out the file by inserting 2-5 random junk lines between each person

The "random junk" here is a chain of words from our English word list.

### Membership Files

We simply create one file per organization with its members names (sorted alphabetically) written one per line.

## Acknowledgements/Credits

* Noah Veltman's original [Command Line Murders mystery game](https://github.com/veltman/clmystery) (idea, structure, person/street names)
* Project Gutenberg's [*The Adventures of Sherlock Holmes*](https://gutenberg.org/files/1661/1661-0.txt) (seed text for file filler)
* https://www.ef.com/wwen/english-resources/english-grammar/nationalities/ (adjectival nationality names)
* https://www.ef.com/wwen/english-resources/english-vocabulary/top-3000-words/ (most common English words, for generating short lines of gibberish for street files)