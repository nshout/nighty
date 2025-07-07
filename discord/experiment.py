from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Final, Iterator, List, Optional, Sequence, Tuple, Union
from .enums import HubType, try_enum
from .metadata import Metadata
from .utils import SequenceProxy, SnowflakeList, murmurhash32, utcnow
if TYPE_CHECKING:
    from .abc import Snowflake
    from .guild import Guild
    from .state import ConnectionState
    from .types.experiment import (
        Filters as FiltersPayload,
        GuildExperiment as GuildExperimentPayload,
        Override as OverridePayload,
        Population as PopulationPayload,
        Rollout as RolloutPayload,
        UserExperiment as AssignmentPayload,
    )
__all__ = (
    'ExperimentRollout',
    'ExperimentFilters',
    'ExperimentPopulation',
    'ExperimentOverride',
    'HoldoutExperiment',
    'GuildExperiment',
    'UserExperiment',
)
class ExperimentRollout:
    __slots__ = ('population', 'bucket', 'ranges')
    def __init__(self, population: ExperimentPopulation, data: RolloutPayload):
        bucket, ranges = data
        self.population = population
        self.bucket: int = bucket
        self.ranges: List[Tuple[int, int]] = [(range['s'], range['e']) for range in ranges]
    def __repr__(self) -> str:
        return f'<ExperimentRollout bucket={self.bucket} ranges={self.ranges!r}>'
    def __contains__(self, item: int, /) -> bool:
        for start, end in self.ranges:
            if start <= item <= end:
                return True
        return False
class ExperimentFilters:
    __slots__ = ('population', 'options')
    FILTER_KEYS: Final[Dict[int, str]] = {
        1604612045: 'guild_has_feature',
        2404720969: 'guild_id_range',
        3730341874: 'guild_age_range_days',
        2918402255: 'guild_member_count_range',
        3013771838: 'guild_ids',
        4148745523: 'guild_hub_types',
        188952590: 'guild_has_vanity_url',
        2294888943: 'guild_in_range_by_hash',
        3399957344: 'min_id',
        1238858341: 'max_id',
        2690752156: 'hash_key',
        1982804121: 'target',
        1183251248: 'guild_features',
    }
    def __init__(self, population: ExperimentPopulation, data: FiltersPayload):
        self.population = population
        self.options: Metadata = self.array_object(data)
    def __repr__(self) -> str:
        keys = (
            'features',
            'id_range',
            'age_range',
            'member_count_range',
            'ids',
            'hub_types',
            'range_by_hash',
            'has_vanity_url',
        )
        attrs = [f'{attr}={getattr(self, attr)!r}' for attr in keys if getattr(self, attr) is not None]
        if attrs:
            return f'<ExperimentFilters {" ".join(attrs)}>'
        return '<ExperimentFilters>'
    def __contains__(self, guild: Guild, /) -> bool:
        return self.is_eligible(guild)
    @classmethod
    def array_object(cls, array: list) -> Metadata:
        metadata = Metadata()
        for key, value in array:
            try:
                key = cls.FILTER_KEYS[int(key)]
            except (KeyError, ValueError):
                pass
            if isinstance(value, str) and value.isdigit():
                value = int(value)
            elif value and isinstance(value, list) and isinstance(value[0], list):
                value = cls.array_object(value)
            metadata[str(key)] = value
        return metadata
    @staticmethod
    def in_range(num: float, start: Optional[float], end: Optional[float], /) -> bool:
        if start is not None and num < start:
            return False
        if end is not None and num > end:
            return False
        return True
    @property
    def features(self) -> Optional[List[str]]:
        features_filter = self.options.guild_has_feature
        if features_filter is not None:
            return features_filter.guild_features
    @property
    def id_range(self) -> Optional[Tuple[Optional[int], Optional[int]]]:
        id_range_filter = self.options.guild_id_range
        if id_range_filter is not None:
            return id_range_filter.min_id, id_range_filter.max_id
    @property
    def age_range(self) -> Optional[Tuple[Optional[int], Optional[int]]]:
        age_range_filter = self.options.guild_age_range_days
        if age_range_filter is not None:
            return age_range_filter.min_id, age_range_filter.max_id
    @property
    def member_count_range(self) -> Optional[Tuple[Optional[int], Optional[int]]]:
        member_count_range_filter = self.options.guild_member_count_range
        if member_count_range_filter is not None:
            return member_count_range_filter.min_id, member_count_range_filter.max_id
    @property
    def ids(self) -> Optional[List[int]]:
        ids_filter = self.options.guild_ids
        if ids_filter is not None:
            return ids_filter.guild_ids
    @property
    def hub_types(self) -> Optional[List[HubType]]:
        hub_types_filter = self.options.guild_hub_types
        if hub_types_filter is not None:
            return [try_enum(HubType, hub_type) for hub_type in hub_types_filter.guild_hub_types]
    @property
    def range_by_hash(self) -> Optional[Tuple[int, int]]:
        range_by_hash_filter = self.options.guild_in_range_by_hash
        if range_by_hash_filter is not None:
            return range_by_hash_filter.hash_key, range_by_hash_filter.target
    @property
    def has_vanity_url(self) -> Optional[bool]:
        has_vanity_url_filter = self.options.guild_has_vanity_url
        if has_vanity_url_filter is not None:
            return has_vanity_url_filter.target
    def is_eligible(self, guild: Guild, /) -> bool:
        features = self.features
        if features is not None:
            if not any(feature in guild.features for feature in features):
                return False
        id_range = self.id_range
        if id_range is not None:
            if not self.in_range(guild.id, *id_range):
                return False
        age_range = self.age_range
        if age_range is not None:
            if not self.in_range((utcnow() - guild.created_at).days, *age_range):
                return False
        member_count_range = self.member_count_range
        if member_count_range is not None and guild.member_count is not None:
            if not self.in_range(guild.member_count, *member_count_range):
                return False
        ids = self.ids
        if ids is not None:
            if guild.id not in ids:
                return False
        hub_types = self.hub_types
        if hub_types is not None:
            if not guild.hub_type or guild.hub_type not in hub_types:
                return False
        range_by_hash = self.range_by_hash
        if range_by_hash is not None:
            hash_key, target = range_by_hash
            result = murmurhash32(f'{hash_key}:{guild.id}', signed=False)
            if result > 0:
                result += result
            else:
                result = (result % 0x100000000) >> 0
            if target and (result % 10000) >= target:
                return False
        has_vanity_url = self.has_vanity_url
        if has_vanity_url is not None:
            if not bool(guild.vanity_url_code) == has_vanity_url:
                return False
        return True
