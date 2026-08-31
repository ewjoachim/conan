"""Checklist for concerts organised end-to-end by Negitachi."""

from dataclasses import dataclass

StateValue = bool | str
State = dict[str, StateValue]


@dataclass(frozen=True)
class Sub:
    id: str
    label: str
    hint: str = ""
    note_key: str = ""
    note_placeholder: str = ""
    note_inline: bool = False  # render note input on the same line as the sub


@dataclass(frozen=True)
class Item:
    id: str
    label: str
    type: str = "simple"
    hint: str = ""
    placeholder: str = ""
    subs: tuple[Sub, ...] = ()
    leading_subs: tuple[Sub, ...] = ()  # rendered before note_key/extra_notes
    note_key: str = ""
    note_placeholder: str = ""
    indent: bool = False
    simple_only: bool = False  # shown/counted only when NOT collab and NOT scenario
    artistic_only: bool = False  # shown/counted only when collab OR scenario
    extra_notes: tuple[
        tuple[str, str], ...
    ] = ()  # (state_key, placeholder) shown in yes branch
    visible_when: str = ""  # item only shown when state["yn_<visible_when>"] == "y"


@dataclass(frozen=True)
class Step:
    id: str
    num: str
    title: str
    items: tuple[Item, ...]
    conditional_key: str = ""


# Options for the special "CoTech au courant" item.
COTECH_OPTIONS_ORGA: tuple[tuple[str, str], ...] = (
    ("np", "Pas pertinent"),
    ("direct", "CoTech mis en contact direct"),
    ("passage", "ConAn transmet les demandes"),
)


