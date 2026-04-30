from api.vendo_catalog import lookup, AI_SLUGS

def test_known_integration_returns_metadata():
    meta = lookup("telegram")
    assert meta is not None
    assert meta["kind"] == "integration"
    assert meta["native_env_map"] == {"bot_token": "TELEGRAM_BOT_TOKEN"}
    assert meta["docs_url"] == "https://core.telegram.org/bots/api"

def test_known_ai_returns_proxy_url():
    meta = lookup("anthropic")
    assert meta["kind"] == "ai"
    assert meta["proxy_url"] == "https://anthropic-proxy.vendo.run"

def test_unknown_slug_returns_none():
    assert lookup("zzz_unknown") is None

def test_ai_slugs_set_matches():
    assert AI_SLUGS == {"openrouter", "openai", "anthropic"}
