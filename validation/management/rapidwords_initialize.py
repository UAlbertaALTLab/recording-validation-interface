from librecval import REPOSITORY_ROOT


def map_function_to_all_rapidwords(f):
    ans = []
    with open(REPOSITORY_ROOT / "private" / "rapidwords.txt", "r") as rapidwords:
        ans = [f(rapidword.strip()) for rapidword in rapidwords]
    return ans
