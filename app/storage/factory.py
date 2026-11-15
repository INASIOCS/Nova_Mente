"""Seleção do backend de persistência conforme STORAGE_BACKEND."""

from __future__ import annotations

import logging

from app.core.config import get_settings
from app.storage.base import StorageBackend
from app.storage.local import LocalStorage

logger = logging.getLogger(__name__)


def criar_storage(forcar: str | None = None) -> tuple[StorageBackend, str | None]:
    """Devolve o backend ativo e um aviso, quando houver degradação.

    Com STORAGE_BACKEND=oci e credenciais válidas, usa o OCI Object Storage.
    Se a autenticação falhar, cai para o backend local e devolve o aviso —
    a aplicação não quebra, mas fica explícito que o requisito obrigatório
    do edital não foi exercido naquela execução.
    """
    cfg = get_settings()
    escolhido = (forcar or cfg.storage_backend or "local").strip().lower()

    if escolhido == "oci":
        try:
            from app.storage.oci_storage import OCIObjectStorage

            backend = OCIObjectStorage()
            return backend, None
        except Exception as exc:
            aviso = (
                "OCI Object Storage indisponível — usando persistência local. "
                f"Motivo: {exc}"
            )
            logger.warning(aviso)
            return LocalStorage(), aviso

    return LocalStorage(), None
