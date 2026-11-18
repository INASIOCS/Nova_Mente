"""Diagnóstico da integração com o OCI Object Storage (camada Always Free).

Verifica, em ordem, cada elo da cadeia e para no primeiro que falhar, dizendo
exatamente o que corrigir. Nenhum segredo é impresso: OCIDs e fingerprint
aparecem truncados.

Etapas:
1. arquivo de configuração (`~/.oci/config`, perfil `DEFAULT`);
2. credenciais válidas (assinatura aceita pelo serviço) + namespace do tenancy;
3. existência do bucket;
4. escrita e leitura reais de um objeto de teste, removido no fim.

Uso:
    .venv\\Scripts\\python.exe scripts/verificar_oci.py
    .venv\\Scripts\\python.exe scripts/verificar_oci.py --criar-bucket

`--criar-bucket` cria o bucket (Standard, NoPublicAccess) no compartimento de
`OCI_COMPARTMENT_ID` ou, se vazio, no compartimento raiz do tenancy. Só use se
preferir criar por aqui em vez de pelo console.
"""

from __future__ import annotations

import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from app.core.config import get_settings  # noqa: E402

OK = "[ok]   "
FALHA = "[falha]"
AVISO = "[aviso]"


def _curto(valor: str | None, visiveis: int = 6) -> str:
    """Mostra apenas o fim de um identificador, para nao expor o valor inteiro."""
    if not valor:
        return "(vazio)"
    texto = str(valor)
    if len(texto) <= visiveis:
        return "*" * len(texto)
    return f"...{texto[-visiveis:]}"


def _titulo(texto: str) -> None:
    print(f"\n{texto}")
    print("-" * len(texto))


