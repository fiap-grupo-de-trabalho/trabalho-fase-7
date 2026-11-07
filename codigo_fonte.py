import oracledb
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import trapezoid
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

COLUNAS = ["id", "ciclo", "modulo", "tipo", "codigo_sensor", "ocupantes", "temperatura_c",
           "consumo_kwh", "geracao_solar_kwh", "carga_bateria_pct", "critico", "status"]

LIMITE_CONSUMO = 40
LIMITE_BATERIA = 30
LIMITE_GERACAO = 30

REDE = {
    "Usina Solar": ["Armazenamento", "Comunicacao", "Suporte Medico"],
    "Armazenamento": ["Habitacao Alfa", "Habitacao Beta"],
    "Comunicacao": ["Laboratorio Central"],
    "Suporte Medico": ["Habitacao Alfa"],
    "Habitacao Alfa": ["Agricultura Norte"],
    "Habitacao Beta": [],
    "Laboratorio Central": ["Agricultura Norte"],
    "Agricultura Norte": [],
}

historico = []
fila_manutencao = []
sessao_agentes = []
margem = " " * 4


def conectar():
    print("===== CONEXÃO COM O BANCO ORACLE =====")
    usuario = input(margem + "Usuário: ")
    senha = input(margem + "Senha: ")
    try:
        conn = oracledb.connect(user=usuario, password=senha, dsn="oracle.fiap.com.br:1521/ORCL")
    except Exception as e:
        print("Erro ao conectar:", e)
        return None
    else:
        print("Conexão realizada com sucesso!")
        return conn


def ler_dados(conn):
    cursor = conn.cursor()
    cursor.execute(f"SELECT {', '.join(COLUNAS)} FROM sifsm_leituras ORDER BY id")
    dados = cursor.fetchall()
    return pd.DataFrame.from_records(dados, columns=COLUNAS)


def inserir(conn, r):
    cursor = conn.cursor()
    cursor.execute(f"""INSERT INTO sifsm_leituras (ciclo, modulo, tipo, codigo_sensor, ocupantes, temperatura_c,
        consumo_kwh, geracao_solar_kwh, carga_bateria_pct, critico, status) VALUES ({r['ciclo']}, '{r['modulo']}',
        '{r['tipo']}', '{r['codigo_sensor']}', {r['ocupantes']}, {r['temperatura_c']}, {r['consumo_kwh']},
        {r['geracao_solar_kwh']}, {r['carga_bateria_pct']}, {r['critico']}, '{r['status']}')""")


def carregar_csv(conn: oracledb.Connection):
    confirma = input(margem + "Isso apaga a tabela e carrega o CSV. Confirma? [S/N] ")
    if confirma.upper() != "S":
        print("Operação cancelada.")
        return
    try:
        df = pd.read_csv("dados_aurora_siger.csv")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sifsm_leituras")
        for _, linha in df.iterrows():
            inserir(conn, linha)
        conn.commit()
    except FileNotFoundError:
        print("Arquivo dados_aurora_siger.csv não encontrado.")
    except Exception as e:
        print("Erro ao carregar os dados:", e)
    else:
        historico.append(f"Carga do CSV com {len(df)} registros")
        print(f"{len(df)} registros gravados no banco.")


def cadastrar(conn):
    print("----- CADASTRAR LEITURA -----")
    try:
        r = {
            "ciclo": int(input(margem + "Ciclo: ")),
            "modulo": input(margem + "Módulo: "),
            "tipo": input(margem + "Tipo: "),
            "codigo_sensor": input(margem + "Código do sensor: ").upper(),
            "ocupantes": int(input(margem + "Ocupantes: ")),
            "temperatura_c": float(input(margem + "Temperatura (°C): ")),
            "consumo_kwh": float(input(margem + "Consumo (kWh): ")),
            "geracao_solar_kwh": float(input(margem + "Geração solar (kWh): ")),
            "carga_bateria_pct": float(input(margem + "Carga da bateria (%): ")),
            "critico": int(input(margem + "Módulo crítico? (1 sim / 0 não): ")),
            "status": input(margem + "Status (ativo, alerta, manutencao): "),
        }
        if r["carga_bateria_pct"] < 0 or r["carga_bateria_pct"] > 100:
            raise ValueError("a carga da bateria deve estar entre 0 e 100")
        if r["critico"] not in (0, 1):
            raise ValueError("crítico deve ser 0 ou 1")
        inserir(conn, r)
        conn.commit()
    except ValueError as erro:
        print("Valor inválido:", erro)
    except Exception as e:
        print("Erro na transação do banco:", e)
    else:
        historico.append(f"Cadastro da leitura do sensor {r['codigo_sensor']}")
        print("Leitura cadastrada!")


