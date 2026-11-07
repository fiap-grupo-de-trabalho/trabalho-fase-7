# Relatório Técnico - SIFSM (Sistema Integrado de Futuro Sustentável em Marte)

**Fase 7 - A Aurora Constrói os Alicerces de um Futuro Sustentável em Marte | Ciência da Computação - FIAP**

**Grupo 18** - Rodrigo Gomes Dias

## 1. Contexto da solução

A colônia Aurora Siger depende de energia solar e de uma bateria central para manter habitação, agricultura, laboratório, comunicação e suporte médico funcionando. Sem um sistema que junte os dados, a equipe só percebe um problema quando ele já aconteceu: um módulo crítico consumindo demais, a bateria descendo abaixo do seguro durante a noite ou um chamado de manutenção esquecido.

O SIFSM é um protótipo em Python com menu no terminal que integra:

- banco de dados Oracle com CRUD das leituras dos módulos;
- tratamento de erros com `try`, `except`, `else` e `finally`;
- uma regra booleana de alerta, também representada como circuito lógico;
- fila, pilha, tabela hash e grafo;
- simulação do estado de carga da bateria com integração numérica;
- regressão linear simples para estimar o consumo;
- agentes simulados com ferramentas, handoff e guardrail;
- análise final com recomendações e limitações.

Não há sensores reais nem APIs externas. Os dados são simulados, como permitido no enunciado.

## 2. Dados e banco de dados

A base `dados_aurora_siger.csv` tem 8 módulos registrados em 5 ciclos (40 leituras). Ela é carregada no Oracle pela opção 1 do menu.

| Campo | Descrição |
|---|---|
| `id` | Chave primária gerada pelo Oracle (identity) |
| `ciclo` | Ciclo de leitura (1 a 5) |
| `modulo` / `tipo` | Nome e tipo do módulo |
| `codigo_sensor` | Código do sensor do módulo (ex: `MED01`) |
| `ocupantes` | Pessoas no módulo durante o ciclo |
| `temperatura_c` | Temperatura interna (°C) |
| `consumo_kwh` | Energia consumida no ciclo |
| `geracao_solar_kwh` | Energia solar disponível para o módulo |
| `carga_bateria_pct` | Carga da bateria que atende o módulo (%) |
| `critico` | 1 se o módulo é essencial para a vida, 0 se não |
| `status` | ativo, alerta ou manutencao |

A tabela é criada pelo `script_banco.sql`. A conexão usa `oracledb.connect` no servidor `oracle.fiap.com.br`, igual ao exemplo do Cap. 3. Cada operação do CRUD monta a instrução SQL e chama `execute` e `commit`:

| Operação | Instrução | Opção |
|---|---|---|
| Cadastrar | `INSERT INTO sifsm_leituras ...` | 2 |
| Listar | `SELECT ... ORDER BY id` (exibido com Pandas) | 3 |
| Alterar | `UPDATE sifsm_leituras SET ... WHERE id = ...` | 4 |
| Excluir | `DELETE FROM sifsm_leituras WHERE id = ...` | 5 |

### Tratamento de erros

- Falha na conexão (usuário ou senha errados): `except` mostra a mensagem do Oracle e o sistema encerra sem quebrar; o `else` confirma a conexão.
- Cadastro: `ValueError` para texto em campo numérico, bateria fora de 0 a 100 ou crítico diferente de 0 e 1 (lançado com `raise`); `Exception` para erro na transação; `else` confirma a gravação.
- Alteração: usa `try`, `except`, `else` e `finally` (mensagem de fim da operação sempre aparece).
- Id inexistente ou não numérico em alterar e excluir é avisado antes de executar o SQL.
- Carga do CSV: `FileNotFoundError` se o arquivo não existir.
- O menu tem um `try` geral para que nenhum erro inesperado derrube o sistema.

## 3. Regra booleana e circuito lógico

Variáveis de entrada:

- **A** = consumo maior que 40 kWh
- **B** = módulo crítico
- **C** = bateria abaixo de 30%
- **D** = geração solar maior ou igual a 30 kWh

**ALERTA = (A AND B) OR (C AND NOT D)**

Ou seja: há alerta quando um módulo essencial consome demais, ou quando a bateria está baixa e o sol não consegue repor a carga. A opção 6 imprime a tabela verdade com as 16 combinações e aplica a regra em todas as leituras do banco. Com a base atual, 9 de 40 leituras (22,5%) acionaram o alerta.

O arquivo `circuito_logico.png` mostra o circuito equivalente: uma porta AND para A e B, uma porta NOT em D, uma segunda AND para C e NOT D, e uma porta OR que liga o LED de alerta. No Arduino (ou Tinkercad), A a D seriam entradas digitais vindas de sensores ou chaves, e o LED ficaria no pino 13 com resistor. A mesma decisão pode ser feita por software (Python) ou por hardware (portas lógicas), o que mostra a equivalência entre os dois.

