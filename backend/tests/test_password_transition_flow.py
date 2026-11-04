# ruff: noqa: F811
"""Actual old credential lifecycle connected to the new policy's public consumers."""

import json
import secrets
from contextlib import closing
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from tests.historical_backend import archive_backend, execute_original
from tests.password_helpers import call, link_token, login_password
from tests.test_iam import ORIGIN, SyntheticSecret, csrf
from tests.test_password_transition import legacy_database, migrate  # noqa: F401
from y3management.application import create_app
from y3management.config import Settings
from y3management.database import Database

pytestmark = pytest.mark.postgres


def original_lifecycle(settings: Settings, tmp_path: Path, mode: str) -> dict[str, Any]:
    old = archive_backend(tmp_path, "774661b33086334fe4ddf30b92de27432814defd")
    private = old / "input.json"
    private.write_text(
        json.dumps({"password": "Historical password " + secrets.token_urlsafe(24), "mode": mode})
    )
    private.chmod(0o600)
    execute_original(
        old,
        settings,
        """import json
from contextlib import closing
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import text
from tests.test_iam import ORIGIN,csrf,cli_bootstrap
from tests.test_iam_mfa import Authenticator,call,enroll,login_mfa
from tests.test_iam_mfa_management_races import provision
from tests.test_iam_emergency import operator,request,issue
from y3management.application import create_app
from y3management.config import load_settings
from y3management.database import Database
cfg=load_settings();data=json.loads(Path('input.json').read_text());db=Database(cfg)
private=Path('installer').absolute();private.mkdir(mode=0o700);output=private/'enrollment'
cli_bootstrap(cfg,data['password'],enrollment_file=output)
with TestClient(create_app(cfg,database=db),base_url=ORIGIN) as target:
 key=Authenticator();enroll(target,output.read_text().strip().split('#token=')[1],key)
 login_mfa(target,data['password'],key)
 result={'password':data['password']}
 with closing(TestClient(target.app,base_url=ORIGIN)) as actor:
  result['actor'],_=provision(target,actor,data['password'])
 with db.session() as session:
  target_query="SELECT id FROM iam_accounts WHERE login_id='master.test'"
  result['target']=str(session.execute(text(target_query)).scalar_one())
 if data['mode'] in ('password','both','passkey'):
  service,principal,ident=operator(cfg,db,Path('operator').absolute())
  req=request(service,principal,ident,data['mode']);result['old_token']=issue(service,principal,req)
  result['case']=str(req.operation_id)
 else:
  with closing(TestClient(target.app,base_url=ORIGIN)) as wrong:
   for _ in range(5 if data['mode']=='cooldown' else 4):
    body={'login_id':'master.test','password':'Incorrect historical password'}
    assert call(wrong,'/auth/login',csrf(wrong),body).status_code==401
   if data['mode']=='cooldown':
    body={'login_id':'master.test','password':data['password']}
    assert call(wrong,'/auth/login',csrf(wrong),body).status_code==429
 Path('result.json').write_text(json.dumps(result));Path('result.json').chmod(0o600)
""",
    )
    result = dict(json.loads((old / "result.json").read_text()))
    result["password"] = SyntheticSecret(result["password"])
    if "old_token" in result:
        result["old_token"] = SyntheticSecret(result["old_token"])
    return result


