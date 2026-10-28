"""Test end-to-end de l'API FUTURA.

Usage :
    # terminal 1 — base jetable
    $env:DATABASE_URL = "sqlite:///./_test.db"
    uvicorn app.main:app --port 8099

    # terminal 2
    python tests/e2e_api.py

Aucun paquet externe : urllib suffit. Le script ne touche pas futura.db.
"""
import json
import sys
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8099"

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:  # Python < 3.7
    pass

failures = []
checks = 0


def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        BASE + path, data=data, method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")


def check(label, condition, detail=""):
    global checks
    checks += 1
    if condition:
        print(f"  OK   {label}")
    else:
        print(f"  FAIL {label} {detail}")
        failures.append(label)


def main():
    print("\n[1] Santé et profils")
    status, body = call("GET", "/health")
    check("GET /health", status == 200 and body["status"] == "ok", status)

    status, users = call("GET", "/api/users/")
    check("GET /api/users/ → 2 profils", status == 200 and len(users) == 2, users)
    names = {u["name"] for u in users} if status == 200 else set()
    check("profils Maryse + Laeticia", names == {"Maryse", "Laeticia"}, names)
    maryse = next(u for u in users if u["name"] == "Maryse")

    print("\n[2] Contenu")
    status, parcours_list = call("GET", "/api/parcours/?target=Maryse")
    check("18 parcours pour Maryse", status == 200 and len(parcours_list) == 18, len(parcours_list))

    pid = parcours_list[0]["id"]
    status, parcours = call("GET", f"/api/parcours/{pid}")
    check(f"GET /api/parcours/{pid}", status == 200 and parcours["id"] == pid, status)
    check("4 questions de carnet", len(parcours["carnet"]) == 4)
    check("4 exercices", len(parcours["exercises"]) == 4)

    status, _ = call("GET", "/api/parcours/inconnu_xyz")
    check("parcours inconnu → 404", status == 404, status)

    print("\n[3] Progression par étape")
    status, progress = call("GET", f"/api/parcours/{pid}/progress?user_id={maryse['id']}")
    check("progression initiale vide", status == 200 and progress["etapes"] == [], progress)

    for etape in (1, 2, 3):
        status, body = call("PATCH", f"/api/parcours/{pid}/etape",
                            {"user_id": maryse["id"], "etape": etape})
        check(f"étape {etape} enregistrée", status == 200 and etape in body["etapes"], body)

    status, body = call("PATCH", f"/api/parcours/{pid}/etape",
                        {"user_id": maryse["id"], "etape": 9})
    check("étape invalide → 400", status == 400, status)

    print("\n[4] Carnet PISA")
    reponses = {q["process"]: f"réponse {q['process']}" for q in parcours["carnet"]}
    status, body = call("PATCH", f"/api/parcours/{pid}/carnet",
                        {"user_id": maryse["id"], "reponses": reponses})
    check("carnet enregistré → étape 4", status == 200 and 4 in body["etapes"], body)

    status, progress = call("GET", f"/api/parcours/{pid}/progress?user_id={maryse['id']}")
    check("carnet relu depuis l'API",
          progress["carnet"].get("formular") == reponses["formular"], progress["carnet"])
    check("4 étapes validées", progress["etapes"] == [1, 2, 3, 4], progress["etapes"])

    print("\n[5] Exercices")
    status, body = call("POST", f"/api/parcours/{pid}/exercice",
                        {"user_id": maryse["id"], "exercise_id": parcours["exercises"][0]["id"],
                         "response": "réponse fausse zzz"})
    check("mauvaise réponse rejetée", status == 200 and body["correct"] is False, body)

    for ex in parcours["exercises"]:
        status, body = call("POST", f"/api/parcours/{pid}/exercice",
                            {"user_id": maryse["id"], "exercise_id": ex["id"],
                             "response": ex["expected_answer"]})
        check(f"exercice {ex['level']} accepté", status == 200 and body["correct"] is True, body)

    status, progress = call("GET", f"/api/parcours/{pid}/progress?user_id={maryse['id']}")
    check("étape 5 validée automatiquement", 5 in progress["etapes"], progress["etapes"])

    print("\n[6] Complétion et XP")
    status, body = call("POST", f"/api/parcours/{pid}/complete",
                        {"user_id": maryse["id"],
                         "metacognition": {"facil": "todo", "dificil": "nada", "diferente": "más"}})
    check("parcours complété", status == 200 and body["status"] == "completed", body)
    check(f"XP attribués ({parcours['xp_reward']})", body["xp_earned"] == parcours["xp_reward"], body)

    status, body2 = call("POST", f"/api/parcours/{pid}/complete",
                         {"user_id": maryse["id"], "metacognition": {}})
    check("double complétion sans double XP", body2["status"] == "already_completed", body2)

    status, summary = call("GET", f"/api/users/{maryse['id']}/summary")
    check("résumé : 1 parcours terminé", summary["parcours_done"] == 1, summary)
    check("résumé : XP à jour", summary["xp"] == parcours["xp_reward"], summary)
    check("badge Exploradora gagné",
          any(b["id"] == "exploradora" for b in summary["badges"]), summary["badges"])

    print("\n[7] Sœur et bien-être")
    status, sisters = call("GET", f"/api/users/{maryse['id']}/sisters")
    check("stats de la sœur", status == 200 and sisters["sister"]["name"] == "Laeticia", sisters)

    status, _ = call("POST", f"/api/wellbeing/{maryse['id']}",
                     {"sleep_hours": 8, "movement_minutes": 30, "mood": "feliz", "focus_level": 4})
    check("bien-être enregistré", status == 200, status)
    status, wb = call("GET", f"/api/wellbeing/{maryse['id']}")
    check("bien-être relu", wb.get("sleep_hours") == 8 and wb.get("mood") == "feliz", wb)

    print("\n[8] Pages et assets")
    for path in ("/", "/static/index.html", "/static/theme.css", "/static/app.js",
                 "/static/parcours_template.html", "/static/progreso.html",
                 "/static/hermanas.html", "/static/laboratorio.html",
                 "/static/manifest.json", "/sw.js",
                 "/static/icons/icon-192.png", "/static/icons/icon-512.png"):
        req = urllib.request.Request(BASE + path, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                check(f"GET {path}", resp.status == 200, resp.status)
        except urllib.error.HTTPError as exc:
            check(f"GET {path}", False, exc.code)

    print(f"\n{'=' * 60}")
    print(f"{checks - len(failures)}/{checks} vérifications réussies")
    if failures:
        print("Échecs : " + ", ".join(failures))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
