from __future__ import annotations

import sqlite3
import urllib.parse
from sqlite3 import IntegrityError
from typing import Dict, List, Callable, Optional, Union, Tuple
import re

import pandas as pd
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


def make_bgg_search_link(title: str) -> str:
    query = urllib.parse.quote(title)
    return (
        f"<a href='https://boardgamegeek.com/geeksearch.php?action=search&q={query}&objecttype=boardgame' "
        f"target='_blank'>BGG</a>"
    )


def make_youtube_link(youtube_url: str) -> str:
    return f"<a href='{youtube_url}' target='_blank'>YouTube</a>"


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


#
# PARSE LIBRARY
#
def build_raw_data(
    videos_data: List[Union[str, Tuple[str, int, int]]],
    year: int,
    parser: Callable[[Dict, str], RawEntry],
    before_return_hook: Callable[[List[RawEntry]], List[RawEntry]],
) -> List[RawEntry]:
    raw_data: List[RawEntry] = []

    for video_data in videos_data:
        if type(video_data) == str:
            video_url = video_data
            start_index = 1
            end_index = -1
        else:
            video_url = video_data[0]
            start_index = video_data[1]
            end_index = video_data[2]
        video_id = get_id(video_url)
        chapters = get_chapters(video_id)[start_index:end_index]
        for chapter in chapters:
            try:
                raw_data.append(parser(chapter, video_id, year))
            except (Exception,) as e:
                print(f"ERROR: {year} {video_url} : {chapter}")
                raise e

    return before_return_hook(raw_data)


class DB:
    db_file: str
    table_name: str = "entry"

    def __init__(self, path: str):
        self.db_file = path
        connection = sqlite3.connect(self.db_file)
        cursor = connection.cursor()
        cursor.execute(
            """ SELECT count(name) FROM sqlite_master WHERE type='table' AND name='entry' """
        )
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                """CREATE TABLE entry
                    (
                        year numeric NOT NULL,
                        player text NOT NULL,
                        title text NOT NULL,
                        position numeric NOT NULL,
                        url text NOT NULL,
                        bgg_search text NOT NULL,
                        youtube_link text NOT NULL,
                        PRIMARY KEY (year, player, position),
                        CHECK(
                             length("player") > 0 AND
                             length("title") > 0 AND
                             length("url") > 0 AND
                             length("bgg_search") > 0 AND
                             length("youtube_link") > 0
                        )
                    )"""
            )
            connection.commit()
        connection.close()

    def add_entry(self, data):
        connection = sqlite3.connect(self.db_file)
        try:
            self._add_entry(data, connection)
            connection.commit()
        finally:
            connection.close()

    def _add_entry(self, connection, data):
        c = connection.cursor()
        data_placeholder = "(" + ", ".join(map(lambda x: "?", data)) + ")"
        command = f"""INSERT INTO {self.table_name} VALUES {data_placeholder}"""
        c.execute(command, data)

    def add_from_raw_data(self, raw_data: List[RawEntry]) -> None:
        try:
            connection = sqlite3.connect(self.db_file)
            for entry in raw_data:
                try:
                    entry_data = (
                        entry.year,
                        entry.name,
                        entry.title,
                        entry.position,
                        entry.url,
                        make_bgg_search_link(entry.title),
                        make_youtube_link(entry.url),
                    )
                    self._add_entry(connection, entry_data)
                except IntegrityError as e:
                    # skip it if it's already there
                    if (
                        not str(e)
                        == "UNIQUE constraint failed: entry.year, entry.player, entry.position"
                    ):
                        raise e
            connection.commit()
        finally:
            connection.close()

    def get_dataframe(self) -> pd.DataFrame:
        connection = sqlite3.connect(self.db_file)
        connection.row_factory = sqlite3.Row
        c = connection.cursor()

        c.execute("SELECT * FROM '%s'" % self.table_name)
        db_entries = c.fetchall()
        connection.close()

        data = []
        for db_entry in db_entries:
            game = f"**{db_entry['title']}**   [ {db_entry['bgg_search']} ] [ {db_entry['youtube_link']} ]"
            data.append(
                (
                    db_entry["year"],
                    db_entry["player"],
                    db_entry["title"],
                    game,
                    db_entry["position"],
                )
            )

        headers = ["Year", "Player", "Game Title", "Game", "Position"]
        df = pd.DataFrame(data)
        df.columns = headers
        return df
