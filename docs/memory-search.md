# Memory Search

v2 implements practical keyword memory search rather than claiming vector search. Uploaded files can be indexed into `MemoryDocument` and `MemoryChunk` rows. The search endpoint scores chunks by query term frequency and returns snippets.

The `memory.search` tool exposes the same retrieval behavior to the agent engine. Trace spans record memory tool calls and retrieved chunks.

pgvector embeddings are a roadmap item. The README and UI describe the current implementation as keyword-based search.
