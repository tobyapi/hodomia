"""Available audition sources; comparison stems never become a mixed four-stem set."""


def stems(result):
    return {**result.get('stems', {}), **result.get('separationComparison', {}).get('stems', {})}
