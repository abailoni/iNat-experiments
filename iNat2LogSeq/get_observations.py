import os
from typing import Union, List

import numpy as np
import pandas as pd
import pyinaturalist as inat
import requests
from datetime import datetime, timedelta

# # For bird songs:
# inat.get_observation_species_counts()
#
# inat.get_observation_species_counts()

from .get_taxa import create_species_taxon_page
from .parse_inat_urls import get_observations_search_filters_from_url, get_extension_audio_file
from .utils import write_lines_to_file


def create_observation_flashcards(observations_url,
                                  journals_dir="/Users/alberto-mac/repositories/logseq-cards-graph/journals",
                                  assets_dir="/Users/alberto-mac/repositories/logseq-cards-graph/assets",
                                  journal_date_format="%Y_%m_%d",
                                  mode="photos",
                                  csv_added_observations_path="/Users/alberto-mac/repositories/logseq-cards-graph/iNat_photo_obs_in_graph.csv",
                                  max_additions=10,
                                  days_back_from_observed_before: int = None,
                                  observed_before_this_date: str = None,
                                  require_research_grade: bool = True,
                                  captive: bool = False,
                                  extra_tags: List = None
                                  ):
    """

    :param observations_url:
    :param journals_dir:
    :param assets_dir:
    :param journal_date_format:
    :param mode:
    :param csv_added_observations_path:
    :param max_additions:
    :param days_back_from_observed_before: By default, go back as much as possible
    :param observed_before_this_date: By default, today's date. Format: yyyy-MM-dd
    :param require_research_grade:
    :param captive:
    :param extra_tags:
    :return:
    """
    assert mode in ["photos", "sounds"]

    assets_subdir = f"iNat_{mode}"
    # TODO: pass general folder of LogSeq dataset instead
    # Get the date to write in the correct journal note:
    now = datetime.now()  # current date and time
    journal_path = os.path.join(journals_dir, f"{now.strftime(journal_date_format)}.md")

    os.makedirs(os.path.split(csv_added_observations_path)[0], exist_ok=True)

    if os.path.isfile(csv_added_observations_path):
        # obs_in_logseq_graph = np.genfromtxt('csv_added_observations_path', delimiter=',').astype('int')
        try:
            obs_in_logseq_graph = pd.read_csv(csv_added_observations_path, index_col=None).to_numpy().astype('int')
            assert obs_in_logseq_graph.ndim == 2, obs_in_logseq_graph.shape
            obs_in_logseq_graph = obs_in_logseq_graph[:, 0]
        except pd.errors.EmptyDataError:
            obs_in_logseq_graph = np.array([-1], dtype='int')
        obs_in_logseq_graph = np.sort(obs_in_logseq_graph)
    else:
        obs_in_logseq_graph = np.array([-1], dtype='int')

    search_filters = get_observations_search_filters_from_url(observations_url)

    # Compute d2 date (observed before d2):
    if observed_before_this_date is not None:
        assert isinstance(observed_before_this_date, str)
        try:
            observed_before_this_date = datetime.strptime(observed_before_this_date, '%Y-%m-%d')
            search_filters["d2"] = observed_before_this_date.strftime("%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Incorrect data format, should be YYYY-MM-DD: {observed_before_this_date}")
    else:
        observed_before_this_date = now

    # Compute d1 date (observed after d1):
    if days_back_from_observed_before is not None:
        assert isinstance(days_back_from_observed_before, int)
        d = observed_before_this_date - timedelta(days=days_back_from_observed_before)
        search_filters.setdefault("d1", d.strftime("%Y-%m-%d"))

    # Note: this does not assure that the community taxon is also a species (checked later):
    search_filters.setdefault("hrank", "species")
    # Increase the results per page:
    search_filters.setdefault("per_page", 100)
    # search_filters.setdefault("identified", True) # Now covered by research grade, depending on user's choice
    if mode == "photos":
        # search_filters.setdefault("photos", mode == "photos")
        search_filters["photos"] = True
    elif mode == "sounds":
        # search_filters.setdefault("sounds", mode == "sounds")
        search_filters["sounds"] = True
    if require_research_grade:
        search_filters["quality_grade"] = "research"
    if captive:
        assert not require_research_grade, "Captive observations cannot be research grade (set `research_grade` to False)"
        search_filters["captive"] = True
    # search_filters["verifiable"] = True
    # search_filters.pop("d1")
    # search_filters.pop("d2")
    response = inat.get_observations(**search_filters)
    my_observations = inat.Observation.from_json_list(response)

    intro_block_written = False
    new_journal_lines = []
    i = 0
    # Start from the most recent...?
    for obs in my_observations:
        if i >= max_additions:
            break

        # Check whether the obs was already added as flashcard:
        index = np.searchsorted(obs_in_logseq_graph, obs.id)
        add_obs = True if index == len(obs_in_logseq_graph) else obs_in_logseq_graph[index] != obs.id

        if add_obs:
            # Research grade already filters out all obs without community ID of species.
            # If we don't look for research grade, we should get the community ID only if it is a species:
            identified_taxon_id = obs.community_taxon_id if require_research_grade else obs.taxon.id
            if obs.community_taxon_id is not None and not require_research_grade:
                community_taxon = inat.Taxon.from_json_list(inat.get_taxa_by_id(taxon_id=obs.community_taxon_id))[0]
                identified_taxon_id = community_taxon.id if community_taxon.rank == "species" else identified_taxon_id

            # FIXME: cannot handle hybrid taxa atm
            if inat.Taxon.from_json_list(inat.get_taxa_by_id(taxon_id=identified_taxon_id))[0].rank == "hybrid":
                continue

            if not intro_block_written:
                new_journal_lines.append(f"- ## iNat {mode} flashcards")
                extra_line = f"  [[iNat {mode} flashcards]]"

                # Add some optional tags to flashcards:
                if extra_tags is not None:
                    assert isinstance(extra_tags, (tuple, list))
                    if len(extra_tags) > 0:
                        extra_line += f", [[{ ']], [['.join(extra_tags) + ']]'}"
                new_journal_lines.append(extra_line)
                new_journal_lines.append("  collapsed:: true")
                intro_block_written = True
            # "num_identification_agreements"
            obs_date = obs.created_at.strftime('%d/%m/%Y, %H:%M')
            print(f"Downloading observation of {obs.taxon.name} ({obs_date})...")
            # print(f"Creating taxa and ancestors...")
            taxon_name, full_taxon_name = create_species_taxon_page(identified_taxon_id)

            # Download image or sound:
            if mode == "photos":
                asset_response = requests.get(obs.photos[0].medium_url)
                asset_filename = f"iNat_obs_{mode}_{obs.id}.jpg"
            elif mode == "sounds":
                file_url = obs.sounds[0]["file_url"]
                file_extension = get_extension_audio_file(file_url)
                asset_response = requests.get(file_url)
                asset_filename = f"iNat_obs_{mode}_{obs.id}" + file_extension
            else:
                raise ValueError(mode)
            asset_path = os.path.join(assets_dir, assets_subdir, asset_filename)
            open(asset_path, "wb").write(asset_response.content)

            # Create first bullet point with image and some extra info (place, date):
            # TODO: this is not Windows proof
            new_journal_lines.append(
                f"\t- ![{asset_filename}](../assets/{assets_subdir}/{asset_filename}){{:height 200, :width 200}}"
            )
            guessed_places = obs.place_guess.split(', ')
            new_journal_lines.append(
                f"\t  [Observation]({obs.uri}) by [[{obs.user.username}]] on {obs_date} "
            )
            new_journal_lines.append(f"\t  {'[[' + ']], [['.join(guessed_places) + ']]'} #card")
            # new_journal_lines.append(f"\t  [[iNat {mode} flashcards]] #card")
            new_journal_lines.append("\t  collapsed:: true")

            # Create second (nested) bullet point with link to Species page:
            new_journal_lines.append("\t\t- {{embed [[" + full_taxon_name + "]]}}")

            # Add obs ID to array
            obs_in_logseq_graph = np.insert(obs_in_logseq_graph, index, obs.id)
            i += 1

    # Append new lines to today's journal page:
    write_lines_to_file(journal_path, new_journal_lines)
    pd.DataFrame(obs_in_logseq_graph, columns=["Observation ID"]).to_csv(csv_added_observations_path, index=None)
