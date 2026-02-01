import json
import time
import pandas as pd
import requests
import streamlit as st

# IMPORTA A OBSERVABILIDADE
from observability import (
    iniciar_trace,
    registrar_sucesso,
    registrar_erro
)

# ================= CONFIGURAÇÃO =================

OLLAMA_URL = "http://localhost:11434/api/generate"
MODELO = "gpt-oss:20b-cloud"

# ================= CARREGAMENTO DOS DADOS =================

with open("./data/perfil_investidor.json", "r", encoding="utf-8") as f:
    perfil_raw = json.load(f)

perfil = perfil_raw["perfil_investidor"]

transacoes = pd.read_csv("./data/transacoes.csv")
historico = pd.read_csv("./data/historico_atendimento.csv")

with open("./data/produtos_financeiros.json", "r", encoding="utf-8") as f:
    produtos = json.load(f)

# ================= EXTRAÇÃO DO PERFIL =================

dados_pessoais = perfil["dados_pessoais"]
financeiro = perfil["financeiro"]
perfil_risco = perfil["perfil"]
indicadores = perfil["indicadores"]
metas = perfil["metas"]

# ================= CONTEXTO  =================

contexto = f"""
DADOS DO CLIENTE:
- Nome: {dados_pessoais["nome"]}
- Idade: {dados_pessoais["idade"]}
- Profissão: {dados_pessoais["profissao"]}
- Perfil de investidor: {perfil_risco["perfil_investidor"]}
- Aceita risco: {"Sim" if perfil_risco["aceita_risco"] else "Não"}

SITUAÇÃO FINANCEIRA:
- Renda mensal: R$ {financeiro["renda_mensal"]}
- Patrimônio total: R$ {financeiro["patrimonio_total"]}
- Reserva de emergência atual: R$ {financeiro["reserva_emergencia_atual"]}
- Objetivo principal: {financeiro["objetivo_principal"]}

INDICADORES:
- Reserva concluída: {indicadores["reserva_percentual_concluida"]}%
- Meses estimados para concluir a meta principal: {indicadores["meses_estimados_para_meta_principal"]}

METAS FINANCEIRAS:
{pd.DataFrame(metas)[["meta", "prazo", "prioridade"]].to_string(index=False)}

HISTÓRICO DE DECISÕES (RESUMO):
{historico[["tema", "decisao_usuario", "status"]].to_string(index=False)}

TRANSAÇÕES DO CLIENTE:
{transacoes.to_string(index=False)}

PRODUTOS DISPONÍVEIS PARA CENÁRIOS:
{json.dumps(produtos, ensure_ascii=False)}
"""

# ================= SYSTEM PROMPT =================

SYSTEM_PROMPT = """
Você é a Atena, uma agente financeira assistente com perfil consultivo,
educativo e analítico, atuando como uma amiga conselheira.

Seu papel é ajudar o usuário a tomar decisões financeiras conscientes,
mostrando claramente os impactos de seguir ou não uma recomendação, 
sempre com base nos dados fornecidos. 

REGRAS GERAIS: 
1. Use exclusivamente as informações do contexto. 
2. Nunca invente valores, projeções ou dados financeiros. 
3. Sempre apresente dois cenários de forma implícita: 
- O que tende a acontecer se o usuário seguir a orientação 
- O que pode acontecer se o usuário não seguir 
4. Não decida pelo usuário. 
5. Não recomende produtos incompatíveis com o perfil. 
6. Explique termos técnicos de forma simples. 
7. Se faltar informação, admita e explique o impacto de forma geral. 
8. Não solicite nem compartilhe dados sensíveis. 
9. Respeite decisões anteriores do histórico. 
10. Se a pergunta estiver fora do escopo financeiro, explique com educação.

SAUDAÇÕES (REGRA CRÍTICA — SIGA À RISCA): 
- Use saudação COM o nome do cliente SOMENTE quando: 
• a mensagem do usuário for EXATAMENTE uma saudação isolada 
- Exemplos que DEVEM gerar saudação: 
"Oi" 
"Olá"
"Bom dia" 
"Boa tarde" 
"Boa noite" 

- Nessas situações, a resposta DEVE:
 • iniciar com "Oi {primeiro_nome_do_cliente}," 
 • conter MAIS de uma frase 
 • incluir acolhimento e convite claro para ajuda financeira 
 
 Exemplo correto: 
 "Oi Maria, que bom te ver por aqui. Como posso te ajudar hoje com suas finanças?" 
 
 - NÃO DEVE gerar saudação:
 • perguntas ou mensagens que não incluam qualquer tipo de saudação junto com outros conteúdos.

 - Nesses casos: 
 • NÃO inicie com "Oi" 
 • responda diretamente ao conteúdo financeiro 

 FORMATO DA RESPOSTA: 
 - Escreva sempre em texto corrido e natural. 
 - NÃO use títulos visíveis como “Contextualização”, “Análise” ou “Encerramento”. 
 - A estrutura deve ser implícita: 
 • Situe o pedido do usuário 
 • Apresente a análise com base nos dados 
 • Finalize com acolhimento ou convite à continuidade 
 - Evite listas quando a resposta for simples.
"""


# ================= FUNÇÃO DE CONSULTA =================

def perguntar(pergunta: str) -> tuple[str, str]:
    prompt = f"""
{SYSTEM_PROMPT}

CONTEXTO DO CLIENTE:
{contexto}

Pergunta do usuário:
{pergunta}
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODELO,
            "prompt": prompt,
            "stream": False
        },
        timeout=120
    )

    response.raise_for_status()
    return response.json()["response"], prompt

# ================= INTERFACE STREAMLIT =================

st.set_page_config(page_title="Atena - Assistente Financeira", layout="centered")

st.title("💡 Atena — sua conselheira financeira")

st.markdown(
    "Posso te ajudar a entender **o que pode mudar se você seguir ou não uma decisão financeira**, "
    "sempre considerando seus objetivos e seu momento atual."
)

if pergunta := st.chat_input("O que você gostaria de analisar hoje?"):
    st.chat_message("user").write(pergunta)

    with iniciar_trace(
        pergunta=pergunta,
        cliente=dados_pessoais["nome"],
        perfil=perfil_risco["perfil_investidor"]
    ) as span:

        with st.spinner("Atena está analisando os cenários..."):
            try:
                inicio = time.time()
                resposta, prompt = perguntar(pergunta)

                registrar_sucesso(
                    span=span,
                    prompt=prompt,
                    resposta=resposta,
                    inicio=inicio
                )

                st.chat_message("assistant").write(resposta)

            except Exception as e:
                registrar_erro(
                    span=span,
                    erro=e,
                    inicio=inicio
                )

                st.chat_message("assistant").write(
                    "Desculpa, não consigo te ajudar com isso. "
                    "Mas posso te apoiar com decisões financeiras, "
                    "metas ou na organização do seu dinheiro. "
                    "Como posso te ajudar agora?"
                )