STEPS: tuple[Step, ...] = (
    Step(
        id="s_gen",
        num="Bloc 1",
        title="Généralités",
        items=(
            Item(id="sg_collab", label="Collab ?", type="yesno"),
            Item(
                id="sg_scenario",
                label="Concert à scénario ?",
                type="yesno",
                hint="Est-ce que le concert va passer par une phase d'écriture avec des impacts sur la PL...",
            ),
            Item(
                id="sl_payant",
                label="Concert payant ?",
                type="yesno",
                subs=(
                    Sub(
                        id="sl_payant_tarifs",
                        label="Tarifs décidés",
                        hint="Voir avec le trésorier",
                    ),
                    Sub(
                        id="sl_payant_billetterie",
                        label="Billetterie créée",
                        hint="Vérifier avec le Bureau",
                    ),
                ),
            ),
        ),
    ),
    Step(
        id="s_prealables",
        num="Bloc 2",
        title="Actions préalables",
        items=(
            Item(
                id="sap_negiagenda",
                label="NegiAgenda",
                hint='Ajout du concert dans le NegiAgenda avec un "?"',
            ),
            Item(
                id="sap_sondage",
                label="Création du sondage",
                hint=(
                    "Copier le sondage template et suivre le mode d'emploi : "
                    '<a href="https://moodle.negitachi.fr/course/section.php?id=501" '
                    'target="_blank">https://moodle.negitachi.fr/course/section.php?id=501</a>'
                ),
            ),
            Item(
                id="sap_mail",
                label="Mail d'info membres",
                hint="Envoyer un mail de contexte avec le lien du sondage.",
            ),
            Item(
                id="sap_infos_importantes",
                label="#info-importantes",
                hint="Poster le lien dans #infos-importantes, ou déléguer à quelqu'un qui a les droits.",
            ),
            Item(
                id="sap_relances",
                label="Relances",
                hint="Vérifier le nombre de réponses manquantes et relancer si besoin.",
            ),
            Item(
                id="sap_decision",
                label="Décision",
                hint="Télécharger le .xlsx, le cleaner, partager dans #waconan pour acter la participation.",
            ),
        ),
    ),
    Step(
        id="s_collab",
        num="Bloc 3",
        title="Collab",
        conditional_key="sg_collab",
        items=(
            Item(id="sc_groupes", label="Groupes", type="collabs_list"),
            Item(
                id="sc_hebergement",
                label="Hébergement des invités ?",
                type="yesno",
                subs=(
                    Sub(
                        id="sc_hebergement_a",
                        label="Coordination avec la personne qui s'en occupe",
                        hint="Identifier le bon interlocuteur et voir qui s'occupe de quoi",
                    ),
                    Sub(
                        id="sc_hebergement_b",
                        label="Hébergement communiqué aux groupes concernés",
                        hint="Tout le monde sait où il dort et c'est plus à nous de gérer !",
                    ),
                ),
            ),
        ),
    ),
    Step(
        id="s_salle",
        num="Bloc 4",
        title="Salle et Admin",
        items=(
            Item(
                id="ss_coordination",
                label="Coordination pour chercher la salle",
                hint="Identifier le(s) bonne(s) personne(s) avec qui partager le boulot",
            ),
            Item(
                id="ss_trouvee",
                label="Salle trouvée",
                hint="On peut remplir le lieu dans l'en-tête \\o/",
            ),
            Item(
                id="ss_devis_recu",
                label="Devis reçu",
                hint="On a reçu la proposition tarifaire de la salle",
            ),
            Item(id="ss_devis_transmis", label="Devis transmis au trésorier"),
            Item(id="ss_devis_signe", label="Devis signé renvoyé"),
            Item(
                id="ss_contrat_recu",
                label="Contrat reçu",
                hint="Ça peut être un contrat, des CGU, une convention...",
            ),
            Item(
                id="ss_contrat_complete",
                label="Contrat complété",
                hint="Souvent avec le nom du groupe, le nombre de personnes, la sonorisation...",
            ),
            Item(id="ss_contrat_transmis", label="Contrat transmis au bureau"),
            Item(id="ss_contrat_signe", label="Contrat signé renvoyé"),
        ),
    ),
    Step(
        id="s_date",
        num="Bloc 5",
        title="Date",
        items=(
            Item(id="sd_sondage", label="Sondage/Frama envoyé"),
            Item(id="sd_depile", label="Sondage/Frama dépilé"),
            Item(
                id="sd_dates_envoyees",
                label="Dates possibles envoyées à la salle... ou inversement",
                hint="Ça va sans doute être un ping pong avant qu'on arrive à trouver une date commune",
            ),
            Item(
                id="sd_date_ok",
                label="Date choisie",
                hint="On peut remplir la date dans l'en-tête \\o/",
            ),
            Item(
                id="sap_maj_negiagenda",
                label="MAJ NegiAgenda",
                hint='Enlever les dates caduques, enlever le "?" de la bonne date',
            ),
        ),
    ),
    Step(
        id="s_moodle",
        num="Bloc 6",
        title="Discord & Moodle",
        items=(
            Item(
                id="sg_discord",
                label="Création du chan Discord du concert",
                hint="Demander à Vincent",
            ),
            Item(
                id="sm_discord_orga",
                label="Création du chan Discord d'orga du concert",
                hint="Demander de nouveau à Vincent",
            ),
            Item(
                id="sm_cours",
                label="Création du cours Moodle",
                hint="Demander à Eve ou au Bureau.",
            ),
            Item(
                id="sm_infos",
                label="Informations basiques",
                hint="Zone texte et média : lieu, heure (mettre ? si inconnu).",
            ),
            Item(
                id="sm_poireaux",
                label="Poireaux présents",
                hint="Créer la section et la remplir avec les infos du sondage préalable.",
            ),
            Item(
                id="sm_recap",
                label="Mail de récap",
                hint=(
                    "Objet : [Concert] Nom - Date. Acter le concert, copier le lien "
                    "Moodle, demander de prévenir si changement."
                ),
            ),
        ),
    ),
    Step(
        id="s_scenario",
        num="Bloc 7",
        title="Scénario",
        conditional_key="sg_scenario",
        items=(
            Item(
                id="ssc_equipe",
                label="Team Écriture constituée",
                hint="À voir si auto_role ou autre chose",
            ),
            Item(id="ssc_valide", label="Scénario écrit"),
            Item(id="ssc_pl", label="PL prête à être validée"),
            Item(
                id="ssc_intervenants",
                label="Intervenants externes ?",
                type="yesno",
                hint="Est-ce qu'on fait intervenir une voix off ? des comédiens ? autre chose 🤯?",
            ),
            Item(
                id="ssc_livret",
                label="Livret ?",
                type="yesno",
                subs=(
                    Sub(
                        id="ssc_livret_a",
                        label="Informations rassemblées",
                        hint=(
                            "La liste des chansons, les compositeur.ices, "
                            "interprètes, arrangeur.euse.... est accessible et "
                            "complète dans un Gdoc"
                        ),
                    ),
                    Sub(
                        id="ssc_livret_b",
                        label="Mise en page",
                        hint=(
                            "Le livret est mis en page proprement et les "
                            "illustrations sont placées, le tout en suivant les "
                            "modèles de l'imprimeur."
                        ),
                    ),
                    Sub(id="ssc_livret_c", label="Envoyé à l'impression"),
                    Sub(
                        id="ssc_livret_d",
                        label="Livrets récupérés",
                        note_key="st_ssc_livret_d",
                        note_placeholder="Par qui ?",
                        note_inline=True,
                    ),
                ),
            ),
            Item(
                id="ssc_plan_feu",
                label="Plan feu",
                hint=(
                    "Un document qui reprend les chansons, déplacements et "
                    "lumière souhaitées, le plus d'informations possibles pour "
                    "le régisseur"
                ),
            ),
            Item(id="ssc_transmis", label="Scénario transmis à tout le monde"),
        ),
    ),
    Step(
        id="s_pl",
        num="Bloc 8",
        title="Playlist",
        items=(
            Item(id="sp_recue", label="PL reçue des Wacos", simple_only=True),
            Item(
                id="sp_transmise",
                label="Proposition de PL transmise aux Wacos",
                artistic_only=True,
            ),
            Item(id="sp_validation", label="Validation reçue", artistic_only=True),
            Item(
                id="sp_morceaux",
                label="Centralisation des infos morceaux dans un fichier",
                artistic_only=True,
            ),
            Item(
                id="sp_sacem",
                label="SACEM ?",
                type="yesno",
                artistic_only=True,
                subs=(
                    Sub(id="sp_sacem_a", label="Contacter Lia (ou sa succession)"),
                    Sub(id="sp_sacem_b", label="Effectuer la déclaration SACEM"),
                    Sub(
                        id="sp_sacem_c",
                        label="Conserver la confirmation dans le dossier concert",
                    ),
                ),
            ),
        ),
    ),
    Step(
        id="s_repets",
        num="Bloc 9",
        title="Répétitions spécifiques",
        items=(Item(id="sr_repets", label="", type="orga_repets"),),
    ),
    Step(
        id="s_comites",
        num="Bloc 10",
        title="Comités internes",
        items=(
            Item(
                id="sci_comcom",
                label="Informations à transmettre à ComCom (#ComcomConan)",
                type="textfield",
                placeholder="Pack presse, description, logos…",
            ),
            Item(id="sci_cotech", label="CoTech au courant", type="cotech"),
        ),
    ),
    Step(
        id="s_logi",
        num="Bloc 11",
        title="Logistique miamesque",
        items=(
            Item(
                id="sl_catering",
                label="Catering ?",
                type="yesno",
                hint="Est-ce qu'on doit s'occuper de fournir à manger/boire à un moment de l'organisation ?",
                subs=(
                    Sub(
                        id="sl_catering_a",
                        label="Doc de choix envoyé avec deadline",
                        hint=(
                            "Création d'un document dans lequel chaque "
                            "participant.e pourra faire son choix si choix il y "
                            "a. Indiquer une <strong>deadline</strong>"
                        ),
                    ),
                    Sub(
                        id="sl_catering_b",
                        label="Relance faite",
                        hint="On est gentils, on fait <strong>une</strong> relance",
                    ),
                    Sub(
                        id="sl_catering_c",
                        label="Choix validés et fermeture du fichier",
                    ),
                ),
            ),
            Item(
                id="sl_resto",
                label="Resto à organiser ?",
                type="yesno",
                leading_subs=(
                    Sub(
                        id="sl_resto_sondage_envoye",
                        label="Sondage envoyé",
                        hint=(
                            "Préciser le resto et si possible envoyer la carte "
                            "pour savoir qui veut participer"
                        ),
                    ),
                    Sub(
                        id="sl_resto_sondage_depile",
                        label="Sondage dépilé",
                        hint="Est-ce que ça vaut la peine d'organiser pour tout le monde ?",
                    ),
                ),
                extra_notes=(
                    ("st_sl_resto_nom", "Nom du resto…"),
                    ("st_sl_resto_heure", "Heure…"),
                    ("st_sl_resto_nb", "Nombre de personnes…"),
                ),
                subs=(Sub(id="sl_resto_resa", label="Réservation faite"),),
            ),
            Item(
                id="sl_commande",
                label="Commande à faire à l'avance ?",
                type="yesno",
                indent=True,
                visible_when="sl_resto",
                leading_subs=(
                    Sub(
                        id="sl_commande_sondage",
                        label="Choix et sondage envoyé avec deadline",
                        hint=(
                            "GForm ou Moodle : choisir le format qui permet de "
                            "récupérer la commande de chacun avec la somme dûe. "
                            "On a une <strong>deadline</strong> après laquelle "
                            "les gens se débrouilleront tout seuls"
                        ),
                    ),
                ),
                subs=(
                    Sub(
                        id="sl_commande_b",
                        label="Choix validés et fermeture du fichier",
                    ),
                    Sub(id="sl_commande_c", label="Transmis au resto"),
                ),
            ),
        ),
    ),
    Step(
        id="s_extras",
        num="Bloc 12",
        title="Autre chose ?",
        items=(Item(id="s_extras_extras", type="extras", label=""),),
    ),
)


