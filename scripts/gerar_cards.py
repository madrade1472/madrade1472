#!/usr/bin/env python3
"""Gera os cards SVG do perfil (estatísticas, commits, linguagens, atividade).

Roda sem dependências externas. Usa METRICS_TOKEN se existir, senão GITHUB_TOKEN.
Saída em assets/cards/{nome}-{dark|light}.svg
"""
import datetime as dt
import json
import os
import pathlib
import urllib.request
from xml.sax.saxutils import escape

USUARIO = os.environ.get("PERFIL_USUARIO", "madrade1472")
TOKEN = os.environ.get("METRICS_TOKEN") or os.environ.get("GITHUB_TOKEN")
SAIDA = pathlib.Path(__file__).resolve().parent.parent / "assets" / "cards"

FONTE = "'Segoe UI', Inter, -apple-system, BlinkMacSystemFont, Helvetica, Arial, sans-serif"
MONO = "'JetBrains Mono', 'SFMono-Regular', Consolas, 'Liberation Mono', monospace"

TEMAS = {
    "dark": dict(bg="#0d1117", bg2="#161b22", borda="#21262d", texto="#e6edf3",
                 sub="#8b949e", acento="#58a6ff", acento2="#a371f7", grade="#21262d",
                 vazio="#161b22"),
    "light": dict(bg="#ffffff", bg2="#f6f8fa", borda="#d0d7de", texto="#1f2328",
                  sub="#59636e", acento="#0969da", acento2="#8250df", grade="#eaeef2",
                  vazio="#ebedf0"),
}

MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def gql(query, **variaveis):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variaveis}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json",
                 "User-Agent": "perfil-cards"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        dados = json.load(r)
    if dados.get("errors"):
        raise RuntimeError(dados["errors"])
    return dados["data"]


def coletar():
    base = gql("""query($u:String!){ user(login:$u){
        createdAt followers{totalCount}
        pullRequests{totalCount} issues{totalCount}
        contributionsCollection{ contributionYears }
    }}""", u=USUARIO)["user"]

    anos = sorted(base["contributionsCollection"]["contributionYears"])
    commits_ano, prs_rev, dias = {}, 0, {}
    for ano in anos:
        ini = f"{ano}-01-01T00:00:00Z"
        fim = f"{ano}-12-31T23:59:59Z"
        c = gql("""query($u:String!,$a:DateTime!,$b:DateTime!){ user(login:$u){
            contributionsCollection(from:$a,to:$b){
              totalCommitContributions restrictedContributionsCount
              totalPullRequestReviewContributions
              contributionCalendar{ weeks{ contributionDays{ date contributionCount } } }
            }}}""", u=USUARIO, a=ini, b=fim)["user"]["contributionsCollection"]
        commits_ano[ano] = c["totalCommitContributions"]
        prs_rev += c["totalPullRequestReviewContributions"]
        for w in c["contributionCalendar"]["weeks"]:
            for d in w["contributionDays"]:
                dias[d["date"]] = d["contributionCount"]

    repos, cursor = [], None
    while True:
        r = gql("""query($u:String!,$c:String){ user(login:$u){
            repositories(first:100, after:$c, ownerAffiliations:OWNER, isFork:false){
              pageInfo{hasNextPage endCursor}
              nodes{ stargazerCount languages(first:15, orderBy:{field:SIZE,direction:DESC}){
                edges{ size node{ name color } } } } } }}""", u=USUARIO, c=cursor)
        bloco = r["user"]["repositories"]
        repos += bloco["nodes"]
        if not bloco["pageInfo"]["hasNextPage"]:
            break
        cursor = bloco["pageInfo"]["endCursor"]

    linguagens = {}
    for rp in repos:
        for e in rp["languages"]["edges"]:
            nome = e["node"]["name"]
            if nome == "Jupyter Notebook":
                nome = "Python"  # notebook é Python, o tamanho do JSON distorce
            item = linguagens.setdefault(nome, {"bytes": 0, "cor": e["node"]["color"] or "#8b949e"})
            item["bytes"] += e["size"]
            if nome == "Python":
                item["cor"] = "#3572A5"

    return dict(
        anos=anos, commits_ano=commits_ano, dias=dias, linguagens=linguagens,
        repos=len(repos), estrelas=sum(r["stargazerCount"] for r in repos),
        prs=base["pullRequests"]["totalCount"], issues=base["issues"]["totalCount"],
        revisoes=prs_rev, seguidores=base["followers"]["totalCount"],
    )


def sequencias(dias):
    hoje = dt.date.today()
    datas = sorted(d for d in dias if dt.date.fromisoformat(d) <= hoje)
    maior = atual = corrida = 0
    for d in datas:
        corrida = corrida + 1 if dias[d] > 0 else 0
        maior = max(maior, corrida)
    # sequência atual tolera hoje ainda sem contribuição
    i = len(datas) - 1
    if i >= 0 and dias[datas[i]] == 0:
        i -= 1
    while i >= 0 and dias[datas[i]] > 0:
        atual += 1
        i -= 1
    ativos = sum(1 for d in datas if dias[d] > 0)
    return atual, maior, ativos


