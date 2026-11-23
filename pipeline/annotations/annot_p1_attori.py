"""Annotazione manuale di autori, vittime e violazioni per il periodo 1.

Ogni incidente ha una lista di "atti": chi (autori), contro chi (vittime), che cosa (violazioni), quanti (numero).
- autori: id dal registro ATTORI; ruolo = autore | sostegno (es. "soutenus par des FAZ")
- vittime: gruppo come lo descrive il rapporto; identita = appartenenze dichiarate nel testo (etniche, nazionali,
  politiche, religiose, professionali); condizione = civili | sfollati | rifugiati | refoulés | militanti |
  combattenti | militari; categorie = donne, bambini, anziani, disabili, donne incinte, minori...
- numero: min/max come numeri; testo = formula del rapporto; precisione = esatto | minimo | intervallo |
  approssimato | ordine_di_grandezza | indeterminato
- certezza: affermato | condizionale (auraient, selon certaines sources) | sospetto | antefatto (evento richiamato
  come contesto, non oggetto dell'incidente)
Il rapporto descrive tutti gli incidenti come "presunti": la certezza qui registra solo le formule del testo.
Nessuna qualificazione giuridica per incidente: il rapporto la fa solo in forma aggregata (cap. V).
"""

ATTORI = {
    "JUFERI": {"fr": "JUFERI (Jeunesse de l'UFERI)", "en": "JUFERI (UFERI youth wing)", "tipo": "milizia di partito"},
    "UFERI": {"fr": "UFERI", "en": "UFERI", "tipo": "partito politico"},
    "FAZ": {"fr": "Forces armées zaïroises (FAZ)", "en": "Zairian Armed Forces (FAZ)", "tipo": "forze statali"},
    "DSP": {"fr": "Division spéciale présidentielle (DSP)", "en": "Special Presidential Division (DSP)",
            "tipo": "forze statali"},
    "GARDE_CIVILE": {"fr": "Garde civile", "en": "Civil Guard", "tipo": "forze statali"},
    "GENDARMERIE": {"fr": "Gendarmerie", "en": "Gendarmerie", "tipo": "forze statali"},
    "SNIP": {"fr": "SNIP", "en": "SNIP", "tipo": "servizi di sicurezza statali"},
    "BSRS": {"fr": "BSRS", "en": "BSRS", "tipo": "forze statali"},
    "FORCES_SECURITE_ZAIROISES": {"fr": "Forces de sécurité zaïroises", "en": "Zairian security forces",
                                  "tipo": "forze statali (non specificate)"},
    "AUTORITES_PROVINCIALES": {"fr": "Gouverneur et autorités locales", "en": "Governor and local authorities",
                               "tipo": "autorità civili"},
    "ENTREPRISE_PUBLIQUE": {"fr": "Régie des voies maritimes", "en": "Régie des voies maritimes",
                            "tipo": "impresa pubblica"},
    "POPULATION_LOCALE": {"fr": "Population locale", "en": "Local population", "tipo": "civili"},
    "MOBILES": {"fr": "« Mobiles »", "en": "\"Mobiles\"", "tipo": "gruppo di refoulés (vedi nota 99 del rapporto)"},
    "MAYI_MAYI_HUNDE_NYANGA": {"fr": "Mayi-Mayi hunde et nyanga", "en": "Hunde and Nyanga Mayi-Mayi",
                               "tipo": "gruppo armato"},
    "ELEMENTS_ARMES_HUTU": {"fr": "Éléments armés / miliciens hutu", "en": "Armed Hutu elements / militias",
                            "tipo": "gruppo armato"},
    "EX_FAR_INTERAHAMWE": {"fr": "Ex-FAR/Interahamwe", "en": "Ex-FAR/Interahamwe", "tipo": "gruppo armato straniero"},
    "ELEMENTS_ARMES_NANDE": {"fr": "Éléments armés nande (Ngilima)", "en": "Armed Nande elements (Ngilima)",
                             "tipo": "gruppo armato"},
    "ARMEE_RWANDAISE": {"fr": "Militaires rwandais", "en": "Rwandan soldiers", "tipo": "esercito straniero"},
    "ARMEE_OUGANDAISE": {"fr": "Militaires ougandais", "en": "Ugandan soldiers", "tipo": "esercito straniero"},
    "NON_SPECIFICATO": {"fr": "Non précisé", "en": "Not specified", "tipo": "non specificato"},
}


