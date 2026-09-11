import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import db
from app.chem.embeddings import get_embedder
from app.db import get_session
from app.main import create_app
from app.models.molecule import Base, KnownMolecule
from app.models.project import Project  # noqa: F401 — ensure table is registered

SEED_ROWS = [
    ("CC(=O)Oc1ccccc1C(=O)O", "CHEMBL25", "ASPIRIN"),
    ("CC(C)Cc1ccc(cc1)C(C)C(=O)O", "CHEMBL521", "IBUPROFEN"),
    ("CN1C=NC2=C1C(=O)N(C(=O)N2C)C", "CHEMBL113", "CAFFEINE"),
]


@pytest.fixture(scope="session")
def client(tmp_path_factory):
    import asyncio

    db_path = tmp_path_factory.mktemp("db") / "test.db"
    test_engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
    TestSession = async_sessionmaker(test_engine, expire_on_commit=False)

    async def setup() -> None:
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with TestSession() as session:
            embedder = get_embedder()
            for smiles, chembl_id, name in SEED_ROWS:
                session.add(
                    KnownMolecule(
                        canonical_smiles=smiles,
                        chembl_id=chembl_id,
                        name=name,
                        fingerprint=embedder.embed_smiles(smiles),
                    )
                )
            await session.commit()

    async def override_session():
        async with TestSession() as session:
            yield session

    asyncio.run(setup())
    db.engine = test_engine
    db.SessionLocal = TestSession
    app = create_app()
    app.dependency_overrides[get_session] = override_session
    with TestClient(app) as client:
        yield client
