# import altair as alt
# import pandas as pd
import os

from IPython.display import Image
# from pyinaturalist import (
#     Taxon,
#     enable_logging,
#     get_taxa,
#     get_taxa_autocomplete,
#     get_taxa_by_id,
#     pprint,
# )
import pyinaturalist as inat

from rich import print

# inat.enable_logging()

from .parse_inat_urls import get_taxon_id
from .utils import write_lines_to_file, get_local_names_from_taxa_names_attribute


def create_species_taxon_page(taxon,
                              taxon_directory="/Users/alberto-mac/repositories/logseq-cards-graph/pages/iNat_taxon",
                              locales=("en", "it", "de", "fr", "es")):
    """
    Currently it expect a species taxa.
    It checks if the page is already present
    """
    if isinstance(taxon, (int, str)):
        taxon_id = taxon if isinstance(taxon, int) else get_taxon_id(taxon)
        response = inat.get_taxa(taxon_id=taxon_id,
                                 all_names=True,
                                 rank="species"  # Only get species
                                 )
        taxon = inat.Taxon.from_json_list(response)
        # Check that we got exactly one result:
        assert len(taxon) == 1
        taxon = taxon[0]

    if isinstance(taxon, inat.Taxon):
        # FIXME: should check if it has all names...!

        assert taxon.rank == 'species'

        # -----------------
        # Write ancestors pages:
        # -----------------
        ancestors = inat.Taxon.from_json_list(inat.get_taxa_by_id(taxon.ancestor_ids[:-1]))
        # Only keep ancestors up to the class:
        ancestors = [anc for anc in ancestors if anc.rank_level <= 70]
        ancestors_names = [anc.name for anc in ancestors]
        # ancestors_full_names = [anc.name for anc in ancestors]
        for i in range(len(ancestors)):
            # Compose page name of the ancestor and create .md file:
            anc = ancestors[i]
            ancestor_page_name = '___'.join(ancestors_names[:i + 1]) + ".md"
            ancestor_page_path = os.path.join(taxon_directory, ancestor_page_name)
            if not os.path.exists(ancestor_page_path):
                page_content = [
                    # f"full-name:: {{{{cloze {anc.full_name}}}}}",
                    f"rank:: [[{anc.rank}]]",
                    f"full-name:: {anc.full_name}",
                    f"alias:: [[{anc.name}]]",
                    f"iNat-url:: {anc.url}",
                    f"wiki-url:: {anc.wikipedia_url}",
                ]
                write_lines_to_file(ancestor_page_path, page_content)

        # -----------------
        # Write species page:
        # -----------------
        page_name = '___'.join(ancestors_names + [taxon.name]) + ".md"
        page_path = os.path.join(taxon_directory, page_name)
        if not os.path.exists(page_path):
            local_names = get_local_names_from_taxa_names_attribute(taxon,
                                                                    locales=locales)
            page_content = [
                f"rank:: [[{taxon.rank}]]",
                f"alias:: [[{taxon.name}]]",
            ]
            for loc in locales:
                if loc in local_names:
                    # page_content.append(f"{loc}:: {{{{cloze {', '.join(local_names[loc])}}}}}")
                    page_content.append(f"{loc}:: {', '.join(local_names[loc])}")
            page_content += [
                f"iNat-url:: {taxon.url}",
                f"wiki-url:: {taxon.wikipedia_url}",
                # f"rank:: [[{taxon.rank}]]",
            ]
            write_lines_to_file(page_path, page_content)
        return taxon.name, '/'.join(ancestors_names + [taxon.name])
    else:
        raise ValueError(f"Passed taxon type is not supported: {taxon}")

# basic_fields = ['preferred_common_name', 'observations_count', 'wikipedia_url', 'wikipedia_summary']
# print({f: response['results'][0][f] for f in basic_fields})

# taxa = Taxon.from_json_list(response)