def listar(conn):
    print("----- LISTAR LEITURAS -----")
    df = ler_dados(conn)
    if df.empty:
        print("Não há leituras cadastradas.")
    else:
        print(df.to_string(index=False))


def buscar_id(conn):
    try:
        leitura_id = int(input(margem + "Id da leitura: "))
    except ValueError:
        print("Digite um número inteiro.")
        return None
    df = ler_dados(conn)
    if leitura_id not in df["id"].values:
        print(f"Não existe leitura com id = {leitura_id}")
        return None
    return leitura_id


def alterar(conn):
    print("----- ALTERAR LEITURA -----")
    leitura_id = buscar_id(conn)
    if leitura_id is None:
        return
    try:
        consumo = float(input(margem + "Novo consumo (kWh): "))
        bateria = float(input(margem + "Nova carga da bateria (%): "))
        status = input(margem + "Novo status: ")
        cursor = conn.cursor()
        cursor.execute(f"""UPDATE sifsm_leituras SET consumo_kwh = {consumo}, carga_bateria_pct = {bateria},
            status = '{status}' WHERE id = {leitura_id}""")
        conn.commit()
    except ValueError:
        print("Digite números no consumo e na bateria.")
    except Exception as e:
        print("Erro na transação do banco:", e)
    else:
        historico.append(f"Alteração da leitura {leitura_id}")
        print("Leitura alterada!")
    finally:
        print("Fim da operação de alteração.")


def excluir(conn):
    print("----- EXCLUIR LEITURA -----")
    leitura_id = buscar_id(conn)
    if leitura_id is None:
        return
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM sifsm_leituras WHERE id = {leitura_id}")
    conn.commit()
    historico.append(f"Exclusão da leitura {leitura_id}")
    print("Leitura excluída!")


def regra_alerta(consumo, critico, bateria, geracao):
    a = consumo > LIMITE_CONSUMO
    b = critico == 1
    c = bateria < LIMITE_BATERIA
    d = geracao >= LIMITE_GERACAO
    return (a and b) or (c and not d)


def mostrar_tabela_verdade():
    print("ALERTA = (A AND B) OR (C AND NOT D)")
    print(f"A = consumo > {LIMITE_CONSUMO} kWh | B = módulo crítico")
    print(f"C = bateria < {LIMITE_BATERIA}% | D = geração solar >= {LIMITE_GERACAO} kWh")
    print(" A B C D | ALERTA")
    for a in (0, 1):
        for b in (0, 1):
            for c in (0, 1):
                for d in (0, 1):
                    s = (a and b) or (c and not d)
                    print(f" {a} {b} {c} {d} |   {int(s)}")
    print("Circuito: porta AND(A,B) e porta AND(C, NOT D) ligadas em uma porta OR que acende o LED de alerta.")


def aplicar_regra(conn):
    print("----- REGRA BOOLEANA DE ALERTA -----")
    mostrar_tabela_verdade()
    df = ler_dados(conn)
    fila_manutencao.clear()
    for _, r in df.iterrows():
        if regra_alerta(r["consumo_kwh"], r["critico"], r["carga_bateria_pct"], r["geracao_solar_kwh"]):
            fila_manutencao.append(f"Ciclo {r['ciclo']} - {r['modulo']} ({r['codigo_sensor']}): "
                                   f"consumo {r['consumo_kwh']} kWh, bateria {r['carga_bateria_pct']}%")
    print(f"\n{len(fila_manutencao)} leituras acionaram o alerta e entraram na fila de manutenção:")
    for chamado in fila_manutencao:
        print(" -", chamado)


