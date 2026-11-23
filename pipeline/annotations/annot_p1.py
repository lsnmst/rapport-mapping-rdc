"""Annotazione manuale (lettura del testo) dei luoghi del periodo 1.
ruolo: evento | riferimento | contenitore | origine | destinazione
ambito: puntuale | multi-sito | itinerario | areale | provinciale
rel: relazione spaziale dichiarata nel testo (distanza_km, da, verso | direzione)
"""
E, R, C, O, D = "evento", "riferimento", "contenitore", "origine", "destinazione"


def P(nome, ruolo, tipo, dentro=None, rel=None, nota=None, principale=False):
    d = {"nome": nome, "ruolo": ruolo, "tipo": tipo}
    if dentro: d["dentro"] = dentro
    if rel: d["rel"] = rel
    if nota: d["nota"] = nota
    if principale: d["principale"] = True
    return d


KOL = [{"nome": "Kolwezi", "tipo": "ville"}]
MAS = [{"nome": "Masisi", "tipo": "territoire"}]
RUT = [{"nome": "Rutshuru", "tipo": "territoire"}]
KIN = [{"nome": "Kinshasa", "tipo": "ville"}]

A = {
 "P1-001": ("multi-sito", [
    P("Kolwezi", E, "ville", nota="uccisioni nei quartieri periferici", principale=True),
    P("Musonoie", E, "cité", dentro=KOL, rel={"distanza_km": 3, "da": "Kolwezi", "verso": "Kapata"},
      nota="scontro FAZ-JUFERI"),
    P("Kapata", R, "localité")]),
 "P1-002": ("puntuale", [
    P("Kolwezi", E, "ville", principale=True),
    P("rivière Mutshinsenge", E, "rivière", dentro=KOL, nota="uccisioni di donne lungo il fiume")]),
 "P1-003": ("puntuale", [P("gare de Kolwezi", E, "gare", dentro=KOL, principale=True)]),
 "P1-004": ("puntuale", [P("gare de Kolwezi", E, "gare", dentro=KOL, principale=True)]),
 "P1-005": ("puntuale", [P("Kolwezi", E, "ville", nota="luoghi di raccolta dei refoulés (dal paragrafo di contesto)",
                           principale=True)]),
 "P1-006": ("itinerario", [
    P("Kolwezi", O, "ville"), P("Luena", E, "ville", nota="gare"), P("Kamina", E, "ville", nota="gare"),
    P("Mwene Ditu", D, "ville"), P("Mbuji-Mayi", D, "ville"), P("Kananga", D, "ville")]),
 "P1-007": ("puntuale", [P("Likasi", E, "ville", principale=True)]),
 "P1-008": ("puntuale", [P("Kipushi", E, "ville", nota="dal paragrafo di contesto", principale=True)]),
 "P1-009": ("multi-sito", [P(n, E, "ville", principale=(n == "Lubumbashi")) for n in
                           ["Lubumbashi", "Likasi", "Kolwezi", "Kambove", "Luena"]]),
 "P1-010": ("multi-sito", [
    P("Ntoto", E, "village", nota="mercato; al confine tra i territori di Walikale e Masisi", principale=True,
      dentro=[{"nome": "Walikale", "tipo": "territoire"}, {"nome": "Masisi", "tipo": "territoire"}]),
    P("Buoye", E, "village", rel={"vicino_a": "Ntoto"}),
    P("rivière Lowa", E, "rivière", nota="annegamenti durante la fuga"),
    P("Walikale", C, "territoire"), P("Masisi", C, "territoire")]),
 "P1-011": ("puntuale", [
    P("Kambule", E, "quartier", dentro=[{"nome": "Katoyi", "tipo": "village"}] + MAS, principale=True),
    P("Katoyi", C, "village", dentro=MAS)]),
 "P1-012": ("puntuale", [P("Mulinde", E, "village", dentro=MAS, principale=True)]),
 "P1-013": ("puntuale", [
    P("Ngingwe", E, "village", dentro=[{"nome": "Bashali", "tipo": "chefferie"}] + MAS,
      nota="nel nord-est del territorio di Masisi", principale=True)]),
 "P1-014": ("multi-sito", [
    P("Kiusha", E, "village", dentro=[{"nome": "Bashali", "tipo": "chefferie"}] + MAS, principale=True),
    P("Muhongozi", E, "village", dentro=MAS)]),
 "P1-015": ("multi-sito", [
    P("Binza", E, "village", dentro=MAS, nota="nel nord del territorio di Masisi", principale=True),
    P("Kalembe", E, "village", dentro=MAS, rel={"vicino_a": "Binza"})]),
 "P1-016": ("puntuale", [
    P("Kibachiro", E, "village", dentro=[{"nome": "Karobe", "tipo": "colline"}] + MAS, principale=True),
    P("Karobe", C, "colline")]),
 "P1-017": ("puntuale", [
    P("camp de Mugunga", E, "camp", rel={"distanza_km": "qualche", "da": "Goma"}, principale=True),
    P("Goma", R, "ville")]),
 "P1-018": ("puntuale", [P("Mutobo", E, "village", dentro=MAS, principale=True)]),
 "P1-019": ("puntuale", [P("Bikenge", E, "village", dentro=MAS, principale=True)]),
 "P1-020": ("areale", [
    P("Goma", E, "ville", principale=True), P("Rutshuru", E, "territoire"), P("Masisi", E, "territoire"),
    P("Lubero", E, "territoire")]),
 "P1-021": ("puntuale", [
    P("ferme d'Osso", E, "ferme", dentro=MAS,
      rel={"distanza_km": 40, "da": "Goma", "direzione": "nord-ouest"}, principale=True),
    P("Goma", R, "ville")]),
 "P1-022": ("multi-sito", [
    P("Bukombo", E, "village", dentro=RUT, principale=True),
    P("paroisse de Birambizu", E, "paroisse", dentro=RUT, nota="nuovi attacchi nelle settimane seguenti")]),
 "P1-023": ("puntuale", [
    P("monastère de Mokoto", E, "monastère", dentro=MAS, nota="nel nord-est del territorio di Masisi",
      principale=True),
    P("Kitchanga", D, "localité", nota="rifugio dei sopravvissuti")]),
 "P1-024": ("multi-sito", [
    P("Bunagana", E, "localité", dentro=RUT, nota="dintorni", principale=True),
    P("Jomba", E, "localité", dentro=RUT, nota="dintorni"),
    P("Chengerero", E, "village", dentro=RUT, rel={"distanza_km": 10, "da": "Bunagana"}),
    P("camp de Katale", O, "camp", nota="provenienza degli aggressori"),
    P("camp de Mugunga", O, "camp", nota="provenienza degli aggressori")]),
 "P1-025": ("puntuale", [
    P("Masisi", E, "localité", nota="il centro di Masisi e i villaggi vicini", principale=True),
    P("Bikenge", R, "village", nota="rimando all'incidente P1-019")]),
 "P1-026": ("puntuale", [P("Vitshumbi", E, "village", dentro=RUT, principale=True)]),
 "P1-027": ("puntuale", [P("Vitshumbi", E, "village", dentro=RUT, principale=True)]),
 "P1-028": ("puntuale", [P("Kibirizi", E, "village", dentro=[{"nome": "Bwito", "tipo": "chefferie"}] + RUT,
                           principale=True)]),
 "P1-029": ("puntuale", [P("Kanyabayonga", E, "village", dentro=[{"nome": "Lubero", "tipo": "territoire"}],
                           principale=True)]),
 "P1-030": ("puntuale", [
    P("Kitchanga", E, "localité", nota="campi nei dintorni; all'incrocio dei territori di Masisi, Walikale e Lubero",
      principale=True)]),
 "P1-031": ("puntuale", [P("Kinshasa", E, "ville", principale=True)]),
 "P1-032": ("puntuale", [P("camp Tshatshi", E, "camp militaire", dentro=KIN, principale=True)]),
 "P1-033": ("multi-sito", [
    P("Maluku", E, "quartier", dentro=[{"nome": "Nsele", "tipo": "commune"}] + KIN, principale=True),
    P("Mangengenge", E, "centre de formation", dentro=KIN, nota="detenzione presso la Garde civile"),
    P("fleuve Congo", E, "fleuve", nota="corpi gettati nel fiume")]),
 "P1-034": ("multi-sito", [
    P("Kinshasa", E, "ville", nota="manifestazione", principale=True),
    P("Limete", E, "commune", dentro=KIN, nota="residenza di Antoine Gizenga, sede del PALU"),
    P("camp Kokolo", E, "camp militaire", dentro=KIN, nota="detenzione")]),
 "P1-035": ("puntuale", [P("Luozi", E, "localité", principale=True)]),
 "P1-036": ("provinciale", [P("Bas-Zaïre", E, "province", nota="oggi Kongo-Central", principale=True)]),
 "P1-037": ("provinciale", [P("Orientale", E, "province", principale=True)]),
 "P1-038": ("provinciale", [P("Orientale", E, "province", principale=True)]),
 "P1-039": ("puntuale", [P("Kampene", E, "localité", dentro=[{"nome": "Pangi", "tipo": "territoire"}],
                           nota="mercato", principale=True)]),
 "P1-040": ("puntuale", [
    P("Tchoko", E, "village", dentro=[{"nome": "Kailo", "tipo": "territoire"}],
      rel={"vicino_a": "Kindu"}, principale=True),
    P("Kindu", R, "ville")]),
 "P1-041": ("puntuale", [P("Kananga", E, "ville", principale=True)]),
}

if __name__ == "__main__":
    import json, sys
    src = json.load(open(sys.argv[1]))
    for inc in src["incidents"]:
        ambito, luoghi = A[inc["id"]]
        inc["ambito"] = ambito
        inc["luoghi"] = luoghi
        inc.pop("places", None); inc.pop("territoire_hint", None); inc.pop("chefferie_hint", None)
    src["schema"] = __doc__
    json.dump(src, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
    from collections import Counter
    print(Counter(i["ambito"] for i in src["incidents"]))
    print(Counter(l["ruolo"] for i in src["incidents"] for l in i["luoghi"]))
