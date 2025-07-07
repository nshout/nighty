from __future__ import annotations
from typing import Any, Optional, TYPE_CHECKING, List
from .utils import parse_time, _bytes_to_base64_data, MISSING
from .guild import Guild
__all__ = (
    'Template',
)
if TYPE_CHECKING:
    import datetime
    from .types.template import Template as TemplatePayload
    from .state import ConnectionState
    from .user import User
class _FriendlyHttpAttributeErrorHelper:
    __slots__ = ()
    def __getattr__(self, attr):
        raise AttributeError('PartialTemplateState does not support http methods.')
class _PartialTemplateState:
    def __init__(self, *, state):
        self.__state = state
        self.http = _FriendlyHttpAttributeErrorHelper()
    @property
    def user(self):
        return self.__state.user
    @property
    def self_id(self):
        return self.__state.user.id
    @property
    def member_cache_flags(self):
        return self.__state.member_cache_flags
    def store_emoji(self, guild, packet):
        return None
    def _get_voice_client(self, id):
        return None
    def _get_message(self, id):
        return None
    def _get_guild(self, id):
        return self.__state._get_guild(id)
    async def query_members(self, **kwargs: Any) -> List[Any]:
        return []
    def __getattr__(self, attr):
        raise AttributeError(f'PartialTemplateState does not support {attr!r}.')
class Template:
    __slots__ = (
        'code',
        'uses',
        'name',
        'description',
        'creator',
        'created_at',
        'updated_at',
        'source_guild',
        'is_dirty',
        'state',
    )
    def __init__(self, *, state: ConnectionState, data: TemplatePayload) -> None:
        self.state = state
        self._store(data)
    def _store(self, data: TemplatePayload) -> None:
        self.code: str = data['code']
        self.uses: int = data['usage_count']
        self.name: str = data['name']
        self.description: Optional[str] = data['description']
        creator_data = data.get('creator')
        self.creator: Optional[User] = None if creator_data is None else self.state.create_user(creator_data)
        self.created_at: Optional[datetime.datetime] = parse_time(data.get('created_at'))
        self.updated_at: Optional[datetime.datetime] = parse_time(data.get('updated_at'))
        guild_id = int(data['source_guild_id'])
        guild: Optional[Guild] = self.state._get_guild(guild_id)
        self.source_guild: Guild
        if guild is None:
            source_serialised = data['serialized_source_guild']
            source_serialised['id'] = guild_id
            state = _PartialTemplateState(state=self.state)
            self.source_guild = Guild(data=source_serialised, state=state)
        else:
            self.source_guild = guild
        self.is_dirty: Optional[bool] = data.get('is_dirty', None)
    def __repr__(self) -> str:
        return (
            f'<Template code={self.code!r} uses={self.uses} name={self.name!r}'
            f' creator={self.creator!r} source_guild={self.source_guild!r} is_dirty={self.is_dirty}>'
        )
    async def create_guild(self, name: str, icon: bytes = MISSING) -> Guild:
        base64_icon = None
        if icon is not MISSING:
            base64_icon = _bytes_to_base64_data(icon)
        data = await self.state.http.create_from_template(self.code, name, base64_icon)
        return Guild(data=data, state=self.state)
    async def sync(self) -> Template:
        data = await self.state.http.sync_template(self.source_guild.id, self.code)
        return Template(state=self.state, data=data)
    async def edit(
        self,
        *,
        name: str = MISSING,
        description: Optional[str] = MISSING,
    ) -> Template:
        payload = {}
        if name is not MISSING:
            payload['name'] = name
        if description is not MISSING:
            payload['description'] = description
        data = await self.state.http.edit_template(self.source_guild.id, self.code, payload)
        return Template(state=self.state, data=data)
    async def delete(self) -> None:
        await self.state.http.delete_template(self.source_guild.id, self.code)
    @property
    def url(self) -> str:
        return f'https://discord.new/{self.code}'