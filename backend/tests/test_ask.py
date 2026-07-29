import pytest

import scripts.ask as ask


# 验证命令行帮助只输出用法，不会触发 RAG Chain 初始化。
def test_ask_help_exits_before_creating_chain(monkeypatch, capsys):
    def fail_create_chain():
        raise AssertionError("help should not create rag chain")

    monkeypatch.setattr(ask, "create_rag_chain", fail_create_chain)

    with pytest.raises(SystemExit) as exc_info:
        ask.main(["--help"])

    assert exc_info.value.code == 0
    assert "KingIAsk 命令行问答" in capsys.readouterr().out
