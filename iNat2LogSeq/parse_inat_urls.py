import re


def get_taxon_id(inat_taxa_url, ensure_valid_url=True):
    """
    Example: https://www.inaturalist.org/taxa/873626-Pinus-sylvestris-sylvestris
    """
    regex = r'www\.inaturalist\.org/taxa/(\d*)'
    matches = re.finditer(regex, inat_taxa_url, re.MULTILINE)
    matched_tax_id = None
    for matchNum, match in enumerate(matches, start=1):
        assert len(match.groups()) == 1
        for groupNum in range(0, len(match.groups())):
            groupNum = groupNum + 1
            matched_tax_id = int(match.group(groupNum))
            # print("Group {groupNum} found at {start}-{end}: {group}".format(groupNum=groupNum,
            #                                                                 start=match.start(groupNum),
            #                                                                 end=match.end(groupNum),
            #                                                                 group=match.group(groupNum)))

    if ensure_valid_url:
        assert matched_tax_id is not None, f"The passed url is not a valid one for taxa: {inat_taxa_url} "
    return matched_tax_id


def get_observations_search_filters_from_url(inat_obs_search_url):
    """
    https://www.inaturalist.org/observations?place_id=any&user_id=rhem42&verifiable=any
    """
    assert inat_obs_search_url.startswith("https://www.inaturalist.org/observations?")
    _, url_filter_options = inat_obs_search_url.split("www.inaturalist.org/observations?")
    pattern = r'([^&]+)&?'
    # pattern = r'([^=]*)=([^&]*)&?'
    search_kwargs = {}
    for search_option in re.findall(pattern, url_filter_options):
        pattern2 = r'([^=]+)'
        matches = [m for m in re.findall(pattern2, search_option)]
        assert len(matches) == 1 or len(matches) == 2
        if matches[0] != "view":
            if len(matches) == 2:
                search_kwargs[matches[0]] = matches[1]
            else:
                search_kwargs[matches[0]] = True
    return search_kwargs


def get_extension_audio_file(audio_file_url):
    """
    :param audio_file_url: Example https://static.inaturalist.org/sounds/106308.mp3?1591992369
    :return:
    """
    regex = r"sounds\/[^.]+(.[^?]+)\?\d+"

    matches = re.finditer(regex, audio_file_url, re.MULTILINE)

    extension = []
    for matchNum, match in enumerate(matches, start=1):
        for groupNum in range(0, len(match.groups())):
            groupNum = groupNum + 1
            extension.append(match.group(groupNum))
    assert len(extension) == 1
    return extension[0]
