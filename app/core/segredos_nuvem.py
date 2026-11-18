"""Ponte entre os *Secrets* do Streamlit Community Cloud e o ambiente.

Na nuvem do Streamlit não existe arquivo `.env`: as credenciais ficam no painel
(`Settings -> Secrets`), em formato TOML, e chegam à aplicação por `st.secrets`.
Como toda a configuração do NovaMente (`app.core.config`) é lida de variáveis de
ambiente, este módulo copia os segredos para o ambiente **antes** da primeira
leitura da configuração.

Nada aqui roda localmente: sem `secrets.toml` o módulo não faz absolutamente
nada e o `.env` continua sendo a fonte da verdade.

Nenhum valor de segredo é registrado em log ou impresso na interface.
"""

from __future__ import annotations

import os
import stat
from pathlib import Path
from typing import Any

# Seções TOML que não viram variáveis de ambiente simples.
_SECOES_ESTRUTURADAS = {"oci"}

# Perfil escrito no arquivo de configuração gerado para o SDK do OCI.
_PERFIL_OCI = "DEFAULT"


def _segredos() -> dict[str, Any] | None:
    """Devolve os segredos do Streamlit, ou None fora da nuvem."""
    try:
        import streamlit as st
    except Exception:
        return None

    try:
        # Sem arquivo de segredos o Streamlit levanta exceção já no acesso.
        return dict(st.secrets)
    except Exception:
        return None


def _exportar_valores_simples(segredos: dict[str, Any]) -> list[str]:
    """Copia as chaves de topo para variáveis de ambiente maiúsculas."""
    exportadas: list[str] = []
    for chave, valor in segredos.items():
        if chave in _SECOES_ESTRUTURADAS or isinstance(valor, dict):
            continue
        if not isinstance(valor, (str, int, float, bool)):
            continue
        nome = str(chave).upper()
        # Uma variável de ambiente real (ex.: a do Docker) tem precedência.
        if os.environ.get(nome):
            continue
        os.environ[nome] = str(valor)
        exportadas.append(nome)
    return exportadas


def _materializar_credencial_oci(secao: dict[str, Any]) -> bool:
    """Escreve `config` e a chave privada do OCI a partir dos segredos.

    O SDK do OCI autentica por arquivo. Na nuvem do Streamlit não há disco
    persistente nem `~/.oci`, então recriamos os dois arquivos a cada boot, em
    um diretório do próprio contêiner, com permissão restrita.
    """
    obrigatorios = ("user", "fingerprint", "tenancy", "region", "key_content")
    if any(not str(secao.get(campo, "")).strip() for campo in obrigatorios):
        return False

    destino = Path.home() / ".oci"
    destino.mkdir(parents=True, exist_ok=True)

    caminho_chave = destino / "novamente_api_key.pem"
    conteudo_chave = str(secao["key_content"]).strip() + "\n"
    caminho_chave.write_text(conteudo_chave, encoding="utf-8")
    try:
        caminho_chave.chmod(stat.S_IRUSR | stat.S_IWUSR)  # 0600
    except OSError:
        # Windows pode recusar; o SDK apenas emite um aviso.
        pass

    linhas = [
        f"[{_PERFIL_OCI}]",
        f"user={secao['user']}",
        f"fingerprint={secao['fingerprint']}",
        f"tenancy={secao['tenancy']}",
        f"region={secao['region']}",
        f"key_file={caminho_chave}",
    ]
    if str(secao.get("pass_phrase", "")).strip():
        linhas.append(f"pass_phrase={secao['pass_phrase']}")

    caminho_config = destino / "config"
    caminho_config.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    try:
        caminho_config.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass

    os.environ["OCI_CONFIG_FILE"] = str(caminho_config)
    os.environ["OCI_PROFILE"] = _PERFIL_OCI
    for chave in ("namespace", "bucket_name", "compartment_id"):
        valor = str(secao.get(chave, "")).strip()
        if valor:
            os.environ[f"OCI_{chave.upper()}"] = valor
    os.environ.setdefault("OCI_REGION", str(secao["region"]))
    os.environ.setdefault("STORAGE_BACKEND", "oci")
    return True


def preparar_sqlite() -> None:
    """Garante um sqlite3 recente para o ChromaDB.

    O ChromaDB exige sqlite3 >= 3.35. A imagem da Streamlit Community Cloud pode
    trazer uma versão anterior, e nesse caso o `import chromadb` falha e o
    sistema cai no índice em memória. O pacote `pysqlite3-binary` (instalado
    apenas no Linux) resolve, desde que substitua o módulo padrão antes do
    primeiro import do ChromaDB.
    """
    import sys

    try:
        import sqlite3

        versao = tuple(int(p) for p in sqlite3.sqlite_version.split("."))
        if versao >= (3, 35, 0):
            return
    except Exception:
        pass

    try:
        import pysqlite3  # type: ignore[import-not-found]
    except Exception:
        return

    sys.modules["sqlite3"] = pysqlite3
    sys.modules["sqlite3.dbapi2"] = pysqlite3.dbapi2


def aplicar_segredos_do_streamlit() -> dict[str, Any]:
    """Prepara o ambiente a partir dos segredos. Idempotente e silenciosa.

    Devolve um pequeno diagnóstico (sem valores) para a interface, se quiser
    exibir de onde veio a configuração.
    """
    preparar_sqlite()

    segredos = _segredos()
    if not segredos:
        return {"origem": "ambiente", "variaveis": [], "oci": False}

    exportadas = _exportar_valores_simples(segredos)

    secao_oci = segredos.get("oci")
    oci_pronto = False
    if isinstance(secao_oci, dict):
        try:
            oci_pronto = _materializar_credencial_oci(dict(secao_oci))
        except Exception:
            oci_pronto = False

    return {"origem": "streamlit-secrets", "variaveis": exportadas, "oci": oci_pronto}
