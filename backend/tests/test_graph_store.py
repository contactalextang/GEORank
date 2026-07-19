import unittest
from unittest.mock import patch

from app.services import graph_store
from app.services.graph_store import add_entities_and_relations, _sanitize_graph_payload


class GraphStoreContractTests(unittest.IsolatedAsyncioTestCase):
    async def test_drops_unapproved_entity_label_without_opening_session(self):
        # 标签会拼进 Cypher，注入型类型必须被丢弃且绝不打开 Neo4j 会话。
        with patch.object(
            graph_store, "_new_driver", side_effect=AssertionError("must not open a session")
        ):
            await add_entities_and_relations(
                "company-id",
                [{"name": "Injected", "type": "Person`) MATCH (n) DETACH DELETE n //"}],
                [],
            )

    async def test_drops_unapproved_relationship_type_without_opening_session(self):
        # 纯注入型关系（无任何合法实体/关系）应被全部丢弃并早返回，不打开会话。
        with patch.object(
            graph_store, "_new_driver", side_effect=AssertionError("must not open a session")
        ):
            await add_entities_and_relations(
                "company-id",
                [],
                [{"from": "Company", "to": "Product", "type": "OWNS`] DELETE n //"}],
            )

    def test_sanitize_keeps_only_whitelisted_and_skips_bad_rows(self):
        entities = [
            {"name": "Anthropic", "type": "Company"},
            {"name": "Claude", "type": "Product"},
            {"name": "example.com", "type": "Domain"},  # 不支持 → 跳过
            {"name": "", "type": "Person"},              # 空名 → 跳过
            {"name": "Anthropic", "type": "Company"},    # 重复 → 跳过
        ]
        relations = [
            {"from": "Anthropic", "to": "Claude", "type": "HAS_PRODUCT"},
            {"from": "Anthropic", "to": "Claude", "type": "OWNS"},  # 不支持 → 跳过
            {"from": "", "to": "Claude", "type": "HAS_PRODUCT"},    # 缺端点 → 跳过
        ]
        clean_entities, clean_relations = _sanitize_graph_payload(entities, relations)
        self.assertEqual([e["name"] for e in clean_entities], ["Anthropic", "Claude"])
        self.assertEqual(len(clean_relations), 1)
        self.assertEqual(clean_relations[0]["type"], "HAS_PRODUCT")


if __name__ == "__main__":
    unittest.main()
