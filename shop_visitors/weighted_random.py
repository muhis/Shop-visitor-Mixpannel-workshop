"""
Weighted random, based on https://stackoverflow.com/a/5599357
"""
import random
import bisect
from typing import List


def weighted_choice(choices):
    total, cumulative = 0, []
    for c, w in choices:
        total += w
        cumulative.append((total, c))
    r = random.uniform(0, total)
    # return index
    return bisect.bisect(cumulative, (r,))


def random_choice(choice_list: List):
    """
    Return one item from a list of item,weight tuples.
    """
    choice_index = weighted_choice(choice_list)
    return choice_list[choice_index][0]