def fmt(n):
    return f"{n:,}".replace(",", ".")


def moldura(t, w, h, corpo, titulo):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(titulo)}">
<title>{escape(titulo)}</title>
<style>
  .t{{font-family:{FONTE};fill:{t['texto']}}}
  .s{{font-family:{FONTE};fill:{t['sub']}}}
  .m{{font-family:{MONO}}}
  .entra{{opacity:0;animation:entra .7s cubic-bezier(.2,.7,.2,1) forwards}}
  @keyframes entra{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:none}}}}
  @media (prefers-reduced-motion: reduce){{.entra,.cresce,.barra{{animation:none!important;opacity:1!important;transform:none!important}}}}
</style>
<defs>
  <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{t['acento']}"/><stop offset="1" stop-color="{t['acento2']}"/>
  </linearGradient>
</defs>
<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="14" fill="{t['bg']}" stroke="{t['borda']}"/>
{corpo}
</svg>"""


def card_commits(d, t):
    w, h = 840, 210
    total = sum(d["commits_ano"].values())
    ano = dt.date.today().year
    atual, maior, ativos = sequencias(d["dias"])
    desde = d["anos"][0]

    kpis = [
        (fmt(d["commits_ano"].get(ano, 0)), f"commits em {ano}"),
        (fmt(d["prs"]), "pull requests"),
        (fmt(d["seguidores"]), "seguidores"),
        (fmt(d["repos"]), "repositórios"),
        (f"{atual} {'dia' if atual == 1 else 'dias'}", "sequência atual"),
        (f"{maior} dias", "maior sequência"),
        (fmt(ativos), "dias ativos"),
        (fmt(d["estrelas"]), "estrelas"),
    ]
    x0, y0, cw, ch = 330, 34, 125, 72
    cel = []
    for i, (valor, rot) in enumerate(kpis):
        cx, cy = x0 + (i % 4) * cw, y0 + (i // 4) * (ch + 10)
        cel.append(f"""<g class="entra" style="animation-delay:{.25 + i * .07:.2f}s">
  <rect x="{cx}" y="{cy}" width="{cw - 10}" height="{ch}" rx="10" fill="{t['bg2']}" stroke="{t['borda']}"/>
  <text x="{cx + 14}" y="{cy + 33}" class="t" font-size="21" font-weight="700">{escape(valor)}</text>
  <text x="{cx + 14}" y="{cy + 54}" class="s" font-size="11.5">{escape(rot)}</text>
</g>""")

    corpo = f"""
<g class="entra">
  <text x="32" y="48" class="s m" font-size="12" letter-spacing="2">TOTAL DE COMMITS</text>
  <text x="30" y="122" font-family="{FONTE}" font-size="72" font-weight="800" fill="url(#g)" letter-spacing="-2">{fmt(total)}</text>
  <text x="32" y="152" class="s" font-size="13">na vida toda, desde {desde}</text>
</g>
<g class="entra" style="animation-delay:.15s">{faixa_anos(d, t, 32, 172, 270)}</g>
<line x1="306" y1="32" x2="306" y2="{h - 32}" stroke="{t['borda']}"/>
{''.join(cel)}"""
    return moldura(t, w, h, corpo, f"{total} commits no GitHub")


def faixa_anos(d, t, x, y, largura):
    anos = d["anos"]
    maxc = max(d["commits_ano"].values()) or 1
    passo = largura / len(anos)
    partes = []
    for i, a in enumerate(anos):
        v = d["commits_ano"][a]
        bh = max(2, 16 * v / maxc)
        bx = x + i * passo
        partes.append(
            f'<rect x="{bx:.1f}" y="{y - bh:.1f}" width="{passo - 8:.1f}" height="{bh:.1f}" rx="2" fill="url(#g)" opacity="{.35 + .65 * v / maxc:.2f}"><title>{a}: {v} commits</title></rect>'
            f'<text x="{bx:.1f}" y="{y + 14}" class="s m" font-size="9.5">{a}</text>')
    return "".join(partes)


def card_linguagens(d, t):
    w, h = 410, 210
    total = sum(v["bytes"] for v in d["linguagens"].values()) or 1
    ordem = sorted(d["linguagens"].items(), key=lambda kv: -kv[1]["bytes"])
    top, resto = ordem[:7], ordem[7:]
    if resto:
        top.append(("Outras", {"bytes": sum(v["bytes"] for _, v in resto), "cor": t["sub"]}))

    barra, x = [], 24
    largura = w - 48
    for i, (nome, v) in enumerate(top):
        bw = largura * v["bytes"] / total
        barra.append(f'<rect x="{x:.1f}" y="62" width="{max(bw, 1.5):.1f}" height="10" fill="{v["cor"]}"><title>{escape(nome)}</title></rect>')
        x += bw
    leg = []
    for i, (nome, v) in enumerate(top):
        lx, ly = 24 + (i % 2) * 185, 104 + (i // 2) * 26
        pct = 100 * v["bytes"] / total
        leg.append(f"""<g class="entra" style="animation-delay:{.2 + i * .06:.2f}s">
  <circle cx="{lx + 5}" cy="{ly - 4}" r="5" fill="{v['cor']}"/>
  <text x="{lx + 17}" y="{ly}" class="t" font-size="13">{escape(nome)}</text>
  <text x="{lx + 170}" y="{ly}" class="s m" font-size="11.5" text-anchor="end">{pct:.1f}%</text>
