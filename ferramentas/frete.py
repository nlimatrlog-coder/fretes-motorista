#!/usr/bin/env python3
"""Calculadora de frete — N LIMA TRANSPORTES.

Uso rápido (linha de comando):
    python3 ferramentas/frete.py --km 650 --t 37 --rs-t 95 --diesel 6.20 --kml 2.3

Ou importando:
    from frete import Frete, calcula
    r = calcula(Frete(km_carregado=650, toneladas=37, rs_por_t=95, ...))

Todos os valores padrão abaixo são PREMISSAS — substitua pelos dados reais.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, asdict


@dataclass
class Frete:
    km_carregado: float
    toneladas: float
    rs_por_t: float
    km_vazio: float | None = None          # None = volta vazia igual à ida (cenário base)
    preco_diesel: float = 6.20             # PREMISSA R$/L — pesquisar preço atual
    km_l_carregado: float = 2.2            # PREMISSA
    km_l_vazio: float = 2.8                # PREMISSA
    arla_pct: float = 0.05                 # PREMISSA: ARLA ≈ 5% do volume de diesel
    preco_arla: float = 3.50               # PREMISSA R$/L
    pneu_rs_km: float = 0.45               # PREMISSA (cavalo + carreta)
    manut_rs_km: float = 0.55              # PREMISSA
    pedagios: float = 0.0
    comissao_pct: float = 0.10             # PREMISSA: comissão do motorista sobre receita bruta
    diarias_alimentacao: float = 0.0
    outros: float = 0.0
    fixos_mensais: float = 0.0             # custos fixos do caminhão no mês
    viagens_mes: float = 0.0               # para ratear fixos (0 = não rateia)
    frete_retorno: float = 0.0             # receita do frete de retorno, se houver


def calcula(f: Frete) -> dict:
    km_vazio = f.km_carregado if f.km_vazio is None else f.km_vazio
    if f.frete_retorno and f.km_vazio is None:
        km_vazio = 0.0  # volta carregada: tratar a volta como km carregado
    km_retorno_carregado = f.km_carregado if f.frete_retorno and f.km_vazio is None else 0.0
    km_total = f.km_carregado + km_vazio + km_retorno_carregado

    litros = (f.km_carregado + km_retorno_carregado) / f.km_l_carregado + km_vazio / f.km_l_vazio
    diesel = litros * f.preco_diesel
    arla = litros * f.arla_pct * f.preco_arla
    pneus = km_total * f.pneu_rs_km
    manut = km_total * f.manut_rs_km

    receita = f.toneladas * f.rs_por_t + f.frete_retorno
    comissao = receita * f.comissao_pct
    variaveis = diesel + arla + pneus + manut + f.pedagios + comissao + f.diarias_alimentacao + f.outros
    fixo_rateado = f.fixos_mensais / f.viagens_mes if f.viagens_mes else 0.0
    custo_total = variaveis + fixo_rateado
    margem = receita - custo_total

    margem_contrib = receita - variaveis
    viagens_be = f.fixos_mensais / margem_contrib if f.fixos_mensais and margem_contrib > 0 else None

    return {
        "km_total": km_total,
        "pct_km_vazio": km_vazio / km_total if km_total else 0,
        "litros_diesel": litros,
        "diesel": diesel, "arla": arla, "pneus": pneus, "manutencao": manut,
        "pedagios": f.pedagios, "comissao": comissao,
        "diarias_alimentacao": f.diarias_alimentacao, "outros": f.outros,
        "custo_variavel": variaveis, "fixo_rateado": fixo_rateado,
        "custo_total": custo_total, "receita": receita,
        "margem": margem, "margem_pct": margem / receita if receita else 0,
        "margem_contribuicao": margem_contrib,
        "custo_por_km": custo_total / km_total if km_total else 0,
        "receita_por_km": receita / km_total if km_total else 0,
        "margem_por_km": margem / km_total if km_total else 0,
        "custo_por_t": custo_total / f.toneladas if f.toneladas else 0,
        "viagens_mes_p_cobrir_fixos": viagens_be,
    }


def brl(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def imprime(r: dict) -> None:
    linhas = [
        ("Km total (ida + volta)", f"{r['km_total']:,.0f} km".replace(',', '.')),
        ("% km vazio", f"{r['pct_km_vazio']:.0%}"),
        ("Diesel", f"{brl(r['diesel'])} ({r['litros_diesel']:.0f} L)"),
        ("ARLA 32", brl(r["arla"])), ("Pneus", brl(r["pneus"])),
        ("Manutenção", brl(r["manutencao"])), ("Pedágios", brl(r["pedagios"])),
        ("Comissão motorista", brl(r["comissao"])),
        ("Diárias/alimentação", brl(r["diarias_alimentacao"])), ("Outros", brl(r["outros"])),
        ("= Custo variável", brl(r["custo_variavel"])),
        ("Fixo rateado", brl(r["fixo_rateado"])),
        ("= CUSTO TOTAL", brl(r["custo_total"])),
        ("RECEITA", brl(r["receita"])),
        ("MARGEM", f"{brl(r['margem'])} ({r['margem_pct']:.1%})"),
        ("Custo/km", brl(r["custo_por_km"])), ("Receita/km", brl(r["receita_por_km"])),
        ("Margem/km", brl(r["margem_por_km"])), ("Custo/t", brl(r["custo_por_t"])),
    ]
    if r["viagens_mes_p_cobrir_fixos"]:
        linhas.append(("Viagens/mês p/ cobrir fixos", f"{r['viagens_mes_p_cobrir_fixos']:.1f}"))
    w = max(len(a) for a, _ in linhas)
    for a, b in linhas:
        print(f"{a:<{w}}  {b}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Calcula custo e margem de um frete.")
    p.add_argument("--km", type=float, required=True, help="km carregado (ida)")
    p.add_argument("--t", type=float, required=True, help="toneladas")
    p.add_argument("--rs-t", type=float, required=True, help="R$ por tonelada")
    p.add_argument("--km-vazio", type=float)
    p.add_argument("--diesel", type=float, default=Frete.preco_diesel)
    p.add_argument("--kml", type=float, default=Frete.km_l_carregado, help="km/L carregado")
    p.add_argument("--kml-vazio", type=float, default=Frete.km_l_vazio)
    p.add_argument("--pedagios", type=float, default=0.0)
    p.add_argument("--comissao", type=float, default=Frete.comissao_pct, help="fração, ex. 0.10")
    p.add_argument("--fixos", type=float, default=0.0, help="custos fixos mensais do caminhão")
    p.add_argument("--viagens-mes", type=float, default=0.0)
    p.add_argument("--retorno", type=float, default=0.0, help="receita do frete de retorno")
    a = p.parse_args()
    imprime(calcula(Frete(
        km_carregado=a.km, toneladas=a.t, rs_por_t=a.rs_t, km_vazio=a.km_vazio,
        preco_diesel=a.diesel, km_l_carregado=a.kml, km_l_vazio=a.kml_vazio,
        pedagios=a.pedagios, comissao_pct=a.comissao, fixos_mensais=a.fixos,
        viagens_mes=a.viagens_mes, frete_retorno=a.retorno,
    )))
