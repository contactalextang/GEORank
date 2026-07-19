"""
知识图谱服务 — Neo4j
负责公司实体关系的存储与查询
"""
from neo4j import AsyncGraphDatabase
from app.core.config import settings

def _new_driver():
    """Create a loop-local driver so task runners can close it deterministically."""
    return AsyncGraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
    )

_ALLOWED_ENTITY_LABELS = frozenset({"Person", "Product", "Technology", "Company"})
_ALLOWED_RELATIONSHIP_TYPES = frozenset(
    {"FOUNDED_BY", "HAS_PRODUCT", "USES_TECH", "COMPETES_WITH"}
)


def _sanitize_graph_payload(
    entities: list[dict], relations: list[dict]
) -> tuple[list[dict], list[dict]]:
    """过滤出可安全写入的实体/关系。

    实体类型/关系类型会直接拼进 Cypher 标签，必须严格白名单以防标签注入。
    不在白名单或缺字段的条目「跳过」而非抛错，这样 LLM 偶发的异常单条
    数据不会中断整次公司分析（安全性不减弱：越界条目永不进入 Cypher）。
    """
    clean_entities: list[dict] = []
    entity_names: set[str] = set()
    for entity in entities or []:
        entity_type = entity.get("type")
        entity_name = str(entity.get("name") or "").strip()
        if entity_type not in _ALLOWED_ENTITY_LABELS:
            continue
        if not entity_name or entity_name in entity_names:
            continue
        entity_names.add(entity_name)
        clean_entities.append({**entity, "name": entity_name})

    clean_relations: list[dict] = []
    for relation in relations or []:
        relation_type = relation.get("type")
        from_name = str(relation.get("from") or "").strip()
        to_name = str(relation.get("to") or "").strip()
        if relation_type not in _ALLOWED_RELATIONSHIP_TYPES:
            continue
        if not from_name or not to_name:
            continue
        clean_relations.append({**relation, "from": from_name, "to": to_name})

    return clean_entities, clean_relations


async def create_company_node(company_id: str, properties: dict):
    """创建公司节点，并清理该公司上一轮图谱连接。"""
    async with _new_driver() as driver:
        async with driver.session() as session:
            await session.run(
                """
                MERGE (c:Company {id: $id})
                SET c += $props
                WITH c
                OPTIONAL MATCH (c)-[link:HAS_ENTITY]->(old)
                DELETE link
                """,
                id=company_id,
                props=properties,
            )


async def add_entities_and_relations(company_id: str, entities: list[dict], relations: list[dict]):
    """
    将 LLM 抽取的实体和关系写入知识图谱
    entities: [{"name": "...", "type": "Product|Person|Technology", "props": {...}}]
    relations: [{"from": "...", "to": "...", "type": "HAS_PRODUCT|FOUNDED_BY|USES_TECH"}]
    """
    entities, relations = _sanitize_graph_payload(entities, relations)
    if not entities and not relations:
        return

    async with _new_driver() as driver:
        async with driver.session() as session:
            for entity in entities:
                await session.run(
                    f"""
                    MERGE (e:{entity['type']} {{company_id: $company_id, name: $name}})
                    SET e += $props
                    MERGE (c:Company {{id: $company_id}})
                    MERGE (c)-[:HAS_ENTITY]->(e)
                    """,
                    name=entity["name"],
                    props=entity.get("props", {}),
                    company_id=company_id,
                )

            for rel in relations:
                await session.run(
                    f"""
                    MATCH (a {{company_id: $company_id, name: $from_name}})
                    MATCH (b {{company_id: $company_id, name: $to_name}})
                    MERGE (a)-[:{rel['type']}]->(b)
                    """,
                    company_id=company_id,
                    from_name=rel["from"],
                    to_name=rel["to"],
                )


async def get_company_graph(company_id: str) -> dict:
    """获取某公司的完整知识图谱（节点 + 关系）"""
    async with _new_driver() as driver:
        async with driver.session() as session:
            node_result = await session.run(
                """
                MATCH (c:Company {id: $id})-[:HAS_ENTITY]->(n)
                RETURN labels(n) AS labels, properties(n) AS props
                LIMIT 100
                """,
                id=company_id,
            )
            nodes = []
            async for record in node_result:
                properties = dict(record["props"] or {})
                name = str(properties.pop("name", "")).strip()
                if not name:
                    continue
                labels = list(record["labels"] or [])
                nodes.append(
                    {
                        "name": name,
                        "type": labels[0] if labels else "Entity",
                        "properties": properties,
                    }
                )

            relation_result = await session.run(
                """
                MATCH (c:Company {id: $id})-[:HAS_ENTITY]->(a),
                      (c)-[:HAS_ENTITY]->(b),
                      (a)-[r]->(b)
                RETURN a.name AS source, type(r) AS type, b.name AS target
                LIMIT 200
                """,
                id=company_id,
            )
            relationships = [
                {
                    "from": record["source"],
                    "type": record["type"],
                    "to": record["target"],
                }
                async for record in relation_result
                if record["source"] and record["target"]
            ]
            return {"nodes": nodes, "relationships": relationships}
