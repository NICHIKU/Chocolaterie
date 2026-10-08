import json, os
import db
import llm

with open(os.path.join(os.path.dirname(__file__), "data", "catalog.json"), encoding="utf-8") as f:
    CATALOG = json.load(f)

SYSTEM_PROMPT = """Tu es Clémence, conseillère à la Maison Delcourt, chocolatier artisanal à Lille.
Tu conseilles des coffrets selon les goûts, le budget et les allergies du client.
Réponds toujours en français, de façon chaleureuse, détaillée et complète, en présentant plusieurs options.
Ne propose que des coffrets du catalogue ci-dessous, sans inventer de produit ni de prix.
Si la question n'a aucun rapport avec nos chocolats, ramène poliment la conversation vers eux.
Voici notre catalogue complet : """ + json.dumps(CATALOG, ensure_ascii=False)


def customer_context(customer):
    """Décrit au LLM ce que le client a enregistré dans le formulaire."""
    if not any(customer.get(k) for k in ["name", "email", "allergies", "children_ages"]):
        return "\n\nInformations enregistrées sur le client : aucune."
    lines = ["\n\nInformations enregistrées sur le client (saisies par lui dans le formulaire) :"]
    if customer.get("name"):
        lines.append(f"- Nom : {customer['name']}")
    if customer.get("email"):
        lines.append(f"- Email : {customer['email']}")
    if customer.get("allergies"):
        lines.append(f"- Allergies : {customer['allergies']}")
    if customer.get("children_ages"):
        lines.append(f"- Âge des enfants : {customer['children_ages']}")
    lines.append("Appelle le client par son prénom, tiens compte de ces informations et réponds à toute question le concernant.")
    return "\n".join(lines)


def handle_chat(session_id, message):
    db.save_message(session_id, "user", message)
    customer = db.get_customer(session_id)
    print(f"[chat] {customer} : {message}")

    system = SYSTEM_PROMPT + customer_context(customer)
    messages = [{"role": "system", "content": system}] + db.get_history(session_id)

    try:
        reply, usage = llm.chat(llm.BIG_MODEL, messages, max_tokens=1500)
    except Exception:
        reply = "Désolé, une erreur est survenue. Réessayez plus tard."

    db.save_message(session_id, "assistant", reply)
    return {"reply": reply}
