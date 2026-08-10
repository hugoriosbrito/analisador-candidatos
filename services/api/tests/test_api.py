from app.db.seed import seed_database
from app.db.session import SessionLocal

def h(): return {"X-Admin-Key":"test-admin"}
def test_health(client): assert client.get("/api/v1/health").json()["status"]=="ok"
def test_admin_requires_key(client): assert client.post("/api/v1/admin/claims",json={"text":"Uma afirmação factual suficientemente longa."}).status_code==401
def test_demo_workflow_create_research_review_publish(client):
    r=client.post("/api/v1/admin/claims",headers=h(),json={"text":"O indicador demonstrativo cresceu 12% em 2025."}); assert r.status_code==200; cid=r.json()["id"]
    assert client.post(f"/api/v1/admin/claims/{cid}/research",headers=h()).json()["status"]=="AI_REVIEWED"
    assert client.post(f"/api/v1/admin/claims/{cid}/publish",headers=h()).status_code==409
    assert client.post(f"/api/v1/admin/claims/{cid}/review",headers=h(),json={"approved":True,"reviewer":"Teste"}).status_code==200
    assert client.post(f"/api/v1/admin/claims/{cid}/publish",headers=h()).json()["status"]=="PUBLISHED"
    public=client.get(f"/api/v1/claims/{cid}").json(); assert public["assessment"]["published_at"] and public["evidences"]
def test_seed_public_claims(client):
    s=SessionLocal(); seed_database(s); s.close(); assert client.get("/api/v1/claims").json()
