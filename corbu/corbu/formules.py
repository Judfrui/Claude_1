"""Évaluation sûre des formules de métré (ex. « 2 x 3,5 x 0,20 »)."""

import ast
import operator

_OPERATEURS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
}


class FormuleInvalide(ValueError):
    pass


def evaluer(formule: str) -> float:
    """Évalue une expression arithmétique. Accepte la virgule décimale et « x »."""
    texte = (formule or "").strip()
    if not texte:
        return 0.0
    texte = texte.replace(",", ".").replace("×", "*").replace("x", "*").replace("X", "*")
    try:
        arbre = ast.parse(texte, mode="eval")
    except SyntaxError as exc:
        raise FormuleInvalide(f"Formule invalide : {formule}") from exc
    return float(_eval(arbre.body, formule))


def _eval(noeud, formule):
    if isinstance(noeud, ast.Constant) and isinstance(noeud.value, (int, float)):
        return noeud.value
    if isinstance(noeud, ast.BinOp) and type(noeud.op) in _OPERATEURS:
        gauche, droite = _eval(noeud.left, formule), _eval(noeud.right, formule)
        if isinstance(noeud.op, ast.Pow) and abs(droite) > 10:
            raise FormuleInvalide(f"Exposant trop grand : {formule}")
        try:
            return _OPERATEURS[type(noeud.op)](gauche, droite)
        except ZeroDivisionError as exc:
            raise FormuleInvalide(f"Division par zéro : {formule}") from exc
    if isinstance(noeud, ast.UnaryOp) and isinstance(noeud.op, (ast.USub, ast.UAdd)):
        valeur = _eval(noeud.operand, formule)
        return -valeur if isinstance(noeud.op, ast.USub) else valeur
    raise FormuleInvalide(f"Formule invalide : {formule}")
