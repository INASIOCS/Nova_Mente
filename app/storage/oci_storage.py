"""Backend de persistência em OCI Object Storage (camada Always Free).

Requisito OBRIGATÓRIO do edital do Hackathon ONE G10.

Autenticação suportada, nesta ordem:
1. Arquivo de configuração do OCI CLI (`~/.oci/config`) — padrão.
2. Resource Principal (quando rodando dentro da OCI).

Somente serviços da camada Always Free devem ser usados.
"""

from __future__ import annotations

import json

from app.core.config import get_settings
from app.storage.base import ErroStorage, ResultadoUpload


class OCIObjectStorage:
    """Persiste documentos originais e pacotes JSON gerados em um bucket."""

    nome = "oci"

    def __init__(self) -> None:
        cfg = get_settings()
        self.bucket = cfg.oci_bucket_name
        self._regiao = cfg.oci_region
        self._cliente = None
        self._namespace = cfg.oci_namespace or None
        self._erro_init: str | None = None

        try:
            import oci  # noqa: PLC0415
        except ImportError as exc:
            self._erro_init = (
                "SDK do OCI não instalado. Rode: pip install -r requirements.txt"
            )
            raise ErroStorage(self._erro_init) from exc

        config = None
        try:
            config = oci.config.from_file(
                file_location=cfg.oci_config_file, profile_name=cfg.oci_profile
            )
            oci.config.validate_config(config)
            self._cliente = oci.object_storage.ObjectStorageClient(config)
        except Exception as erro_arquivo:
            # tenta Resource Principal (execução dentro da OCI)
            try:
                signer = oci.auth.signers.get_resource_principals_signer()
                self._cliente = oci.object_storage.ObjectStorageClient(
                    config={"region": self._regiao}, signer=signer
                )
            except Exception:
                self._erro_init = (
                    "Não foi possível autenticar no OCI. Verifique "
                    f"'{cfg.oci_config_file}' (perfil '{cfg.oci_profile}'). "
                    f"Detalhe: {erro_arquivo}"
                )
                raise ErroStorage(self._erro_init) from erro_arquivo

        if not self._namespace:
            try:
                self._namespace = self._cliente.get_namespace().data
            except Exception as exc:
                self._erro_init = f"Falha ao obter o namespace do Object Storage: {exc}"
                raise ErroStorage(self._erro_init) from exc

    def disponivel(self) -> bool:
        if self._cliente is None or not self._namespace:
            return False
        try:
            self._cliente.get_bucket(self._namespace, self.bucket)
            return True
        except Exception:
            return False

    def garantir_bucket(self, compartment_id: str) -> bool:
        """Cria o bucket se ele ainda não existir (Standard, Always Free)."""
        import oci

        try:
            self._cliente.get_bucket(self._namespace, self.bucket)
            return True
        except Exception:
            pass

        try:
            detalhes = oci.object_storage.models.CreateBucketDetails(
                name=self.bucket,
                compartment_id=compartment_id,
                public_access_type="NoPublicAccess",
                storage_tier="Standard",
            )
            self._cliente.create_bucket(self._namespace, detalhes)
            return True
        except Exception as exc:
            raise ErroStorage(f"Falha ao criar o bucket '{self.bucket}': {exc}") from exc

    def enviar_bytes(
        self,
        conteudo: bytes,
        objeto_id: str,
        content_type: str = "application/octet-stream",
    ) -> ResultadoUpload:
        if self._cliente is None or not self._namespace:
            return ResultadoUpload(
                bucket=self.bucket,
                objeto_id=objeto_id,
                status_upload="falhou",
                backend=self.nome,
                erro=self._erro_init or "Cliente OCI não inicializado.",
            )

        try:
            self._cliente.put_object(
                namespace_name=self._namespace,
                bucket_name=self.bucket,
                object_name=objeto_id,
                put_object_body=conteudo,
                content_type=content_type,
            )
        except Exception as exc:
            return ResultadoUpload(
                bucket=self.bucket,
                objeto_id=objeto_id,
                status_upload="falhou",
                backend=self.nome,
                erro=str(exc),
            )

        uri = (
            f"https://objectstorage.{self._regiao}.oraclecloud.com"
            f"/n/{self._namespace}/b/{self.bucket}/o/{objeto_id}"
        )
        return ResultadoUpload(
            bucket=self.bucket,
            objeto_id=objeto_id,
            status_upload="concluido",
            backend=self.nome,
            uri=uri,
        )

    def enviar_json(self, dados: dict, objeto_id: str) -> ResultadoUpload:
        bruto = json.dumps(dados, ensure_ascii=False, indent=2).encode("utf-8")
        return self.enviar_bytes(bruto, objeto_id, "application/json")
