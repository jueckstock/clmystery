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
        elif (self.feet < 5) or (self.inches < 6):
            return "short"
        else:
            return "medium-height"
    
    def __str__(self) -> str:
        return f'''{self.feet}'{self.inches}"'''


class Person:
    def __init__(self, first_name: str, last_name: str, sex: str, street: str):
        self.first_name = first_name
        self.last_name = last_name
        self.full_name = first_name + " " + last_name
        self.sex = sex
        self.street = street

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
    
    def __str__(self) -> str:
        if self.vehicle:
            return f"""{self.full_name} is a {self.height.adjective()} ({self.height}) {'male' if self.sex == 'M' else 'female'} \
who lives on {self.street} and holds memberships in {'/'.join(self.memberships)} \
and drives a {self.vehicle.color} {self.vehicle.make} ({self.vehicle.tag})"""
        else:
            return f"""{self.full_name} is a {self.height.adjective()} ({self.height}) {'male' if self.sex == 'M' else 'female'} \
who lives on {self.street} and holds memberships in {'/'.join(self.memberships)}"""


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
    
    # generate memberships
    for p in pop:
        for org in random.sample(member_orgs, NUM_REQUIRED_MEMBERSHIPS):
            p.memberships.add(org)
    
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

    print("murderer:", murderer)
    print(f"{len(sanity_tag_set)} extra tag search suspects")
    print(f"{len(sanity_member_set)} pre-tag search suspects matching memberships")

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
        #else:
        #    print(witness, same_clash, diff_clash)
    
    print("witness:", witness)
    print('-'*40)
    for p in male_name_clashes:
        print(p)
    for p in female_name_clashes:
        print(p)

if __name__ == "__main__":
    main(sys.argv)
