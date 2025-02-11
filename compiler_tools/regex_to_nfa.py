# Conversion from Regex to NFA

from string import ascii_lowercase, ascii_uppercase
import json


class charType:
    SYMBOL = 1
    CONCAT = 2
    UNION = 3
    KLEENE = 4


class NFAState:
    def __init__(self):
        self.next_state = {}


class ExpressionTree:
    def __init__(self, charType, value=None):
        self.charType = charType
        self.value = value
        self.left = None
        self.right = None


def make_exp_tree(regexp):
    """
    Computes AST from regular expression.
    """
    stack = []
    for c in regexp:
        if c == "|":
            z = ExpressionTree(charType.UNION)
            z.right = stack.pop()
            z.left = stack.pop()
            stack.append(z)
        elif c == ".":
            z = ExpressionTree(charType.CONCAT)
            z.right = stack.pop()
            z.left = stack.pop()
            stack.append(z)
        elif c == "*":
            z = ExpressionTree(charType.KLEENE)
            z.left = stack.pop()
            stack.append(z)
        elif c == "(" or c == ")":
            continue
        else:
            stack.append(ExpressionTree(charType.SYMBOL, c))
    return stack[0]


def compPrecedence(a, b):
    """
    Computes the operator precedence of 2 operator and returns the highest.
    """
    p = ["|", ".", "*"]
    return p.index(a) > p.index(b)


def compute_regex(exp_t):
    """
    Computes the epsilon-NFA from a regular expression AST.
    """
    # returns E-NFA
    if exp_t.charType == charType.CONCAT:
        return do_concat(exp_t)
    elif exp_t.charType == charType.UNION:
        return do_union(exp_t)
    elif exp_t.charType == charType.KLEENE:
        return do_kleene_star(exp_t)
    else:
        return eval_symbol(exp_t)


def eval_symbol(exp_t):
    start = NFAState()
    end = NFAState()

    start.next_state[exp_t.value] = [end]
    return start, end


def do_concat(exp_t):
    left_nfa = compute_regex(exp_t.left)
    right_nfa = compute_regex(exp_t.right)

    left_nfa[1].next_state["$"] = [right_nfa[0]]
    return left_nfa[0], right_nfa[1]


def do_union(exp_t):
    start = NFAState()
    end = NFAState()

    first_nfa = compute_regex(exp_t.left)
    second_nfa = compute_regex(exp_t.right)

    start.next_state["$"] = [first_nfa[0], second_nfa[0]]
    first_nfa[1].next_state["$"] = [end]
    second_nfa[1].next_state["$"] = [end]

    return start, end


def do_kleene_star(exp_t):
    start = NFAState()
    end = NFAState()

    starred_nfa = compute_regex(exp_t.left)

    start.next_state["$"] = [starred_nfa[0], end]
    starred_nfa[1].next_state["$"] = [starred_nfa[0], end]

    return start, end


def arrange_transitions(state, states_done, symbol_table, nfa):

    if state in states_done:
        return

    states_done.append(state)

    for symbol in list(state.next_state):
        if symbol not in nfa["letters"]:
            nfa["letters"].append(symbol)
        for ns in state.next_state[symbol]:
            if ns not in symbol_table:
                symbol_table[ns] = sorted(symbol_table.values())[-1] + 1
                q_state = "Q" + str(symbol_table[ns])
                nfa["states"].append(q_state)

            nfa["transition_function"]["Q" + str(symbol_table[state])] = nfa[
                "transition_function"
            ].get("Q" + str(symbol_table[state]), []) + [
                (symbol, "Q" + str(symbol_table[ns]))
            ]

        for ns in state.next_state[symbol]:
            arrange_transitions(ns, states_done, symbol_table, nfa)


def final_st_dfs(nfa):
    for st in nfa["states"]:
        count = 0
        count = len([x for x in nfa["transition_function"].get(st, []) if x != st])

        if count == 0 and st not in nfa["final_states"]:
            nfa["final_states"].append(st)