def estruturas(conn):
    print("----- ESTRUTURAS DE DADOS -----")
    print("1 - Atender próximo chamado (fila)")
    print("2 - Ver histórico de ações (pilha)")
    print("3 - Buscar leituras por código do sensor (tabela hash)")
    print("4 - Módulos afetados por falha na rede (grafo)")
    opcao = input(margem + "Escolha -> ")
    match opcao:
        case "1":
            if len(fila_manutencao) == 0:
                print("Fila vazia. Execute a regra de alerta antes.")
            else:
                print("Atendendo:", fila_manutencao.pop(0))
                print(f"Restam {len(fila_manutencao)} chamados.")
        case "2":
            if len(historico) == 0:
                print("Nenhuma ação registrada.")
            for acao in reversed(historico):
                print(" -", acao)
        case "3":
            df = ler_dados(conn)
            tabela = {}
            for _, r in df.iterrows():
                tabela.setdefault(r["codigo_sensor"], []).append(r)
            codigo = input(margem + f"Código ({', '.join(tabela.keys())}): ").upper()
            if codigo in tabela:
                for r in tabela[codigo]:
                    print(f" ciclo {r['ciclo']} | {r['modulo']} | consumo {r['consumo_kwh']} kWh | "
                          f"bateria {r['carga_bateria_pct']}% | {r['status']}")
            else:
                print("Código não encontrado.")
        case "4":
            modulo = input(margem + f"Módulo com falha ({', '.join(REDE.keys())}): ")
            if modulo not in REDE:
                print("Módulo não existe na rede.")
                return
            visitados = []
            fila = [modulo]
            while len(fila) > 0:
                atual = fila.pop(0)
                for vizinho in REDE[atual]:
                    if vizinho not in visitados:
                        visitados.append(vizinho)
                        fila.append(vizinho)
            if len(visitados) == 0:
                print("Nenhum módulo depende deste.")
            else:
                print("Módulos afetados:", ", ".join(visitados))
        case _:
            print("Opção inválida.")


def simular_bateria(fator_consumo):
    capacidade = 500
    dt = 0.5
    t = np.arange(0, 24 + dt, dt)
    geracao = np.maximum(0, 75 * np.sin(np.pi * (t - 6) / 12))
    consumo = fator_consumo * (25 + 10 * np.sin(np.pi * (t - 14) / 12) ** 2)
    soc = np.zeros(len(t))
    soc[0] = 50
    for i in range(1, len(t)):
        variacao = (geracao[i - 1] - consumo[i - 1]) / capacidade * 100
        soc[i] = min(100, max(0, soc[i - 1] + variacao * dt))
    return t, geracao, consumo, soc


def simulacao():
    print("----- SIMULAÇÃO DO ESTADO DE CARGA DA BATERIA (24 h) -----")
    resultados = {}
    for nome, fator in (("Normal", 1.0), ("Economia 20%", 0.8)):
        t, geracao, consumo, soc = simular_bateria(fator)
        energia_gerada = trapezoid(geracao, t)
        energia_consumida = trapezoid(consumo, t)
        resultados[nome] = (t, soc)
        print(f"\nCenário {nome}:")
        print(f" Energia gerada (integral): {energia_gerada:.1f} kWh")
        print(f" Energia consumida (integral): {energia_consumida:.1f} kWh")
        print(f" Potência média consumida: {energia_consumida / 24:.2f} kW")
        print(f" Carga mínima: {soc.min():.1f}% | carga final: {soc[-1]:.1f}%")
        print(f" Horas com bateria abaixo de {LIMITE_BATERIA}%: {np.sum(soc < LIMITE_BATERIA) * 0.5:.1f} h")
    plt.figure(figsize=(9, 5))
    for nome in resultados:
        plt.plot(resultados[nome][0], resultados[nome][1], label=nome)
    plt.axhline(LIMITE_BATERIA, color="red", linestyle="--", label="Limite de alerta")
    plt.xlabel("Hora do dia")
    plt.ylabel("Carga da bateria (%)")
    plt.title("Estado de carga da bateria - Aurora Siger")
    plt.legend()
    plt.grid(True)
    plt.savefig("graficos_ou_imagens/simulacao_bateria.png")
    plt.close()
    print("\nGráfico salvo em graficos_ou_imagens/simulacao_bateria.png")


