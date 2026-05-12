# Focus Log API — Especificação Completa do Projeto

## 🎯 Objetivo

Construir o backend de um **Log de Performance** — uma API REST que permite registrar sessões de trabalho/estudo com nível de foco e retornar um diagnóstico inteligente de produtividade.

---

## 🛠️ Stack e Requisitos Técnicos

| Item | Escolha |
|------|---------|
| Linguagem | Python 3.11+ |
| Framework | FastAPI (performance nativa com async, validação automática via Pydantic, geração de docs OpenAPI) |
| Armazenamento | SQLite com SQLAlchemy (ORM) — persistência real sem complexidade de setup |
| Gerenciador de dependências | pip com `requirements.txt` ou `pyproject.toml` |

---

## 📐 Arquitetura e Estrutura de Pastas

Arquitetura em camadas, respeitando os princípios SOLID:

```
focus_log_api/
├── app/
│   ├── __init__.py
│   ├── main.py                  # Entry point FastAPI, configuração de middlewares
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py            # Configurações via variáveis de ambiente (pydantic-settings)
│   │   └── security.py          # Rate limiting, headers de segurança
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── registro.py      # POST /registro-foco
│   │           └── diagnostico.py   # GET /diagnostico-produtividade
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── registro.py          # Pydantic schemas (request/response)
│   │   └── diagnostico.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── registro.py          # SQLAlchemy ORM model
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── registro_repository.py  # Camada de acesso a dados (Repository Pattern)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── registro_service.py      # Regras de negócio do registro
│   │   └── diagnostico_service.py   # Lógica de análise e feedback
│   └── db/
│       ├── __init__.py
│       ├── base.py              # Base declarativa SQLAlchemy
│       └── session.py           # Engine, SessionLocal, get_db dependency
├── tests/
│   ├── __init__.py
│   ├── test_registro.py
│   └── test_diagnostico.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

### Princípios SOLID a Aplicar

| Princípio | Aplicação |
|-----------|-----------|
| **S** — Single Responsibility | Cada classe/módulo tem uma única responsabilidade (service ≠ repository ≠ endpoint) |
| **O** — Open/Closed | O `DiagnosticoService` deve ser extensível para novas regras de feedback sem modificar o núcleo (use Strategy Pattern ou lista de regras configurável) |
| **L** — Liskov Substitution | Schemas de request e response separados, sem herança problemática |
| **I** — Interface Segregation | Interfaces/protocolos enxutos (use `Protocol` do Python ou ABCs onde fizer sentido) |
| **D** — Dependency Inversion | Injeção de dependência via `Depends()` do FastAPI para repositórios e serviços |

---

## 🛣️ Endpoints

### `POST /api/v1/registro-foco`

**Request body (JSON):**

```json
{
  "nivel_foco": 4,
  "tempo_minutos": 45,
  "comentario": "Implementei o módulo de autenticação sem interrupções",
  "categoria": "coding",
  "tags": ["backend", "auth"],
  "data": "2025-06-10T14:30:00"
}
```

**Campos:**

| Campo | Tipo | Obrigatório | Validação |
|-------|------|-------------|-----------|
| `nivel_foco` | int | ✅ | 1 a 5 (inclusive) |
| `tempo_minutos` | int | ✅ | > 0, <= 480 (8h) |
| `comentario` | str | ✅ | min 3, max 500 chars |
| `categoria` | enum | ❌ | `coding`, `reuniao`, `estudo`, `outro` |
| `tags` | list[str] | ❌ | max 10 tags, cada tag max 30 chars |
| `data` | datetime | ❌ | default: now (UTC) |

**Response `201`:**

```json
{
  "id": "uuid-aqui",
  "nivel_foco": 4,
  "tempo_minutos": 45,
  "comentario": "...",
  "categoria": "coding",
  "tags": ["backend", "auth"],
  "data": "2025-06-10T14:30:00Z",
  "created_at": "2025-06-10T14:30:00Z"
}
```

**Erros esperados:**

- `422 Unprocessable Entity` — validação Pydantic (nível fora do range, tempo negativo, etc.)
- `400 Bad Request` — regras de negócio customizadas

---

### `GET /api/v1/diagnostico-produtividade`

**Query params opcionais:**

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `data_inicio` | datetime | Filtrar registros a partir desta data |
| `data_fim` | datetime | Filtrar registros até esta data |
| `categoria` | enum | Filtrar por categoria |

**Response `200`:**

```json
{
  "total_registros": 12,
  "media_foco": 3.75,
  "tempo_total_minutos": 380,
  "tempo_total_formatado": "6h 20min",
  "distribuicao_foco": {
    "1": 1, "2": 2, "3": 3, "4": 4, "5": 2
  },
  "categoria_mais_produtiva": "coding",
  "sessao_mais_longa": {
    "tempo_minutos": 90,
    "nivel_foco": 5,
    "categoria": "estudo"
  },
  "feedback": {
    "nivel": "alto",
    "titulo": "Maratona produtiva de alto nível! 🚀",
    "descricao": "Sua média de foco está acima de 4. Continue mantendo sessões focadas e respeite os intervalos para sustentar esse ritmo.",
    "sugestoes": [
      "Continue com sessões de 45-90 minutos",
      "Mantenha o ritual de início de sessão que está funcionando"
    ]
  },
  "periodo_analisado": {
    "inicio": "2025-06-01T00:00:00Z",
    "fim": "2025-06-10T23:59:59Z"
  }
}
```

**Lógica de feedback (estratégias separadas/configuráveis):**

| Média de foco | Nível | Título | Sugestões |
|---------------|-------|--------|-----------|
| < 2 | `crítico` | Atenção: produtividade em risco 🔴 | Pausas longas, eliminação de distrações, revisão de ambiente |
| 2 a 3 | `baixo` | Abaixo do potencial 🟡 | Técnica Pomodoro, silenciar notificações, definir metas claras |
| 3 a 4 | `médio` | No caminho certo 🟢 | Aumentar sessões longas, identificar horário de pico |
| > 4 | `alto` | Maratona produtiva de alto nível! 🚀 | Manter ritual, respeitar descanso, documentar o que funcionou |

**Erros esperados:**

- `404 Not Found` — nenhum registro encontrado (com mensagem clara)
- `400 Bad Request` — `data_inicio > data_fim`

---

## 🔒 Segurança (OWASP API Security Top 10)

### API1 — Broken Object Level Authorization
Use UUIDs como IDs (nunca inteiros sequenciais expostos).

### API2 — Broken Authentication
Adicione suporte a API Key via header `X-API-Key` (configurável por env var; se não configurada, modo aberto para dev).

### API3 — Broken Object Property Level Exposure
Schemas de response explícitos — **nunca** retorne o modelo ORM direto.

### API4 — Unrestricted Resource Consumption
- Rate limiting: máximo 60 requests/minuto por IP (use `slowapi`)
- Paginação no diagnóstico se houver endpoint de listagem
- Limite de tamanho do body: **10KB**

### API8 — Security Misconfiguration
- Headers de segurança via middleware: `X-Content-Type-Options`, `X-Frame-Options`, `Strict-Transport-Security`
- CORS configurável via env var (não `*` em produção)
- Não expor stack traces em produção (`debug=False` por env)

### API10 — Unsafe Consumption of APIs
Sanitize e valide todas as entradas (Pydantic já ajuda, mas adicione `.strip()` em strings).

---

## ⚙️ Configuração via Variáveis de Ambiente

**Arquivo `.env.example`:**

```env
DATABASE_URL=sqlite:///./focus_log.db
API_KEY=           # vazio = sem autenticação (dev mode)
ALLOWED_ORIGINS=http://localhost:3000
DEBUG=true
RATE_LIMIT=60/minute
APP_VERSION=1.0.0
```

---

## 🧪 Testes

Escreva testes com **pytest** + **httpx** (TestClient do FastAPI). Use banco de dados em memória (`sqlite:///:memory:`) nos testes via fixture de override de dependência.

