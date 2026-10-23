"""Lecture et transformations d’automates finis. Bibliothèque standard uniquement."""

from pathlib import Path
import re
from copy import deepcopy
from collections import deque

# Symbole utilisé pour représenter les ε-transitions dans les fichiers
EPSILON = '*'


# STRUCTURE DE DONNÉES

class Automaton:
    """Représente un automate fini (potentiellement non déterministe / asynchrone)."""

    def __init__(self):
        self.nb_symbols      = 0
        self.nb_states       = 0
        self.initial_states  = []     # liste d'entiers
        self.terminal_states = []     # liste d'entiers
        self.transitions     = {}     # {état: {symbole: set(états)}}
        self.alphabet        = []     # ['a', 'b', …]
        self.states          = []     # [0, 1, 2, …]
        self.has_epsilon     = False  # présence de ε-transitions
        self._named_states   = {}     # {int_id → nom_str} pour les états nommés (ex: "P")

    def get(self, state, sym):
        """Retourne l'ensemble des états accessibles depuis (state, sym)."""
        return self.transitions.get(state, {}).get(sym, set())

    def add_transition(self, src, sym, dst):
        if src not in self.transitions:
            self.transitions[src] = {}
        self.transitions[src].setdefault(sym, set()).add(dst)


# LECTURE DE FICHIER

def read_automaton(filename: str) -> Automaton:
    """
    Lit un automate depuis un fichier texte.
    Lève FileNotFoundError ou ValueError en cas d'erreur.
    """
    with Path(filename).open(encoding="utf-8-sig") as stream:
        lines = [line.strip() for line in stream
                 if line.strip() and not line.lstrip().startswith("#")]
    if len(lines) < 5:
        raise ValueError("Le fichier doit contenir au moins cinq lignes.")

    def count(raw, label):
        try:
            value = int(raw)
        except ValueError as error:
            raise ValueError(f"{label} : entier attendu.") from error
        if value < 0:
            raise ValueError(f"{label} : valeur négative interdite.")
        return value

    A = Automaton()
    A.nb_symbols = count(lines[0], "Alphabet")
    if A.nb_symbols > 26:
        raise ValueError("L’alphabet est limité aux lettres a à z.")
    A.alphabet = [chr(ord('a') + i) for i in range(A.nb_symbols)]
    A.nb_states = count(lines[1], "États")
    if A.nb_states == 0:
        raise ValueError("L’automate doit contenir au moins un état.")
    A.states = list(range(A.nb_states))

    def state_list(raw, label):
        parts = raw.split()
        number = count(parts[0], label)
        if len(parts) != number + 1:
            raise ValueError(f"{label} : nombre d’états incohérent.")
        values = [int(value) for value in parts[1:]]
        if len(set(values)) != len(values):
            raise ValueError(f"{label} : état répété.")
        if any(value not in A.states for value in values):
            raise ValueError(f"{label} : état hors limites.")
        return values

    A.initial_states = state_list(lines[2], "États initiaux")
    A.terminal_states = state_list(lines[3], "États terminaux")
    number = count(lines[4], "Transitions")
    if len(lines) != number + 5:
        raise ValueError("Le nombre de transitions ne correspond pas aux lignes présentes.")
    named = {}

    def resolve_state(raw):
        if raw.isdecimal():
            value = int(raw)
            if value not in range(int(lines[1])):
                raise ValueError(f"État numérique hors limites : {raw}")
            return value
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", raw):
            raise ValueError(f"Nom d’état invalide : {raw}")
        if raw not in named:
            named[raw] = len(A.states)
            A.states.append(named[raw])
        return named[raw]

    for line in lines[5:]:
        tokens = line.split()
        if len(tokens) == 1:
            match = re.fullmatch(r"(\d+|[A-Z][A-Z0-9_]*)([a-z]|\*)(\d+|[A-Z][A-Z0-9_]*)", line)
            if not match:
                raise ValueError(f"Transition mal formée : {line}")
            tokens = match.groups()
        if len(tokens) != 3:
            raise ValueError(f"Transition mal formée : {line}")
        source, symbol, destination = tokens
        if symbol not in A.alphabet and symbol != EPSILON:
            raise ValueError(f"Symbole hors alphabet : {symbol}")
        A.add_transition(resolve_state(source), symbol, resolve_state(destination))
        A.has_epsilon |= symbol == EPSILON
    for state in A.states:
        for symbol in A.alphabet:
            A.transitions.setdefault(state, {}).setdefault(symbol, set())
    A.nb_states = len(A.states)
    A._named_states = {value: key for key, value in named.items()}
    return A


