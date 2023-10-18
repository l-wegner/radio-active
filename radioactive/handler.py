"""
    This handler solely depends on pyradios module to communicate with our remote API
"""
import datetime
import json
import sys
from typing import Any, Dict

import requests_cache
from pyradios import RadioBrowser
from zenlog import log

from radioactive.gui import print_search_result, SearchResultColumn


def trim_string(text, max_length=40):
    if len(text) > max_length:
        return text[:max_length - 3] + "..."
    else:
        return text


class Handler:
    """
    radio-browser API handler. This module communicates with the underlying API via PyRadios
    """

    def __init__(self):
        self.API = None
        self.response = None
        self.target_station = None
        self.countries = Dict[str, Any]
        # When RadioBrowser can not be initiated properly due to no internet (probably)
        try:
            expire_after = datetime.timedelta(days=3)
            session = requests_cache.CachedSession(
                cache_name="cache", backend="sqlite", expire_after=expire_after
            )
            self.API = RadioBrowser(session=session)
        except Exception as e:
            log.debug("Error: {}".format(e))
            log.critical("Something is wrong with your internet connection")
            sys.exit(1)

    def get_country_code(self, name):
        if not self.countries:
            self.countries = self.API.countries()
        for country in self.countries:
            if country["name"].lower() == name.lower():
                return country["iso_3166_1"]
        return None

    def station_validator(self):
        """Validates a response from the API and takes appropriate decision"""

        # when no response from the API
        if not self.response:
            log.error("No stations found by the name")
            return []

        # when multiple results found
        if len(self.response) > 1:
            log.warn(f"showing {len(self.response)} stations with the name!")
            print_search_result(self.response,
                                [column_station(50),
                                 # column_uuid.add_column(table)
                                 column_country_code,
                                 column_tags(40)])
            return self.response

        # when exactly one response found
        if len(self.response) == 1:
            log.info(
                "Station found: {}".format(self.response[0]["name"].strip()))
            log.debug(json.dumps(self.response[0], indent=3))
            self.target_station = self.response[0]
            # register a valid click to increase its popularity
            self.API.click_counter(self.target_station["stationuuid"])

            return self.response
            # return self.response[0]["name"].strip()

    # ---------------------------- NAME -------------------------------- #
    def search_by_station_name(self, _name=None, limit=100):
        """search and play a station by its name"""
        try:
            self.response = self.API.search(name=_name, name_exact=False,
                                            limit=limit)
            return self.station_validator()
        except Exception as e:
            log.debug("Error: {}".format(e))
            log.error("Something went wrong. please try again.")
            sys.exit(1)

    # ------------------------- UUID ------------------------ #
    def play_by_station_uuid(self, _uuid):
        """search and play station by its stationuuid"""
        try:
            self.response = self.API.station_by_uuid(_uuid)
            return self.station_validator()  # should return a station name also
        except Exception as e:
            log.debug("Error: {}".format(e))
            log.error("Something went wrong. please try again.")
            sys.exit(1)

    # -------------------------- COUNTRY ----------------------#
    def discover_by_country(self, country_code_or_name, limit):
        # check if it is a code or name
        if len(country_code_or_name.strip()) == 2:
            # it's a code
            log.debug("Country code {} provided".format(country_code_or_name))
            try:
                response = self.API.search(
                    countrycode=country_code_or_name, limit=limit
                )
            except Exception as e:
                log.debug("Error: {}".format(e))
                log.error("Something went wrong. please try again.")
                sys.exit(1)
        else:
            # it's name
            log.debug("Country name {} provided".format(country_code_or_name))
            code = self.get_country_code(country_code_or_name)
            if code:
                try:
                    response = self.API.search(
                        countrycode=code, limit=limit, country_exact=True
                    )
                except Exception as e:
                    log.debug("Error: {}".format(e))
                    log.error("Something went wrong. please try again.")
                    sys.exit(1)
            else:
                log.error("Not a valid country name")
                sys.exit(1)

        if len(response) > 1:
            log.info("Result for country: {}".format(response[0]["country"]))
            print_search_result(response,
                                [column_station(30),
                                 # column_uuid.add_column(table)
                                 column_state,
                                 column_tags(20),
                                 column_language])

            return response
        else:
            log.error(
                "No stations found for the country code/name, recheck it")
            sys.exit(1)

    # ------------------- by state ---------------------

    def discover_by_state(self, state, limit):
        try:
            discover_result = self.API.search(state=state, limit=limit)
        except Exception:
            log.error("Something went wrong. please try again.")
            sys.exit(1)

        if len(discover_result) > 1:
            print_search_result(discover_result,
                                [column_station(30),
                                 # column_uuid.add_column(table)
                                 column_country,
                                 column_tags(20),
                                 column_language])

            return discover_result
        else:
            log.error("No stations found for the state, recheck it")
            sys.exit(1)

    # -----------------by language --------------------

    def discover_by_language(self, language, limit):
        try:
            discover_result = self.API.search(language=language, limit=limit)
        except Exception as e:
            log.debug("Error: {}".format(e))
            log.error("Something went wrong. please try again.")
            sys.exit(1)

        if len(discover_result) > 1:
            print_search_result(discover_result,
                                [column_station(30),
                                 # column_uuid.add_column(table)
                                 column_country,
                                 column_tags(30)])

            return discover_result
        else:
            log.error("No stations found for the language, recheck it")
            sys.exit(1)

    # -------------------- by tag ---------------------- #

    def discover_by_tag(self, tag, limit):
        try:
            discover_result = self.API.search(tag=tag, limit=limit)
        except Exception as e:
            log.debug("Error: {}".format(e))
            log.error("Something went wrong. please try again.")
            sys.exit(1)

        if len(discover_result) > 1:
            print_search_result(discover_result,
                                [column_station(30),
                                 # column_uuid.add_column(table)
                                 column_country,
                                 column_language])
            return discover_result
        else:
            log.error("No stations found for the tag, recheck it")
            sys.exit(1)

    # ---- increase click count ------------- #
    def vote_for_uuid(self, UUID):
        try:
            result = self.API.click_counter(UUID)
            return result
        except Exception as e:
            log.debug(
                "Something went wrong during increasing click count:{}".format(
                    e))


column_station = lambda max_length: SearchResultColumn(
    lambda table: table.add_column("Station", justify="left"),
    lambda station: trim_string(station["name"], max_length=max_length))

column_uuid = SearchResultColumn(
    lambda table: table.add_column("UUID", justify="center"),
    lambda station: trim_string(station["stationuuid"]))

column_country_code = SearchResultColumn(
    lambda table: table.add_column("Country", justify="center"),
    lambda station: station["countrycode"])

column_country = SearchResultColumn(
    lambda table: table.add_column("Country", justify="center"),
    lambda station: trim_string(station["country"], max_length=20))

column_state = SearchResultColumn(
    lambda table: table.add_column("State", justify="center"),
    lambda station: station["state"])

column_tags = lambda max_length: SearchResultColumn(
    lambda table: table.add_column("Tags", justify="center"),
    lambda station: trim_string(station["tags"], max_length=max_length))

column_language = SearchResultColumn(
    lambda table: table.add_column("Language", justify="center"),
    lambda station: trim_string(station["language"]))

