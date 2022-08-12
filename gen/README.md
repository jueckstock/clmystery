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
    * I propose generating license plates in a 4-letter/3-digit scheme where the first 2 letters are deterministically generated from the make, the next 2 from the color, and the 3 digits are generated randomly but with restrictions (e.g., the last digit must be odd) as needed to tune the expected cardinality of the vehicle-registration-search output set; an odd-even-odd digit policy would allow 125 distinct license plates for each make/color combination
    * following the 3-pre/1-post pattern of clue, this would mean only 5 possibilities beyond the fixed make/color portion

We would like the vehicle registration search step to generate a list of at least 2 and no more than 5 candidates (which the player must disambiguate by cross-referencing membership lists).
At the same time, the membership policies and population size must be such that simply having the perp's membership cards (and sex/height) is not sufficient for identification.

To make sure the user should get 2-5 people of the right sex/height/car-color/car-make/final-tag-digit, we need `N *(2 * 3 * 11 * 16 * 5)`, where `N` is our safety factor which must be greater than 2.

With `N = 3`, this means a population size of **15,840** (about 3 times the original CLM world), and 3 expected candidate perps after the vehicle registration search.  *Any* number of memberships would be sufficient to resolve this ambiguity, probably (and we should do a sanity check to make sure the generated case does not disappoint).

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

### Witness Selection

For an ideal experience, we want the witness to have a first name that generates 4-ish hits in `people`, at least 2 of whom are the correct sex and thus must both be looked up/interviewed.

### Clue Generation

We then generate a number of files to fill out the experience:

* templated CLUEs in the `crimescene` file (interspersed with random excerpts of Alice in Wonderland)
* templated INTERVIEW files for the witness and any "red herring" ambiguous matches; random gibberish interview files to make the true interviews hard to find automagically
* street files for each person in `people`, with dictionary word salad on each line except for the witness/red-herring lines, which reference the appropriate interview files

