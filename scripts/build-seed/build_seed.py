"""
Pre-processa a planilha Ford vin_share_Desafio_02.xlsx em uma migration Flyway
(V3__seed_real_data.sql) com ~300 veículos amostrados.

Usa apenas dados D0 (ModelYear, ModelName, DealerCode, SalesDate, VIN_Hash) —
respeita a regra US02 (sem variáveis pós-compra na classificação).

PII (nome, CPF, email, telefone, região) é sintética e determinística por VIN_Hash.
Perfil + score replicam EXATAMENTE a lógica de MlService.classificar (Java).

**Hardening de segurança:** email e telefone são criptografados com AES-256-GCM
usando a mesma chave do backend (env var APP_CRYPTO_KEY, Base64 de 32 bytes).
Assim o seed produzido pode ser carregado direto pelo Flyway e a coluna
no Postgres já vem com ciphertext compatível com o EncryptedStringConverter.

Uso:
    APP_CRYPTO_KEY=<base64-32-bytes> python scripts/build_seed.py \\
        [caminho-do-xlsx]  [n_amostras]  [path/de/saida.sql]

Defaults:
    xlsx       = ./data/Online Retail.xlsx
    n_amostras = 300
    saida      = ./output/V3__seed_real_data.sql

Para alimentar o repo Java SOA, aponte o output para:
    ../challenge-SOA/src/main/resources/db/migration/V3__seed_real_data.sql
"""
from __future__ import annotations

import base64
import hashlib
import os
import sys
import uuid
from datetime import datetime, date
from pathlib import Path

import openpyxl
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


SAMPLE_SIZE_DEFAULT = 300
NAMESPACE_UUID = uuid.UUID("00000000-0000-0000-0000-000000000001")

NOMES = [
    "Maria", "João", "Ana", "Carlos", "Beatriz", "Pedro", "Luiza", "Marcos",
    "Camila", "Rafael", "Juliana", "Fernando", "Patrícia", "Lucas", "Mariana",
    "Roberto", "Cláudia", "André", "Vanessa", "Ricardo", "Letícia", "Eduardo",
    "Larissa", "Bruno", "Fernanda", "Thiago", "Isabela", "Felipe", "Carolina",
    "Daniel",
]
SOBRENOMES = [
    "Silva", "Santos", "Souza", "Oliveira", "Pereira", "Lima", "Costa",
    "Ferreira", "Rodrigues", "Almeida", "Nascimento", "Carvalho", "Gomes",
    "Martins", "Araújo", "Ribeiro", "Alves", "Cardoso", "Barbosa", "Rocha",
    "Mendes", "Dias", "Castro", "Campos", "Cavalcanti", "Moreira", "Pinto",
]
REGIOES = ["SP", "RJ", "MG", "RS", "PR", "SC", "BA", "GO", "DF", "ES", "PE", "CE"]


def load_crypto_key() -> bytes:
    raw = os.environ.get("APP_CRYPTO_KEY")
    if not raw:
        # Default dev key (idêntica à de application.yml). NÃO usar em prod.
        raw = "cHJldmlvcGxzLWRldi1rZXktMzItYnl0ZXMtWFhYWFg="
        print("AVISO: APP_CRYPTO_KEY não definido — usando chave dev. Não use em produção.")
    key = base64.b64decode(raw)
    if len(key) != 32:
        raise SystemExit(f"APP_CRYPTO_KEY deve decodificar para 32 bytes (atual: {len(key)})")
    return key


def encrypt(plaintext: str, key: bytes) -> str:
    """AES-256-GCM compatível com CryptoService.java (IV(12) || CT || TAG(16) → Base64)."""
    if plaintext is None:
        return None
    aesgcm = AESGCM(key)
    iv = os.urandom(12)
    ct_with_tag = aesgcm.encrypt(iv, plaintext.encode("utf-8"), None)
    return base64.b64encode(iv + ct_with_tag).decode("ascii")


def stable_uuid(seed: str) -> uuid.UUID:
    return uuid.uuid5(NAMESPACE_UUID, seed)