def A(autori, vittime, violazioni, numero=None, certezza="affermato", nota=None):
    au = [{"id": a, "ruolo": "autore"} if isinstance(a, str) else {"id": a[0], "ruolo": a[1]} for a in autori]
    d = {"autori": au, "vittime": vittime, "violazioni": violazioni, "certezza": certezza}
    if numero: d["numero"] = numero
    if nota: d["nota"] = nota
    return d


def V(gruppo, identita=(), condizione="civili", categorie=()):
    return {"gruppo": gruppo, "identita": list(identita), "condizione": condizione, "categorie": list(categorie)}


def N(testo, precisione, min=None, max=None, tipo="uccisi"):
    return {"testo": testo, "precisione": precisione, "min": min, "max": max, "tipo": tipo}


IND = lambda tipo="uccisi": N("nombre indéterminé", "indeterminato", tipo=tipo)
KAS = lambda cond="civili", cat=(): V("civils kasaïens", ["kasaïens"], cond, cat)
REF = lambda cat=(): V("refoulés kasaïens", ["kasaïens"], "refoulés", cat)

ATTI = {
 "P1-001": [A(["JUFERI"], KAS(), ["uccisione", "sfollamento_forzato"], IND()),
            A(["JUFERI"], KAS(), ["restrizione_movimento"], nota="divieto di accesso ai siti Gécamines; coprifuoco"),
            ],
 "P1-002": [A(["JUFERI"], KAS(), ["minaccia", "sfollamento_forzato", "uccisione"], IND(),
              nota="ordine di lasciare le case sotto minaccia di morte e incendio"),
            A(["JUFERI"], KAS(), ["sfollamento_forzato"], N("plus de 50 000", "minimo", 50000, tipo="sfollati")),
            A(["JUFERI"], KAS(), ["uccisione"], IND(), nota="ai posti di blocco durante i controlli d'identità"),
            A(["JUFERI"], KAS(), ["uccisione"], N("deux personnes au moins", "minimo", 2)),
            A(["JUFERI"], V("femmes kasaïennes", ["kasaïens"], "civili", ["donne"]), ["uccisione"], IND(),
              nota="fiume Mutshinsenge")],
 "P1-003": [A(["JUFERI"], V("civils du groupe des Mobiles", ["kasaïens"], "refoulés"), ["uccisione"],
              N("trois civils", "esatto", 3, 3)),
            A(["MOBILES"], V("civil katangais", ["katangais"]), ["uccisione"], N("un civil", "esatto", 1, 1),
              nota="rappresaglia")],
 "P1-004": [A(["FAZ"], REF(["anziani", "disabili"]), ["distruzione_incendio", "uccisione"],
              N("au moins une personne âgée et un nombre indéterminé d'handicapés", "minimo", 1),
              nota="un alto ufficiale delle FAZ (non nominato); morti bruciati vivi")],
 "P1-005": [A(["NON_SPECIFICATO"], REF(["bambini"]), ["decessi_per_privazioni"],
              N("des dizaines ; entre 7 et 20 décès par jour", "ordine_di_grandezza", tipo="morti"),
              nota="il paragrafo di contesto attribuisce i decessi alle condizioni imposte dalle autorità")],
 "P1-006": [A(["JUFERI"], REF(["bambini"]), ["attacco_convogli", "decessi_durante_trasferimento",
                                             "negazione_assistenza"],
              N("94 civils kasaïens seraient décédés", "esatto", 94, 94, tipo="morti"), certezza="condizionale",
              nota="94 morti per incidenti di trasporto secondo il comitato dei refoulés; la maggior parte dei "
                   "decessi attribuita a condizioni del viaggio e attacchi ai treni")],
 "P1-007": [A(["JUFERI"], V("Kasaïens travaillant à la Gécamines", ["kasaïens"], "civili"),
              ["persecuzione", "sfollamento_forzato", "uccisione"], IND(tipo="morti"))],
 "P1-008": [A(["JUFERI"], V("civils kasaïens travaillant à la Gécamines", ["kasaïens"]),
              ["persecuzione", "uccisione", "ferimento", "distruzione_beni"],
              N("au moins trois civils", "minimo", 3), nota="500 elementi della JUFERI; feriti in numero indeterminato")],
 "P1-009": [A(["GARDE_CIVILE"], V("éléments de la JUFERI", ["UFERI"], "militanti"), ["uccisione", "ferimento"],
              N("deux tués, au moins sept blessés", "esatto", 2, 2)),
            A(["GARDE_CIVILE", "SNIP"], V("membres de l'UFERI et de la JUFERI", ["UFERI"], "militanti"),
              ["uso_della_forza_letale", "tortura"], N("plusieurs dizaines", "ordine_di_grandezza", tipo="vittime"))],
 "P1-010": [A(["MAYI_MAYI_HUNDE_NYANGA"], V("paysans banyarwanda hutu", ["banyarwanda", "hutu"]), ["uccisione"],
              N("des dizaines", "ordine_di_grandezza"), nota="mercato di Ntoto"),
            A(["MAYI_MAYI_HUNDE_NYANGA"], V("Banyarwanda", ["banyarwanda", "hutu"]), ["uccisione"],
              N("des dizaines", "ordine_di_grandezza"), nota="Buoye, all'uscita dalle chiese; molti annegati nella fuga")],
 "P1-011": [A(["MAYI_MAYI_HUNDE_NYANGA"], V("civils hutu", ["hutu"]), ["uccisione", "distruzione_incendio"], IND(),
              nota="il testo indica Mayi-Mayi hunde")],
 "P1-012": [A(["ELEMENTS_ARMES_HUTU"], V("civils hunde", ["hunde"], "civili", ["bambini"]), ["uccisione"],
              N("au moins douze", "minimo", 12))],
 "P1-013": [A(["ELEMENTS_ARMES_HUTU"], V("personnes, pour la plupart des Hunde", ["hunde"]), ["uccisione"],
              N("une cinquantaine", "approssimato", 50, 50))],
 "P1-014": [A(["ELEMENTS_ARMES_HUTU"], V("civils"), ["distruzione_incendio", "attacco_scuola", "attacco_sanita"],
              nota="Kiusha: scuola primaria e posto di salute"),
            A(["ELEMENTS_ARMES_HUTU"], V("civils"), ["distruzione_incendio", "attacco_luogo_di_culto", "uccisione"],
              IND(), nota="Muhongozi: chiesa")],
 "P1-015": [A(["ELEMENTS_ARMES_HUTU", ("FAZ", "sostegno")],
              V("majorité de Hunde, trois Hutu", ["hunde", "hutu"], "civili", ["donne incinte"]),
              ["uccisione", "mutilazione"], N("au moins 48", "minimo", 48)),
            A(["ELEMENTS_ARMES_HUTU", ("FAZ", "sostegno")], V("habitants de villages voisins"), ["attacco_villaggi"],
              nota="Kalembe e altri villaggi nei dintorni di Binza")],
 "P1-016": [A(["ELEMENTS_ARMES_HUTU"], V("déplacés hunde", ["hunde"], "sfollati", ["donne", "bambini"]),
              ["uccisione"], N("au moins 38", "minimo", 38))],
 "P1-017": [A(["FAZ"], V("réfugiés rwandais", ["rwandais"], "rifugiati"),
              ["rimpatrio_forzato", "saccheggio", "distruzione_incendio"],
              N("plusieurs milliers", "ordine_di_grandezza", tipo="rimpatriati"))],
 "P1-018": [A(["ELEMENTS_ARMES_HUTU"], V("Hunde", ["hunde"]), ["uccisione"], N("une quarantaine", "approssimato", 40, 40),
              nota="tra le vittime un capo consuetudinario (nominato nel rapporto)")],
 "P1-019": [A(["MAYI_MAYI_HUNDE_NYANGA"], V("Hutu", ["hutu"]), ["uccisione"], N("entre 26 et 30", "intervallo", 26, 30),
              nota="il testo indica elementi armati hunde (Mayi-Mayi)"),
            A(["MAYI_MAYI_HUNDE_NYANGA"], V("militaires des FAZ", [], "militari"), ["uccisione"],
              N("quatre", "esatto", 4, 4), nota="vittime militari; movente di vendetta al condizionale")],
 "P1-020": [A(["FORCES_SECURITE_ZAIROISES"], V("Tutsi", ["tutsi"]), ["espulsione_forzata"], IND(tipo="espulsi"),
              nota="verso il Rwanda"),
            A(["FORCES_SECURITE_ZAIROISES", "POPULATION_LOCALE"], V("Tutsi", ["tutsi"]), ["trattamenti_inumani"]),
            A(["FORCES_SECURITE_ZAIROISES"], V("Tutsi", ["tutsi"]), ["saccheggio", "requisizione_beni"])],
 "P1-021": [A(["MAYI_MAYI_HUNDE_NYANGA"], V("civils tutsi déplacés", ["tutsi"], "sfollati"), ["uccisione", "saccheggio"],
              N("au moins 18", "minimo", 18), nota="il testo indica Mayi-Mayi hunde")],
 "P1-022": [A(["ELEMENTS_ARMES_HUTU", "EX_FAR_INTERAHAMWE"], V("Banyarwanda tutsi", ["banyarwanda", "tutsi"]),
              ["uccisione", "saccheggio", "distruzione_incendio"], N("une dizaine", "approssimato", 10, 10),
              nota="alcune vittime bruciate vive"),
            A(["NON_SPECIFICATO"], V("rescapés", ["tutsi"], "sfollati"), ["attacco"],
              nota="nuovi attacchi alla parrocchia di Birambizu; autori non precisati nel testo")],
 "P1-023": [A(["ELEMENTS_ARMES_HUTU"], V("déplacés hunde et tutsi", ["hunde", "tutsi"], "sfollati"),
              ["uccisione", "attacco_luogo_di_culto"], N("plusieurs dizaines", "ordine_di_grandezza"))],
 "P1-024": [A(["ELEMENTS_ARMES_HUTU", "EX_FAR_INTERAHAMWE"], V("civils tutsi", ["tutsi"]), ["uccisione"],
              N("des dizaines", "ordine_di_grandezza"),
              nota="aggressori provenienti dai campi di Katale e Mugunga; tra le vittime un funzionario locale"),
            A(["ARMEE_RWANDAISE", "ARMEE_OUGANDAISE"], V("civils banyarwanda hutu", ["banyarwanda", "hutu"]),
              ["uccisione"], N("au moins une vingtaine", "minimo", 20), certezza="antefatto",
              nota="attacco a Bunagana alcuni giorni prima; attribuzione chiarita dalla versione inglese")],
 "P1-025": [A(["FAZ", "ELEMENTS_ARMES_HUTU"], V("civils, pour la plupart hunde", ["hunde"]),
              ["uccisione", "saccheggio", "distruzione_incendio", "attacco_scuola"],
              N("des dizaines", "ordine_di_grandezza"), nota="movente di rappresaglia al condizionale")],
 "P1-026": [A(["ELEMENTS_ARMES_NANDE"], V("Banyarwanda hutu", ["banyarwanda", "hutu"]), ["uccisione"],
              N("au moins quatre", "minimo", 4), nota="coinvolgimento della Ngilima secondo alcune fonti")],
 "P1-027": [A(["FAZ"], V("civils accusés de soutenir la Ngilima"), ["uccisione", "detenzione_arbitraria", "saccheggio"],
              IND(), nota="operazione Mbata; tra le vittime un pastore; popolazione rinchiusa due giorni nelle chiese")],
 "P1-028": [A(["FAZ"], V("civils"), ["uccisione", "bombardamento_indiscriminato", "distruzione_incendio"],
              N("plus de 120", "minimo", 120))],
 "P1-029": [A(["FAZ"], V("éléments armés nande ou civils suspectés de les soutenir", ["nande"], "civili e combattenti"),
              ["uccisione", "bombardamento_indiscriminato", "distruzione_incendio"], N("plus d'une centaine", "minimo", 100))],
 "P1-030": [A(["ELEMENTS_ARMES_HUTU"], V("civils hunde", ["hunde"]), ["sparizione_forzata"],
              N("deux", "esatto", 2, 2, tipo="scomparsi"), certezza="sospetto",
              nota="la popolazione sospetta le milizie hutu")],
 "P1-031": [A(["FORCES_SECURITE_ZAIROISES"],
              V("opposants politiques, syndicalistes, journalistes", ["opposizione politica"], "civili"),
              ["arresto_arbitrario", "tortura"], N("plus de 20", "minimo", 20, tipo="vittime"))],
 "P1-032": [A(["FORCES_SECURITE_ZAIROISES", "BSRS"], V("manifestants de l'opposition", ["opposizione politica"]),
              ["rapimento", "esecuzione_sommaria"], N("15 personnes", "esatto", 15, 15)),
            A(["FORCES_SECURITE_ZAIROISES", "BSRS"], V("manifestants de l'opposition", ["opposizione politica"]),
              ["rapimento", "detenzione_arbitraria"], N("cinq", "esatto", 5, 5, tipo="detenuti"),
              nota="trasferiti alla CIRCO, poi liberati")],
 "P1-033": [A(["GARDE_CIVILE", "BSRS"], V("militants de l'UDPS", ["UDPS"], "militanti"),
              ["rapimento", "esecuzione_sommaria", "occultamento_cadaveri"], N("six", "esatto", 6, 6)),
            A(["FORCES_SECURITE_ZAIROISES"], V("militants de l'UDPS", ["UDPS"], "militanti", ["minori"]),
              ["uccisione"], N("plusieurs", "indeterminato"), nota="1993-1994, operazioni di repressione")],
 "P1-034": [A(["GARDE_CIVILE", "GENDARMERIE"], V("militants du PALU", ["PALU"], "militanti"),
              ["uccisione", "ferimento", "arresto_arbitrario"], N("au moins sept", "minimo", 7),
              nota="una ventina di feriti; arresti in numero indeterminato"),
            A(["GARDE_CIVILE", "GENDARMERIE"], V("femmes et militants du PALU", ["PALU"], "civili", ["donne"]),
              ["violenza_sessuale", "percosse", "saccheggio"], IND(tipo="vittime"),
              nota="residenza del presidente del partito, Limete")],
 "P1-035": [A(["ENTREPRISE_PUBLIQUE"], V("employés « non originaires »", ["non originaires"]),
              ["licenziamento_discriminatorio"], N("plusieurs", "indeterminato", tipo="licenziati")),
            A(["POPULATION_LOCALE"], V("magistrats « non originaires »", ["non originaires"]),
              ["espulsione_forzata"], N("deux", "esatto", 2, 2, tipo="espulsi"))],
 "P1-036": [A(["FORCES_SECURITE_ZAIROISES"],
              V("familles « non originaires » (Baluba des Kasaï, Bangala de l'Équateur)",
                ["non originaires", "baluba", "bangala"]),
              ["espulsione_forzata"], N("14 familles", "esatto", 14, 14, tipo="famiglie espulse"))],
 "P1-037": [A(["AUTORITES_PROVINCIALES"], V("ressortissants des Kasaï (magistrats, dirigeant UDPS)",
                                            ["kasaïens", "UDPS"], "civili"),
              ["sospensione_arbitraria", "espulsione_forzata"], N("plusieurs", "indeterminato", tipo="vittime"))],
 "P1-038": [A(["FORCES_SECURITE_ZAIROISES", ("AUTORITES_PROVINCIALES", "mandante")],
              V("intellectuels et membres du clergé accusés de soutenir l'opposition", ["opposizione politica"]),
              ["perquisizione_arbitraria"], IND(tipo="vittime"), nota="su ordine del Governatore")],
 "P1-039": [A(["GARDE_CIVILE"], V("femmes", [], "civili", ["donne"]), ["violenza_sessuale", "saccheggio"],
              IND(tipo="vittime"))],
 "P1-040": [A(["GARDE_CIVILE"], V("femmes", [], "civili", ["donne"]), ["violenza_sessuale", "saccheggio"],
              IND(tipo="vittime"))],
 "P1-041": [A(["DSP"], V("civils dont un prêtre catholique", ["clero cattolico"]), ["uccisione", "saccheggio"],
              N("six civils", "esatto", 6, 6), nota="saccheggio di istituzioni cattoliche e negozi")],
}

