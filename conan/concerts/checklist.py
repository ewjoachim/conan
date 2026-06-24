"""The CONAN concert-preparation checklist: its structure and progress logic.

This module is the single source of truth for the checklist (ported from the old
client-side JS ``STEPS`` array). The per-concert progress is stored as a flat
``{key: value}`` dict on ``Concert.state``; the key naming scheme below mirrors
the original app so the semantics are unchanged:

- simple item:    ``state[item.id]``                 -> bool (checked)
- textfield item: ``state["tft_" + item.id]``        -> str  (the text)
                  ``state["tf_" + item.id]``         -> bool (marked transmitted)
- yes/no item:    ``state["yn_" + item.id]``         -> "y" | "n"
                  sub-items:  ``state[sub.id]``      -> bool
- cotech item:    ``state["cotech_mode"]``           -> "np" | "direct" | "passage"
                  ``state["cotech_text"]``           -> str
                  ``state["cotech_transmis"]``       -> bool

UI labels are intentionally in French.
"""

from dataclasses import dataclass

StateValue = bool | str
State = dict[str, StateValue]


@dataclass(frozen=True)
class Sub:
    id: str
    label: str


@dataclass(frozen=True)
class Item:
    id: str
    label: str
    type: str = "simple"  # one of: simple | yesno | textfield | cotech
    hint: str = ""  # may contain trusted HTML (rendered with |safe)
    placeholder: str = ""
    subs: tuple[Sub, ...] = ()


@dataclass(frozen=True)
class Step:
    id: str
    num: str
    title: str
    items: tuple[Item, ...]
    parallel: bool = False


# Options for the special "CoTech au courant" item.
COTECH_OPTIONS: tuple[tuple[str, str], ...] = (
    ("np", "Pas pertinent"),
    ("direct", "Contact direct CoTech"),
    ("passage", "Passage d'information"),
)

STEPS: tuple[Step, ...] = (
    Step(
        id="s1",
        num="Étape 1",
        title="Sondage préalable",
        items=(
            Item(
                id="s1_1",
                label="Création du sondage",
                hint=(
                    "Copier le sondage template et suivre le mode d'emploi : "
                    '<a href="https://moodle.negitachi.fr/course/section.php?id=501" '
                    'target="_blank">https://moodle.negitachi.fr/course/section.php?id=501</a>'
                ),
            ),
            Item(
                id="s1_2",
                label="Mail d'info membres",
                hint="Envoyer un mail de contexte avec le lien du sondage.",
            ),
            Item(
                id="s1_3",
                label="#info-importantes",
                hint="Poster le lien dans #infos-importantes, ou déléguer à quelqu'un qui a les droits.",
            ),
            Item(
                id="s1_4",
                label="Relances",
                hint="Vérifier le nombre de réponses manquantes et relancer si besoin.",
            ),
            Item(
                id="s1_5",
                label="Décision",
                hint="Télécharger le .xlsx, le cleaner, partager dans #waconan pour acter la participation.",
            ),
        ),
    ),
    Step(
        id="s2",
        num="Étape 2",
        title="Moodle",
        parallel=True,
        items=(
            Item(
                id="s2_1",
                label="Création du cours Moodle",
                hint="Demander à Eve ou au bureau.",
            ),
            Item(
                id="s2_2",
                label="Informations basiques",
                hint="Zone texte et média : lieu, heure (mettre ? si inconnu).",
            ),
            Item(
                id="s2_3",
                label="Poireaux présents",
                hint="Créer la section et la remplir avec les infos du sondage préalable.",
            ),
            Item(
                id="s2_4",
                label="Mail de récap",
                hint=(
                    "Objet : [Concert] Nom - Date. Valider participation, copier le lien "
                    "Moodle, demander de prévenir si changement."
                ),
            ),
        ),
    ),
    Step(
        id="s2b",
        num="Étape 2'",
        title="Orga interne",
        parallel=True,
        items=(
            Item(id="s2b_1", label="ComCom au courant"),
            Item(
                id="s2b_2",
                label="Éléments à transmettre à ComCom (#ComcomConan)",
                type="textfield",
                placeholder="Pack presse, description, logos…",
            ),
            Item(id="s2b_4", label="CoTech au courant", type="cotech"),
            Item(
                id="s2b_3",
                label="Trouver une salle ?",
                type="yesno",
                subs=(
                    Sub(id="s2b_3a", label="Se répartir les démarches avec le Bureau"),
                    Sub(id="s2b_3b", label="Confirmer la réservation de salle"),
                    Sub(
                        id="s2b_3c",
                        label="Vérifier les accès et la logistique sur place",
                    ),
                ),
            ),
            Item(
                id="s2b_5",
                label="Organisation des transports ?",
                type="yesno",
                subs=(
                    Sub(id="s2b_5a", label="Sondage transport dans Moodle"),
                    Sub(id="s2b_5b", label="Dépouillage du sondage"),
                    Sub(id="s2b_5c", label="Création d'un Google Doc de coordination"),
                ),
            ),
        ),
    ),
    Step(
        id="s3",
        num="Étape 3",
        title="Suivi de la préparation",
        items=(
            Item(
                id="s3_6",
                label="Confirmation du mandataire reçue",
                hint="Date, heure, durée, format revalidés + salle d'échauffement + sono ok.",
            ),
            Item(id="s3_1", label="PL reçue des Wacos"),
            Item(id="s3_2", label="PL dans Moodle"),
            Item(id="s3_3", label="PL envoyée par mail"),
            Item(
                id="s3_5",
                label="SACEM ?",
                type="yesno",
                subs=(
                    Sub(id="s3_5a", label="Contacter Lia (ou sa succession)"),
                    Sub(id="s3_5b", label="Effectuer la déclaration SACEM"),
                    Sub(
                        id="s3_5c",
                        label="Conserver la confirmation dans le dossier concert",
                    ),
                ),
            ),
        ),
    ),
    Step(
        id="s4",
        num="Étape 4",
        title="Communication interne",
        items=(
            Item(
                id="s4_1",
                label="Mail récap envoyé",
                hint=(
                    "Dans la semaine du concert : vérifier Moodle puis envoyer avec date, "
                    "heure RDV, lieu, matériel, spécificités."
                ),
            ),
        ),
    ),
)


