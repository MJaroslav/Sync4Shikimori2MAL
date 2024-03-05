from sync4s2m.tool import Sync4Shikimori2MAL

import requests
import sys


def main():
    tool = Sync4Shikimori2MAL()
    shikimori_api, myanimelist_api = tool.login()

    # shikilist = tool.get_shikimori_list()
    # for e in shikilist:
    #     print(f"{e[0]}: {e[2]['name']}, kind: {e[2]['kind']}, status: {e[1]['status']}, updated: {e[1]['updated_at']}")

    # mallist = tool.get_myanimelist_list()
    # for e in mallist:
    #     print(f"{e[0]}: {e[2]['title']}, kind: {e[2]['media_type']}, status: {e[1]['status']}, updated: {e[1]['updated_at']}")

    delta = tool.uni_list(tool.get_delta())
    for d in delta:
        params = dict(d[1][1])
        params.update(d[1][2])
        params["title_type"] = d[1][0]
        params["modify_type"] = d[0]
        print(sys.argv[1].replace(r"\n", "\n").format(**params))

if __name__ == "__main__":
    main()
