"""Interface de persistência.

O edital exige OCI Object Storage (camada Always Free). A abstração permite
desenvolver e demonstrar o MVP com o backend local enquanto as credenciais do
OCI não estão disponíveis, trocando apenas a variável STORAGE_BACKEND.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class ResultadoUpload:
    """Rastro de uma persistência, usado no bloco `armazenamento_oci`."""

    bucket: str
    objeto_id: str
    status_upload: str  # "concluido" | "falhou" | "pendente" | "local"
    backend: str
    uri: str | None = None
    erro: str | None = None


class ErroStorage(Exception):
    """Falha de persistência."""


@runtime_checkable
class StorageBackend(Protocol):
    """Contrato de qualquer backend de persistência."""

    nome: str
    bucket: str

    def enviar_bytes(
        self, conteudo: bytes, objeto_id: str, content_type: str
    ) -> ResultadoUpload: ...

    def enviar_json(self, dados: dict, objeto_id: str) -> ResultadoUpload: ...

    def disponivel(self) -> bool: ...
