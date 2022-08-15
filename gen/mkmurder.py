#!/usr/bin/env python3
"""mkmurder: generate a new Command Line Murders mystery
"""
from __future__ import annotations
import argparse
import math
import os
import random
import string
import sys
from collections import defaultdict, namedtuple
from typing import Sequence, Mapping

# tuning parameters
SAFETY_FACTOR = 3
NUM_REQUIRED_MEMBERSHIPS = 3
NUM_INTERVIEW_FILES = 500

# factors for calculating odds/required base population
NUM_SEXES = 2
NUM_HEIGHT_CLASSES = 3
NUM_ODD_DIGITS = 5

# male/female height means/stds from WolframAlpha (2022-08-12)
MALE_HEIGHT_MEAN = 66 # inches (5'6")
MALE_HEIGHT_STD = 8.6 # inches
FEMALE_HEIGHT_MEAN = 62 # inches (5'2")
FEMALE_HEIGHT_STD = 6.7 # inches

# male/female weight means/stds from WolframAlpha (2022-08-12)
MALE_WEIGHT_MEAN = 163 # pounds
MALE_WEIGHT_STD = 66 # pounds
FEMALE_WEIGHT_MEAN = 144 # pounds
FEMALE_WEIGHT_STD = 57 # pounds


Vehicle = namedtuple("Vehicle", ["make", "color", "tag"])


class Height:
    def __init__(self, inches: float):
        all_inches = round(inches)
        self.feet, self.inches = divmod(all_inches, 12)
    
    def adjective(self) -> str:
        if self.feet >= 6:
            return "tall"
        elif (self.feet < 5) or (self.inches < 4):
            return "short"
        else:
            return "medium-height"
    
    def description(self) -> str:
        adj = self.adjective()
        if adj == "tall":
            return "at least 6'"
        elif adj == "short":
            return '''under 5'4"'''
        else:
            return """between 5'4" and 6'"""
    
    def __str__(self) -> str:
        return f'''{self.feet}'{self.inches}"'''


class Person:
    def __init__(self, first_name: str, last_name: str, sex: str, street: str):
        self.first_name = first_name
        self.last_name = last_name
        self.full_name = first_name + " " + last_name
        self.sex = sex
        self.street = street
        self.street_line = None # determined at street-generation time

        self.age = random.randint(18, 80)

        if self.sex == "M":
            self.height = Height(random.normalvariate(MALE_HEIGHT_MEAN, MALE_HEIGHT_STD))
            self.weight = round(random.normalvariate(MALE_WEIGHT_MEAN, MALE_WEIGHT_STD))
        elif self.sex == "F":
            self.height = Height(random.normalvariate(FEMALE_HEIGHT_MEAN, FEMALE_HEIGHT_STD))
            self.weight = round(random.normalvariate(FEMALE_WEIGHT_MEAN, FEMALE_WEIGHT_STD))
        else:
            raise ValueError("sex must be M or F")

        self.vehicle = None
        self.memberships = set()
    
    def sex_formal(self) -> str:
        return "male" if self.sex == "M" else "female"
    
    def sex_informal(self) -> str:
        return "man" if self.sex == "M" else "woman"
    
    def sub_pronoun(self) -> str:
        return "he" if self.sex == "M" else "she"
    
    def obj_pronoun(self) -> str:
        return "him" if self.sex == "M" else "her"
    
    def pos_pronoun(self) -> str:
        return "his" if self.sex == "M" else "her"
    
    def personal_title(self) -> str:
        if self.sex == "M":
            return f"Mr. {self.last_name}"
        else:
            return f"Ms. {self.last_name}"
    
    def __str__(self) -> str:
        if self.vehicle:
            return f"""{self.full_name} is a {self.height.adjective()} ({self.height}) {self.sex_formal()}; \
{self.sub_pronoun()} lives on {self.street} and holds memberships in {'/'.join(self.memberships)}; \
{self.pos_pronoun()} vehicles is a {self.vehicle.color} {self.vehicle.make} ({self.vehicle.tag})"""
        else:
            return f"""{self.full_name} is a {self.height.adjective()} ({self.height}) {self.sex_formal()}; \
{self.sub_pronoun()} lives on {self.street} and holds memberships in {'/'.join(self.memberships)}"""


