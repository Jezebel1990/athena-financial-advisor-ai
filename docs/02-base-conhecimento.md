# Base de Conhecimento

## Visão Geral

O agente Atena utiliza uma base de conhecimento estruturada e organizada em múltiplos arquivos, permitindo personalização contextual, continuidade no atendimento e tomada de decisão baseada em dados reais do cliente.


## Dados Utilizados

Os dados são organizados em arquivos específicos, cada um com uma função estratégica no funcionamento do agente:

| Arquivo | Formato | Descrição | Utilização no Agente |
|---------|---------|-----------|---------------------|
| `historico_atendimento.csv` | CSV | Registro de interações passadas | Fornece contexto sobre temas já discutidos, evitando repetições e permitindo continuidade no atendimento |
| `perfil_investidor.json` | JSON | Perfil financeiro completo | Define perfil de risco, objetivos, metas e tolerância do cliente |
| `produtos_financeiros.json` | JSON | Catálogo de produtos disponíveis | Base para recomendação de produtos compatíveis com perfil e objetivos |
| `transacoes.csv` | CSV | Histórico de transações financeiras | Apoia análises comportamentais e identificação de padrões de gastos |

---

## Adaptações nos Dados

Os dados mockados foram adaptados e enriquecidos para atender à lógica do agente:

- O arquivo `perfil_investidor.json` foi estruturado em blocos lógicos (dados pessoais, financeiros, perfil de risco, metas e indicadores derivados).

- Foram adicionados indicadores calculados, como percentual da reserva de emergência concluída e estimativa de prazo para atingir metas.

- O `historico_atendimento.csv` passou a ser utilizado como memória de curto e médio prazo, permitindo que a Atena:
    - reconheça temas já abordados;
    - ajuste o nível de detalhamento das respostas;
    - respeite decisões anteriores do cliente.
- As metas financeiras foram classificadas por prioridade e horizonte de tempo, auxiliando o motor de regras na definição de recomendações seguras.

---

## Estratégia de Integração

### Como os dados são carregados?

Existem duas possibilidades, injetar os dados diretamente (Ctrl + C, Ctrl + V) ou carregar os arquivos via código, como no exemplo abaixo:


```python
import pandas as pd
import json

#CSVs
historico = pd.read_csv('data/historico_atendimento.csv')
transacoes = pd.read_csv('data/transacoes.csv')

#JSONs
with open('data/perfil_investidor.json', 'r', encoding='utf-8') as f:
    perfil = json.load(f)

with open('data/produtos_financeiros.json', 'r', encoding='utf-8') as f:
    produtos = json.load(f)
```



### Como os dados são usados no prompt?
Os dados são **combinados dinamicamente** para compor o contexto de decisão do agente:

📌 **Dados sensíveis** (perfil, metas) → Inseridos no **system prompt**  
📌 **Dados contextuais** (histórico, transações) → Consultados **conforme necessidade**

#### Template de Prompt Utilizado

```python
DADOS DO CLIENTE:
- Nome: {dados_pessoais["nome"]}
- Idade: {dados_pessoais["idade"]}
- Profissão: {dados_pessoais["profissao"]}
- Perfil de investidor: {perfil_risco["perfil_investidor"]}
- Aceita risco: {"Sim" if perfil_risco["aceita_risco"] else "Não"}

SITUAÇÃO FINANCEIRA:
- Renda mensal: R$ {financeiro["renda_mensal"]:,.2f}
- Patrimônio total: R$ {financeiro["patrimonio_total"]:,.2f}
- Reserva de emergência atual: R$ {financeiro["reserva_emergencia_atual"]:,.2f}
- Objetivo principal: {financeiro["objetivo_principal"]}

INDICADORES DERIVADOS:
- Reserva concluída: {indicadores["reserva_percentual_concluida"]:.1f}%
- Meses estimados para meta principal: {indicadores["meses_estimados_para_meta_principal"]}
- Capacidade de poupança mensal: R$ {indicadores["capacidade_poupanca_mensal"]:,.2f}

METAS FINANCEIRAS:
{pd.DataFrame(metas)[["meta", "valor_necessario", "prazo", "prioridade"]].to_string(index=False)}

HISTÓRICO DE DECISÕES (ÚLTIMAS 5 INTERAÇÕES):
{historico.tail(5)[["tema", "decisao_usuario", "status"]].to_string(index=False)}

PADRÃO DE GASTOS (ÚLTIMOS 30 DIAS):
{transacoes.groupby('categoria')['valor'].sum().to_string()}

PRODUTOS FINANCEIROS DISPONÍVEIS:
{json.dumps(produtos, ensure_ascii=False, indent=2)}
```


---

## Exemplo de Contexto Montado

Exemplo de como os dados são organizados e enviados ao agente.

```
DADOS DO CLIENTE:
- Nome: João Silva
- Idade: 32
- Profissão: Analista de Sistemas
- Perfil de investidor: Moderado
- Aceita risco: Não
- Objetivo principal: Construir reserva de emergência
- Renda mensal: R$ 5.000
- Patrimônio total: R$ 15.000
- Reserva de emergência atual: R$ 10.000 (66,7% concluída)
- Prazo estimado para conclusão da meta principal: 8 meses

METAS FINANCEIRAS:
- Completar reserva de emergência:
  Valor necessário: R$ 15.000
  Prazo: Junho/2026
  Prioridade: Alta
- Entrada do apartamento:
  Valor necessário: R$ 50.000
  Prazo: Dezembro/2027
  Prioridade: Média

HISTÓRICO DE ATENDIMENTO (RESUMO):
- Tema: Tesouro Selic
  Contexto: Uso como reserva de emergência
  Cenários apresentados: Seguir (investir) | Não seguir (manter fora de investimentos)
  Decisão do usuário: Apenas esclarecimento
- Tema: Metas financeiras
  Contexto: Acompanhamento da reserva de emergência
  Cenários apresentados: Separar valor mensal | Adiar aporte
  Status: Em acompanhamento

TRANSAÇÕES RECENTES (PADRÕES RELEVANTES):
- Alimentação: gastos recorrentes mensais
- Moradia: despesas fixas (aluguel e energia)
- Transporte: custos variáveis
- Lazer e saúde: gastos controlados

PRODUTOS FINANCEIROS COMPATÍVEIS:
- Tesouro Selic (baixo risco, liquidez diária)
- CDB com liquidez diária (baixo risco)
```

Esse formato permite que a Atena:
- Contextualize a conversa com base no histórico real do cliente
- Apresente sempre cenários de “seguir” e “não seguir”
- Conecte decisões atuais com impactos futuros nas metas financeiras
- Mantenha um tom próximo, claro e responsável