def regressao(conn):
    print("----- REGRESSÃO LINEAR: CONSUMO x OCUPANTES -----")
    df = ler_dados(conn)
    if len(df) < 5:
        print("Poucos registros para treinar o modelo.")
        return None
    print(df[["ocupantes", "temperatura_c", "consumo_kwh"]].describe().round(2))
    print("\nCorrelação com o consumo:")
    print(df[["ocupantes", "temperatura_c", "geracao_solar_kwh", "consumo_kwh"]].corr()["consumo_kwh"].round(3))
    x = df[["ocupantes"]]
    y = df["consumo_kwh"]
    x_treino, x_teste, y_treino, y_teste = train_test_split(x, y, test_size=0.25, random_state=42)
    modelo = LinearRegression()
    modelo.fit(x_treino, y_treino)
    previsto = modelo.predict(x_teste)
    print(f"\nconsumo = {modelo.intercept_:.2f} + {modelo.coef_[0]:.2f} x ocupantes")
    print(f"Cada ocupante a mais aumenta o consumo em {modelo.coef_[0]:.2f} kWh.")
    print(f"MAE: {mean_absolute_error(y_teste, previsto):.2f} kWh | R²: {r2_score(y_teste, previsto):.3f}")
    plt.figure(figsize=(8, 5))
    plt.scatter(x, y, label="Leituras")
    linha = np.arange(x["ocupantes"].min(), x["ocupantes"].max() + 1)
    plt.plot(linha, modelo.intercept_ + modelo.coef_[0] * linha, color="red", label="Reta ajustada")
    plt.xlabel("Ocupantes")
    plt.ylabel("Consumo (kWh)")
    plt.title("Regressão linear simples")
    plt.legend()
    plt.grid(True)
    plt.savefig("graficos_ou_imagens/regressao_consumo.png")
    plt.close()
    print("Gráfico salvo em graficos_ou_imagens/regressao_consumo.png")
    try:
        ocupantes = int(input(margem + "Quantos ocupantes deseja simular? "))
    except ValueError:
        print("Valor inválido, previsão não realizada.")
    else:
        estimado = modelo.intercept_ + modelo.coef_[0] * ocupantes
        print(f"Consumo estimado: {estimado:.2f} kWh")
        if estimado > LIMITE_CONSUMO:
            print("Acima do limite: recomenda-se redistribuir a tripulação.")
    return modelo


def ferramenta_consumo(df):
    media = df.groupby("modulo")["consumo_kwh"].mean().sort_values(ascending=False)
    return f"Maior consumo médio: {media.index[0]} com {media.iloc[0]:.2f} kWh."


def ferramenta_bateria(df):
    baixas = df[df["carga_bateria_pct"] < LIMITE_BATERIA]
    return f"{len(baixas)} leituras com bateria abaixo de {LIMITE_BATERIA}%."


def ferramenta_manutencao(df):
    pendentes = df[df["status"] != "ativo"]
    return f"{len(pendentes)} leituras em alerta ou manutenção: " + ", ".join(pendentes["modulo"].unique())


def agente_energia(df, pergunta):
    if "bateria" in pergunta:
        return "Agente de Energia: " + ferramenta_bateria(df)
    return "Agente de Energia: " + ferramenta_consumo(df)


def agente_manutencao(df, pergunta):
    return "Agente de Manutenção: " + ferramenta_manutencao(df)


def agente_triador(df, pergunta):
    pergunta = pergunta.lower()
    proibidas = ["desligar suporte", "senha", "dados pessoais", "apagar banco"]
    for palavra in proibidas:
        if palavra in pergunta:
            return "Guardrail: pedido fora do escopo ou inseguro. Encaminhado para um responsável humano."
    if "energia" in pergunta or "consumo" in pergunta or "bateria" in pergunta:
        return agente_energia(df, pergunta)
    if "manutencao" in pergunta or "manutenção" in pergunta or "alerta" in pergunta:
        return agente_manutencao(df, pergunta)
    return "Triador: não entendi. Pergunte sobre energia, consumo, bateria, alerta ou manutenção."


