from core.analyze.textComplexityMetrics import TextComplexityMetrics
from core.analyze.descriptiveTextMetrics import DescriptiveTextMetrics
from core.analyze.morpho_metrics import MorphoMetrics
from core.analyze.ReadabilityIndexCalculator import ReadabilityIndexCalculator

metrics = TextComplexityMetrics()
metrics2 = DescriptiveTextMetrics()

text = """# Базы данных: от реляционных корней к распределённым облакам  
*Полный технический обзор, 2025 г.*

## 1. Введение: что такое база данных?

**База данных (БД)** — это организованная совокупность структурированных данных, хранящихся и обрабатываемых с помощью **системы управления базами данных (СУБД)**. Ключевые цели:
- **Надёжное хранение** (даже при сбоях),
- **Эффективный доступ** (миллионы запросов в секунду),
- **Целостность данных** (ограничения, транзакции),
- **Безопасность** (аутентификация, шифрование),
- **Масштабируемость** (от embedded до petabyte-кластеров).

Без БД невозможны: банкинг, соцсети, IoT, ИИ-тренировки, госуслуги.

## 2. Эволюция: от иерархических к multi-model

### 2.1. Истоки (1960–1970)
- **Иерархические БД** (IBM IMS): дерево записей. Быстро, но жёстко («один ко многим»).
- **Сетевые БД** (CODASYL): граф связей. Гибко, но сложен в разработке.

→ Проблема: **много кода для навигации**, дублирование логики.

### 2.2. Революция: реляционная модель (1970)
Эдгар Кодд (IBM) предложил:
- Данные в **таблицах (отношениях)**,
- Доступ через **декларативный язык — SQL**,
- Теоретическая основа: **реляционная алгебра и исчисление**.

→ 1979: первая коммерческая СУБД — **Oracle V2**.  
→ 1980-е: **PostgreSQL**, **IBM DB2**, **Microsoft SQL Server**.

**ACID** стал стандартом:
- **A**tomicity — «всё или ничего»,
- **C**onsistency — соблюдение ограничений,
- **I**solation — изоляция параллельных транзакций,
- **D**urability — сохранность после коммита.

### 2.3. NoSQL-взрыв (2000-е)
Рост веба → новые требования:
- горизонтальное масштабирование,
- schema-on-read,
- отказ от строгой согласованности (CAP-теорема).

Типы NoSQL:
| Тип | Примеры | Сценарий |
|-----|---------|----------|
| **Key-Value** | Redis, DynamoDB | кэширование, сессии |
| **Document** | MongoDB, Couchbase | гибкие JSON-объекты (CMS, профили) |
| **Column-family** | Cassandra, ScyllaDB | time-series, аналитика |
| **Graph** | Neo4j, Dgraph | рекомендации, фрод-детекция |

→ Компромисс: **BASE** вместо ACID:  
**B**asically available, **S**oft state, **E**ventual consistency.

### 2.4. NewSQL и multi-model (2010–2025)
Возврат к ACID, но с масштабируемостью:
- **Google Spanner** — глобально распределённая ACID-БД с TrueTime,
- **CockroachDB**, **YugabyteDB** — open-source Spanner-клон,
- **PostgreSQL** → multi-model: JSONB, full-text search, PostGIS (гео), pgvector (эмбеддинги).

## 3. Архитектура СУБД: что внутри?

### 3.1. Слои классической СУБД
1. **Query Parser** — разбор SQL → AST.
2. **Query Optimizer** — поиск оптимального плана (cost-based: cardinality, индексы, статистика).
3. **Execution Engine** — выполнение (nested loop, hash join, sort-merge).
4. **Storage Manager**:
   - Buffer Pool (кэш страниц в RAM),
   - WAL (Write-Ahead Log) — для durability,
   - Page Manager (чтение/запись блоков 4–16 КБ),
   - Index Manager (B+Tree, LSM-tree, hash).

### 3.2. B+Tree vs LSM-Tree
| Характеристика | B+Tree (PostgreSQL, MySQL InnoDB) | LSM-Tree (RocksDB, Cassandra) |
|----------------|-----------------------------------|-------------------------------|
| Чтение | O(log N), стабильно | O(log²N), может быть медленнее (много SSTable) |
| Запись | медленнее (случайные I/O, балансировка) | очень быстро (sequential write) |
| Компакция | не требуется | фоновая (merge, delete tombstones) |
| Использование | OLTP, смешанные нагрузки | write-heavy (логи, IoT, аналитика) |

## 4. Транзакции и согласованность

### 4.1. Уровни изоляции (SQL-92)
| Уровень | Dirty Read | Non-Repeatable Read | Phantom Read |
|---------|------------|---------------------|--------------|
| Read Uncommitted | ✅ | ✅ | ✅ |
| Read Committed | ❌ | ✅ | ✅ |
| Repeatable Read | ❌ | ❌ | ✅ (часто — ❌ в PG) |
| Serializable | ❌ | ❌ | ❌ |

→ **PostgreSQL** использует MVCC (Multi-Version Concurrency Control):  
каждая транзакция видит «снимок» базы на момент старта.

### 4.2. Распределённые транзакции
- **2PC (Two-Phase Commit)** — блокирующий, уязвим к отказам координатора.
- **Paxos / Raft** — для согласования лога (в etcd, ZooKeeper).
- **Percolator (Google)** — оптимистичная блокировка поверх Bigtable.

## 5. Масштабирование и отказоустойчивость

### 5.1. Вертикальное vs горизонтальное
- **Vertical scaling** — «купить сервер побольше». Просто, но дорого, предел ~100 ТБ RAM.
- **Horizontal scaling**:
  - **Репликация** (master-slave, multi-leader) → read-scaling, отказоустойчивость,
  - **Шардинг** (by key, by range) → write-scaling, но сложность в JOIN, транзакциях.

### 5.2. Репликация
| Тип | Задержка | Консистентность | Использование |
|-----|----------|------------------|---------------|
| Synchronous | низкая | strong | критичные системы (платежи) |
| Asynchronous | высокая | eventual | аналитика, резервные копии |
| Semi-sync (MySQL) | средняя | «гарантия на 1 slave» | баланс |

→ **Quorum-based** (N/2 + 1): например, в Cassandra: RF=3, W=2, R=2 → strong consistency.

## 6. Современные тренды (2025)

### 6.1. Векторные базы данных
Хранение и поиск по эмбеддингам (для ИИ):
- **pgvector** (PostgreSQL extension),
- **Milvus**, **Qdrant**, **Weaviate** — standalone vector DB,
- Индексы: HNSW, IVF-PQ.

→ Запрос: `SELECT * FROM items ORDER BY embedding <-> ? LIMIT 10`.
6"""
result = metrics.compute(text)
result2 = metrics2.compute(text)
print(result)
print(result2)
mm = MorphoMetrics()
res = mm.compute(text)

calc = ReadabilityIndexCalculator()
res2 = calc.compute(text)

print(f"Существительных (NOUN):       {res['nouns']}")
print(f"Глаголов (VERB + INFN):      {res['verbs']}")
print(f"Прилагательных (ADJF):       {res['adjectives']}")
print(f"Местоимений (NPRO и др.):    {res['pronouns']}")
print(f"Наречий (ADVB):              {res['adverbs']}")
print(f"Предлогов (PREP):            {res['prepositions']}")
print(f"Союзов (CONJ):               {res['conjunctions']}")
print(f"Частиц (PRCL):               {res['particles']}")
print(f"Междометий (INTJ):           {res['interjections']}")
print()
print(f"Всего слов:                  {res['total_words']}")
print()
print(f"Flesch: {res2['flesch_reading_ease']} - {res2['flesch_level']}")
print(f"SMOG:   {res2['smog_grade']} класс")
print(f"«Просто о сложном»: {res2['simple_level']}/5")
