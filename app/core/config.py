"""Configuração central do NovaMente.

Todas as credenciais vêm de variáveis de ambiente (arquivo .env local).
Nenhum segredo é versionado.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Configuração da aplicação, lida de variáveis de ambiente / .env."""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Google Gemini ---
    google_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash"
    gemini_embedding_model: str = "models/gemini-embedding-001"

    # --- Pipeline RAG ---
    chunk_size: int = 1200
    chunk_overlap: int = 150
    top_k: int = 5

    # --- Orquestração de agentes / economia de quota ---
    # O free tier do Gemini limita as requisições de geração por dia. Cada
    # execução completa consome 3 chamadas (Roteador, Redator, Crítico) e 5 se
    # houver rodada de revisão. Estes controles permitem reduzir o consumo
    # durante uma apresentação, ao custo de qualidade do planejamento didático.
    agente_roteador_ativo: bool = True
    max_revisoes: int = 1
    limite_revisao: float = 0.80

    # --- Persistência ---
    storage_backend: str = "local"
    local_storage_dir: str = "storage_local"

    # --- OCI Object Storage ---
    oci_config_file: str = "~/.oci/config"
    oci_profile: str = "DEFAULT"
    oci_namespace: str = ""
    oci_bucket_name: str = "novamente-conteudos-educativos"
    oci_region: str = "sa-saopaulo-1"
    # OCID do compartimento onde o bucket deve ser criado. Vazio = compartimento
    # raiz do tenancy. Usado apenas por scripts/verificar_oci.py --criar-bucket;
    # a aplicação nunca cria recursos na nuvem por conta própria.
    oci_compartment_id: str = ""

    @property
    def base_dir(self) -> Path:
        return BASE_DIR

    @property
    def local_storage_path(self) -> Path:
        path = BASE_DIR / self.local_storage_dir
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def gemini_configurado(self) -> bool:
        return bool(self.google_api_key.strip())


@lru_cache
def get_settings() -> Settings:
    """Settings em cache — uma única instância por processo."""
    return Settings()
