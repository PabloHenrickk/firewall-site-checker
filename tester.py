import requests
import re
import urllib3
import time
import csv
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.panel import Panel
from rich import box

# Desabilita aviso de certificado SSL (necessário devido ao proxy/firewall)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configurações
TIMEOUT = 10
DELAY   = 10  # segundos de espera entre cada teste (evita alertas no firewall)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# Indicadores de bloqueio pelo Fortinet
PALAVRAS_BLOQUEIO = [
    "ACESSO BLOQUEADO",
    "Access Blocked",
    "access blocked",
    "FortiGuard",
    "BLOQUEADO",
    "blocked by FortiGate",
    "Web Page Blocked",
    "This web page is blocked",
    "fortiguard.com",
]

console = Console()

# ── Funções ───────────────────────────────────────────────────────────────────

def carregar_sites(arquivo="sites.txt"):
    """Leitura do arquivo txt com os sites, retornando uma lista."""
    try:
        with open(arquivo, "r", encoding="utf-8") as f:
            sites = []
            for linha in f:
                linha = linha.strip()
                # Ignora linhas vazias e comentários (linhas que iniciam com #)
                if not linha or linha.startswith("#"):
                    continue
                # Garante que o site tem protocolo
                if not linha.startswith("http://") and not linha.startswith("https://"):
                    linha = "https://" + linha
                sites.append(linha)
            return sites
    except FileNotFoundError:
        console.print("[bold red]ERRO:[/] Arquivo 'sites.txt' não encontrado.")
        console.print("Crie o arquivo sites.txt com um site por linha.")
        input("\nPressione Enter para sair...")
        exit(1)


def detectar_bloqueio(html):
    """Verifica se o HTML contém indicadores de bloqueio do firewall."""
    for palavra in PALAVRAS_BLOQUEIO:
        if palavra.lower() in html.lower():
            return True
    return False


def extrair_categoria(html):
    """Tenta extrair a categoria do bloqueio da página do Fortinet."""
    padroes = [
        r'[Cc]ategoria[:\s]+([^\n<"]+)',
        r'[Cc]ategory[:\s]+([^\n<"]+)',
        r'[Cc]ategoria</[^>]+>[^<]*<[^>]+>([^<]+)',
        r'class="[^"]*categ[^"]*"[^>]*>([^<]+)',
    ]
    for padrao in padroes:
        match = re.search(padrao, html)
        if match:
            categoria = match.group(1).strip()
            categoria = re.sub(r'\s+', ' ', categoria)
            categoria = categoria.strip(' \t\n\r:')
            if categoria:
                return categoria
    return "Categoria não identificada"


def testar_site(site):
    """
    Testa o site e retorna (status, categoria).

    Retornos possíveis:
        - ("Liberado",        "-")
        - ("Bloqueado",       "Nome da Categoria")
        - ("ERR_TIMED_OUT",   "-")
        - ("Erro de Conexão", "-")
        - ("Erro SSL",        "-")
        - ("Erro HTTP XXX",   "-")
    """
    try:
        resposta = requests.get(
            site,
            timeout=TIMEOUT,
            headers=HEADERS,
            verify=False,         # Verificação em redes com inspeção SSL corporativa
            allow_redirects=True,
        )
        html = resposta.text

        # Verifica se é uma página de bloqueio do firewall
        if detectar_bloqueio(html):
            categoria = extrair_categoria(html)
            return "Bloqueado", categoria

        # Verifica código HTTP de erro
        if resposta.status_code >= 400:
            return f"Erro HTTP {resposta.status_code}", "-"

        return "Liberado", "-"

    except requests.exceptions.Timeout:
        return "ERR_TIMED_OUT", "-"

    except requests.exceptions.SSLError:
        return "Erro SSL", "-"

    except requests.exceptions.ConnectionError:
        return "Erro de Conexão", "-"

    except requests.exceptions.RequestException as e:
        return f"Erro: {str(e)[:60]}", "-"


def salvar_resultados(resultados, arquivo="resultado.csv"):
    """Salva os resultados em CSV com cabeçalho e timestamp."""
    with open(arquivo, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["Site", "Status", "Categoria", "Data/Hora"])
        writer.writerows(resultados)


def cor_status(status):
    """Retorna a cor rich de acordo com o status."""
    if status == "Liberado":
        return f"[bold green]{status}[/]"
    elif status.startswith("Bloqueado"):
        return f"[bold red]{status}[/]"
    else:
        return f"[bold yellow]{status}[/]"


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    console.print(Panel.fit(
        "[bold cyan]INTERNET CHECKER[/]\n[dim]Verificador de Sites — Fortinet/FortiGuard[/]",
        border_style="cyan"
    ))

    sites = carregar_sites("sites.txt")
    console.print(f"\n  [bold]{len(sites)}[/] site(s) carregado(s) do [cyan]sites.txt[/]\n")

    resultados = []
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")

    # Tabela de resultados ao vivo
    tabela = Table(box=box.ROUNDED, border_style="dim", show_lines=False)
    tabela.add_column("Status",    style="white",  width=22)
    tabela.add_column("Categoria", style="white",  width=38)
    tabela.add_column("Site",      style="dim",    no_wrap=False)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=30),
        TextColumn("[bold]{task.completed}/{task.total}[/]"),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    ) as progress:
        tarefa = progress.add_task("[cyan]Testando sites...", total=len(sites))

        for i, site in enumerate(sites):
            progress.update(tarefa, description=f"[cyan]Testando:[/] {site[:55]}...")
            status, categoria = testar_site(site)
            resultados.append([site, status, categoria, agora])

            # Adiciona linha na tabela
            tabela.add_row(cor_status(status), categoria, site)

            progress.advance(tarefa)

            # Aguarda entre os testes para não disparar alertas no firewall
            if i < len(sites) - 1:
                for s in range(DELAY, 0, -1):
                    progress.update(tarefa, description=f"[dim]Aguardando {s}s até o próximo teste...[/]")
                    time.sleep(1)

    # Exibe tabela completa
    console.print("\n")
    console.print(tabela)

    salvar_resultados(resultados)

    # Resumo final
    total      = len(resultados)
    liberados  = sum(1 for r in resultados if r[1] == "Liberado")
    bloqueados = sum(1 for r in resultados if r[1] == "Bloqueado")
    erros      = total - liberados - bloqueados

    console.print(Panel(
        f"[bold]Total:[/] {total} testados    "
        f"[bold green]Liberados: {liberados}[/]    "
        f"[bold red]Bloqueados: {bloqueados}[/]    "
        f"[bold yellow]Erros/Timeout: {erros}[/]\n\n"
        f"[dim]Relatório salvo em:[/] [cyan]resultado.csv[/]",
        title="RESUMO",
        border_style="cyan"
    ))

    input("\nPressione Enter para fechar...")


if __name__ == "__main__":
    main()