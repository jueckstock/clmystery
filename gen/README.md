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

We will use the existing `people`, `vehicles`, and `memberships/` files as-is.

### Perp Selection

We start by selecting the murderer from the population of `people` in such a way that a single, unambiguous suspect can be identified based on sex, approximate height (short, medium, tall), car registration (make/color/license-plate fragment), and membership set.

### Witness Selection

We progress to selecting a "witness" from `people` in such a way that the witness's first name will yield multiple hits in `people`, at least two of which match the given sex.

### Clue Generation

We then generate a number of files to fill out the experience:

* templated CLUEs in the `crimescene` file (interspersed with random excerpts of Alice in Wonderland)
* templated INTERVIEW files for the witness and any "red herring" ambiguous matches; random gibberish interview files to make the true interviews hard to find automagically
* street files for each person in `people`, with dictionary word salad on each line except for the witness/red-herring lines, which reference the appropriate interview files

