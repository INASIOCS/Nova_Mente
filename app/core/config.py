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

    # --- Provedor de LLM ---
    # "gemini" (padrão, estado entregue) ou "nvidia". Os embeddings seguem o
    # mesmo provedor, a menos que EMBEDDING_PROVIDER diga o contrário.
    llm_provider: str = "gemini"
    embedding_provider: str = ""

    # --- Google Gemini ---
    google_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash"
    gemini_embedding_model: str = "models/gemini-embedding-001"

    # --- NVIDIA (build.nvidia.com, API compatível com OpenAI) ---
    nvidia_api_key: str = ""
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_model: str = "nvidia/nemotron-3.5-lightning-30b-a3b"
    nvidia_embedding_model: str = "nvidia/nemotron-3.5-embed-1b"
    # O Nemotron raciocina antes de responder por padrão: 5,8 s e 914 tokens
    # contra 2,1 s e 247 tokens com o raciocínio desligado, na mesma pergunta.
    nvidia_thinking: bool = False
    nvidia_timeout: int = 180

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

    @property
    def nvidia_configurado(self) -> bool:
        return bool(self.nvidia_api_key.strip())

    @property
    def provedor_llm(self) -> str:
        """Provedor de geração ativo, normalizado."""
        return (self.llm_provider or "gemini").strip().lower()

    @property
    def provedor_embeddings(self) -> str:
        """Provedor de embeddings: o próprio, ou o mesmo da geração."""
        return (self.embedding_provider or self.provedor_llm).strip().lower()

    @property
    def llm_configurado(self) -> bool:
        """Há chave para o provedor de geração escolhido?"""
        if self.provedor_llm == "nvidia":
            return self.nvidia_configurado
        return self.gemini_configurado

    @property
    def modelo_llm_ativo(self) -> str:
        if self.provedor_llm == "nvidia":
            return self.nvidia_model
        return self.gemini_model

    @property
    def nome_provedor_llm(self) -> str:
        return "NVIDIA" if self.provedor_llm == "nvidia" else "Gemini"


@lru_cache
def get_settings() -> Settings:
    """Settings em cache — uma única instância por processo."""
    return Settings()