class ExperimentPopulation:
    __slots__ = ('experiment', 'filters', 'rollouts')
    def __init__(self, experiment: GuildExperiment, data: PopulationPayload):
        rollouts, filters = data
        self.experiment = experiment
        self.filters: ExperimentFilters = ExperimentFilters(self, filters)
        self.rollouts: List[ExperimentRollout] = [ExperimentRollout(self, x) for x in rollouts]
    def __repr__(self) -> str:
        return f'<ExperimentPopulation experiment={self.experiment!r} filters={self.filters!r} rollouts={self.rollouts!r}>'
    def __contains__(self, item: Guild, /) -> bool:
        return self.bucket_for(item) != -1
    def bucket_for(self, guild: Guild, _result: Optional[int] = None, /) -> int:
        if _result is None:
            _result = self.experiment.result_for(guild)
        if not self.filters.is_eligible(guild):
            return -1
        for rollout in self.rollouts:
            for start, end in rollout.ranges:
                if start <= _result <= end:
                    return rollout.bucket
        return -1
class ExperimentOverride:
    __slots__ = ('experiment', 'bucket', '_ids')
    def __init__(self, experiment: GuildExperiment, data: OverridePayload):
        self.experiment = experiment
        self.bucket: int = data['b']
        self._ids: SnowflakeList = SnowflakeList(map(int, data['k']))
    def __repr__(self) -> str:
        return f'<ExperimentOverride bucket={self.bucket} ids={self.ids!r}>'
    def __len__(self) -> int:
        return len(self._ids)
    def __contains__(self, item: Union[int, Snowflake], /) -> bool:
        if isinstance(item, int):
            return item in self._ids
        return item.id in self._ids
    def __iter__(self) -> Iterator[int]:
        return iter(self._ids)
    @property
    def ids(self) -> Sequence[int]:
        return SequenceProxy(self._ids)
class HoldoutExperiment:
    __slots__ = ('dependent', 'name', 'bucket')
    def __init__(self, dependent: GuildExperiment, name: str, bucket: int):
        self.dependent = dependent
        self.name: str = name
        self.bucket: int = bucket
    def __repr__(self) -> str:
        return f'<HoldoutExperiment dependent={self.dependent!r} name={self.name!r} bucket={self.bucket}>'
    def __contains__(self, item: Guild) -> bool:
        return self.is_eligible(item)
    @property
    def experiment(self) -> Optional[GuildExperiment]:
        experiment_hash = murmurhash32(self.name, signed=False)
        experiment = self.dependent.state.guild_experiments.get(experiment_hash)
        if experiment and not experiment.name:
            experiment._name = self.name
        return experiment
    def is_eligible(self, guild: Guild, /) -> bool:
        experiment = self.experiment
        if experiment is None:
            return True
        return experiment.bucket_for(guild) == self.bucket