def main() -> int:
    criar_bucket = "--criar-bucket" in sys.argv
    cfg = get_settings()

    _titulo("NovaMente - diagnostico do OCI Object Storage")
    print(f"backend configurado no .env : {cfg.storage_backend}")
    print(f"bucket esperado             : {cfg.oci_bucket_name}")
    print(f"regiao esperada             : {cfg.oci_region}")
    print(f"arquivo de configuracao     : {cfg.oci_config_file}")
    print(f"perfil                      : {cfg.oci_profile}")

    # --- 1. SDK ------------------------------------------------------------
    _titulo("1. SDK do OCI")
    try:
        import oci
    except ImportError:
        print(f"{FALHA} SDK nao instalado. Rode: pip install -r requirements.txt")
        return 1
    print(f"{OK} oci {oci.__version__}")

    # --- 2. Arquivo de configuracao ---------------------------------------
    _titulo("2. Arquivo de configuracao")
    caminho = Path(cfg.oci_config_file).expanduser()
    if not caminho.exists():
        print(f"{FALHA} '{caminho}' nao existe.")
        print("        Gere o par de chaves de API no console (User settings ->")
        print("        API keys -> Add API key) e salve o bloco de configuracao")
        print("        que o console exibe neste caminho, no perfil DEFAULT.")
        return 1
    print(f"{OK} encontrado em {caminho}")

    try:
        config = oci.config.from_file(
            file_location=cfg.oci_config_file, profile_name=cfg.oci_profile
        )
        oci.config.validate_config(config)
    except Exception as exc:
        print(f"{FALHA} configuracao invalida: {exc}")
        print("        Confira as chaves user, tenancy, fingerprint, key_file e region.")
        return 1

    print(f"{OK} perfil '{cfg.oci_profile}' valido")
    print(f"        user        : {_curto(config.get('user'))}")
    print(f"        tenancy     : {_curto(config.get('tenancy'))}")
    print(f"        fingerprint : {_curto(config.get('fingerprint'), 5)}")
    print(f"        region      : {config.get('region')}")

    chave = Path(str(config.get("key_file", ""))).expanduser()
    if not chave.exists():
        print(f"{FALHA} chave privada nao encontrada em '{chave}'.")
        print("        Ajuste 'key_file' no config para o caminho do .pem baixado.")
        return 1
    print(f"{OK} chave privada presente ({chave.name})")

    if config.get("region") and config["region"] != cfg.oci_region:
        print(
            f"{AVISO} region do config ({config['region']}) difere de "
            f"OCI_REGION ({cfg.oci_region}). A URI publica usa OCI_REGION."
        )

    # --- 3. Credenciais aceitas pelo servico + namespace -------------------
    _titulo("3. Autenticacao e namespace")
    try:
        cliente = oci.object_storage.ObjectStorageClient(config)
        namespace = cfg.oci_namespace or cliente.get_namespace().data
    except Exception as exc:
        print(f"{FALHA} o servico recusou a credencial: {exc}")
        print("        Causas comuns: fingerprint de outra chave, chave privada")
        print("        trocada, ou a chave publica nao foi adicionada ao usuario.")
        return 1
    print(f"{OK} autenticado - namespace: {namespace}")

    # --- 4. Bucket ---------------------------------------------------------
    _titulo("4. Bucket")
    existe = True
    try:
        bucket = cliente.get_bucket(namespace, cfg.oci_bucket_name).data
        print(f"{OK} '{bucket.name}' acessivel")
        print(f"        compartimento : {_curto(bucket.compartment_id)}")
        print(f"        tier          : {getattr(bucket, 'storage_tier', 'n/d')}")
        print(f"        acesso publico: {getattr(bucket, 'public_access_type', 'n/d')}")
    except Exception as exc:
        existe = False
        print(f"{FALHA} bucket '{cfg.oci_bucket_name}' inacessivel: {exc}")

    if not existe and criar_bucket:
        compartimento = cfg.oci_compartment_id or config.get("tenancy")
        print(f"{AVISO} criando o bucket no compartimento {_curto(compartimento)}")
        try:
            detalhes = oci.object_storage.models.CreateBucketDetails(
                name=cfg.oci_bucket_name,
                compartment_id=compartimento,
                public_access_type="NoPublicAccess",
                storage_tier="Standard",
            )
            cliente.create_bucket(namespace, detalhes)
            existe = True
            print(f"{OK} bucket criado")
        except Exception as exc:
            print(f"{FALHA} falha ao criar o bucket: {exc}")
            return 1
    elif not existe:
        print("        Crie o bucket no console (Storage -> Buckets -> Create")
        print(f"        Bucket) com o nome exato '{cfg.oci_bucket_name}',")
        print("        tier Standard e sem acesso publico. Ou rode este script")
        print("        novamente com --criar-bucket.")
        return 1

    # --- 5. Escrita e leitura reais ---------------------------------------
    _titulo("5. Escrita e leitura de um objeto de teste")
    objeto_id = f"diagnostico/teste-{uuid.uuid4().hex[:8]}.txt"
    carga = (
        "NovaMente - objeto de diagnostico. Pode ser removido.\n"
        f"gerado_em={datetime.now(timezone.utc).isoformat()}\n"
    ).encode("utf-8")

    try:
        cliente.put_object(
            namespace_name=namespace,
            bucket_name=cfg.oci_bucket_name,
            object_name=objeto_id,
            put_object_body=carga,
            content_type="text/plain",
        )
        print(f"{OK} escrita: {objeto_id}")
    except Exception as exc:
        print(f"{FALHA} sem permissao de escrita: {exc}")
        print("        Verifique a policy do grupo do usuario sobre o bucket.")
        return 1

    try:
        lido = cliente.get_object(namespace, cfg.oci_bucket_name, objeto_id).data.content
        if lido == carga:
            print(f"{OK} leitura: conteudo identico ao enviado")
        else:
            print(f"{AVISO} leitura devolveu conteudo diferente do enviado")
    except Exception as exc:
        print(f"{AVISO} escreveu mas nao conseguiu ler: {exc}")

    try:
        cliente.delete_object(namespace, cfg.oci_bucket_name, objeto_id)
        print(f"{OK} objeto de teste removido")
    except Exception as exc:
        print(f"{AVISO} objeto de teste ficou no bucket ({objeto_id}): {exc}")

    print(
        f"\n        URI publica dos objetos: https://objectstorage."
        f"{cfg.oci_region}.oraclecloud.com/n/{namespace}/b/{cfg.oci_bucket_name}/o/<objeto>"
    )

    # --- Conclusao ---------------------------------------------------------
    _titulo("Conclusao")
    print(f"{OK} a cadeia completa funciona: config -> credencial -> bucket -> I/O")
    if cfg.storage_backend.strip().lower() != "oci":
        print(f"{AVISO} o .env ainda tem STORAGE_BACKEND={cfg.storage_backend}.")
        print("        Troque para 'oci' para que o pipeline passe a gravar no bucket.")
        return 0
    if not cfg.oci_namespace:
        print(
            "        Dica: fixar OCI_NAMESPACE="
            f"{namespace} no .env economiza uma chamada por execucao."
        )
    print("        Proximo passo: rodar um cenario e conferir status_upload=concluido.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