def arrange_nfa(fa):
    nfa = dict()
    nfa["states"] = []
    nfa["letters"] = []
    nfa["transition_function"] = {}
    nfa["start_states"] = []
    nfa["final_states"] = []
    nfa["states"].append("Q1")
    arrange_transitions(fa[0], [], {fa[0]: 1}, nfa)

    nfa["start_states"].append("Q1")
    final_st_dfs(nfa)
    return nfa


def add_concat(regex):
    non_symbols = ["|", "*", ".", "(", ")"]
    new_reg_exp = []

    for current_char in regex:
        if len(new_reg_exp) > 0:
            prev_char = new_reg_exp[-1]
            if (
                prev_char == ")" or prev_char not in non_symbols or prev_char == "*"
            ) and (current_char == "(" or current_char not in non_symbols):
                new_reg_exp.append(".")
        new_reg_exp.append(current_char)
    return new_reg_exp


def compute_postfix(regexp):
    """
    Computes the postfix form of a regular expression
    """
    stk = []
    res = []
    non_symbols = ["|", "*", ".", "(", ")"]
    for c in regexp:
        if c not in non_symbols or c == "*":
            res.append(c)
        elif c == ")":
            while len(stk) > 0 and stk[-1] != "(":
                res.append(stk.pop())
            stk.pop()
        elif c == "(":
            stk.append(c)
        elif len(stk) == 0 or stk[-1] == "(" or compPrecedence(c, stk[-1]):
            stk.append(c)
        else:
            while len(stk) > 0 and stk[-1] != "(" and not compPrecedence(c, stk[-1]):
                res.append(stk.pop())
            stk.append(c)

    while len(stk) > 0:
        res.append(stk.pop())

    return res


def chartype(char):
    """
    Return the class of a character between "digit", "lowercas ascii",
    "uppercase_ascii" and "other".
    """
    if char.isdigit():
        return "digit"
    elif char in ascii_lowercase:
        return "locase"
    elif char in ascii_uppercase:
        return "upcase"
    else:
        return "other"


def regex_to_intervals(reg_exp: str):
    """
    Replaces the letters(and character classes) for a regular expression
    string with ordinal intervals.
    """
    operators = ["|", "*", "(", ")"]
    inter_reg_exp = []
    idx = 0
    while idx < len(reg_exp):
        letter = reg_exp[idx]
        if letter == "[":
            if reg_exp[idx:].find("]") == -1:
                inter_reg_exp.append((ord(letter), ord(letter)))
                idx += 1
                continue
            inter_reg_exp.append("(")
            idx += 1
            letter = reg_exp[idx]

            while letter != "]":
                if idx + 1 < len(reg_exp) and reg_exp[idx + 1] == "-":
                    prev = reg_exp[idx]
                    next = reg_exp[idx + 2]
                    if chartype(prev) != "other" and chartype(prev) == chartype(next):
                        inter_reg_exp.append((ord(prev), ord(next)))
                        idx += 2
                    else:
                        inter_reg_exp.append((ord(letter), ord(letter)))
                else:
                    inter_reg_exp.append((ord(letter), ord(letter)))

                idx += 1
                if idx > len(reg_exp):
                    raise Exception("Invalid regular expression")

                letter = reg_exp[idx]
                if letter != "]":
                    inter_reg_exp.append("|")

            inter_reg_exp.append(")")

        elif letter not in operators:
            inter_reg_exp.append((ord(letter), ord(letter)))
        else:
            inter_reg_exp.append(letter)
        idx += 1

    return inter_reg_exp


def polish_regex(regex):
    reg = regex_to_intervals(regex)
    reg = add_concat(reg)
    reg = compute_postfix(reg)
    return reg


def out_nfa(nfa):
    with open("test_nfa.json", "w") as outjson:
        outjson.write(json.dumps(nfa, indent=4))


def regex_to_nfa(reg_exp):
    pr = polish_regex(reg_exp)
    et = make_exp_tree(pr)
    fa = compute_regex(et)

    return arrange_nfa(fa)
