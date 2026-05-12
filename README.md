# Focus Log API

API REST para **log de performance** de sessões de trabalho/estudo, com diagnóstico inteligente de produtividade.

---

## Descrição do Projeto

A Focus Log API permite registrar sessões de trabalho com nível de foco e receber um diagnóstico detalhado de produtividade. A API oferece:

- Registro de sessões com validações completas
- Diagnóstico inteligente baseado em média de foco com estratégias de feedback configuráveis
- Filtros por período e categoria
- Segurança seguindo OWASP API Security Top 10

---

## Pré-requisitos

- **Python 3.11+**
- **pip**

---

## Instalação

```bash
# 1. Clone o repositório
git clone <url-do-repositorio>
cd focus_log_api

# 2. Crie e ative o ambiente virtual
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env conforme necessário
```

---

## Como Rodar em Desenvolvimento

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

A API estará disponível em: http://localhost:8000

Documentação interativa (Swagger UI): http://localhost:8000/docs

Documentação alternativa (ReDoc): http://localhost:8000/redoc

---

## Como Rodar os Testes

```bash
pytest tests/ -v
```

Para ver cobertura de código:

```bash
pip install pytest-cov
pytest tests/ -v --cov=app --cov-report=term-missing
```

---

## Como Usar a API

### Interface interativa (recomendado para explorar)

Com o servidor rodando, acesse **http://localhost:8000/docs** — o Swagger UI permite testar todos os endpoints diretamente no browser, sem precisar de nenhuma ferramenta extra.

---

## Endpoints

### `POST /api/v1/registro-foco` — Registrar uma sessão

Registra uma nova sessão de trabalho/estudo com nível de foco.

#### Campos do corpo (JSON)

| Campo | Tipo | Obrigatório | Regras |
|-------|------|:-----------:|--------|
| `nivel_foco` | inteiro | ✅ | 1 (muito baixo) a 5 (excepcional) |
| `tempo_minutos` | inteiro | ✅ | 1 a 480 (máx. 8 horas) |
| `comentario` | string | ✅ | 3 a 500 caracteres |
| `categoria` | string | ❌ | `coding`, `reuniao`, `estudo` ou `outro` |
| `tags` | lista de strings | ❌ | máx. 10 tags, cada uma com máx. 30 caracteres |
| `data` | datetime (ISO 8601) | ❌ | padrão: momento atual em UTC |

#### Exemplo completo

```bash
curl -X POST http://localhost:8000/api/v1/registro-foco \
  -H "Content-Type: application/json" \
  -d '{
    "nivel_foco": 4,
    "tempo_minutos": 90,
    "comentario": "Implementei o módulo de autenticação sem interrupções",
    "categoria": "coding",
    "tags": ["backend", "auth", "fastapi"],
    "data": "2025-06-10T14:30:00"
  }'
```

#### Exemplo mínimo (apenas campos obrigatórios)

```bash
curl -X POST http://localhost:8000/api/v1/registro-foco \
  -H "Content-Type: application/json" \
  -d '{
    "nivel_foco": 3,
    "tempo_minutos": 25,
    "comentario": "Sessão rápida de revisão de código"
  }'
```

#### Resposta de sucesso — `201 Created`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "nivel_foco": 4,
  "tempo_minutos": 90,
  "comentario": "Implementei o módulo de autenticação sem interrupções",
  "categoria": "coding",
  "tags": ["backend", "auth", "fastapi"],
  "data": "2025-06-10T14:30:00Z",
  "created_at": "2025-06-10T17:45:00Z"
}
```

#### Erros de validação — `422 Unprocessable Entity`

Retornado quando algum campo não passa na validação:

```bash
# nivel_foco fora do range (deve ser 1 a 5)
curl -X POST http://localhost:8000/api/v1/registro-foco \
  -H "Content-Type: application/json" \
  -d '{"nivel_foco": 6, "tempo_minutos": 30, "comentario": "Teste"}'
```

```json
{
  "detail": [
    {
      "type": "less_than_equal",
      "loc": ["body", "nivel_foco"],
      "msg": "Input should be less than or equal to 5",
      "input": 6
    }
  ]
}
```

---

### `GET /api/v1/diagnostico-produtividade` — Diagnóstico de produtividade

Analisa todos os registros e retorna métricas de produtividade com feedback inteligente.

#### Parâmetros de query (todos opcionais)

| Parâmetro | Formato | Exemplo |
|-----------|---------|---------|
| `data_inicio` | ISO 8601: `YYYY-MM-DDTHH:MM:SS` | `2025-06-01T00:00:00` |
| `data_fim` | ISO 8601: `YYYY-MM-DDTHH:MM:SS` | `2025-06-30T23:59:59` |
| `categoria` | string | `coding`, `reuniao`, `estudo`, `outro` |

#### Exemplos de uso

```bash
# Diagnóstico de todos os registros
curl http://localhost:8000/api/v1/diagnostico-produtividade

# Filtrar por período
curl "http://localhost:8000/api/v1/diagnostico-produtividade?data_inicio=2025-06-01T00:00:00&data_fim=2025-06-30T23:59:59"

# Filtrar por categoria
curl "http://localhost:8000/api/v1/diagnostico-produtividade?categoria=coding"

