import json
from pprint import pprint
from copy import deepcopy
import heapq


def set_e_closure(state_set: set[str], nfa):
    """
    Calculates the epsilon-closure of a set of states of a NFA.
    """
    e_closure = state_set
    while True:
        e_closure_prime = deepcopy(e_closure)
        for state in e_closure:
            e_closure_prime |= {
                x[1]
                for x in nfa["transition_function"].get(state, state)
                if x[0] == "$"
            }

        if e_closure_prime == e_closure:
            break
        else:
            e_closure = e_closure_prime

    return e_closure


def move(state_set: set[str], letter: str, nfa: dict):
    """
    Calculates the state set that results from moving from a state in `state_set`
    with a given `letter`
    """
    move_set = set()
    move_set_old = set()
    S = set()

    for state in state_set:
        move_set_old |= {
            x[1] for x in nfa["transition_function"].get(state, []) if x[0] == letter
        }

    for state in state_set:
        for label, state in nfa["transition_function"].get(state, []):
            if label != "$" and intersection(label, letter):
                move_set.add(state)
                S.add(tuple(intersection(label, letter)))

    return move_set, S


def intersection(inter_a, inter_b):
    min_inter = min([inter_a, inter_b])
    max_inter = max([inter_a, inter_b])

    if max_inter[0] <= min_inter[1]:
        return [max_inter[0], min_inter[1]]
    else:
        return []


def set_contruction(nfa: dict):
    """
    Set construction of a DFA from a eps-NFA
    """
    dfa = dict()
    dfa["letters"] = [x for x in nfa["letters"] if x != "$"]
    dfa["transition_function"] = dict()
    dfa["states"] = [set_e_closure(set(nfa["start_states"]), nfa)]
    dfa["start_states"] = [set_e_closure(set(nfa["start_states"]), nfa)]
    dfa["final_states"] = []

    unmarked = [set_e_closure(set(nfa["start_states"]), nfa)]

    while unmarked:
        A = unmarked.pop()
        for letter in disjoin_intervals(dfa["letters"]):
            state_set, interval = move(A, letter, nfa)

            if not interval:
                continue

            U = set_e_closure(state_set, nfa)

            if U not in dfa["states"]:
                if U & set(nfa["final_states"]):
                    dfa["final_states"].append(U)

                dfa["states"].append(U)
                unmarked.append(U)

            for segment in disjoin_intervals(interval):
                dfa["transition_function"][state_set_to_string(A)] = dfa[
                    "transition_function"
                ].get(state_set_to_string(A), []) + [(segment, state_set_to_string(U))]

    dfa["start_states"] = [state_set_to_string(state) for state in dfa["start_states"]]
    dfa["final_states"] = [state_set_to_string(state) for state in dfa["final_states"]]

    return dfa


def state_set_to_string(state_set: set[str]):
    return ",".join(sorted(list(state_set), key=lambda x: int(x[1:])))


def load_nfa():
    with open("test_nfa.json", "r") as inpjson:
        nfa = json.loads(inpjson.read())
    return nfa


def disjoin_intervals(intervals):
    intervals = list(intervals)
    heapq.heapify(intervals)
    disjoint_intervals = []

    while len(intervals) != 1:
        old_min = heapq.heappop(intervals)
        new_min = heapq.heappop(intervals)

        if old_min[1] >= new_min[0]:
            left = (old_min[0], new_min[0])
            right = (new_min[0] + 1, new_min[1])
            disjoint_intervals.append(left)
            heapq.heappush(intervals, right)
        else:
            disjoint_intervals.append(old_min)
            heapq.heappush(intervals, new_min)
    disjoint_intervals.append(intervals.pop())
    return disjoint_intervals


def consume(string: str, dfa: dict):
    current_state = dfa["start_states"][0]
    for char in string:
        ordinal = ord(char)
        transition = False
        for label, state in dfa["transition_function"][current_state]:
            if ordinal >= label[0] and ordinal <= label[1]:
                current_state = state
                transition = True

        if transition == False:
            return False

    if current_state in dfa["final_states"]:
        return True
    else:
        return False


if __name__ == "__main__":
    nfa = load_nfa()

    dfa = set_contruction(nfa)
    print(consume("carro", dfa))
    print(consume("_hola", dfa))
    print(consume("", dfa))
    print(consume("ab012a", dfa))
    print(consume("ab012a+", dfa))

#     print("Start States")
#     pprint(dfa["start_states"])

#     print("Final States")
#     pprint(dfa["final_states"])

#     print("Transition function")
#     pprint(dfa["transition_function"])