@pytest.mark.parametrize(
    "variant",
    [
        "password",
        "both",
        "passkey",
        "stale",
        "foreign",
        "epoch",
        "post_security",
        "post_reset",
        "post_master",
    ],
)
def test_actual_legacy_case_cutover_public_handoff_and_completion(
    legacy_database: tuple[Settings, Database], tmp_path: Path, variant: str
) -> None:
    settings, db = legacy_database
    data = original_lifecycle(
        settings, tmp_path, variant if variant in ("both", "passkey") else "password"
    )
    # Controlled old-source clock shift preserves the original 30-minute duration and FKs.
    foreign_case = uuid4()
    with db.session() as session:
        session.execute(
            text(
                "UPDATE iam_emergency_cases SET issued_at=issued_at-interval '31 minutes',"
                "checked_at=checked_at-interval '31 minutes',"
                "expires_at=expires_at-interval '31 minutes' WHERE id=:i"
            ),
            {"i": data["case"]},
        )
        session.execute(
            text(
                "UPDATE iam_emergency_credentials SET expires_at=expires_at-interval '31 minutes' "
                "WHERE case_id=:i"
            ),
            {"i": data["case"]},
        )
        if variant == "stale":
            session.execute(
                text(
                    "UPDATE iam_accounts SET row_version=row_version+1,"
                    "security_version=security_version+1 WHERE id=:a"
                ),
                {"a": data["target"]},
            )
        if variant == "foreign":
            # Historical counterexample only; never used to prepare a current caller/login.
            org, account = uuid4(), uuid4()
            session.execute(
                text("INSERT INTO organization_organizations VALUES(:o,'Foreign history')"),
                {"o": org},
            )
            session.execute(
                text(
                    "INSERT INTO iam_accounts(id,organization_id,login_id,state,password_hash) "
                    "VALUES(:a,:o,'foreign.history','ACTIVE','synthetic-history')"
                ),
                {"a": account, "o": org},
            )
            session.execute(
                text("INSERT INTO iam_login_ids VALUES('foreign.history',:a)"), {"a": account}
            )
            old = dict(
                session.execute(
                    text("SELECT * FROM iam_emergency_cases WHERE id=:i"), {"i": data["case"]}
                )
                .mappings()
                .one()
            )
            old.update(id=foreign_case, organization_id=org, account_id=account)
            session.execute(
                text(
                    "INSERT INTO iam_emergency_cases("
                    + ",".join(old)
                    + ") VALUES ("
                    + ",".join(":" + k for k in old)
                    + ")"
                ),
                old,
            )
        session.commit()
    migrate(settings, "upgrade", "head")
    if variant in ("epoch", "post_security", "post_reset", "post_master"):
        with db.session() as session:
            if variant == "post_master":
                session.execute(
                    text("DELETE FROM iam_admin_grants WHERE account_id=:a"), {"a": data["target"]}
                )
            else:
                assignment = {
                    "epoch": "trainer_role_epoch=trainer_role_epoch+2",
                    "post_security": "security_version=security_version+1",
                    "post_reset": "reset_generation=reset_generation+1",
                }[variant]
                session.execute(
                    text("UPDATE iam_accounts SET " + assignment + " WHERE id=:a"),
                    {"a": data["target"]},
                )
            session.commit()
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as actor:
        login_password(actor, data["password"], "second.master")
        route = f"/admin/master-accounts/{data['target']}/emergency-recovery"
        state = actor.get("/api/v1" + route)
        if variant == "post_master":
            assert state.status_code == 404
            with db.session() as session:
                expected = dict(
                    session.execute(
                        text(
                            "SELECT row_version,security_version,"
                            "reset_generation,password_reset_pending,"
                            "password_hash IS NOT NULL AS password_ready "
                            "FROM iam_accounts WHERE id=:a"
                        ),
                        {"a": data["target"]},
                    )
                    .mappings()
                    .one()
                )
            assert (
                call(
                    actor,
                    route + "/handoff",
                    csrf(actor),
                    {
                        "operation_id": str(uuid4()),
                        "supersedes_case_id": data["case"],
                        "expected": expected,
                        "identity_confirmed": True,
                    },
                ).status_code
                == 404
            )
            return
        assert state.status_code == 200
        body = {
            "operation_id": str(uuid4()),
            "supersedes_case_id": data["case"],
            "expected": state.json()["snapshot"],
            "identity_confirmed": True,
        }
        if variant == "foreign":
            assert (
                call(
                    actor,
                    route + "/handoff",
                    csrf(actor),
                    {**body, "supersedes_case_id": str(foreign_case)},
                ).status_code
                == 404
            )
            assert (
                call(
                    actor,
                    route + "/handoff",
                    csrf(actor),
                    {**body, "approval_origin_case_id": str(foreign_case)},
                ).status_code
                == 422
            )
        response = call(actor, route + "/handoff", csrf(actor), body)
        if variant in ("passkey", "stale", "post_security", "post_reset"):
            assert response.status_code == 409
            with db.session() as session:
                assert (
                    session.execute(
                        text("SELECT count(*) FROM iam_password_emergency_cases")
                    ).scalar_one()
                    == 0
                )
            return
        assert response.status_code == 201
        with db.session() as session:
            assert (
                session.execute(
                    text(
                        "SELECT c.expires_at=e.expires_at AND e.expires_at=s.expires_at "
                        "FROM iam_password_emergency_cases c "
                        "JOIN iam_password_emergency_credentials e "
                        "ON e.case_id=c.id JOIN iam_security_states s ON s.id=e.id"
                    )
                ).scalar_one()
                is True
            )
        if variant in ("foreign", "epoch"):
            first_token = link_token(response.json()["recipient_link"])
            followup = actor.get("/api/v1" + route).json()
            response = call(
                actor,
                route + "/handoff",
                csrf(actor),
                {
                    "operation_id": str(uuid4()),
                    "supersedes_case_id": body["operation_id"],
                    "expected": followup["snapshot"],
                    "identity_confirmed": True,
                },
            )
            assert response.status_code == 201
            with closing(TestClient(actor.app, base_url=ORIGIN)) as old_recipient:
                assert (
                    call(
                        old_recipient,
                        "/auth/emergency-recovery/inspect",
                        csrf(old_recipient),
                        {"emergency_token": first_token},
                    ).status_code
                    == 401
                )
        with closing(TestClient(actor.app, base_url=ORIGIN)) as recipient:
            assert (
                call(
                    recipient,
                    "/auth/emergency-recovery/inspect",
                    csrf(recipient),
                    {"emergency_token": data["old_token"]},
                ).status_code
                == 401
            )
            new = SyntheticSecret("Current password " + secrets.token_urlsafe(24))
            assert (
                call(
                    recipient,
                    "/auth/emergency-recovery/password/complete",
                    csrf(recipient),
                    {
                        "emergency_token": link_token(response.json()["recipient_link"]),
                        "new_password": new,
                    },
                ).status_code
                == 204
            )
            assert recipient.get("/api/v1/auth/me").status_code == 401
            login_password(recipient, new)
            assert actor.get("/api/v1/auth/me").status_code == 200
        with db.session() as session:
            row = session.execute(
                text(
                    "SELECT kind,legacy_parent_id,legacy_origin_id,legacy_origin_factors,"
                    "completed_at IS NOT NULL FROM iam_password_emergency_cases WHERE id=:i"
                ),
                {"i": body["operation_id"]},
            ).one()
            assert tuple(map(str, row[:4])) == (
                "legacy_handoff",
                data["case"],
                data["case"],
                variant if variant == "both" else "password",
            )
            assert row[4] is (variant not in ("foreign", "epoch"))