# AFFICHAGE

def _label(state, ini, ter) -> str:
    """Préfixe ES/E/S/ pour l'affichage d'un état."""
    return ("E" if state in ini else " ") + ("S" if state in ter else " ")


def display_automaton(A: Automaton, title: str = "Automate",
                      names: dict = None) -> None:
    """
    Affiche l'automate sous forme de table de transitions.
    names : dict optionnel {entier → chaîne} pour nommer les états.
    """
    if names is None:
        names = {s: str(s) for s in A.states}

    syms = list(A.alphabet)
    if A.has_epsilon:
        syms.append(EPSILON)

    # ── Largeurs de colonnes ──────────────────────────────────
    def cell_content(s, sym):
        dsts = A.get(s, sym)
        if not dsts:
            return "--"
        # Affiche le nom du sous-ensemble cible (fusion des noms si plusieurs)
        parts = []
        for d in sorted(dsts):
            parts.append(names.get(d, str(d)))
        if len(parts) == 1:
            return parts[0]
        return "{" + ", ".join(parts) + "}"

    max_cell = max(
        (len(cell_content(s, sym)) for s in A.states for sym in syms),
        default=2
    )
    max_cell  = max(max_cell, max((len(str(sy)) for sy in syms), default=0), 2)
    cell_w    = max_cell + 2   # padding

    max_lbl   = max(len(names.get(s, str(s))) + 2 for s in A.states)
    lbl_w     = max(max_lbl + 2, 6)

    bar = "+" + "-" * lbl_w + ("+" + "-" * cell_w) * len(syms) + "+"

    # ── En-tête ───────────────────────────────────────────────
    print(f"\n{'═'*60}")
    print(f"  {title}")
    print(f"{'═'*60}")
    alph_str = "{" + ", ".join(A.alphabet) + "}"
    if A.has_epsilon:
        alph_str += " ∪ {ε}"
    print(f"  Alphabet  : {alph_str}")
    print(f"  États     : {{{', '.join(names.get(s, str(s)) for s in A.states)}}}")
    print(f"  Initiaux  : {{{', '.join(names.get(s, str(s)) for s in A.initial_states)}}}")
    print(f"  Terminaux : {{{', '.join(names.get(s, str(s)) for s in A.terminal_states)}}}")
    print()

    # ── Table ─────────────────────────────────────────────────
    print(bar)
    hdr = "|" + f"{'':>{lbl_w}}" + "|"
    for sy in syms:
        disp = 'ε' if sy == EPSILON else sy
        hdr += f" {disp:^{cell_w-1}}|"
    print(hdr)
    print(bar)

    for s in A.states:
        marker = _label(s, A.initial_states, A.terminal_states)
        lbl    = f"{marker}{names.get(s, str(s))}"
        row    = f"|{lbl:>{lbl_w}}|"
        for sy in syms:
            c   = cell_content(s, sy)
            row += f" {c:^{cell_w-1}}|"
        print(row)

    print(bar)
    print()


# FERMETURE EPSILON

def eps_closure(states, A: Automaton) -> frozenset:
    """Calcule la ε-fermeture d'un ensemble d'états."""
    closure = set(states)
    stack   = list(states)
    while stack:
        s = stack.pop()
        for d in A.get(s, EPSILON):
            if d not in closure:
                closure.add(d)
                stack.append(d)
    return frozenset(closure)


# VÉRIFICATIONS DE PROPRIÉTÉS

