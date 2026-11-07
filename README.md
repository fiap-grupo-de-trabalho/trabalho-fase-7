# SIFSM - Sistema Integrado de Futuro Sustentável em Marte

Projeto da Fase 7 (A Aurora Constrói os Alicerces de um Futuro Sustentável em Marte) - Ciência da Computação FIAP.

O SIFSM é um protótipo em Python, com menu no terminal, que guarda as leituras dos módulos da colônia Aurora Siger em um banco Oracle, faz o CRUD dessas leituras, aplica uma regra booleana de alerta, organiza chamados e buscas com estruturas de dados, simula o estado de carga da bateria da colônia, estima o consumo com regressão linear e responde perguntas por meio de agentes simulados com guardrail.

## Integrantes

| Nome | GitHub |
|---|---|
| Leonardo Tims | [timsleo](https://github.com/timsleo) |
| Matheus Fuchelberguer Neves | [Fuchens28](https://github.com/Fuchens28) |
| Rodrigo Gomes Dias | [rodrigogmdias](https://github.com/rodrigogmdias) |

## Arquivos

| Arquivo | Descrição |
|---|---|
| `codigo_fonte.py` | Arquivo principal do sistema (menu, CRUD, regra, estruturas, simulação, regressão e agentes) |
| `script_banco.sql` | Criação da tabela `sifsm_leituras` no Oracle |
| `dados_aurora_siger.csv` | Base simulada com 8 módulos em 5 ciclos (40 leituras) |
| `circuito_logico.png` | Circuito lógico da regra de alerta com portas AND, NOT, OR e LED |
| `relatorio_tecnico.md` | Relatório técnico do projeto |
| `link_video.txt` | Link do vídeo no YouTube (não listado) |
| `pyproject.toml` / `uv.lock` | Dependências gerenciadas pelo uv |
| `requirements.txt` | Mesmas dependências para instalar com pip |
| `graficos_ou_imagens/` | Gráficos gerados pela simulação e pela regressão |

A simulação computacional está dentro do `codigo_fonte.py` (opção 8 do menu).

### Colunas da tabela

`id`, `ciclo`, `modulo`, `tipo`, `codigo_sensor`, `ocupantes`, `temperatura_c`, `consumo_kwh`, `geracao_solar_kwh`, `carga_bateria_pct`, `critico` (1 ou 0) e `status` (ativo, alerta ou manutencao).

## Dependências

- Python 3.12 ou superior
- oracledb (conexão com o Oracle da FIAP)
- Pandas, NumPy, Matplotlib, SciPy e scikit-learn

Todas foram usadas nas fases do curso.

## Como executar

1. Crie a tabela no Oracle executando o `script_banco.sql` (SQL Developer ou outro cliente).
2. Instale as dependências e rode o sistema:

```bash
uv sync
uv run codigo_fonte.py
```

Sem o uv:

```bash
pip install -r requirements.txt
python codigo_fonte.py
```

3. Informe usuário e senha do Oracle (`oracle.fiap.com.br:1521/ORCL`).
4. Escolha a opção 1 para carregar o CSV no banco e depois use as demais opções.

## Funcionalidades do menu

1. **Carregar dados do CSV para o banco**: apaga a tabela e grava as 40 leituras do CSV.
2. **Cadastrar leitura**: INSERT com validação (números, bateria entre 0 e 100, crítico 0 ou 1).
3. **Listar leituras**: SELECT exibido em DataFrame do Pandas.
4. **Alterar leitura**: UPDATE de consumo, bateria e status pelo id.
5. **Excluir leitura**: DELETE pelo id.
6. **Aplicar regra booleana**: mostra a tabela verdade de `ALERTA = (A AND B) OR (C AND NOT D)` e coloca as leituras em alerta na fila de manutenção.
7. **Estruturas de dados**: fila de chamados, pilha do histórico de ações, tabela hash por código do sensor e grafo da rede elétrica (busca em largura dos módulos afetados).
8. **Simulação da bateria**: 24 h de geração solar e consumo, método de Euler para a carga e integral numérica (regra do trapézio) para a energia, comparando o cenário normal com economia de 20%.
9. **Regressão linear**: análise exploratória, correlação, modelo `consumo = b0 + b1 x ocupantes`, MAE, R² e previsão.
10. **Assistente multiagente**: agente triador encaminha para o agente de energia ou de manutenção, que usam funções determinísticas sobre o banco, com guardrail.
11. **Análise final**: resumo dos resultados, recomendações e limitações.

## Exemplo de execução

```
========== SIFSM - AURORA SIGER ==========
Escolha uma opção: 6
----- REGRA BOOLEANA DE ALERTA -----
ALERTA = (A AND B) OR (C AND NOT D)
...
9 leituras acionaram o alerta e entraram na fila de manutenção:
 - Ciclo 1 - Agricultura Norte (AGR01): consumo 40.94 kWh, bateria 66.3%
 - Ciclo 1 - Suporte Medico (MED01): consumo 43.25 kWh, bateria 25.5%
...
Escolha uma opção: 9
consumo = 15.03 + 2.48 x ocupantes
MAE: 2.76 kWh | R²: 0.880
    Quantos ocupantes deseja simular? 12
Consumo estimado: 44.80 kWh
Acima do limite: recomenda-se redistribuir a tripulação.
```
