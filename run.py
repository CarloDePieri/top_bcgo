from typing import Callable

import pandas as pd
import numpy as np
import gradio as gr

from top_bgco import DB


db = DB("lite.db")
available_years = db.get_available_years()

dataframes = {}
for df_year in available_years:
    dataframes[str(df_year)] = db.get_dataframe(df_year)

table_headers = ["Game", "Player", "Position"]

game_filter = ""
player_filter = ""


def filter_game(year: int) -> Callable[[str], pd.DataFrame]:
    _df = dataframes[str(year)]

    def wrapped(title: str) -> pd.DataFrame:
        global game_filter
        game_filter = title
        return _df.loc[
            np.where(
                _df["Game Title"].str.lower().str.contains(game_filter)
                & _df["Player"].str.lower().str.contains(player_filter)
            )
        ][table_headers].sort_values(by="Position")

    return wrapped


def filter_player(year: int) -> Callable[[str], pd.DataFrame]:
    _df = dataframes[str(year)]

    def wrapped(name: str) -> pd.DataFrame:
        global player_filter
        player_filter = name
        return _df.loc[
            np.where(
                _df["Player"].str.lower().str.contains(player_filter)
                & _df["Game Title"].str.lower().str.contains(game_filter)
            )
        ][table_headers].sort_values(by="Position")

    return wrapped


with gr.Blocks() as demo:
    gr.Markdown("# TOP games by BoardGameCo")

    with gr.Row():
        with gr.Column(scale=2):
            search = gr.Textbox(show_label=False, placeholder="Game Title")
        with gr.Column(scale=1):
            player = gr.Textbox(show_label=False, placeholder="Player")

    for tab_year in reversed(available_years):
        with gr.Tab(str(tab_year)):
            df = dataframes[str(tab_year)]
            with gr.Row():
                table = gr.DataFrame(
                    df[table_headers].sort_values(by="Position"),
                    every=1,
                    datatype=["markdown", "str", "number"],
                )

        search.change(filter_game(tab_year), search, table)
        player.change(filter_player(tab_year), player, table)


demo.queue().launch(server_port=7865, server_name="0.0.0.0")