if __name__ == "__main__":
    import json, sys
    from collections import Counter
    src = json.load(open(sys.argv[1]))
    for inc in src["incidents"]:
        inc["atti"] = ATTI[inc["id"]]
    src["attori"] = ATTORI
    src["schema_atti"] = __doc__
    json.dump(src, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
    allv = Counter(v for i in src["incidents"] for a in i["atti"] for v in a["violazioni"])
    allA = Counter(x["id"] for i in src["incidents"] for a in i["atti"] for x in a["autori"])
    prec = Counter(a.get("numero", {}).get("precisione", "—") for i in src["incidents"] for a in i["atti"])
    cert = Counter(a["certezza"] for i in src["incidents"] for a in i["atti"])
    print("atti:", sum(len(i["atti"]) for i in src["incidents"]))
    print("autori:", dict(allA.most_common()))
    print("violazioni:", dict(allv.most_common()))
    print("precisione numeri:", dict(prec))
    print("certezza:", dict(cert))

MACRO = {
    "uccisioni": ["uccisione", "esecuzione_sommaria", "uso_della_forza_letale", "bombardamento_indiscriminato",
                  "mutilazione", "occultamento_cadaveri"],
    "violenza_sessuale": ["violenza_sessuale"],
    "tortura_maltrattamenti": ["tortura", "trattamenti_inumani", "percosse", "ferimento", "minaccia"],
    "privazione_liberta": ["arresto_arbitrario", "detenzione_arbitraria", "rapimento", "sparizione_forzata"],
    "sfollamento_espulsione": ["sfollamento_forzato", "espulsione_forzata", "rimpatrio_forzato", "restrizione_movimento"],
    "distruzione_saccheggio": ["saccheggio", "distruzione_incendio", "distruzione_beni", "requisizione_beni",
                               "perquisizione_arbitraria"],
    "attacchi_beni_protetti": ["attacco_scuola", "attacco_sanita", "attacco_luogo_di_culto", "attacco_convogli",
                               "attacco_villaggi", "attacco"],
    "persecuzione_discriminazione": ["persecuzione", "licenziamento_discriminatorio", "sospensione_arbitraria"],
    "decessi_per_condizioni_imposte": ["decessi_per_privazioni", "decessi_durante_trasferimento",
                                       "negazione_assistenza"],
}
INV = {v: k for k, vs in MACRO.items() for v in vs}

if __name__ == "__main__":
    out = json.load(open(sys.argv[2]))
    missing = set()
    for inc in out["incidents"]:
        for a in inc["atti"]:
            a["categorie"] = sorted({INV.get(v, "altro") for v in a["violazioni"]})
            missing |= {v for v in a["violazioni"] if v not in INV}
        inc["categorie"] = sorted({c for a in inc["atti"] for c in a["categorie"]})
    out["macro_violazioni"] = MACRO
    json.dump(out, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
    print("non mappate:", missing or "nessuna")
    print("incidenti per categoria:", dict(Counter(c for i in out["incidents"] for c in i["categorie"]).most_common()))
