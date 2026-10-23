"""Menu du projet d’automates finis."""
import argparse
import sys
from pathlib import Path
from copy import deepcopy
from automates import (
    read_automaton, display_automaton, check_standard, check_deterministic,
    check_complete, standardize, complete_aut, determinize, minimize,
    recognize, complement,
)

BASE_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

def pipeline(filename: str) -> None:
    """Exécute toutes les étapes du traitement sur un automate."""

    print(f"\n{'█'*60}")
    print(f"  Fichier : {filename}")
    print(f"{'█'*60}")

    # ── Étape 1 : Lecture ─────────────────────────────────────
    try:
        A = read_automaton(filename)
    except Exception as e:
        print(f"\n  ✗ Erreur de lecture : {e}")
        return

    display_automaton(A, "AUTOMATE INITIAL",
                      names={s: A._named_states.get(s, str(s)) for s in A.states})

    # ── Étape 2 : Propriétés ──────────────────────────────────
    print("─" * 60)
    print("  PROPRIÉTÉS DE L'AUTOMATE")
    print("─" * 60)

    is_std, std_msg  = check_standard(A)
    is_det, det_why  = check_deterministic(A)
    is_cmp, miss_cmp = check_complete(A) if is_det else (False, [])

    print(f"\n  Standard     : {'✓ OUI' if is_std else '✗ NON'}")
    if not is_std:
        print(f"    Raison : {std_msg}")

    print(f"  Déterministe : {'✓ OUI' if is_det else '✗ NON'}")
    for r in det_why:
        print(f"    · {r}")

    if is_det:
        print(f"  Complet      : {'✓ OUI' if is_cmp else '✗ NON'}")
        if not is_cmp:
            for s, sym in miss_cmp[:5]:
                print(f"    · δ({s}, '{sym}') non définie")
            if len(miss_cmp) > 5:
                print(f"    · … et {len(miss_cmp)-5} autres")
    else:
        print("  Complet      : N/A (automate non déterministe)")
    print()

    # ── Étape 3 : Standardisation ─────────────────────────────
    AF = A   # par défaut on travaille sur l'automate original

    if not is_std:
        print("─" * 60)
        print("  STANDARDISATION")
        print("─" * 60)
        choix_std = input("  L'automate n'est pas standard. Voulez-vous le standardiser ? (o/n) > ").strip().lower()
        if choix_std == 'o':
            AF = standardize(A)
            display_automaton(AF, "AUTOMATE STANDARDISÉ",
                              names={s: AF._named_states.get(s, str(s)) for s in AF.states})
        else:
            print("\n  ✓ Standardisation ignorée.")
    print()

    # ── Étape 4 : Déterminisation / Complétion ─────────────────
    print("─" * 60)
    choix_det = input("  Voulez-vous procéder à la déterminisation/complétion et à la minimisation ? (o/n) > ").strip().lower()
    if choix_det != 'o':
        print("\n  ✓ Traitement arrêté après l'affichage des propriétés.")
        return
    print("─" * 60)
    print("  DÉTERMINISATION / COMPLÉTION")
    print("─" * 60)

    is_det_af, _    = check_deterministic(AF)
    AFDC            = None
    afdc_names      = None   # dict int → chaîne
    rmap            = None   # dict int → frozenset

    if is_det_af:
        is_cmp_af, _ = check_complete(AF)
        if is_cmp_af:
            print("\n  ✓ L'automate est déjà déterministe et complet → AFDC = AF")
            AFDC       = deepcopy(AF)
            afdc_names = {s: str(s) for s in AFDC.states}
            rmap       = {s: frozenset([s]) for s in AFDC.states}
        else:
            print("\n  → Complétion de l'automate déterministe…")
            AFDC, afdc_names, _ = complete_aut(AF)
            rmap       = {s: frozenset([s]) for s in AFDC.states}
            display_automaton(AFDC, "AUTOMATE DÉTERMINISTE COMPLET (après complétion)", afdc_names)
    else:
        print("\n  → Déterminisation + complétion (construction par sous-ensembles)…")
        AFDC, afdc_names, rmap = determinize(AF)

        # Tableau de correspondance
        print("\n  Correspondance des états :")
        max_w = max(len(v) for v in afdc_names.values()) + 2
        print(f"  {'Nouvel état':^{max_w}} | États d'origine")
        print("  " + "─" * (max_w + 22))
        for idx in sorted(AFDC.states):
            orig  = rmap.get(idx, frozenset())
            o_str = ("{" + ",".join(str(s) for s in sorted(orig)) + "}"
                     if orig else "{∅}")
            print(f"  {afdc_names[idx]:^{max_w}} | {o_str}")

        display_automaton(AFDC, "AUTOMATE DÉTERMINISTE COMPLET (AFDC)", afdc_names)

    # ── Étape 5 : Minimisation ────────────────────────────────
    print("─" * 60)
    print("  MINIMISATION")
    print("─" * 60)

    AFDCM, corr, s2c = minimize(AFDC, afdc_names)

    if AFDCM.nb_states == AFDC.nb_states:
        print("\n  ✓ L'automate était déjà minimal.")

    # Les noms AFDCM = noms AFDC des représentants
    afdcm_names = {rep: afdc_names.get(rep, str(rep)) for rep in AFDCM.states}

    print("\n  Correspondance AFDC → AFDCM :")
    print(f"  {'État AFDCM':^12} | États AFDC correspondants")
    print("  " + "─" * 40)
    for rep, old_list in corr.items():
        old_n = [afdc_names.get(s, str(s)) for s in old_list]
        print(f"  {afdcm_names[rep]:^12} | {{ {', '.join(old_n)} }}")

    display_automaton(AFDCM, "AUTOMATE MINIMAL (AFDCM)", afdcm_names)

    # ── Étape 6 : Reconnaissance de mots ─────────────────────
    print("─" * 60)
    print("  RECONNAISSANCE DE MOTS  (automate utilisé : AFDCM)")
    print("  Tapez 'fin' pour terminer la reconnaissance.")
    print("─" * 60)

    while True:
        word = input("\n  Mot > ").strip()
        if word.lower() == 'fin':
            break
        ok, err = recognize(word, AFDCM)
        if err:
            print(f"  ✗ Erreur : {err}")
        elif ok:
            print(f"  ✓ '{word}' est ACCEPTÉ par l'automate")
        else:
            print(f"  ✗ '{word}' est REFUSÉ par l'automate")

    # ── Étape 7 : Automate complémentaire ─────────────────────
    print("\n" + "─" * 60)
    print("  AUTOMATE COMPLÉMENTAIRE")
    print("─" * 60)
    print("  À partir de quel automate construire le complémentaire ?")
    print("    1. AFDC")
    print("    2. AFDCM")
    ch = input("  Votre choix (1/2) > ").strip()

    if ch == '2':
        base_auto  = AFDCM
        base_name  = "AFDCM"
        base_names = None
    else:
        base_auto  = AFDC
        base_name  = "AFDC"
        base_names = afdc_names

    Acomp = complement(base_auto)
    print(f"\n  Complémentaire construit à partir de l'{base_name}.")
    display_automaton(Acomp,
                      f"AUTOMATE COMPLÉMENTAIRE (depuis {base_name})",
                      base_names)


def main():
    parser = argparse.ArgumentParser(description="Traitement d’automates finis — projet EFREI")
    parser.add_argument("fichier", nargs="?", help="Fichier texte à traiter (facultatif)")
    args = parser.parse_args()
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    print("\nTRAITEMENT D’AUTOMATES FINIS — EFREI P2, 2025–2026")
    print("Exemples disponibles : 01 à 44 et exemple. Entrée vide pour quitter.")
    try:
        if args.fichier:
            pipeline(args.fichier)
            return
        while True:
            number = input("\nNuméro de l’automate (ou quitter) > ").strip()
            if number.lower() in ("", "quitter", "quit", "q", "exit"):
                break
            name = f"{int(number):02d}" if number.isdecimal() else number
            filename = DATA_DIR / f"{name}.txt"
            if not filename.is_file():
                print("Fichier introuvable. Choisir un numéro de 01 à 44 ou exemple.")
                continue
            pipeline(str(filename))
            if input("\nTraiter un autre automate ? (o/n) > ").strip().lower() != "o":
                break
    except (EOFError, KeyboardInterrupt):
        print("\nFin du programme.")


if __name__ == "__main__":
    main()
