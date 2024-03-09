import json


TYPE_ANIME = "anime"
TYPE_MANGA = "manga"
TYPE_RANOBE = "ranobe"
TYPE = [TYPE_ANIME, TYPE_MANGA, TYPE_RANOBE]

MODIFY_ADDED = "added"
MODIFY_EDITED = "edited"
MODIFY_REMOVED = "removed"
MODIFY_UNMODIFIED = "unmodified"
MODIFY = [MODIFY_ADDED, MODIFY_EDITED, MODIFY_REMOVED, MODIFY_UNMODIFIED]

WATCH_PLANNED = "planned"
WATCH_WATCHING = "watching"
WATCH_COMPLETED = "completed"
WATCH_REWATCHING = "rewatching"
WATCH_ON_HOLD = "on_hold"
WATCH_DROPPED = "dropped"
WATCH = [
    WATCH_PLANNED,
    WATCH_WATCHING,
    WATCH_COMPLETED,
    WATCH_REWATCHING,
    WATCH_ON_HOLD,
    WATCH_DROPPED,
]


class Title:
    def __init__(
        self,
        type_: str,
        title = None,
        raw_title: dict = None,
        parse_func=None,
        modify_type: str = MODIFY_UNMODIFIED,
        delta: dict = {},
    ):
        self._type_ = type_
        self._modify_type_ = modify_type
        self._delta_ = json.dumps(delta)
        if title:
            self._id_ = title.get_id()
            self._raw_ = title.get_raw()
            self._name_ = title.get_name()
            self._watch_status_ = title.get_watch_status()
            self._episodes_ = title.get_episodes()
            self._chapters_ = title.get_chapters()
            self._volumes_ = title.get_volumes()
            self._rewatches_ = title.get_rewatches()
            self._comment_ = title.get_comment()
            self._score_ = title.get_score()
        else:
            self._raw_ = raw_title
            parse_func(self, raw_title)
        self.validate()

    def validate(self):
        flag = False
        if self.get_id() < 1:
            raise ValueError(f"Title {self._raw_} not validated: id {self.get_id()}")
        if self.get_modify_type() not in MODIFY:
            raise ValueError(f"Title {self._raw_} not validated: modify type {self.get_modify_type()}")
        if self.get_type() not in TYPE:
            raise ValueError(f"Title {self._raw_} not validated: type {self.get_type()}")
        if self.get_watch_status() not in WATCH:
            raise ValueError(f"Title {self._raw_} not validated: watch status {self.get_watch_status}")
        if self.get_episodes() < 0:
            raise ValueError(f"Title {self._raw_} not validated: episodes {self.get_episodes()}")
        if self.get_chapters() < 0:
            raise ValueError(f"Title {self._raw_} not validated: chapters {self.get_chapters()}")
        if self.get_volumes() < 0:
            raise ValueError(f"Title {self._raw_} not validated: volumes {self.get_volumes()}")
        if self.get_watch_count() < 0:
            raise ValueError(f"Title {self._raw_} not validated: watch count {self.get_volumes()}")
        score = self.get_score()
        if score < 0 or score > 10:
            raise ValueError(f"Title {self._raw_} not validated: score {score}")
        if self.get_rewatches() < 0:
            raise ValueError(f"Title {self._raw_} not validated: rewatches {self.get_rewatches()}")

    def _parse_title_(self, raw_title: dict):
        raise NotImplementedError()

    def get_raw(self) -> str:
        return self._raw_

    def get_id(self) -> int:
        return self._id_

    def get_type(self) -> str:
        return self._type_

    def is_anime(self) -> bool:
        return self.get_type() == TYPE_ANIME

    def is_manga(self) -> bool:
        return self.get_type() == TYPE_MANGA

    def is_ranobe(self) -> bool:
        return self.get_type() == TYPE_RANOBE

    def get_modify_type(self) -> str:
        return self._modify_type_

    def is_added(self) -> bool:
        return self.get_modify_type() == MODIFY_ADDED

    def is_edited(self) -> bool:
        return self.get_modify_type() == MODIFY_EDITED

    def is_removed(self) -> bool:
        return self.get_modify_type() == MODIFY_REMOVED

    def get_name(self) -> str:
        return self._name_

    def get_watch_status(self) -> str:
        return self._watch_status_

    def is_planned(self) -> bool:
        return self.get_watch_status() == WATCH_PLANNED

    def is_watching(self) -> bool:
        return self.get_watch_status() == WATCH_WATCHING

    def is_completed(self) -> bool:
        return self.get_watch_status() == WATCH_COMPLETED

    def is_rewatching(self) -> bool:
        return self.get_watch_status() == WATCH_REWATCHING

    def is_on_hold(self) -> bool:
        return self.get_watch_status() == WATCH_ON_HOLD

    def is_dropped(self) -> bool:
        return self.get_watch_status() == WATCH_DROPPED

    def get_watch_count(self) -> int:
        return max(self.get_episodes(), self.get_chapters())

    def get_episodes(self) -> int:
        return self._episodes_

    def get_chapters(self) -> int:
        return self._chapters_

    def get_volumes(self) -> int:
        return self._volumes_

    def get_comment(self) -> str:
        return self._comment_

    def has_comment(self) -> bool:
        return bool(self.get_comment())

    def get_score(self) -> int:
        return self._score_

    def get_rewatches(self) -> int:
        return self._rewatches_

    def get_delta(self) -> dict:
        return self._delta_

    def to_dict(self, for_comparing=False) -> dict:
        result = {}
        result["id"] = self.get_id()
        result["name"] = self.get_name()
        result["watch_status"] = self.get_watch_status()
        result["watch_count"] = self.get_watch_count()
        result["episodes"] = self.get_episodes()
        result["chapters"] = self.get_chapters()
        result["volumes"] = self.get_volumes()
        result["comment"] = self.get_comment()
        result["score"] = self.get_score()
        result["rewatches"] = self.get_rewatches()
        if not for_comparing:
            result["title_type"] = self.get_type()
            result["modify_type"] = self.get_modify_type()
            result["delta"] = self.get_delta()
        return result

    def format(self, template: str) -> str:
        return template.format(**self.to_dict())

    def delta_dict(self, other) -> dict:
        return dict(self.to_dict().items() ^ other.to_dict().items())

    def __eq__(self, other) -> bool:
        return self.to_dict() == other

    def __str__(self) -> str:
        return self.format(
            "{modify_type} {title_type} {id} '{name}' with delta {delta}"
        )


