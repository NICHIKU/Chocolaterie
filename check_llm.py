"""Vérifie qu'Ollama répond avec le modèle configuré. Usage : python check_llm.py"""
import time
import llm

print(f"Modèle : {llm.BIG_MODEL} | serveur : {llm.BASE_URL}")
print("(la première réponse est plus longue : le modèle se charge en mémoire)")
t = time.time()
try:
    text, usage = llm.chat(llm.BIG_MODEL, [{"role": "user", "content": "Dis bonjour en une phrase, en français."}], max_tokens=60)
    print("Réponse :", text)
    print("Usage   :", usage, f"| {time.time() - t:.1f} s")
except Exception as e:
    print("ERREUR :", e)
    print("Ollama est-il lancé (icône de lama près de l'horloge) ? Le modèle est-il téléchargé (ollama list) ?")
