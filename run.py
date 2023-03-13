import pandas as pd
import numpy as np
import gradio as gr
import json


with open("gradio.json", "r") as f:
    data = json.load(f)

# create data
headers = ["Year", "Player", "Game Title", "Game", "Position"]
table_headers = ["Year", "Player", "Game", "Position"]
df = pd.DataFrame(data)
df.columns = headers
# df

game_filter = ""
player_filter = ""


def filter_game(title: str) -> pd.DataFrame:
    global game_filter
    game_filter = title
    return df.loc[
        np.where(
            df["Game Title"].str.lower().str.contains(game_filter)
            & df["Player"].str.lower().str.contains(player_filter)
        )
    ][table_headers].sort_values(by="Position")


def filter_player(name: str) -> pd.DataFrame:
    global player_filter
    player_filter = name
    return df.loc[
        np.where(
            df["Player"].str.lower().str.contains(player_filter)
            & df["Game Title"].str.lower().str.contains(game_filter)
        )
    ][table_headers].sort_values(by="Position")


with gr.Blocks() as demo:
    gr.Markdown("# TOP BoardGameCo")
    with gr.Row():
        player = gr.Textbox(show_label=False, placeholder="Player")
        search = gr.Textbox(show_label=False, placeholder="Game Title")
    with gr.Row():
        table = gr.DataFrame(
            df[table_headers].sort_values(by="Position"),
            every=1,
            datatype=["number", "str", "markdown", "number"],
        )
    search.change(filter_game, search, table)
    player.change(filter_player, player, table)

demo.queue().launch()  # Run the demo using queuing