## 4. Estruturas de dados

| Estrutura | Onde é usada | Por quê |
|---|---|---|
| Fila (lista com `append` e `pop(0)`) | Chamados de manutenção gerados pela regra de alerta | O primeiro alerta registrado é o primeiro atendido (FIFO) |
| Pilha (lista com `append`, lida do topo) | Histórico das ações do CRUD | A última ação aparece primeiro, como num histórico para desfazer |
| Tabela hash (dicionário) | Busca das leituras pelo código do sensor | Acesso direto pela chave, sem percorrer a tabela toda |
| Grafo (dicionário de adjacência) | Rede elétrica entre módulos | Representa dependências; a busca em largura mostra quem fica sem energia quando um módulo falha |
| Lista / DataFrame | Leituras vindas do banco | Base para regra, regressão e análises |

Exemplo do grafo: se a Usina Solar falha, a busca em largura mostra que os outros 7 módulos são afetados. Se a Habitação Alfa falha, só a Agricultura Norte é afetada.

## 5. Simulação computacional e matemática

A opção 8 simula 24 horas da bateria da colônia (capacidade de 500 kWh, passo de 0,5 h, carga inicial de 50%).

- Geração solar: `G(t) = max(0, 75 sen(π (t - 6) / 12))` kW, com sol entre 6 h e 18 h.
- Consumo: `C(t) = f (25 + 10 sen²(π (t - 14) / 12))` kW, onde `f` é 1 no cenário normal e 0,8 no cenário com economia.
- Estado de carga pelo método de Euler: `SOC(t + dt) = SOC(t) + (G - C) / capacidade x 100 x dt`, limitado entre 0% e 100%.
- Energia gerada e consumida pela integral definida, calculada com a regra do trapézio (`scipy.integrate.trapezoid`). A potência média é a média da função: integral dividida por 24 h.

| Cenário | Energia gerada | Energia consumida | Carga mínima | Carga final | Horas abaixo de 30% |
|---|---|---|---|---|---|
| Normal | 572,1 kWh | 720,0 kWh | 9,8% | 20,4% | 10,0 h |
| Economia 20% | 572,1 kWh | 576,0 kWh | 18,9% | 49,2% | 5,5 h |

Interpretação: no cenário normal a área sob a curva de consumo é maior que a da geração, então a bateria termina o dia mais vazia do que começou e não se sustenta. Com 20% de economia, as duas áreas ficam quase iguais, a bateria volta a 49% e o tempo abaixo do limite cai quase pela metade. O gráfico fica em `graficos_ou_imagens/simulacao_bateria.png`.

Limitações: curvas fixas, sem tempestades de poeira, sem perdas na bateria e sem variação entre dias.

## 6. Modelo linear

A opção 9 faz uma análise exploratória (`describe`) e calcula a correlação das variáveis com o consumo:

| Variável | Correlação com o consumo |
|---|---|
| ocupantes | 0,950 |
| temperatura_c | -0,246 |
| geracao_solar_kwh | -0,033 |

Como o número de ocupantes tem a correlação mais forte, ele foi escolhido para a regressão linear simples. Os dados foram divididos em 75% treino e 25% teste.

**consumo = 15,03 + 2,48 x ocupantes**

- Intercepto (15,03 kWh): consumo base do módulo vazio (iluminação mínima, ventilação, equipamentos ligados).
- Coeficiente (2,48 kWh): cada ocupante a mais aumenta o consumo em cerca de 2,5 kWh no ciclo.
- Avaliação no teste: MAE de 2,76 kWh e R² de 0,880, ou seja, o modelo explica cerca de 88% da variação do consumo.

O usuário informa um número de ocupantes e o sistema estima o consumo. Exemplo: 12 ocupantes resultam em 44,80 kWh, acima do limite de 40 kWh, e o sistema recomenda redistribuir a tripulação. O gráfico da reta fica em `graficos_ou_imagens/regressao_consumo.png`.

Limitações: poucos dados, dados simulados e só uma variável. A temperatura tem correlação negativa fraca e poderia entrar numa regressão múltipla com mais dados.

## 7. Integração de IA (sistema multiagente simulado)

A opção 10 simula uma arquitetura de agentes:

- **Agente triador**: lê a pergunta e decide para quem encaminhar (handoff).
- **Agente de energia**: responde sobre consumo e bateria.
- **Agente de manutenção**: responde sobre alertas e módulos em manutenção.
- **Ferramentas**: funções determinísticas que consultam o banco (`ferramenta_consumo`, `ferramenta_bateria`, `ferramenta_manutencao`). O agente não inventa números, ele só repassa o resultado da ferramenta, como num RAG simples sobre os dados do próprio sistema.
- **Guardrail**: bloqueia pedidos como "desligar suporte", "senha", "dados pessoais" e "apagar banco" e encaminha para um responsável humano.
- **Sessão**: as perguntas e respostas ficam guardadas em uma lista durante a execução.

