"""Backend de persistência local — fallback de desenvolvimento.

ATENÇÃO: este backend NÃO satisfaz o requisito obrigatório do edital
(OCI Object Storage). Ele existe para permitir desenvolvimento e demonstração
sem credenciais OCI. O campo `status_upload` retorna "local" para deixar
explícito que não houve upload para a nuvem.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.core.config import get_settings
from app.storage.base import ErroStorage, ResultadoUpload


class LocalStorage:
    """Grava os artefatos em disco, espelhando a estrutura do bucket."""

    nome = "local"

    def __init__(self, diretorio: Path | None = None) -> None:
        cfg = get_settings()
        self._raiz = Path(diretorio) if diretorio else cfg.local_storage_path
        self._raiz.mkdir(parents=True, exist_ok=True)
        self.bucket = cfg.oci_bucket_name

    def disponivel(self) -> bool:
        return True

    def _caminho(self, objeto_id: str) -> Path:
        destino = self._raiz / objeto_id
        destino.parent.mkdir(parents=True, exist_ok=True)
        return destino

    def enviar_bytes(
        self, conteudo: bytes, objeto_id: str, content_type: str = "application/octet-stream"
    ) -> ResultadoUpload:
        try:
            destino = self._caminho(objeto_id)
            destino.write_bytes(conteudo)
        except OSError as exc:
            raise ErroStorage(f"Falha ao gravar '{objeto_id}' no disco: {exc}") from exc

        return ResultadoUpload(
            bucket=self.bucket,
            objeto_id=objeto_id,
            status_upload="local",
            backend=self.nome,
            uri=destino.resolve().as_uri(),
        )

    def enviar_json(self, dados: dict, objeto_id: str) -> ResultadoUpload:
        bruto = json.dumps(dados, ensure_ascii=False, indent=2).encode("utf-8")
        return self.enviar_bytes(bruto, objeto_id, "application/json")
