from __future__ import annotations
from typing import List, Literal, Optional, Tuple, TypedDict, Union
from typing_extensions import NotRequired
class ExperimentResponse(TypedDict):
    fingerprint: NotRequired[str]
    assignments: List[UserExperiment]
class ExperimentResponseWithGuild(ExperimentResponse):
    guild_experiments: NotRequired[List[GuildExperiment]]
class RolloutData(TypedDict):
    s: int
    e: int
Rollout = Tuple[int, List[RolloutData]]
Filters = List[
    Union[
        Tuple[Literal[1604612045], Tuple[Tuple[Literal[1183251248], List[str]]]],
        Tuple[
            Literal[2404720969], Tuple[Tuple[Literal[3399957344], Optional[int]], Tuple[Literal[1238858341], int]]
        ],
        Tuple[
            Literal[2918402255], Tuple[Tuple[Literal[3399957344], Optional[int]], Tuple[Literal[1238858341], int]]
        ],
        Tuple[Literal[3013771838], Tuple[Tuple[Literal[3013771838], List[int]]]],
        Tuple[Literal[4148745523], Tuple[Tuple[Literal[4148745523], List[int]]]],
        Tuple[Literal[188952590], Tuple[Tuple[Literal[188952590], bool]]],
        Tuple[Literal[2294888943], Tuple[Tuple[Literal[2690752156], int], Tuple[Literal[1982804121], int]]],
    ]
]
Population = Tuple[
    List[Rollout],
    Filters,
]
class Override(TypedDict):
    b: int
    k: List[int]
Holdout = Tuple[
    int,
    str,
]
UserExperiment = Tuple[
    int,
    int,
    int,
    Literal[-1, 0],
    int,
    int,
    Literal[0, 1],
    Literal[0, 1],
]
GuildExperiment = Tuple[
    int,
    Optional[str],
    int,
    List[Population],
    List[Override],
    List[List[Population]],
    Optional[str],
    Optional[int],
    Literal[0, 1],
    Literal[0, 1],
]