# Combinar filtros: período + categoria
curl "http://localhost:8000/api/v1/diagnostico-produtividade?data_inicio=2025-06-01T00:00:00&data_fim=2025-06-30T23:59:59&categoria=estudo"
```

#### Resposta de sucesso — `200 OK`

```json
{
  "total_registros": 12,
  "media_foco": 3.75,
  "tempo_total_minutos": 380,
  "tempo_total_formatado": "6h 20min",
  "distribuicao_foco": {
    "1": 1,
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 2
  },
  "categoria_mais_produtiva": "coding",
  "sessao_mais_longa": {
    "tempo_minutos": 90,
    "nivel_foco": 5,
    "categoria": "estudo"
  },
  "feedback": {
    "nivel": "médio",
    "titulo": "No caminho certo 🟢",
    "descricao": "Sua produtividade está em um bom nível! Foque agora em identificar o que já está funcionando.",
    "sugestoes": [
      "Tente aumentar a duração das sessões longas progressivamente",
      "Identifique seu horário de pico de energia"
    ]
  },
  "periodo_analisado": {
    "inicio": "2025-06-01T00:00:00Z",
    "fim": "2025-06-30T23:59:59Z"
  }
}
```

#### Níveis de feedback por média de foco

| Média de foco | Nível | Título |
|:---:|---|---|
| < 2 | `crítico` | Atenção: produtividade em risco 🔴 |
| 2 a 3 | `baixo` | Abaixo do potencial 🟡 |
| 3 a 4 | `médio` | No caminho certo 🟢 |
| > 4 | `alto` | Maratona produtiva de alto nível! 🚀 |

#### Erros possíveis

```bash
# Sem registros → 404
curl http://localhost:8000/api/v1/diagnostico-produtividade
# {"detail": "Nenhum registro de foco encontrado..."}

# data_inicio posterior a data_fim → 400
curl "http://localhost:8000/api/v1/diagnostico-produtividade?data_inicio=2025-12-31T00:00:00&data_fim=2025-01-01T00:00:00"
# {"detail": "O parâmetro 'data_inicio' não pode ser posterior ao 'data_fim'."}
```

---

### `GET /health` — Health check

Verifica se a API está no ar.

```bash
curl http://localhost:8000/health
```

```json
{
  "status": "ok",
  "version": "1.0.0",
  "debug": true
}
```

---

## Autenticação (opcional)

Por padrão, a API roda em **modo aberto** (sem autenticação), ideal para desenvolvimento.

Para habilitar a autenticação por API Key, defina a variável `API_KEY` no arquivo `.env`:

```env
API_KEY=minha-chave-secreta-aqui
```

Com a chave configurada, todas as requisições devem incluir o header `X-API-Key`:

```bash
curl -X POST http://localhost:8000/api/v1/registro-foco \
  -H "Content-Type: application/json" \
  -H "X-API-Key: minha-chave-secreta-aqui" \
  -d '{"nivel_foco": 5, "tempo_minutos": 60, "comentario": "Sessão com auth"}'
```

Requisição sem a chave (quando autenticação está ativa) retorna `401 Unauthorized`:

```json
{
  "detail": "API Key inválida ou ausente. Forneça o header X-API-Key."
}
```

---


## Variáveis de Ambiente

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `DATABASE_URL` | `sqlite:///./focus_log.db` | URL de conexão com o banco de dados |
| `API_KEY` | `` (vazio) | Chave de API para autenticação. Vazio = modo dev sem auth |
| `ALLOWED_ORIGINS` | `http://localhost:3000` | Origens permitidas para CORS (separadas por vírgula) |
| `DEBUG` | `true` | Modo debug. Em produção, definir como `false` |
| `RATE_LIMIT` | `60/minute` | Limite de requisições por IP por minuto |
| `APP_VERSION` | `1.0.0` | Versão da aplicação |

---

## Decisões Técnicas

### Por que FastAPI?
- **Performance nativa**: async/await out-of-the-box
- **Validação automática**: Pydantic v2 integrado, schemas com type hints
- **Documentação automática**: OpenAPI/Swagger gerado automaticamente
- **Dependency Injection**: sistema de `Depends()` para inversão de dependência (SOLID-D)

### Por que SQLite?
- **Zero configuração**: sem necessidade de servidor de banco de dados externo
- **Persistência real**: adequado para o escopo do projeto técnico
- **SQLAlchemy ORM**: facilidade de migrar para PostgreSQL/MySQL em produção apenas mudando a `DATABASE_URL`

### Arquitetura em Camadas (SOLID)
- **`api/`** — Endpoints HTTP (entrada/saída apenas)
- **`services/`** — Regras de negócio (Strategy Pattern no DiagnosticoService)
- **`repositories/`** — Acesso a dados (Repository Pattern)
- **`schemas/`** — Contratos de API (request ≠ response, nunca expõe ORM)
- **`models/`** — Entidades do banco de dados

### Segurança (OWASP)
- IDs como UUIDs (API1 — BOLA)
- API Key configurável por env var (API2)
- Schemas explícitos, nunca retorna ORM direto (API3)
- Rate limiting com SlowAPI, limite de 10KB no body (API4)
- Security headers via middleware, CORS configurável (API8)
- Sanitização de strings com `.strip()` (API10)

---

## Melhorias Futuras

1. **Autenticação JWT** — substituir API Key por tokens JWT com refresh
2. **PostgreSQL** — migrar para banco de dados mais robusto em produção
3. **Alembic** — migrações de banco de dados versionadas
4. **Exportação de relatórios** — PDF/CSV das sessões e diagnósticos
5. **Notificações** — alertas quando a produtividade está baixa
6. **Dashboard** — endpoints para gráficos de evolução temporal
7. **Docker** — containerização com docker-compose
8. **CI/CD** — pipeline de testes automáticos com GitHub Actions