class GuildExperiment:
    __slots__ = (
        'state',
        'hash',
        '_name',
        'revision',
        'populations',
        'overrides',
        'overrides_formatted',
        'holdout',
        'aa_mode',
        'trigger_debugging',
    )
    def __init__(self, *, state: ConnectionState, data: GuildExperimentPayload):
        (
            hash,
            hash_key,
            revision,
            populations,
            overrides,
            overrides_formatted,
            holdout_name,
            holdout_bucket,
            aa_mode,
            trigger_debugging,
            *_,
        ) = data
        self.state = state
        self.hash: int = hash
        self._name: Optional[str] = hash_key
        self.revision: int = revision
        self.populations: List[ExperimentPopulation] = [ExperimentPopulation(self, x) for x in populations]
        self.overrides: List[ExperimentOverride] = [ExperimentOverride(self, x) for x in overrides]
        self.overrides_formatted: List[List[ExperimentPopulation]] = [
            [ExperimentPopulation(self, y) for y in x] for x in overrides_formatted
        ]
        self.holdout: Optional[HoldoutExperiment] = (
            HoldoutExperiment(self, holdout_name, holdout_bucket)
            if holdout_name is not None and holdout_bucket is not None
            else None
        )
        self.aa_mode: bool = aa_mode == 1
        self.trigger_debugging: bool = trigger_debugging == 1
    def __repr__(self) -> str:
        return f'<GuildExperiment hash={self.hash}{f" name={self._name!r}" if self._name else ""}>'
    def __hash__(self) -> int:
        return self.hash
    def __eq__(self, other: object, /) -> bool:
        if isinstance(other, GuildExperiment):
            return self.hash == other.hash
        return NotImplemented
    @property
    def name(self) -> Optional[str]:
        return self._name
    @name.setter
    def name(self, value: Optional[str], /) -> None:
        if not value:
            self._name = None
        elif murmurhash32(value, signed=False) != self.hash:
            raise ValueError('The name provided does not match the experiment hash')
        else:
            self._name = value
    def result_for(self, guild: Snowflake, /) -> int:
        if not self.name:
            raise ValueError('The experiment name must be set to compute the result')
        return murmurhash32(f'{self.name}:{guild.id}', signed=False) % 10000
    def bucket_for(self, guild: Guild, /) -> int:
        if self.holdout and not self.holdout.is_eligible(guild):
            return -1
        hash_result = self.result_for(guild)
        for override in self.overrides:
            if guild.id in override.ids or guild.owner_id in override.ids:
                return override.bucket
        for overrides in self.overrides_formatted:
            for override in overrides:
                pop_bucket = override.bucket_for(guild, hash_result)
                if pop_bucket != -1:
                    return pop_bucket
        if self.aa_mode:
            return -1
        for population in self.populations:
            pop_bucket = population.bucket_for(guild, hash_result)
            if pop_bucket != -1:
                return pop_bucket
        return -1
    def guilds_for(self, bucket: int, /) -> List[Guild]:
        return [x for x in self.state.guilds if self.bucket_for(x) == bucket]
class UserExperiment:
    __slots__ = (
        'state',
        '_name',
        'hash',
        'revision',
        'assignment',
        'override',
        'population',
        '_result',
        'aa_mode',
        'trigger_debugging',
    )
    def __init__(self, *, state: ConnectionState, data: AssignmentPayload):
        (hash, revision, bucket, override, population, hash_result, aa_mode, trigger_debugging, *_) = data
        self.state = state
        self._name: Optional[str] = None
        self.hash: int = hash
        self.revision: int = revision
        self.assignment: int = bucket
        self.override: bool = override == 0
        self.population: int = population
        self._result: int = hash_result
        self.aa_mode: bool = aa_mode == 1
        self.trigger_debugging: bool = trigger_debugging == 1
    def __repr__(self) -> str:
        return f'<UserExperiment hash={self.hash}{f" name={self._name!r}" if self._name else ""} bucket={self.bucket}>'
    def __hash__(self) -> int:
        return self.hash
    def __eq__(self, other: object, /) -> bool:
        if isinstance(other, UserExperiment):
            return self.hash == other.hash
        return NotImplemented
    @property
    def name(self) -> Optional[str]:
        return self._name
    @name.setter
    def name(self, value: Optional[str], /) -> None:
        if not value:
            self._name = None
        elif murmurhash32(value, signed=False) != self.hash:
            raise ValueError('The name provided does not match the experiment hash')
        else:
            self._name = value
    @property
    def bucket(self) -> int:
        if self.aa_mode:
            return -1
        return self.assignment
    @property
    def result(self) -> int:
        if self._result:
            return self._result
        elif not self.name:
            raise ValueError('The experiment name must be set to compute the result')
        else:
            return murmurhash32(f'{self.name}:{self.state.self_id}', signed=False) % 10000