from sync4s2m.tool import Sync4Shikimori2MAL

import requests


def main():
    tool = Sync4Shikimori2MAL()
    shikimori_api, myanimelist_api = tool.login()


    # result = shikimori_api.client.get(
    #     f"/users/{shikimori_api.whoami['id']}/anime_rates",
    #     params={"limit": 5000},
    # ).json()
    # sresult = {e["anime"]["id"]: e["anime"]["name"] for e in result}

    # result = myanimelist_api.client.get(
    #     "/users/@me/animelist", params={"limit": 1000}
    # ).json()
    # mresult = {e["node"]["id"]: e["node"]["title"] for e in result["data"]}


    # result = {
    #     sid: [sname, mresult[sid] if sid in mresult else ""]
    #     for sid, sname in sresult.items()
    # }
    # for mid, mname in mresult.items():
    #     if mid in result:
    #         result[mid][1] = mname
    #     else:
    #         result[mid] = ["", mname]
    # result = list(map(lambda e: (e[0], e[1][0], e[1][1]), result.items()))
    # result.sort(key=lambda e: (int(e[0]), e[1], e[2]))
    # result = list(map(str, result))
    # print("\n".join(result))

    shikilist = tool.get_shikimori_list()

    for e in shikilist:
        t = e[0]
        print(f"{t}: {e[1][t]['name']}, kind: {e[1][t]['kind']}")
    # shikilist = [(e[0], e[1]["anime"]["name"] if "anime" in e[1] else e[1]["manga"]["name"] if "manga" in e[1] else e[1]["ranobe"]["name"]) for e in shikilist]
    # shikilist1 = [(e[0], e[1]["name"]) for e in shikilist]
    # shikilist2 = list(map(str, shikilist1))
    # print("\n".join(shikilist2))
    # for t, data in shikilist:
    #     d = None
    #     if t == "manga":
    #         print(d)
    #     if data:
    #         if "anime" in data:
    #             d = data["anime"]
    #         elif "manga" in data:
    #             d = data["manga"]
    #         elif "ranobe" in data:
    #             t = "ranobe"
    #             d = data["ranobe"]
    #         else:
    #             t = "UNKNOWN"
    #             d = {}
    #         d = d["name"] if d and "name" in d else "UNTITLED???"
    #     print(f"('{t}', '{d}')")


if __name__ == "__main__":
    main()
