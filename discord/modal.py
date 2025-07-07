from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional, Union
from .components import _component_factory
from .enums import InteractionType
from .interactions import _wrapped_interaction
from .mixins import Hashable
from .utils import _generate_nonce
if TYPE_CHECKING:
    from .application import IntegrationApplication
    from .components import ActionRow
    from .interactions import Interaction
    from .types.interactions import Modal as ModalPayload, ModalSubmitInteractionData
__all__ = (
    'Modal',
)
class Modal(Hashable):
    __slots__ = ('state', 'interaction', 'id', 'nonce', 'title', 'custom_id', 'components', 'application')
    def __init__(self, *, data: ModalPayload, interaction: Interaction):
        self.state = interaction.state
        self.interaction = interaction
        self.id = int(data['id'])
        self.nonce: Optional[Union[int, str]] = data.get('nonce')
        self.title: str = data.get('title', '')
        self.custom_id: str = data.get('custom_id', '')
        self.components: List[ActionRow] = [_component_factory(d) for d in data.get('components', [])]
        self.application: IntegrationApplication = interaction.state.create_integration_application(data['application'])
    def __str__(self) -> str:
        return self.title
    def to_dict(self) -> ModalSubmitInteractionData:
        return {
            'id': str(self.id),
            'custom_id': self.custom_id,
            'components': [c.to_dict() for c in self.components],
        }
    async def submit(self):
        interaction = self.interaction
        return await _wrapped_interaction(
            self.state,
            _generate_nonce(),
            InteractionType.modal_submit,
            None,
            interaction.channel,
            self.to_dict(),
            application_id=self.application.id,
        )