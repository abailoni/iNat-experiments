import argparse
import sys

from iNat2LogSeq.get_observations import create_observation_flashcards


# TODO: allow to get ones not identified by community...?

def main():
    # print(sys.argv)
    parser = argparse.ArgumentParser(description='iNat2LogSeq parameters')

    # settings for CPU vs GPU
    parser.add_argument('--type', required=True, help='photos or sounds')
    parser.add_argument('-u', '--url', type=str, help='iNaturalist url',
                        default="https://www.inaturalist.org/observations?place_id=any&subview=table&user_id=rhem42"
                        )
    # FIXME: currently one page is set to 60 items (no more than those)
    parser.add_argument('--max', type=int, default=30, help='Max downloaded items')
    parser.add_argument('--days_back', type=int, default=None, help='How many days to go back')
    parser.add_argument('--observed_before_this_date', type=str, default=None,
                        help='Only observations before this date')
    parser.add_argument('--dont_require_research_grade', action="store_false", help='')
    parser.add_argument('--in_captivity', action="store_true", help='Also get obs in captivity')
    parser.add_argument('-t', '--extra_tags', nargs='*', help='Optional extra tags to add to flashcards',
                        default=None)
    # Use like:
    # python arg.py -l 1234 2345 3456 4567
    args = parser.parse_args()
    extra_kwargs = {}
    if args.type == "sounds":
        extra_kwargs["csv_added_observations_path"] = \
            "/Users/alberto-mac/repositories/logseq-cards-graph/iNat_sounds_obs_in_graph.csv"

    create_observation_flashcards(args.url,
                                  mode=args.type,
                                  max_additions=args.max,
                                  days_back_from_observed_before=args.days_back,
                                  observed_before_this_date=args.observed_before_this_date,
                                  require_research_grade=args.dont_require_research_grade,
                                  captive=args.in_captivity,
                                  extra_tags=args.extra_tags,
                                  **extra_kwargs
                                  )


if __name__ == '__main__':
    main()
