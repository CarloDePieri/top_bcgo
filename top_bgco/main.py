from __future__ import annotations

import urllib.parse
import json
from typing import Dict, List, Callable, Optional
import re
import requests
from dataclasses import dataclass
from dataclasses_json import dataclass_json


#
# UTILS
#
def get_chapters(video_id: str) -> Dict:
    query = f"https://yt.lemnoslife.com/videos?part=chapters&id={video_id}"
    return requests.get(query).json()["items"][0]["chapters"]["chapters"]


def get_url_for_chapter(video_id: str, time: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}&t={time}"


def parse_chapters(video_id: str) -> Dict:
    chapters = get_chapters(video_id)[1:-1]

    video_data = []

    for chapter in chapters:
        chapter_data = {"url": get_url_for_chapter(video_id, chapter["time"])}
        title = chapter["title"]
        regex = r"(\d*)\ (Devon|Alex|Meg)\ ?-\ (.*)"
        matches = re.finditer(regex, title)
        try:
            chapter_data["position"], chapter_data["who"], chapter_data["game"] = list(
                matches
            )[0].groups()
        except (Exception,) as e:
            print(chapter)
            pass
        video_data.append(chapter_data)

    return video_data


def get_id(video_url: str) -> str:
    regex = r"v=(.*)(&?)"
    matches = re.finditer(regex, video_url)
    return list(matches)[0].groups()[0]


def make_gradio_title(name: str, youtube_url: str) -> str:
    query = urllib.parse.quote(name)
    return (
        f"**{name}**   [ <a href='https://boardgamegeek.com/geeksearch.php?action=search&q={query}&objecttype=boardgame'"
        f" target='_blank'>BGG</a> ] [ <a href='{youtube_url}' target='_blank'>YouTube</a> ]"
    )


#
# DATA STRUCTURES
#
@dataclass_json
@dataclass
class RawEntry:
    year: int
    name: str
    title: str
    position: int
    url: str


@dataclass_json
@dataclass
class Game:
    title: str
    position: int
    url: str

    def __eq__(self, other):
        return self.title == other.title and self.position == other.position


@dataclass_json
@dataclass
class Person:
    name: str
    games: List[Game]

    def __eq__(self, other):
        return self.name == other.name

    def get_game(self, title: str) -> Optional[Game]:
        for game in filter(lambda x: x.title == title, self.games):
            return game
        return None

    def get_game_by_position(self, position: int) -> Optional[Game]:
        for game in filter(lambda x: x.position == position, self.games):
            return game
        return None


@dataclass_json
@dataclass
class Year:
    year: int
    people: List[Person]

    def __init__(self, year: int, people: List[Person] = None):
        self.year = year
        self.people = []
        if people:
            self.people = people

    def __eq__(self, other):
        return self.year == other.year

    def get_person(self, name: str) -> Optional[Person]:
        for people in filter(lambda x: x.name == name, self.people):
            return people
        return None


#
# PARSE LIBRARY
#
def build_raw_data(
    video_urls: List[str],
    year: int,
    parser: Callable[[Dict, str], RawEntry],
    before_return_hook: Callable[[List[RawEntry]], List[RawEntry]],
) -> List[RawEntry]:
    raw_data: List[RawEntry] = []

    for video_url in video_urls:
        video_id = get_id(video_url)
        chapters = get_chapters(video_id)[1:-1]
        for chapter in chapters:
            try:
                raw_data.append(parser(chapter, video_id, year))
            except (Exception,) as e:
                print(f"ERROR: {year} {video_url} : {chapter}")
                raise e

    return before_return_hook(raw_data)


@dataclass_json()
@dataclass()
class DB:
    years: List[Year]

    def __init__(self, years: List[Year] = []):
        self.years = years

    def get_year(self, year: int) -> Optional[Year]:
        for y in filter(lambda x: x.year == year, self.years):
            return y
        return None

    def add_from_raw_data(self, raw_data: List[RawEntry]) -> None:
        for year in set(map(lambda x: x.year, raw_data)):
            # make sure the year exists
            y = self.get_year(year)
            if not y:
                y = Year(year=year, people=[])

            for entry in raw_data:
                # make sure the person is there as well
                person = y.get_person(entry.name)
                if not person:
                    person = Person(entry.name, [])
                    y.people.append(person)

                # add the game
                game = Game(title=entry.title, position=entry.position, url=entry.url)
                if game not in person.games:
                    person.games.append(game)
                else:
                    old_game = person.get_game(game.title)
                    print(f"{old_game.title} {old_game.position} {old_game.url}")
                    print(f"{game.title} {game.position} {game.url}")
                    raise Exception(
                        f"Error, game {game.title} already present for {person.name} in {y.year}."
                    )

            self.years.append(y)

    def save_to_file(self, path: str) -> None:
        with open(path, "w+") as f:
            f.write(self.to_json())

    def save_for_gradio(self, path: str) -> None:
        data = []
        for year in self.years:
            for person in year.people:
                for game in person.games:
                    data.append(
                        [
                            year.year,
                            person.name,
                            game.title,
                            make_gradio_title(game.title, game.url),
                            game.position,
                        ]
                    )

        with open(path, "w+") as f:
            json.dump(data, f)

    def __repr__(self):
        years_str = ", ".join(map(lambda x: f"Year({x.year})", self.years))
        return f"DB(years=[{years_str}])"

    @classmethod
    def from_file(cls, path: str) -> DB:
        with open(path, "r") as f:
            data_str = f.read()
        return DB.from_json(data_str)