def load_seed_list(filename: str) -> Sequence[str]:
    with open(filename, "rt") as fd:
        items = []
        for line in fd:
            items.append(line.strip())
    return items


def load_weighted_seed_list(filename: str) -> Sequence[str]:
    with open(filename, "rt") as fd:
        items = []
        for line in fd:
            count, item = line.strip().split(maxsplit=1)
            items.extend([item]*int(count))
    return items


class SeedText:
    '''Load plain text [from a Project Gutenberg book] so random paragraphs can be selected.'''
    def __init__(self, textfile: str):
        with open(textfile, "rt", encoding="utf-8") as fd:
            raw_text = fd.read()
        raw_lines = raw_text.split('\n')
        
        paragraphs = []
        buff = []
        for line in raw_lines:
            if line:
                buff.append(line)
            elif buff:
                paragraphs.append(' '.join(buff))
                buff = []
        self._paragraphs = paragraphs
    
    def random_excerpt(self, num_paragraphs: int = 1):
        '''Return a random passage from the seed text.'''
        start = random.randrange(len(self._paragraphs))
        return '\n'.join(self._paragraphs[start:start+num_paragraphs])


def oxford_comma(items: Sequence[str]) -> str:
    if not isinstance(items, list):
        items = list(items)
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    elif len(items) > 2:
        return ', '.join(items[:-1]) + ', and ' + items[-1]
    else:
        return items[0]