### `test_registro.py`

- ✅ Criação com dados válidos → `201`
- ✅ `nivel_foco = 0` → `422`
- ✅ `nivel_foco = 6` → `422`
- ✅ `tempo_minutos = 0` → `422`
- ✅ `tempo_minutos = 481` → `422`
- ✅ `comentario` vazio → `422`

### `test_diagnostico.py`

- ✅ Sem registros → `404`
- ✅ Com registros → `200` e campos corretos
- ✅ Lógica de feedback para cada faixa de média
- ✅ Filtro por data

---

## 📄 README.md (Conteúdo Obrigatório)

O README deve conter:

1. Descrição do projeto
2. Pré-requisitos
3. Instalação passo a passo
4. Como rodar em desenvolvimento
5. Como rodar os testes
6. Documentação dos endpoints (com exemplos `curl`)
7. Variáveis de ambiente explicadas
8. Decisões técnicas (por que FastAPI, por que SQLite, arquitetura escolhida)
9. Melhorias futuras

---

## ✅ Checklist Final

Antes de considerar pronto, confirme:

- [ ] Todos os endpoints respondem corretamente
- [ ] Validações retornam `422` com mensagens claras em português
- [ ] Nenhum stack trace exposto nas respostas de erro
- [ ] Testes passando com `pytest`
- [ ] `README.md` completo
- [ ] `.env.example` presente
- [ ] `.gitignore` incluindo `.env`, `*.db`, `__pycache__`, `.venv`
- [ ] Código comentado em português nos pontos não triviais
- [ ] IDs são UUIDs, não inteiros sequenciais