def agentes(conn):
    print("----- ASSISTENTE MULTIAGENTE (SIMULADO) -----")
    print("Digite uma pergunta ou 'sair' para voltar.")
    df = ler_dados(conn)
    while True:
        pergunta = input(margem + "Pergunta: ")
        if pergunta.lower() == "sair":
            break
        resposta = agente_triador(df, pergunta)
        sessao_agentes.append((pergunta, resposta))
        print(resposta)
        print("(Sugestão da IA: a decisão final deve ser validada pela equipe humana.)")


def analise_final(conn, modelo):
    print("----- ANÁLISE FINAL DA COLÔNIA -----")
    df = ler_dados(conn)
    if df.empty:
        print("Sem dados para analisar.")
        return
    alertas = 0
    for _, r in df.iterrows():
        if regra_alerta(r["consumo_kwh"], r["critico"], r["carga_bateria_pct"], r["geracao_solar_kwh"]):
            alertas += 1
    print(f"Leituras: {len(df)} | consumo total: {df['consumo_kwh'].sum():.1f} kWh | "
          f"geração solar total: {df['geracao_solar_kwh'].sum():.1f} kWh")
    print(f"Leituras em alerta pela regra booleana: {alertas} ({alertas / len(df) * 100:.1f}%)")
    print(ferramenta_consumo(df))
    print(ferramenta_bateria(df))
    if modelo is not None:
        print(f"Modelo linear: cada ocupante adiciona {modelo.coef_[0]:.2f} kWh ao consumo.")
    t, geracao, consumo, soc = simular_bateria(1.0)
    t, geracao, consumo, soc_eco = simular_bateria(0.8)
    print(f"Simulação: carga mínima {soc.min():.1f}% no cenário normal e {soc_eco.min():.1f}% com economia de 20%.")
    print("\nRecomendações:")
    print(" - Priorizar a fila de manutenção dos módulos críticos com consumo alto.")
    print(" - Adotar o modo economia à noite para manter a bateria acima do limite.")
    print(" - Processar a regra booleana localmente (CPU embarcada) e deixar o treino do modelo para horários com sobra solar.")
    print("\nLimitações:")
    print(" - Dados simulados e poucos registros, o modelo usa só uma variável.")
    print(" - A simulação usa curvas fixas de geração e consumo, sem tempestades de poeira.")
    print(" - Os agentes usam palavras-chave e não um modelo de linguagem real.")


def menu():
    conn = conectar()
    if conn is None:
        return
    modelo = None
    while True:
        print("\n========== SIFSM - AURORA SIGER ==========")
        print("1 - Carregar dados do CSV para o banco")
        print("2 - Cadastrar leitura")
        print("3 - Listar leituras")
        print("4 - Alterar leitura")
        print("5 - Excluir leitura")
        print("6 - Aplicar regra booleana de alerta")
        print("7 - Estruturas de dados (fila, pilha, hash, grafo)")
        print("8 - Simulação da bateria")
        print("9 - Regressão linear do consumo")
        print("10 - Assistente multiagente")
        print("11 - Análise final")
        print("0 - Sair")
        opcao = input("Escolha uma opção: ").strip()
        try:
            match opcao:
                case "1":
                    carregar_csv(conn)
                case "2":
                    cadastrar(conn)
                case "3":
                    listar(conn)
                case "4":
                    alterar(conn)
                case "5":
                    excluir(conn)
                case "6":
                    aplicar_regra(conn)
                case "7":
                    estruturas(conn)
                case "8":
                    simulacao()
                case "9":
                    modelo = regressao(conn)
                case "10":
                    agentes(conn)
                case "11":
                    analise_final(conn, modelo)
                case "0":
                    print("Encerrando o SIFSM. Até mais!")
                    break
                case _:
                    print("Opção inválida.")
        except Exception as e:
            print("Erro inesperado:", e)
    conn.close()


if __name__ == "__main__":
    menu()
