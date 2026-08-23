"""One-off/idempotent seed of this deployment's own node row, run at
deploy time via `python -m app.seed`. Values come entirely from this
environment's .env — nothing about the node is hardcoded in code."""

import asyncio

from sqlalchemy import select

from app.core.config import settings
from app.core.db import async_session_factory
from app.models.node import Node


async def seed_local_node() -> None:
    server_name = settings.reality_server_names.split(",")[0].strip()

    async with async_session_factory() as session:
        result = await session.execute(select(Node).where(Node.node_id == settings.node_id))
        node = result.scalar_one_or_none()

        if node is None:
            node = Node(node_id=settings.node_id)
            session.add(node)

        node.name = settings.node_id
        node.host = settings.node_host
        node.vless_port = settings.xray_vless_port
        node.xray_api_host = "xray"
        node.xray_api_port = settings.xray_api_port
        node.reality_public_key = settings.reality_public_key
        node.reality_short_id = settings.reality_short_id
        node.reality_server_name = server_name
        node.hysteria_port = settings.hysteria_port
        node.hysteria_cert_fingerprint = settings.hysteria_cert_fingerprint
        node.is_local = True
        node.status = "online"
        node.is_active = True

        await session.commit()
        print(f"Seeded node '{node.node_id}' (id={node.id})")


if __name__ == "__main__":
    asyncio.run(seed_local_node())