Toda resposta termina lembrando que a decisão final deve ser validada pela equipe humana. O triador usa palavras-chave e não um modelo de linguagem; em uma versão futura ele poderia ser um LLM ou um fluxo low-code com webhooks, mantendo as mesmas ferramentas e o mesmo guardrail.

## 8. Arquitetura computacional, processamento e aceleração

| Parte do SIFSM | Onde rodar | Motivo |
|---|---|---|
| Regra booleana de alerta | Microcontrolador ou CPU local do módulo | Poucas operações lógicas, resposta imediata e quase nenhum consumo; pode até ser feita com portas lógicas |
| CRUD e consultas ao banco | CPU do servidor da colônia | Operações sequenciais, o gargalo é o acesso ao disco e à rede, não o cálculo |
| Simulação da bateria | CPU (vetorizada com NumPy) | Com muitos cenários ou módulos, as mesmas contas se repetem e podem ser paralelizadas em GPU |
| Treino da regressão | CPU hoje; GPU ou TPU se houver milhões de leituras | Multiplicação de matrizes se beneficia de processamento paralelo |
| Agentes com LLM real | NPU, GPU ou TPU | Inferência de redes neurais exige aceleradores e muita memória |

Pontos de arquitetura:

- **Computação heterogênea**: cada tarefa vai para a unidade mais adequada. A regra simples não precisa de GPU, e o modelo de linguagem não deve rodar em microcontrolador.
- **Hierarquia de memória e movimentação de dados**: o sistema lê o banco uma vez e trabalha com o DataFrame em memória. Mover dados do disco ou da rede para o processador gasta mais tempo e energia que o cálculo em si; por isso a regra roda perto do sensor e só os alertas sobem para o servidor.
- **Paralelismo**: o NumPy aplica a mesma operação em vetores inteiros (SIMD na CPU); na GPU, milhares de núcleos fariam o mesmo com muitos cenários.
- **Chiplets e grandes sistemas de IA**: aparecem como opção futura para um centro de dados da colônia, mas consomem muita energia.
- **Sustentabilidade**: processamento também gasta energia. A recomendação do sistema é rodar tarefas pesadas (treino de modelo, simulações grandes) nos horários de sobra solar, que a própria simulação mostra (entre 10 h e 17 h).

## 9. Sustentabilidade, cidadania digital e impacto socioambiental

- **Uso responsável dos recursos**: o SIFSM junta energia (bateria e geração), dados (banco), automação (regra e alerta) e simulação. Assim a equipe vê o consumo de cada módulo e age antes que a bateria chegue ao limite.
- **Simulação antes da implantação**: a simulação mostrou que, sem economia, a bateria fecha o dia com 20% e passa 10 h abaixo do limite. A medida de 20% de economia foi testada no computador antes de ser aplicada na colônia, sem desperdiçar energia real.
- **Redes inteligentes e resiliência**: o grafo mostra que a Usina Solar é um ponto único de falha (derruba os 7 módulos). Isso justifica investir em armazenamento local nos módulos críticos e em rotas alternativas.
- **Cidadania digital e privacidade**: a base guarda apenas o número de ocupantes, não quem são. O guardrail bloqueia pedidos de dados pessoais e senhas. A tripulação deve saber quais dados são coletados e para quê.
- **Economia dos dados**: dados de presença e consumo podem revelar a rotina das pessoas. Se fossem usados para vigiar ou punir a tripulação, o sistema perderia a confiança. O uso deve ficar limitado à gestão de energia.
- **Impacto ambiental da IA**: um agente com LLM rodando o tempo todo gastaria a energia que a colônia precisa para viver. Por isso o protótipo usa funções determinísticas e deixa a IA pesada só para quando trouxer benefício real.
- **Responsabilidade humana e inclusão**: o sistema sugere, mas não decide sozinho. Ações sobre módulos críticos, como o Suporte Médico, precisam de validação humana, e a redistribuição de tripulação deve considerar as necessidades de cada pessoa, não só o número do modelo.

## 10. Limitações e melhorias

Limitações:

- Dados simulados e poucos registros (40 leituras).
- Regressão com uma única variável.
- Simulação com curvas fixas, sem eventos climáticos de Marte.
- Agentes baseados em palavras-chave.
- SQL montado com f-string, como nos exemplos da aula; em produção seria melhor usar parâmetros para evitar SQL injection.

Melhorias:

- Ler sensores reais via Arduino e gravar direto no banco.
- Regressão múltipla com temperatura e horário.
- Simular tempestades de poeira e degradação da bateria.
- Trocar o triador por um modelo de linguagem com as mesmas ferramentas e guardrails.
- Painel visual para a tripulação acompanhar os alertas.