def check_standard(A: Automaton):
    """
    Vérifie si l'automate est standard.
    Retourne (bool, message).
    """
    if len(A.initial_states) != 1:
        return False, f"Un unique état initial est requis : {A.initial_states}"
    init = A.initial_states[0]
    for s in A.states:
        for sym in [*A.alphabet, EPSILON]:
            if init in A.get(s, sym):
                return False, (f"L'état initial {init} est accessible "
                               f"depuis l'état {s} par '{sym}'")
    return True, "Standard"


def check_deterministic(A: Automaton):
    """
    Vérifie si l'automate est déterministe.
    Retourne (bool, liste_de_raisons).
    """
    reasons = []
    if len(A.initial_states) != 1:
        reasons.append(f"Un unique état initial est requis : {A.initial_states}")
    if A.has_epsilon:
        reasons.append("Présence de ε-transitions (automate asynchrone)")
    for s in A.states:
        for sym in A.alphabet:
            d = A.get(s, sym)
            if len(d) > 1:
                reasons.append(f"δ({s}, '{sym}') = {sorted(d)}  (ambiguïté)")
    return (not reasons), reasons


def check_complete(A: Automaton):
    """
    Vérifie si l'automate déterministe est complet.
    Retourne (bool, liste_de_transitions_manquantes).
    """
    missing = [(s, sym) for s in A.states
               for sym in A.alphabet if not A.get(s, sym)]
    return (not missing), missing


# STANDARDISATION

def standardize(A: Automaton) -> Automaton:
    """
    Standardise l'automate : crée un unique état initial i₀
    sans aucune transition entrante.
    """
    SA  = deepcopy(A)
    i0  = max(SA.states) + 1
    SA.states.append(i0)
    SA.nb_states += 1

    SA.transitions[i0] = {sym: set() for sym in SA.alphabet}
    if SA.has_epsilon:
        SA.transitions[i0][EPSILON] = set()

    # Copier les transitions de tous les anciens états initiaux
    for old in SA.initial_states:
        for sym in SA.alphabet:
            SA.transitions[i0][sym] |= SA.get(old, sym)
        if SA.has_epsilon:
            SA.transitions[i0][EPSILON] |= SA.get(old, EPSILON)

    # Si un ancien état initial est terminal, i0 l'est aussi
    if any(s in SA.terminal_states for s in SA.initial_states):
        if i0 not in SA.terminal_states:
            SA.terminal_states.append(i0)

    SA.initial_states = [i0]
    print(f"\n  ✓ Nouvel état initial créé : {i0}")
    return SA


# COMPLÉTION

def complete_aut(A: Automaton):
    """
    Complète un automate déterministe non complet
    en ajoutant un état puits nommé P.
    Retourne (automate_complété, names_dict, bool_modifié).
    """
    if not check_deterministic(A)[0]:
        raise ValueError("La complétion attend un automate déterministe.")
    CA = deepcopy(A)
    ok, missing = check_complete(CA)
    if ok:
        names = {s: str(s) for s in CA.states}
        return CA, names, False

    sink = max(CA.states) + 1
    CA.states.append(sink)
    CA.nb_states += 1
    CA.transitions[sink] = {sym: {sink} for sym in CA.alphabet}

    for s, sym in missing:
        CA.transitions[s][sym] = {sink}

    # Noms : tous les états normaux gardent leur numéro, le puits s'appelle P
    # (sauf s'il y a déjà un état nommé P dans l'automate d'origine)
    names = {s: CA._named_states.get(s, str(s)) for s in CA.states}
    # Choisir un nom libre pour le nouveau puits
    puits_name = "P"
    existing_names = set(names.values())
    suffix = 0
    while puits_name in existing_names:
        suffix += 1
        puits_name = f"P{suffix}"
    names[sink] = puits_name

    print(f"\n  ✓ État puits ajouté : P")
    return CA, names, True


# DÉTERMINISATION + COMPLÉTION  (construction par sous-ensembles)

def _make_name(fset: frozenset) -> str:
    """Nom d'affichage d'un sous-ensemble d'états — format {1,3} comme dans le cours."""
    if not fset:
        return "{P}"                   # état puits (∅)
    return "{" + ",".join(str(s) for s in sorted(fset)) + "}"


