import re

from top_bgco import RawEntry, get_url_for_chapter, DB, build_raw_data
from typing import Dict, List

# Init the DB
db = DB("lite.db")

print(">> Database created")

#
# 2020
#
data_2020 = [
    "https://www.youtube.com/watch?v=lBZ4myP_-Is",
    "https://www.youtube.com/watch?v=oSycUrG3hOI",
    "https://www.youtube.com/watch?v=ZIm1SGQCbr8",
    ("https://www.youtube.com/watch?v=tbZKxpK9s3s", 2, -1),
    "https://www.youtube.com/watch?v=Cf7n1zsrWJI",
]


def parse_2020(chapter: Dict, video_id: str, year: int) -> RawEntry:
    """This parser works well with the format of the 2020 top 50 videos."""
    regex = r"(\d*)\ -\ (.*)"
    matches = re.finditer(regex, chapter["title"])
    position, game = list(matches)[0].groups()
    url = get_url_for_chapter(video_id, chapter["time"])
    return RawEntry(year, "Alex", game, int(position), url)


def before_return_hook_2020(entries: List[RawEntry]) -> List[RawEntry]:
    return entries


# Parse and build raw data
raw_data_2020 = build_raw_data(
    videos_data=data_2020,
    year=2020,
    parser=parse_2020,
    before_return_hook=before_return_hook_2020,
)
# Add it to the db
db.add_from_raw_data(raw_data_2020)

print(">> 2020: 0K")


#
# 2021
#
data_2021 = [
    ("https://www.youtube.com/watch?v=QnQQ2igVvmg", 4, -1),
    ("https://www.youtube.com/watch?v=L_5kNoP8fAk", 3, -1),
    ("https://www.youtube.com/watch?v=fj7zIwzLM1Y", 3, -1),
    ("https://www.youtube.com/watch?v=05vYqiT3d2A", 3, -1),
    ("https://www.youtube.com/watch?v=qXWeuzhDy0A", 2, -1),
    ("https://www.youtube.com/watch?v=bgyYefZ3GhE", 4, -1),
    ("https://www.youtube.com/watch?v=BC7TLbG5fvc", 3, -1),
    ("https://www.youtube.com/watch?v=B4rXsEP8VDQ", 3, -1),
    ("https://www.youtube.com/watch?v=nttm4rAZPes", 2, -1),
    ("https://www.youtube.com/watch?v=4tQNDSqc2R4", 2, -1),
]


def count_down_from(_from: int) -> int:
    for i in range(0, _from):
        yield _from - i


# Since there's no index in the chapter title let's generate it dynamically
get_position = count_down_from(100)


def parse_2021(chapter: Dict, video_id: str, year: int) -> RawEntry:
    """This parser works well with the format of the 2021 top 100 videos."""
    url = get_url_for_chapter(video_id, chapter["time"])
    return RawEntry(year, "Alex", chapter["title"], next(get_position), url)


def before_return_hook_2021(entries: List[RawEntry]) -> List[RawEntry]:
    return entries


# Parse and build raw data
raw_data_2021 = build_raw_data(
    videos_data=data_2021,
    year=2021,
    parser=parse_2021,
    before_return_hook=before_return_hook_2021,
)
# Add it to the db
db.add_from_raw_data(raw_data_2021)

print(">> 2021: 0K")


#
# 2022
#
data_2022 = [
    "https://www.youtube.com/watch?v=7Y8NuZxZCxM",
    "https://www.youtube.com/watch?v=oHCpZ3KXvSs",
    "https://www.youtube.com/watch?v=BVdTCNJytgk",
    "https://www.youtube.com/watch?v=K3k0Ig901wc",
    "https://www.youtube.com/watch?v=WcQDObGcON8",
    "https://www.youtube.com/watch?v=4dWCVA3bZ1k",
    "https://www.youtube.com/watch?v=yC4Zo-JSjLk",
    "https://www.youtube.com/watch?v=CW2SD-FROqU",
    "https://www.youtube.com/watch?v=0ouNMQi4wp8",
    "https://www.youtube.com/watch?v=McwVKKoV2ws",
]


def parse_2022(chapter: Dict, video_id: str, year: int) -> RawEntry:
    """This parser works well with the format of the 2022 top 100 videos."""
    regex = r"(\d*)\ (Devon|Alex|Meg)\ ?-\ (.*)"
    matches = re.finditer(regex, chapter["title"])
    position, who, game = list(matches)[0].groups()
    url = get_url_for_chapter(video_id, chapter["time"])
    return RawEntry(year, who, game, int(position), url)


def before_return_hook_2022(entries: List[RawEntry]) -> List[RawEntry]:
    to_add = [
        # Per questo manca proprio il chapter
        RawEntry(
            2022,
            "Meg",
            "The Guild of Merchant Explorers",
            75,
            "https://www.youtube.com/watch?v=BVdTCNJytgk&t=2240",
        ),
    ]

    def skip(entry: RawEntry) -> RawEntry:
        return entry not in [
            # Qua hanno solo chiacchierato, lo ripetono piu' avanti
            RawEntry(
                2022,
                "Devon",
                "Vindication",
                50,
                "https://www.youtube.com/watch?v=4dWCVA3bZ1k&t=65",
            ),
        ]

    def fix(entry: RawEntry) -> RawEntry:
        # Questo ha il nome sbagliato
        if entry == RawEntry(
            2022,
            "Alex",
            "Welcome To...",
            92,
            "https://www.youtube.com/watch?v=7Y8NuZxZCxM&t=3356",
        ):
            entry.name = "Devon"
        return entry

    return list(filter(skip, map(fix, entries))) + to_add


# Parse and build raw data
raw_data_2022 = build_raw_data(
    videos_data=data_2022,
    year=2022,
    parser=parse_2022,
    before_return_hook=before_return_hook_2022,
)
# Add it to the db
db.add_from_raw_data(raw_data_2022)

print(">> 2022: 0K")

print(">> DB POPULATED! <<")
