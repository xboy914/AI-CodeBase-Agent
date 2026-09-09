from codebase_agent.retrieval import (
    lexical_score,
    rank_lexical,
    reciprocal_rank_fusion,
    tokenize,
)


def chunk(path: str, symbol: str, content: str, line: int = 1) -> dict:
    return {
        "path": path,
        "symbol": symbol,
        "kind": "function",
        "content": content,
        "start_line": line,
        "end_line": line + 4,
    }


def test_tokenize_normalizes_code_terms():
    assert tokenize("useAuth TOKEN_2") == {"useauth", "token_2"}


def test_exact_symbol_match_receives_strong_boost():
    exact = chunk("src/hooks.ts", "useAuth", "export function useAuth() {}")
    generic = chunk("src/auth.ts", "login", "use auth state")

    assert lexical_score("useAuth", exact) > lexical_score("useAuth", generic)


def test_lexical_ranking_can_retrieve_exact_file_match():
    payloads = [
        chunk("src/components/Button.tsx", "Button", "export const Button = () => null"),
        chunk("src/auth/session.ts", "readSession", "export function readSession() {}"),
    ]

    ranked = rank_lexical("session.ts", payloads, limit=2)

    assert ranked[0]["path"] == "src/auth/session.ts"


def test_rrf_promotes_items_found_by_both_retrievers_and_deduplicates():
    shared = chunk("src/auth.ts", "useAuth", "export function useAuth() {}")
    semantic_only = chunk("src/session.ts", "session", "load user state", line=10)
    lexical_only = chunk("src/hooks.ts", "useAuthToken", "read token", line=20)

    fused = reciprocal_rank_fusion(
        [semantic_only, shared],
        [shared, lexical_only],
        limit=3,
    )

    assert fused[0]["path"] == "src/auth.ts"
    assert len(fused) == 3
    assert all("retrieval_score" in item for item in fused)