def determinize(A: Automaton):
    """
    Construction par sous-ensembles.
    Retourne (AFDC, names{int→str}, rmap{int→frozenset_origine}).
    """
    # ε-fermeture de l'ensemble initial
    if A.has_epsilon:
        init = eps_closure(A.initial_states, A)
    else:
        init = frozenset(A.initial_states)

    SINK      = frozenset()   # ensemble vide → état puits
    state_map = {init: 0}
    queue     = deque([init])
    counter   = 1
    new_trans = {}

    while queue:
        cur  = queue.popleft()
        cidx = state_map[cur]
        new_trans[cidx] = {}

        for sym in A.alphabet:
            # Union des transitions sur sym depuis tous les états de cur
            raw = set()
            for s in cur:
                raw |= A.get(s, sym)

            # ε-fermeture du résultat
            if A.has_epsilon and raw:
                tgt = eps_closure(raw, A)
            else:
                tgt = frozenset(raw)

            if not tgt:
                tgt = SINK   # transition vers état puits

            if tgt not in state_map:
                state_map[tgt] = counter
                counter += 1
                queue.append(tgt)

            new_trans[cidx][sym] = {state_map[tgt]}

    # ── Construire l'AFDC ─────────────────────────────────────
    AFDC = Automaton()
    AFDC.alphabet        = A.alphabet[:]
    AFDC.nb_symbols      = A.nb_symbols
    AFDC.states          = list(range(counter))
    AFDC.nb_states       = counter
    AFDC.initial_states  = [0]
    AFDC.transitions     = new_trans
    AFDC.has_epsilon     = False

    rmap = {v: k for k, v in state_map.items()}

    for idx, orig in rmap.items():
        if any(s in A.terminal_states for s in orig):
            AFDC.terminal_states.append(idx)

    names = {idx: _make_name(orig) for idx, orig in rmap.items()}
    return AFDC, names, rmap


# MINIMISATION  (raffinement de partition — algorithme de Moore)

