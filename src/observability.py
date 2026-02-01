import time
from dotenv import load_dotenv
from langfuse import get_client

load_dotenv()
langfuse = get_client()

# -----------------------------
# Utilidades
# -----------------------------
def estimar_tokens(texto: str) -> int:
    if not texto:
        return 0
    return int(len(texto.split()) * 1.3)

def estimar_custo(tokens: int, preco_1k_tokens=0.002):
    # custo fictício (modelo GPT-like)
    return round((tokens / 1000) * preco_1k_tokens, 6)


# -----------------------------
# Trace principal
# -----------------------------
def iniciar_trace(pergunta: str, cliente: str, perfil: str):
    return langfuse.start_as_current_span(
        name="consulta_atena",
        input=pergunta,
        metadata={
            "cliente": cliente,
            "perfil_investidor": perfil,
            "app": "Atena",
            "canal": "chat"
        }
    )


# -----------------------------
# Sucesso
# -----------------------------
def registrar_sucesso(span, prompt: str, resposta: str, inicio: float):
    latency_ms = int((time.time() - inicio) * 1000)

    input_tokens = estimar_tokens(prompt)
    output_tokens = estimar_tokens(resposta)
    total_tokens = input_tokens + output_tokens
    custo_estimado = estimar_custo(total_tokens)

    span.update(
        output=resposta,
        status="SUCCESS",
        metadata={
            # Performance
            "latency_ms": latency_ms,

            # Tokens
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,

            # Custos (simulado)
            "estimated_cost_usd": custo_estimado,

            # Observabilidade
            "modelo": "ollama-local",
            "token_strategy": "estimativa_palavras"
        }
    )


# -----------------------------
# Erro
# -----------------------------
def registrar_erro(span, erro: Exception, inicio: float):
    latency_ms = int((time.time() - inicio) * 1000)

    span.update(
        status="ERROR",
        status_message=str(erro),
        metadata={
            "latency_ms": latency_ms,
            "error_type": type(erro).__name__,
            "error_message": str(erro)
        }
    )