@pytest.mark.parametrize("mode", ["cooldown", "four_failures"])
def test_actual_password_login_retains_old_policy_failure_budget(
    legacy_database: tuple[Settings, Database], tmp_path: Path, mode: str
) -> None:
    settings, db = legacy_database
    data = original_lifecycle(settings, tmp_path, mode)
    migrate(settings, "upgrade", "head")
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
        with closing(TestClient(client.app, base_url=ORIGIN)) as fresh:
            login_password(fresh, data["password"], "second.master")
        if mode == "four_failures":
            login_password(client, data["password"])
            assert call(client, "/auth/logout", csrf(client), {}).status_code == 204
            assert (
                call(
                    client,
                    "/auth/login",
                    csrf(client),
                    {"login_id": "master.test", "password": "Incorrect current password"},
                ).status_code
                == 401
            )
        response = call(
            client,
            "/auth/login",
            csrf(client),
            {"login_id": "master.test", "password": data["password"]},
        )
        assert response.status_code == 429
        assert client.get("/api/v1/auth/me").status_code == 401
        with db.session() as session:
            counts = session.execute(
                text(
                    "SELECT policy_version,count(*) FROM iam_attempts "
                    "WHERE outcome='failure' GROUP BY policy_version ORDER BY policy_version"
                )
            ).all()
            assert [tuple(row) for row in counts] == (
                [(1, 5)] if mode == "cooldown" else [(1, 4), (2, 1)]
            )