def main(argv):
    ap = argparse.ArgumentParser(description="generate a new Commane Line Murders mystery")
    ap.add_argument("-d", "--seed-dir", default=".", help="directory in which to find seed files (people, vehicles, etc.)")
    ap.add_argument("-o", "--output-dir", default="./mystery", help="directory in which to put copied/generated files")
    args = ap.parse_args()

    # load all seed data from seed files
    female_names = load_weighted_seed_list(os.path.join(args.seed_dir, "female_names"))
    male_names = load_weighted_seed_list(os.path.join(args.seed_dir, "male_names"))
    last_names = load_weighted_seed_list(os.path.join(args.seed_dir, "last_names"))
    car_colors = load_seed_list(os.path.join(args.seed_dir, "car_colors"))
    car_makes = load_seed_list(os.path.join(args.seed_dir, "car_makes"))
    street_names = load_seed_list(os.path.join(args.seed_dir, "street_names"))
    member_orgs = load_seed_list(os.path.join(args.seed_dir, "member_orgs"))
    hair_colors = load_seed_list(os.path.join(args.seed_dir, "hair_colors"))
    hair_styles = load_seed_list(os.path.join(args.seed_dir, "hair_styles"))
    nationality_adjectives = load_seed_list(os.path.join(args.seed_dir, "nationality_adjectives"))
    coincidental_suspicions = load_seed_list(os.path.join(args.seed_dir, "coincidental_suspicions"))
    word_list = load_seed_list(os.path.join(args.seed_dir, "word_list"))
    text_filler = SeedText(os.path.join(args.seed_dir, "holmes.txt"))

    # compute population size as a function of our parameters and sanity check it
    popsize = SAFETY_FACTOR * (NUM_SEXES * NUM_HEIGHT_CLASSES * NUM_ODD_DIGITS * len(car_colors) * len(car_makes))
    if (popsize / (NUM_SEXES * NUM_HEIGHT_CLASSES * math.comb(len(member_orgs), NUM_REQUIRED_MEMBERSHIPS))) < 2:
        raise ValueError("the SAFETY_FACTOR is too low or something is messed up with our seed files")
    
    # compute male/female skew and generate the base population
    nfemales = math.floor(popsize * 0.51)
    nmales = popsize - nfemales
    pop = []
    fname_index = defaultdict(lambda : ([], [])) # indices used later for witness vetting
    lname_index = defaultdict(lambda : ([], []))
    for i in range(nmales):
        p = Person(
            random.choice(male_names),
            random.choice(last_names),
            "M",
            random.choice(street_names)
        )
        fname_index[p.first_name][0].append(p)
        lname_index[p.last_name][0].append(p)
        pop.append(p)
    for i in range(nfemales):
        p = Person(
            random.choice(female_names),
            random.choice(last_names),
            "F",
            random.choice(street_names)
        )
        fname_index[p.first_name][1].append(p)
        lname_index[p.last_name][1].append(p)
        pop.append(p)
    
    # randomize the order of the population so listings don't have all males then all females
    random.shuffle(pop)
    
    # generate memberships
    member_map = defaultdict(list)
    for p in pop:
        for org in random.sample(member_orgs, NUM_REQUIRED_MEMBERSHIPS):
            p.memberships.add(org)
            member_map[org].append(p)
    
    # generate cars ("a chicken in every pot and two cars in every garage...")
    color_letters = string.ascii_uppercase
    make_letters = color_letters[::-1]
    tag_history = set()
    for p in pop:
        color_index = random.randrange(len(car_colors))
        make_index = random.randrange(len(car_makes))
        safe_tag = False
        while not safe_tag:
            tag_prefix = (color_letters[(color_index + 1) % 26] + color_letters[(color_index * 2) % 26] + 
                make_letters[(make_index + 1) % 26] + make_letters[(make_index * 2) % 26])
            tag_suffix = format(random.randrange(1000), "03")
            tag = tag_prefix + tag_suffix
            if tag not in tag_history:
                tag_history.add(tag)
                safe_tag = True
        p.vehicle = Vehicle(car_makes[make_index], car_colors[color_index], tag)
    
    # pick the murderer!
    good_murderer = False
    while not good_murderer:
        murderer = random.choice(pop)

        # sanity check the murderer
        sanity_tag_set = []
        sanity_member_set = []
        sanity_doppelganger_set = []
        for p in pop:
            if p is murderer:
                continue
            
            sex_match = (p.sex == murderer.sex)
            height_match = (p.height.adjective() == murderer.height.adjective())
            tag_match = (p.vehicle.tag[:3] == murderer.vehicle.tag[:3]) and (p.vehicle.tag[-1] == murderer.vehicle.tag[-1])
            members_match = (p.memberships == murderer.memberships)
            
            if sex_match and height_match and tag_match:
                sanity_tag_set.append(p)
            if sex_match and height_match and members_match:
                sanity_member_set.append(p)
            if sex_match and height_match and tag_match and members_match:
                sanity_doppelganger_set.append(p)
        
        if len(sanity_doppelganger_set) > 0:
            print("we have doppelgangers: " + "; ".join(map(str, sanity_doppelganger_set)))
            continue
        if len(sanity_tag_set) < 1 or len(sanity_tag_set) > 4:
            print(f"we have too few/many tag matches ({len(sanity_tag_set)})")
            continue
        if len(sanity_member_set) < 1:
            print("we have no other citizens with the murderers memberships! " + str(murderer))
            continue
        good_murderer = True

    #print("murderer:", murderer)
    #rint(f"{len(sanity_tag_set)} extra tag search suspects")
    #rint(f"{len(sanity_member_set)} pre-tag search suspects matching memberships")

    # pick the witness (in a sanity-vetted way, to ensure good results for the witness search)
    good_witness = False
    while not good_witness:
        witness = random.choice(pop)
        if witness is murderer: # just no...
            continue

        male_name_clashes = (set(fname_index[witness.first_name][0]) | set(lname_index[witness.first_name][0])) - {witness}
        female_name_clashes = (set(fname_index[witness.first_name][1]) | set(lname_index[witness.first_name][1])) - {witness}
        if witness.sex == "M":
            same_clash = len(male_name_clashes)
            diff_clash = len(female_name_clashes)
        else:
            same_clash = len(female_name_clashes)
            diff_clash = len(male_name_clashes)

        if (0 < same_clash < 3) and (0 < diff_clash < 6):
            good_witness = True
            red_herrings = male_name_clashes | female_name_clashes
        #else:
        #    print(witness, same_clash, diff_clash)
    
    #print("witness:", witness)
    #print('-'*40)
    #for p in male_name_clashes:
    #    print(p)
    #for p in female_name_clashes:
    #    print(p)

    # add a little color/flair to the clues about the witness
    witness_hair_color = random.choice(hair_colors)
    witness_hair_style = random.choice(hair_styles)
    witness_nationality = random.choice(nationality_adjectives)
    
    # and be able to give distinguishing clues about the red-herring witness candidates
    other_hair_colors = hair_colors[:]
    other_hair_colors.remove(witness_hair_color)
    other_nationalities = nationality_adjectives[:]
    other_nationalities.remove(witness_nationality)

    # make sure the destination directory exists
    os.makedirs(args.output_dir, exist_ok=True)

    # generate the crimescene file in the destination directory
    clues = [
        f"""\
Footage from an ATM security camera is blurry \
but shows that the perpetrator is a \
{murderer.height.adjective()} {murderer.sex_formal()}, \
{murderer.height.description()}.""",
        f"""\
Found a wallet believed to belong to the killer: \
no ID, just loose change and membership cards for \
{oxford_comma(murderer.memberships)}. \
The cards are totally untraceable and have no name, for some reason.""",
        f"""\
Questioned the barista at the local coffee shop. \
He said a {witness.sex_informal()} left right before \
they heard the shots.  The name on {witness.pos_pronoun()} latte \
was {witness.first_name}; {witness.sub_pronoun()} had \
{witness_hair_color} {witness_hair_style} hair and a pronounced {witness_nationality} accent.""",
    ]

    def write_crime_report(fd: file, body: str):
        report_number = ''.join(random.choice("0123456789") for _ in range(16))
        fd.write(f"""\
*******
Crime Scene Report #{report_number}
********

{body}

""")

    # GENERATE THE `crimescene` FILE
    with open(os.path.join(args.output_dir, "crimescene"), "wt", encoding="utf-8") as fd:
        slots = []
        while len(slots) < 3:
            slot = random.randrange(1000)
            if slot not in slots:
                slots.append(slot)
        
        last = 0
        for clue, slot in zip(clues, slots):
            for _ in range(last, slot):
                filler = text_filler.random_excerpt(random.randint(1, 10))
                write_crime_report(fd, filler)
            last = slot
            write_crime_report(fd, "CLUE: " + clue)
    
    # GENERATE THE `interviews/` FILES for the WITNESS and the RED HERRINGS
    def write_interview_file(body: str) -> str:
        while True:
            inum = random.randrange(100000000)
            iname = os.path.join(args.output_dir, "interviews", f"interview-{inum:08}")
            try:
                fd = open(iname, "wt", encoding="utf-8")
                fd.write(body)
                return os.path.basename(iname)
            except OSError:
                continue # try again
            finally:
                fd.close()
    
    os.makedirs(os.path.join(args.output_dir, "interviews"), exist_ok=True)
    interview_map = {}

    # the murderer doesn't want to be interviewed
    interview_map[id(murderer)] = write_interview_file("""\
Home appears to be empty, no answer at the door.

After questioning neighbors, appears that the occupant may have left for a trip recently.

Considered a suspect until proven otherwise, but would have to eliminate other suspects to confirm.
""")

    # the witness gives vital clues
    interview_map[id(witness)] = write_interview_file(f"""\
Interviewed {witness.personal_title()} at 2:04pm. \
Witness stated that {witness.sub_pronoun()} did not see anyone \
{witness.sub_pronoun()} could identify as the shooter and that \
{witness.sub_pronoun()} ran away as soon as the shots were fired.

However, {witness.sub_pronoun()} reports seeing the car that fled the scene. \
Describes it as a {murderer.vehicle.color} {murderer.vehicle.make}, \
with a license plate that starts with "{murderer.vehicle.tag[:3]}" \
and ends with "{murderer.vehicle.tag[-1]}."
""")

    # the red-herring witnesses are all disappointing in sex-specific ways
    for rh in red_herrings:
        if rh.sex == witness.sex:
            body = f"""\
{rh.personal_title()} has {random.choice(other_hair_colors)} hair \
and a distinct {random.choice(other_nationalities)} accent.  Not the witness from the cafe.
"""
        else:
            body = f"""\
{rh.personal_title()} is not a {witness.sex_informal()}.  Not the witness from the cafe.
"""
        interview_map[id(rh)] = write_interview_file(body)
    
    # the membership-match perp candidates all have alibis
    for pc in sanity_member_set:
        interview_map[id(pc)] = write_interview_file(f"""\
{pc.personal_title()} {random.choice(coincidental_suspicions)}, but has never owned \
a car matching the witness's description and has a solid alibi for the morning \
in question. Not considered a suspect.
""")

    # as do the car-tag-close-match candidates (but we need to identify their membership mismatches)
    for pc in sanity_tag_set:
        missing_org = (murderer.memberships - pc.memberships).pop()
        interview_map[id(pc)] = write_interview_file(f"""\
{pc.personal_title()} {random.choice(coincidental_suspicions)}, but has \
never been a member of {missing_org} and has a solid alibi for the morning \
in question. Not considered a suspect.
""")

    # now fill up the `interviews/` with distracting fluff to hide the good stuff...
    for _ in range(NUM_INTERVIEW_FILES - len(interview_map)):
        write_interview_file(text_filler.random_excerpt())

    # GENERATE THE `streets/` FILES
    street_map = defaultdict(list)
    for p in pop:
        street_map[p.street].append(p)
    
    def write_junk_lines(fd: file, count: int) -> int:
        for _ in range(count):
            words = random.randint(5, 10)
            print(" ".join(random.choice(word_list) for _ in range(words)), file=fd)
        return count
    
    os.makedirs(os.path.join(args.output_dir, "streets"), exist_ok=True)
    for street, residents in street_map.items():
        with open(os.path.join(args.output_dir, "streets", street.replace(" ", "_")), "wt", encoding="utf-8") as fd:
            line_no = write_junk_lines(fd, random.randint(50, 100)) + 1
            for p in residents:
                p.street_line = line_no
                try:
                    interview_file = interview_map[id(p)]
                    interview_num = interview_file.split('-')[-1]
                    print(f"SEE INTERVIEW #{interview_num}", file=fd)
                except KeyError:
                    write_junk_lines(fd, 1)
                line_no += write_junk_lines(fd, random.randint(2, 5)) + 1

    # GENERATE THE `people` FILE
    with open(os.path.join(args.output_dir, "people"), "wt", encoding="utf-8") as fd:
        fd.write("""\
***************
To go to the street someone lives on, use the file
for that street name in the 'streets' subdirectory.
To knock on their door and investigate, read the line number
they live on from the file.  If a line looks like gibberish, you're at the wrong house.
***************

NAME	SEX	AGE	ADDRESS
""")
        for p in pop:
            fd.write(f"""\
{p.full_name}\t{p.sex}\t{p.age}\t{p.street}, line {p.street_line}
""")

    # GENERATE THE `vehicles` FILE
    with open(os.path.join(args.output_dir, "vehicles"), "wt", encoding="utf-8") as fd:
        fd.write("""\
***************
Vehicle and owner information from the Terminal City Department of Motor Vehicles
***************

""")
        for p in pop:
            fd.write(f"""\
License Plate {p.vehicle.tag}
Make: {p.vehicle.make}
Color: {p.vehicle.color}
Owner: {p.full_name}
Height: {p.height}
Weight: {p.weight} lbs

""")

    # GENERATE THE `memberships/` FILES
    os.makedirs(os.path.join(args.output_dir, "memberships"), exist_ok=True)
    for org, members in member_map.items():
        members.sort(key=lambda p: (p.last_name, p.first_name))
        with open(os.path.join(args.output_dir, "memberships", org.replace(" ", "_")), "wt", encoding="utf-8") as fd:
            for m in members:
                print(m.full_name, file=fd)


if __name__ == "__main__":
    main(sys.argv)
