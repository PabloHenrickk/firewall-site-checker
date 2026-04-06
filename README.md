# 🌐 Internet Checker — Verificador de Sites (Fortinet/FortiGuard)

Ferramenta para automatizar testes de acesso a sites dentro de redes corporativas
que utilizam firewall Fortinet/FortiGuard.

---

## 📁 Estrutura do Projeto

```
internet_checker/
│
├── sites.txt         ← Lista de sites que você quer testar (você edita isso)
├── tester.py         ← Script principal
├── requirements.txt  ← Dependências Python
├── resultado.csv     ← Gerado automaticamente após cada execução
└── README.md         ← Este arquivo
```

---

## ⚙️ Configuração (fazer só uma vez)

### 1. Instalar Python
Baixe em: https://www.python.org/downloads/
Durante a instalação, marque ✅ **"Add Python to PATH"**

### 2. Abrir a pasta no VS Code
- File → Open Folder → selecione a pasta `internet_checker`

### 3. Abrir o terminal no VS Code
- Menu Terminal → New Terminal

### 4. Instalar as dependências
```bash
pip install -r requirements.txt
```

---

## ▶️ Como usar

### 1. Edite o arquivo `sites.txt`
Coloque os sites que deseja testar, um por linha:
```
https://www.espn.com/espnplus/
https://www.netflix.com
https://www.youtube.com
```
- Linhas começando com `#` são **comentários** (ignoradas pelo script)
- Pode escrever sem o `https://` que o script adiciona automaticamente

### 2. Execute o script
No terminal do VS Code:
```bash
python tester.py
```

****Ou caso desejar, crie um arquivo .bar com as linhas abaixo****
----------------------------|
        @echo off
        cd /d "%~dp0"
        python tester.py
        pause
----------------------------|

### 3. Veja os resultados
- **No terminal**: resultado colorido em tempo real
- **No arquivo `resultado.csv`**: relatório completo (abre no Excel)

---

## 📊 Resultados possíveis

| Status             | Significado                                              |
|--------------------|----------------------------------------------------------|
| `Liberado`         | Site carregou normalmente                                |
| `Bloqueado`        | Firewall bloqueou — a categoria aparece na coluna ao lado |
| `ERR_TIMED_OUT`    | Site não respondeu dentro do tempo limite                |
| `Erro de Conexão`  | Não foi possível conectar ao site                        |
| `Erro SSL`         | Problema com certificado (comum em redes com inspeção SSL)|
| `Erro HTTP 403`    | Servidor recusou o acesso                                |

---

## 🔧 Configurações avançadas (no tester.py)

No topo do arquivo `tester.py` você pode ajustar:

```python
TIMEOUT = 10  # Aumentar se a rede for lenta (ex: 15 ou 20)
DELAY   = 10  #Tempo para pular para o próximo site, evitando alertas

```

---

## ❓ Dúvidas e Correções

**O CSV abre com caracteres estranhos no Excel?**
Abra o Excel → Dados → De Texto/CSV → selecione o arquivo → escolha delimitador `;`

**O script diz "Liberado" mas o site abre a página de bloqueio?**
O Fortinet pode usar uma mensagem diferente. Abra a página de bloqueio,
clique em "Ver código-fonte" (Ctrl+U), procure o texto que identifica o bloqueio
e adicione em `PALAVRAS_BLOQUEIO` dentro do `tester.py`.
