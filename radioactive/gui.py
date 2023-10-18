from typing import Optional, Callable, List

from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from zenlog import log

from radioactive.alias import Station
from radioactive.player import Player


class SearchResultColumn:
    def __init__(self, add_column: Callable[[Table], None],
                 extract_value: Callable[[Station], str]):
        self._add_column = add_column
        self._extract_value = extract_value

    def add_column(self, table: Table):
        self._add_column(table)

    def extract_value(self, station: Station) -> str:
        return self._extract_value(station)

def print_welcome_screen():
    welcome = Panel(
        """
        :radio: Play any radios around the globe right from this Terminal [yellow]:zap:[/yellow]!
        :smile: Author: Dipankar Pal
        :question: Type '--help' for more details on available commands
        :bug: Visit: https://github.com/deep5050/radio-active to submit issues
        :star: Show some love by starring the project on GitHub [red]:heart:[/red]
        :dollar: You can donate me at https://deep5050.github.io/payme/
        :x: Press Ctrl+C to quit
        """,
        title="[b]RADIOACTIVE[/b]",
        width=85,
    )
    print(welcome)


def print_update_screen(app):
    if app.is_update_available():
        update_msg = (
            "\t[blink]An update available, run [green][italic]pip install radio-active=="
            + app.get_remote_version()
            + "[/italic][/green][/blink]\nSee the changes: https://github.com/deep5050/radio-active/blob/main/CHANGELOG.md"
        )
        update_panel = Panel(
            update_msg,
            width=85,
        )
        print(update_panel)
    else:
        log.debug("Update not available")


def print_favorite_table(alias):
    log.info("Your favorite station list is below")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Station", justify="left")
    table.add_column("URL / UUID", justify="left")
    if len(alias.alias_map) > 0:
        for entry in alias.alias_map:
            table.add_row(entry["name"], entry["uuid_or_url"])
        print(table)
        log.info(f"Your favorite stations are saved in {alias.alias_path}")
    else:
        log.info("You have no favorite station list")

def print_current_play_panel(player: Optional[Player], curr_station_name=""):
    print()
    now_playing = curr_station_name
    if player:
        now_playing += f"\n{player.read_title()}"
    panel_station_name = Text(now_playing, justify="center")

    station_panel = Panel(panel_station_name, title="[blink]:radio:[/blink]", width=85)
    console = Console()
    console.print(station_panel)


def print_search_result(result: List[Station], columns: List[SearchResultColumn]):
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("ID", justify="center")

    for column in columns:
        column.add_column(table)
    for i, res in enumerate(result):
        table.add_row(
            *([str(i + 1)] + [column.extract_value(res) for column in columns])
        )
    console = Console()
    console.print(table)
    log.info(
        "If the table does not fit into your screen, \
        \ntry to maximize the window , decrease the font by a bit and retry"
    )