def minimize(AFDC: Automaton, names: dict = None):
    """
    Minimise un AFDC par raffinement de partition.
    Retourne (AFDCM, correspondance{nouv→[anciens]}, s2c{ancien→nouv}).
    """
    if not check_deterministic(AFDC)[0] or not check_complete(AFDC)[0]:
        raise ValueError("La minimisation attend un automate déterministe complet.")
    # Un état inaccessible ne participe pas à l’automate minimal.
    reachable = set(AFDC.initial_states)
    pending = list(reachable)
    while pending:
        state = pending.pop()
        for symbol in AFDC.alphabet:
            for target in AFDC.get(state, symbol):
                if target not in reachable:
                    reachable.add(target)
                    pending.append(target)
    AFDC = deepcopy(AFDC)
    AFDC.states = [state for state in AFDC.states if state in reachable]
    AFDC.nb_states = len(AFDC.states)
    AFDC.terminal_states = [state for state in AFDC.terminal_states if state in reachable]
    if names is None:
        names = {s: str(s) for s in AFDC.states}

    def sname(s):
        return names.get(s, str(s))
    term     = set(AFDC.terminal_states)
    non_term = set(AFDC.states) - term
    partition = [g for g in [non_term, term] if g]

    def find_class(state: int) -> int:
        for i, g in enumerate(partition):
            if state in g:
                return i
        return -1   # état inconnu (ne devrait pas arriver)

    def signature(state: int) -> tuple:
        """Signature = tuple des classes atteintes sur chaque symbole."""
        return tuple(
            find_class(next(iter(AFDC.get(state, sym) or {-1})))
            for sym in AFDC.alphabet
        )

    # ── Affichage des partitions successives ──────────────────
    print("\n  Partitions successives :")
    print(f"  P0 : {[[sname(s) for s in sorted(g, key=sname)] for g in partition]}")

    iteration = 0
    while True:
        new_part: list = []
        for group in partition:
            sigs: dict = {}
            for s in group:
                sigs.setdefault(signature(s), set()).add(s)
            new_part.extend(sigs.values())

        iteration += 1

        # Vérifier la stabilité
        if {frozenset(g) for g in new_part} == {frozenset(g) for g in partition}:
            print(f"  P{iteration} = P{iteration-1}  → stable, minimisation terminée")
            break

        partition = new_part
        print(f"  P{iteration} : {[[sname(s) for s in sorted(g, key=sname)] for g in partition]}")

        # Afficher les transitions en termes de classes
        for i, group in enumerate(partition):
            rep = next(iter(group))
            tr  = []
            for sym in AFDC.alphabet:
                dsts = AFDC.get(rep, sym)
                d    = next(iter(dsts)) if dsts else -1
                tr.append(f"{sym}→C{find_class(d)}")
            print(f"    C{i}{[sname(s) for s in sorted(group, key=sname)]}: {', '.join(tr)}")

    # ── Réordonner : la classe contenant l'état initial est #0 ─
    init = AFDC.initial_states[0] if AFDC.initial_states else 0
    for i, g in enumerate(partition):
        if init in g:
            partition[0], partition[i] = partition[i], partition[0]
            break

    # ── Reconstruire les classes après réordonnancement ────────
    def find_class2(state) -> int:
        for i, g in enumerate(partition):
            if state in g:
                return i
        return -1

    s2c = {s: find_class2(s) for i, g in enumerate(partition) for s in g}

    # Représentant de chaque classe = état initial si présent, sinon premier trié
    def pick_rep(group):
        for s in group:
            if s in set(AFDC.initial_states):
                return s
        return sorted(group, key=lambda s: names.get(s, str(s)))[0]

    reps = [pick_rep(g) for g in partition]

    # ── Construire l'AFDCM en gardant les noms des représentants ─
    n     = len(partition)
    AFDCM = Automaton()
    AFDCM.alphabet    = AFDC.alphabet[:]
    AFDCM.nb_symbols  = AFDC.nb_symbols
    AFDCM.states      = reps[:]
    AFDCM.nb_states   = n
    AFDCM.has_epsilon = False

    init_set = set(AFDC.initial_states)
    for i, group in enumerate(partition):
        rep = reps[i]
        if any(s in init_set for s in group):
            AFDCM.initial_states.append(rep)
        if any(s in term for s in group):
            AFDCM.terminal_states.append(rep)

    AFDCM.transitions = {}
    for i, group in enumerate(partition):
        rep = reps[i]
        AFDCM.transitions[rep] = {}
        for sym in AFDC.alphabet:
            dsts = AFDC.get(rep, sym)
            if dsts:
                target_class = s2c[next(iter(dsts))]
                AFDCM.transitions[rep][sym] = {reps[target_class]}
            else:
                AFDCM.transitions[rep][sym] = set()

    corr = {reps[i]: sorted(g) for i, g in enumerate(partition)}
    return AFDCM, corr, s2c


# RECONNAISSANCE DE MOTS

def recognize(word: str, A: Automaton):
    """
    Vérifie si le mot est accepté par l'automate A.
    Retourne (accepté: bool, erreur: str|None).
    """
    cur = set(A.initial_states)
    if A.has_epsilon:
        cur = set(eps_closure(cur, A))

    for ch in word:
        if ch not in A.alphabet:
            return False, f"Symbole '{ch}' hors alphabet {A.alphabet}"
        nxt = set()
        for s in cur:
            nxt |= A.get(s, ch)
        if A.has_epsilon and nxt:
            nxt = set(eps_closure(nxt, A))
        cur = nxt
        if not cur:
            return False, None

    return bool(cur & set(A.terminal_states)), None


# AUTOMATE COMPLÉMENTAIRE

def complement(A: Automaton) -> Automaton:
    """
    Construit l'automate du langage complémentaire
    en échangeant états terminaux et non-terminaux.
    A doit être un AFD complet.
    """
    if not check_deterministic(A)[0] or not check_complete(A)[0]:
        raise ValueError("Le complément attend un automate déterministe complet.")
    C = deepcopy(A)
    term_set       = set(A.terminal_states)
    C.terminal_states = sorted(s for s in A.states if s not in term_set)
    return C


