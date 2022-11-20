import pyinaturalist as inat
import pandas as pd

def write_lines_to_file(path,
                        lines,
                        write_mode='a+',
                        append_initial_line=True):
    if 'a' in write_mode and append_initial_line:
        lines = ["\n"] + lines
    with open(path, write_mode) as f:
        f.write('\n'.join(lines))


def get_local_names_from_taxa_names_attribute(taxon, locales):
    """
    Commonly used locales: 'it', 'de', 'en', 'fr',
    :param taxon:
    :param locales:
    :return:
    """
    assert isinstance(taxon, inat.Taxon)
    assert isinstance(locales, (list, tuple))

    df_names = pd.DataFrame(taxon.names)
    df_names = df_names[df_names["is_valid"] & df_names["locale"].isin(locales)].sort_values("position", ascending=True)
    return df_names.groupby("locale")["name"].apply(lambda x: x.to_list()).to_dict()