class TitleList(object):
    def __init__(self, titles: list[Title] = []):
        self.__title_dict__ = {title.get_id(): title for title in titles}

    def print_list(self, template: str):
        for _, title in self.__title_dict__.items():
            print(title.format(template))

    def __len__(self):
        return len(self.__title_dict__)

    def __getitem__(self, key) -> Title:
        return self.__title_dict__[key]

    def __delitem__(self, key):
        del self.__title_dict__[key]

    def __contains__(self, item) -> bool:
        return (
            isinstance(item, Title)
            and item.get_id() in self.__title_dict__
        )

    def __add__(self, other):
        if isinstance(other, TitleList):
            self.update(other)
        elif isinstance(other, Title):
            self.append(other)
        else:
            raise NotImplementedError(f"Can't add {type(other)} to TitleList")

    def __iter__(self):
        return iter(self.items())

    def update(self, other):
        self.__title_dict__.update(dict(other))

    def append(self, title: Title):
        self.__title_dict__[title["id"]] = title

    def items(self) -> list[Title]:
        return [e[1] for e in self.__title_dict__.items()]

    def delta(self, another):
        added = [
            Title(
                title.get_type(), title, modify_type=MODIFY_ADDED, delta=title.to_dict(True)
            )
            for title in filter(lambda title: title not in another, self)
        ]
        removed = [
            Title(
                title.get_type(),
                title,
                modify_type=MODIFY_REMOVED,
                delta=title.to_dict(True),
            )
            for title in filter(lambda title: title not in self, another)
        ]
        edited = []
        for another_title in list(filter(lambda title: title in self, another)):
            title = self[another_title.get_id()]
            another_title_dict = another_title.to_dict(True)
            title_dict = title.to_dict(True)
            if title_dict != another_title_dict:
                edited.append(
                    Title(
                        title.get_type(),
                        title,
                        modify_type=MODIFY_EDITED,
                        delta=title.delta_dict(another_title),
                    )
                )
        return TitleList(added + edited + removed)

    def commit(self, client, commit_func):
        if not commit_func:
            raise ValueError("Commit function cannot be None")
        else:
            commit_func(client)
    
    def to_list(self) -> list[dict]:
        return [title.to_dict() for title in self.items()]


def parse_shikimori(self: Title, raw_title: dict):
    type_ = self.get_type()
    obj = raw_title["manga" if type_ == "ranobe" else type_]
    self._id_ = obj["id"]
    self._name_ = obj["name"]
    self._watch_status_ = raw_title["status"]
    self._episodes_ = raw_title["episodes"]
    if self._episodes_ is None:
        self._episodes_ = 0
    self._chapters_ = raw_title["chapters"]
    if self._chapters_ is None:
        self._chapters_ = 0
    self._volumes_ = raw_title["volumes"]
    if self._volumes_ is None:
        self._volumes_ = 0
    self._score_ = raw_title["score"]
    self._comment_ = raw_title["text"] if raw_title["text"] else ""
    self._rewatches_ = raw_title["rewatches"]


def parse_myanimelist(self: Title, raw_title: dict):
    node = raw_title["node"]
    list_status = raw_title["list_status"]
    self._id_ = node["id"]
    self._name_ = node["title"]
    status = list_status["status"]
    if status == "plan_to_read" or status == "plan_to_watch":
        status = "planned"
    if status == "reading":
        status = "watching"
    if (
        "is_rewatching" in list_status
        and list_status["is_rewatching"]
        or "is_rereading" in list_status
        and list_status["is_rereading"]
    ):
        status = "rewatching"
    self._watch_status_ = status
    self._episodes_ = list_status.get("num_episodes_watched", 0)
    self._chapters_ = list_status.get("num_chapters_read", 0)
    self._volumes_ = list_status.get("num_volumes_read", 0)
    self._score_ = list_status["score"]
    self._comment_ = list_status["comments"] if "comments" in list_status and list_status["comments"] else ""
    self._rewatches_ = list_status.get(
        "num_times_rewatched", list_status.get("num_times_reread", 0)
    )
