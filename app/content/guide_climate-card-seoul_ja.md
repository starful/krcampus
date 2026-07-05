---
{
  "layout": "guide",
  "id": "climate-card-seoul",
  "title": "ソウルで暮らす学生のための「気候同行カード」活用ガイド",
  "category": "Budget",
  "tags": [
    "節約"
  ],
  "description": "ソウルの公共交通機関が乗り放題になる「気候同行カード」を使って、毎月の交通費を賢く節約する方法をご紹介します。",
  "thumbnail": "https://images.unsplash.com/photo-1561414927-6d86591d0c4f?w=500",
  "date": "2026-07-05",
  "lang": "ja",
  "basic_info": {
    "name_ja": "Climate Card Guide for Students in Seoul"
  },
  "features": [
    "節約"
  ]
}
---

# Comprehensive Guide to PostgreSQL Performance Tuning

PostgreSQL is one of the most powerful, open-source relational database management systems available today. While it is highly capable out of the box, default configurations are typically conservative to ensure compatibility across a wide range of hardware. To unlock its full potential for high-volume, production-grade applications, database administrators and developers must engage in systematic performance tuning. This guide covers database optimization, focusing on system configurations, indexing strategies, query execution analysis, and routine maintenance.

## Understanding the Query Planner and EXPLAIN
Before optimizing any database, you must understand how PostgreSQL executes queries. The query planner evaluates multiple execution paths and selects the most efficient plan based on table statistics.
To inspect this plan, use the `EXPLAIN` statement. Adding the `ANALYZE` option executes the query and returns actual runtimes alongside estimated costs:
sql
EXPLAIN ANALYZE SELECT * FROM orders WHERE customer_id = 4512 AND status = 'completed';

Key metrics to look for in the output include:
* **Sequential Scan (Seq Scan):** The planner reads the entire table from disk. This is slow for large datasets.
* **Index Scan:** The planner uses an index to locate rows. This is highly efficient.
* **Bitmap Index Scan:** A hybrid approach that scans indexes first, builds a memory bitmap of matching pages, and then reads those pages.
* **Actual Time:** The time taken (in milliseconds) to execute each node of the query.
If the planner miscalculates costs, it is often due to outdated statistics. Running `ANALYZE` manually updates these statistics, allowing the planner to make better choices.

## Key Configuration Parameters
PostgreSQL's default configurations are designed for minimal hardware. For dedicated database servers, adjusting memory allocation parameters is the most impactful step you can take.

### Table 1: Key postgresql.conf Parameters
| Parameter | Default Value | Recommended Setting | Description |
| :--- | :--- | :--- | :--- |
| `shared_buffers` | 128MB | 25% of total system RAM | Amount of memory used for shared memory buffers. |
| `work_mem` | 4MB | 32MB - 64MB (per operation) | Memory allocated for internal sort operations and hash tables. |
| `maintenance_work_mem` | 64MB | 10% of RAM (up to 2GB) | Memory used for maintenance operations like `VACUUM` and `CREATE INDEX`. |
| `effective_cache_size` | 4GB | 50% to 75% of system RAM | Guide to the planner on how much memory is available for disk caching. |
| `random_page_cost` | 4.0 | 1.1 (for SSDs) / 4.0 (for HDDs) | Planner's estimate of the cost of a non-sequentially fetched disk page. |

* **Shared Buffers:** Controls memory used to cache data blocks. If your active dataset fits here, disk I/O drops to near zero, speeding up reads.
* **Work Memory (`work_mem`):** Allocated per query operation (e.g., sort, hash join). If a query exceeds `work_mem`, it spills to disk. Set carefully to avoid exhausting memory.
* **Random Page Cost (`random_page_cost`):** Modern SSDs have negligible seek times. Reducing this to `1.1` tells the planner that random access is cheap, encouraging index scans.

## Indexing Strategies for High Performance
Indices accelerate data retrieval but introduce write overhead. Choosing the correct index type is critical.

### Table 2: PostgreSQL Index Types and Use Cases
| Index Type | Standard Use Case | Example Query / Operator | Best For |
| :--- | :--- | :--- | :--- |
| **B-Tree** | Equality, range, sorting | `=`, `<`, `>`, `BETWEEN` | Default choice for general-purpose queries. |
| **GIN** | Multi-value data, full-text | `@>`, `@@`, array contains | JSONB, arrays, and full-text search indexing. |
| **GiST** | Geometric, spatial, ranges | `&&` (overlaps), distance | Geospatial mapping and range types. |
| **BRIN** | Extremely large ordered datasets | Date/timestamp-ordered tables | Timeseries data with highly correlated columns. |

To maximize index efficiency:
1. **Use Covering Indexes (`INCLUDE`):** This allows appending non-key payload columns to a B-Tree index, enabling Index-Only Scans.
   sql
   CREATE INDEX idx_orders_customer ON orders(customer_id) INCLUDE (order_total);
   
2. **Implement Partial Indexes:** If you frequently query a subset of rows, index only those rows to save space and speed up updates.
   sql
   CREATE INDEX idx_active_users ON users(id) WHERE status = 'active';
   
3. **Avoid Over-Indexing:** Monitor unused indexes using `pg_stat_user_indexes` and drop them to free disk space and improve write throughput.

## Query Optimization Techniques
Writing clean SQL is as important as configuring the database server. Poorly structured queries bypass indexes and strain resources.
* **Avoid `SELECT *`:** Only request columns your application needs. This reduces network payload, memory usage, and enables Index-Only Scans.
* **Use CTEs Wisely:** PostgreSQL handles CTEs efficiently, but complex recursive CTEs can still degrade performance if not monitored.
* **Optimize Joins:** Ensure foreign keys are indexed. Match data types across join conditions to avoid implicit conversion overhead.
* **Batch Updates and Deletes:** Modifying millions of rows in one transaction locks tables and bloats logs. Break large operations into smaller batches.

## Routine Database Maintenance
PostgreSQL uses Multi-Version Concurrency Control (MVCC). When a row is updated or deleted, the old version remains on disk as a "dead tuple," causing bloat.
* **Autovacuum Tuning:** Ensure settings are aggressive enough to clean dead tuples and update statistics:
  ini
  autovacuum_vacuum_scale_factor = 0.05
  autovacuum_analyze_scale_factor = 0.02
  
* **Reindexing:** Run `REINDEX CONCURRENTLY` to rebuild fragmented indexes in the background without locking reads or writes.

## Frequently Asked Questions (FAQ)

**Q: How do I identify slow queries in PostgreSQL?**
A: Enable the `pg_stat_statements` extension. It tracks execution statistics for all SQL statements, allowing you to find queries with high cumulative runtimes.

**Q: What is the ideal value for `max_connections`?**
A: High connection counts degrade performance due to lock contention. Keep this value reasonable and use a connection pooler like PgBouncer to manage active connections.

**Q: Why is my index not being used?**
A: The planner bypasses indexes if it determines a sequential scan is faster. This happens with small tables, queries returning a large percentage of rows, or outdated statistics. Run `ANALYZE` to update statistics.

**Q: What is table bloat, and how can I fix it?**
A: Table bloat occurs when deleted or updated rows leave "dead tuples" that occupy physical space. Autovacuum recovers this space. For extreme bloat, use `pg_repack` to rebuild the table without locking.

**Q: How often should I run `ANALYZE` manually?**
A: Autovacuum handles this automatically, but you should run `ANALYZE` manually after bulk data loads or major schema changes to ensure planning accuracy.