def _is_artistic(state: State) -> bool:
    return state.get("yn_sg_scenario") == "y"


def is_cotech_done(state: State) -> bool:
    """The CoTech item is done once a mode is picked (and, for "passage", transmitted)."""
    mode = state.get("cotech_mode")
    if not mode:
        return False
    if mode == "passage":
        return bool(state.get("cotech_transmis"))
    return True


def item_done(item: Item, state: State) -> bool:
    if item.type in {"collabs_list", "orga_repets", "extras"}:
        return True
    artistic = _is_artistic(state)
    if item.simple_only and artistic:
        return True  # not applicable in this context, don't block
    if item.artistic_only and not artistic:
        return True
    if item.type == "yesno":
        yn = state.get(f"yn_{item.id}")
        if not yn:
            return False
        if yn == "n":
            return True
        return all(state.get(sub.id) for sub in (*item.leading_subs, *item.subs))
    if item.type == "cotech":
        return is_cotech_done(state)
    if item.type == "textfield":
        return bool(state.get(f"tf_{item.id}"))
    return bool(state.get(item.id))


def is_step_done(step: Step, state: State) -> bool:
    if step.conditional_key and state.get(f"yn_{step.conditional_key}") != "y":
        return True
    return all(item_done(item, state) for item in step.items)