</g>""")
    corpo = f"""
<text x="24" y="40" class="s m entra" font-size="12" letter-spacing="2">LINGUAGENS MAIS USADAS</text>
<clipPath id="c"><rect x="24" y="62" width="{largura}" height="10" rx="5"/></clipPath>
<g clip-path="url(#c)"><g class="barra" style="transform-origin:24px 0;animation:cresce 1.1s cubic-bezier(.2,.7,.2,1) forwards;transform:scaleX(0)">{''.join(barra)}</g></g>
<style>@keyframes cresce{{to{{transform:scaleX(1)}}}}</style>
{''.join(leg)}"""
    return moldura(t, w, h, corpo, "Linguagens mais usadas")


def card_atividade(d, t):
    w, h = 410, 210
    hoje = dt.date.today()
    meses = []
    a, m = hoje.year, hoje.month
    for _ in range(12):
        meses.append((a, m))
        m -= 1
        if m == 0:
            a, m = a - 1, 12
    meses.reverse()
    soma = {k: 0 for k in meses}
    for dia, n in d["dias"].items():
        dd = dt.date.fromisoformat(dia)
        if (dd.year, dd.month) in soma:
            soma[(dd.year, dd.month)] += n
    maxv = max(soma.values()) or 1
    x0, base, alt, larg = 24, 168, 100, (w - 48) / 12
    barras = []
    for i, k in enumerate(meses):
        v = soma[k]
        bh = max(3, alt * v / maxv)
        bx = x0 + i * larg
        barras.append(f"""<g>
  <rect class="cresce" x="{bx + 3:.1f}" y="{base - bh:.1f}" width="{larg - 6:.1f}" height="{bh:.1f}" rx="4" fill="url(#g)"
        style="transform-origin:0 {base}px;transform:scaleY(0);animation:sobe .9s cubic-bezier(.2,.7,.2,1) {.1 + i * .05:.2f}s forwards"><title>{MESES[k[1]-1]}/{k[0]}: {v}</title></rect>
  <text x="{bx + larg / 2:.1f}" y="{base + 18}" class="s m" font-size="10" text-anchor="middle">{MESES[k[1]-1]}</text>
</g>""")
    total12 = sum(soma.values())
    corpo = f"""
<text x="24" y="40" class="s m entra" font-size="12" letter-spacing="2">ÚLTIMOS 12 MESES</text>
<text x="{w - 24}" y="40" class="t entra" font-size="13" font-weight="600" text-anchor="end">{fmt(total12)} contribuições</text>
<line x1="24" y1="{base}" x2="{w - 24}" y2="{base}" stroke="{t['grade']}"/>
<line x1="24" y1="{base - alt}" x2="{w - 24}" y2="{base - alt}" stroke="{t['grade']}" stroke-dasharray="3 4"/>
<line x1="24" y1="{base - alt / 2}" x2="{w - 24}" y2="{base - alt / 2}" stroke="{t['grade']}" stroke-dasharray="3 4"/>
<style>@keyframes sobe{{to{{transform:scaleY(1)}}}}</style>
{''.join(barras)}"""
    return moldura(t, w, h, corpo, "Contribuições nos últimos 12 meses")


def main():
    if not TOKEN:
        raise SystemExit("defina METRICS_TOKEN ou GITHUB_TOKEN")
    d = coletar()
    SAIDA.mkdir(parents=True, exist_ok=True)
    for nome_tema, t in TEMAS.items():
        (SAIDA / f"commits-{nome_tema}.svg").write_text(card_commits(d, t), encoding="utf-8")
        (SAIDA / f"linguagens-{nome_tema}.svg").write_text(card_linguagens(d, t), encoding="utf-8")
        (SAIDA / f"atividade-{nome_tema}.svg").write_text(card_atividade(d, t), encoding="utf-8")
    print(json.dumps({"commits": sum(d["commits_ano"].values()), "por_ano": d["commits_ano"],
                      "repos": d["repos"], "prs": d["prs"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
