# QA Dataset Schema

Each line in `qa_pairs.jsonl` is a JSON object with:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Unique identifier (e.g., "q001") |
| `question` | string | yes | The question to ask |
| `ground_truth` | string | yes | The correct answer |
| `expected_sources` | list[str] | no | S3 keys of relevant source documents |
| `difficulty` | string | yes | "easy", "medium", "hard" |
| `category` | string | yes | "factoid", "analytical", "multi_hop", "unanswerable" |

## Distribution Target (30 pairs)
- 10 factoid (easy, answer in one chunk)
- 8 analytical (medium, requires reasoning)
- 7 multi-hop (hard, answer spans multiple chunks/documents)
- 5 unanswerable (not in corpus — tests hallucination resistance)