@dataclass(frozen=True)
class Progress:
    total: int = 0
    done: int = 0
    pct: int = 0


def _item_progress(item: Item, state: State) -> tuple[int, int]:
    if item.type in {"collabs_list", "orga_repets", "extras"}:
        return 0, 0
    artistic = _is_artistic(state)
    if item.simple_only and artistic:
        return 0, 0
    if item.artistic_only and not artistic:
        return 0, 0
    if item.visible_when and state.get(f"yn_{item.visible_when}") != "y":
        return 0, 0
    if item.type == "yesno":
        yn = state.get(f"yn_{item.id}")
        total, done = 1, (1 if yn else 0)
        if yn == "y":
            all_subs = (*item.leading_subs, *item.subs)
            total += len(all_subs)
            done += sum(1 for sub in all_subs if state.get(sub.id))
        return total, done
    return 1, (1 if item_done(item, state) else 0)


def compute_progress(state: State) -> Progress:
    total = 0
    done = 0
    for step in STEPS:
        if step.conditional_key and state.get(f"yn_{step.conditional_key}") != "y":
            continue
        for item in step.items:
            t, d = _item_progress(item, state)
            total += t
            done += d
    pct = round(done / total * 100) if total else 0
    return Progress(total=total, done=done, pct=pct)


STEPS_BY_ID: dict[str, Step] = {step.id: step for step in STEPS}
ITEMS_BY_ID: dict[str, Item] = {item.id: item for step in STEPS for item in step.items}


def _toggle_keys() -> frozenset[str]:
    keys: set[str] = set()
    for item in ITEMS_BY_ID.values():
        if item.type == "simple":
            keys.add(item.id)
        if item.type == "textfield":
            keys.add(f"tf_{item.id}")
        if item.type == "cotech":
            keys.add("cotech_transmis")
        keys.update(sub.id for sub in (*item.leading_subs, *item.subs))
    return frozenset(keys)


TOGGLE_KEYS: frozenset[str] = _toggle_keys()
YESNO_IDS: frozenset[str] = frozenset(
    item.id for item in ITEMS_BY_ID.values() if item.type == "yesno"
)
TEXT_KEYS: frozenset[str] = (
    frozenset(item.note_key for item in ITEMS_BY_ID.values() if item.note_key)
    | frozenset(key for item in ITEMS_BY_ID.values() for key, _ in item.extra_notes)
    | frozenset(
        sub.note_key
        for item in ITEMS_BY_ID.values()
        for sub in item.subs
        if sub.note_key
    )
    | frozenset(
        f"tft_{item.id}" for item in ITEMS_BY_ID.values() if item.type == "textfield"
    )
    | (
        frozenset({"cotech_text"})
        if any(item.type == "cotech" for item in ITEMS_BY_ID.values())
        else frozenset()
    )
)
COTECH_MODES: frozenset[str] = frozenset(value for value, _label in COTECH_OPTIONS_ORGA)