def parse_sales_date(value) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    s = str(value).strip()
    for fmt in ("%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def vin_from_hash(vin_hash: str) -> str:
    return vin_hash[:17].upper()


def synth_cliente(vin_hash: str):
    h = hashlib.sha256(vin_hash.encode()).digest()
    nome = NOMES[h[0] % len(NOMES)]
    sobrenome = SOBRENOMES[h[1] % len(SOBRENOMES)]
    cpf = "".join(str(b % 10) for b in h[2:13])
    regiao = REGIOES[h[13] % len(REGIOES)]
    email = f"{nome.lower()}.{sobrenome.lower()}.{h[14]:02x}@example.com"
    email = email.replace("ã", "a").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ç", "c")
    ddd = 11 + (h[15] % 79)
    fone_suffix = "".join(str(b % 10) for b in h[16:24])
    telefone = f"+55{ddd}9{fone_suffix}"
    return f"{nome} {sobrenome}", cpf, email, telefone, regiao


def classificar(dealer_code: str, modelo: str, versao: str, regiao: str):
    seed_input = f"{dealer_code}|{modelo}|{versao}|{regiao}".encode()
    digest = hashlib.sha256(seed_input).digest()
    bucket = digest[0] % 100
    score_base = digest[1] / 255.0

    if bucket < 35:
        return "FIEL", round(0.10 + score_base * 0.20, 3)
    if bucket < 60:
        return "ECONOMICO", round(0.30 + score_base * 0.25, 3)
    if bucket < 85:
        return "ESQUECIDO", round(0.55 + score_base * 0.20, 3)
    return "ABANDONO", round(0.78 + score_base * 0.22, 3)


def derivar_prioridade(score: float) -> str:
    if score >= 0.85: return "CRITICA"
    if score >= 0.65: return "ALTA"
    if score >= 0.40: return "MEDIA"
    return "BAIXA"


SCRIPTS = {
    "FIEL": "Cliente fiel — oferecer pacote de manutenção preventiva premium e enfatizar histórico de relacionamento com a marca.",
    "ABANDONO": "Cliente de alto risco de evasão — oferta agressiva de primeira revisão com desconto + brinde institucional. Abordar antes da 1ª revisão.",
    "ESQUECIDO": "Cliente esquecido — lembrete proativo de manutenção + agendamento facilitado. Oferecer combo revisão + lavagem.",
    "ECONOMICO": "Cliente sensível a preço — apresentar oferta promocional com parcelamento e comparativo de custo total de propriedade.",
}
PERFIS_GERAM_LEAD = {"ABANDONO", "ESQUECIDO"}


def sql_str(s: str | None) -> str:
    if s is None:
        return "NULL"
    return "'" + s.replace("'", "''") + "'"


def sql_date(d: date | None) -> str:
    if d is None:
        return "NULL"
    return f"DATE '{d.isoformat()}'"


def main():
    repo_root = Path(__file__).resolve().parent.parent
    default_xlsx = repo_root / "data" / "vin_share_Desafio_02.xlsx"
    default_out = repo_root / "output" / "V3__seed_real_data.sql"

    xlsx_path = Path(sys.argv[1]) if len(sys.argv) > 1 else default_xlsx
    n_samples = int(sys.argv[2]) if len(sys.argv) > 2 else SAMPLE_SIZE_DEFAULT
    out_path = Path(sys.argv[3]) if len(sys.argv) > 3 else default_out

    if not xlsx_path.exists():
        print(f"ERRO: planilha não encontrada em {xlsx_path}")
        sys.exit(1)

    crypto_key = load_crypto_key()

    print(f"Lendo {xlsx_path}...")
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    ws = wb["vin_share"]

    seen_vins: dict[str, dict] = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        (
            country, scheduleID, maintID, svOrder, svDate, svOpen, svClose,
            deptCode, repairType, svType, svCode, maintNum, dealerCode,
            mainSrc, isAgenda, statusUSA, vinHash, modelYear, modelName,
            km, invoiceDate, salesDate, deliveryDate, regDate, warrStart
        ) = row

        if not vinHash or vinHash in seen_vins:
            continue
        if not modelName or not modelYear or not dealerCode or not salesDate:
            continue
        sd = parse_sales_date(salesDate)
        if sd is None:
            continue

        seen_vins[vinHash] = {
            "modelo": str(modelName).strip().title(),
            "ano": int(modelYear),
            "dealer": str(dealerCode),
            "data_compra": sd,
        }
        if len(seen_vins) >= n_samples * 4:
            break

    print(f"{len(seen_vins):,} VINs únicos. Amostrando {n_samples}...")

    vin_list = sorted(seen_vins.keys())
    step = max(1, len(vin_list) // n_samples)
    sampled = vin_list[::step][:n_samples]

    clientes_rows = []
    veiculos_rows = []
    leads_rows = []

    for vin_hash in sampled:
        v = seen_vins[vin_hash]
        nome_completo, cpf, email, telefone, regiao = synth_cliente(vin_hash)
        cliente_id = stable_uuid("cliente:" + vin_hash)
        veiculo_id = stable_uuid("veiculo:" + vin_hash)

        perfil, score = classificar(v["dealer"], v["modelo"], "Padrão", regiao)

        # Criptografa PII no formato que CryptoService.decrypt entende
        email_enc = encrypt(email, crypto_key)
        telefone_enc = encrypt(telefone, crypto_key)

        clientes_rows.append((
            cliente_id, nome_completo, cpf, email_enc, telefone_enc, regiao,
            perfil, score,
        ))

        vin = vin_from_hash(vin_hash)
        valor_compra = 80000.0 + (int(vin_hash[17:21], 16) % 250000)
        veiculos_rows.append((
            veiculo_id, cliente_id, v["modelo"][:80], "Padrão", v["ano"],
            vin, v["data_compra"], round(valor_compra, 2), f"FORD-{v['dealer']}",
        ))

        if perfil in PERFIS_GERAM_LEAD:
            lead_id = stable_uuid("lead:" + vin_hash)
            prioridade = derivar_prioridade(score)
            leads_rows.append((
                lead_id, cliente_id, veiculo_id, score, prioridade,
                SCRIPTS[perfil],
            ))

    print(f"Gerados: {len(clientes_rows)} clientes, {len(veiculos_rows)} veículos, {len(leads_rows)} leads")

    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "-- Seed determinístico com amostra real da base Ford vin_share_Desafio_02.xlsx",
        "-- D0: ModelName/ModelYear/DealerCode/SalesDate vêm da planilha original.",
        "-- PII (nome, CPF, email, telefone, região): sintética e estável por VIN_Hash.",
        "-- Perfil e score são produzidos pela MESMA lógica do MlService.classificar (Java).",
        "-- *** Email e telefone vêm criptografados com AES-256-GCM, formato compatível",
        "--     com o EncryptedStringConverter do backend (mesma chave APP_CRYPTO_KEY). ***",
        "-- Gerado por scripts/build_seed.py.",
        "",
        "INSERT INTO clientes (id, nome, cpf, email, telefone, regiao, perfil, score_risco, criado_em, classificado_em) VALUES",
    ]
    for i, (cid, nome, cpf, email_enc, tel_enc, reg, perfil, score) in enumerate(clientes_rows):
        sep = "," if i < len(clientes_rows) - 1 else ";"
        lines.append(
            f"  ('{cid}', {sql_str(nome)}, {sql_str(cpf)}, {sql_str(email_enc)}, "
            f"{sql_str(tel_enc)}, {sql_str(reg)}, {sql_str(perfil)}, {score}, NOW(), NOW()){sep}"
        )

    lines.append("")
    lines.append("INSERT INTO veiculos (id, cliente_id, modelo, versao, ano, vin, data_compra, valor_compra, concessionaria_id, criado_em) VALUES")
    for i, (vid, cid, modelo, versao, ano, vin, dc, valor, conc) in enumerate(veiculos_rows):
        sep = "," if i < len(veiculos_rows) - 1 else ";"
        lines.append(
            f"  ('{vid}', '{cid}', {sql_str(modelo)}, {sql_str(versao)}, {ano}, "
            f"{sql_str(vin)}, {sql_date(dc)}, {valor}, {sql_str(conc)}, NOW()){sep}"
        )

    if leads_rows:
        lines.append("")
        lines.append("INSERT INTO leads (id, cliente_id, veiculo_id, score_risco, prioridade, status, script_oferta, criado_em, atualizado_em) VALUES")
        for i, (lid, cid, vid, score, prio, script) in enumerate(leads_rows):
            sep = "," if i < len(leads_rows) - 1 else ";"
            lines.append(
                f"  ('{lid}', '{cid}', '{vid}', {score}, {sql_str(prio)}, "
                f"'ABERTO', {sql_str(script)}, NOW(), NOW()){sep}"
            )

    lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Migration escrita em {out_path}")


if __name__ == "__main__":
    main()