def is_cotech_done(state: State) -> bool:
    """The CoTech item is done once a mode is picked (and, for "passage", transmitted)."""
    mode = state.get("cotech_mode")
    if not mode:
        return False
    if mode == "passage":
        return bool(state.get("cotech_transmis"))
    return True


def item_done(item: Item, state: State) -> bool:
    if item.type == "cotech":
        return is_cotech_done(state)
    if item.type == "textfield":
        return bool(state.get(f"tf_{item.id}"))
    if item.type == "yesno":
        yn = state.get(f"yn_{item.id}")
        if not yn:
            return False
        if yn == "y":
            return all(state.get(sub.id) for sub in item.subs)
        return True
    return bool(state.get(item.id))


def is_step_done(step: Step, state: State) -> bool:
    return all(item_done(item, state) for item in step.items)


@dataclass(frozen=True)
class Progress:
    total: int = 0
    done: int = 0
    pct: int = 0


def _item_progress(item: Item, state: State) -> tuple[int, int]:
    """Return ``(total, done)`` checkable units contributed by one item.

    A yes/no item counts as one unit, plus one per sub-item once answered "yes".
    """
    if item.type == "yesno":
        yn = state.get(f"yn_{item.id}")
        total, done = 1, (1 if yn else 0)
        if yn == "y":
            total += len(item.subs)
            done += sum(1 for sub in item.subs if state.get(sub.id))
        return total, done
    return 1, (1 if item_done(item, state) else 0)


def compute_progress(state: State) -> Progress:
    total = 0
    done = 0
    for step in STEPS:
        for item in step.items:
            item_total, item_done_count = _item_progress(item, state)
            total += item_total
            done += item_done_count
    pct = round(done / total * 100) if total else 0
    return Progress(total=total, done=done, pct=pct)


# Lookup tables / allowlists used by views to validate incoming keys, so a
# request can only ever flip or set a state key the checklist actually defines.
STEPS_BY_ID: dict[str, Step] = {step.id: step for step in STEPS}
ITEMS_BY_ID: dict[str, Item] = {item.id: item for step in STEPS for item in step.items}


def _toggle_keys() -> frozenset[str]:
    keys: set[str] = {"cotech_transmis"}
    for step in STEPS:
        for item in step.items:
            if item.type == "simple":
                keys.add(item.id)
            elif item.type == "textfield":
                keys.add(f"tf_{item.id}")
            for sub in item.subs:
                keys.add(sub.id)
    return frozenset(keys)


# Boolean keys a "toggle" request may flip.
TOGGLE_KEYS: frozenset[str] = _toggle_keys()
# Item ids that accept a yes/no answer.
YESNO_IDS: frozenset[str] = frozenset(
    item.id for item in ITEMS_BY_ID.values() if item.type == "yesno"
)
# Free-text keys a "field" request may set.
TEXT_KEYS: frozenset[str] = frozenset(
    [
        *(
            f"tft_{item.id}"
            for item in ITEMS_BY_ID.values()
            if item.type == "textfield"
        ),
        "cotech_text",
    ]
)
COTECH_MODES: frozenset[str] = frozenset(value for value, _label in COTECH_OPTIONS)
