from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal


def _to_cents(amount) -> int:
    """Convert a monetary amount to integer cents."""
    return int(
        (Decimal(str(amount)) * 100).quantize(
            Decimal(1),
            rounding=ROUND_HALF_UP,
        )
    )


def calculate_balances(transactions) -> dict[int, int]:
    """
    Calculate each user's net balance in cents.

    Positive balance: the user should receive money.
    Negative balance: the user owes money.
    Zero balance: the user is settled.

    Assumptions:
    - transaction.owner_id identifies the payer.
    - transaction.participants contains the people sharing the cost.
    - transaction.items contains items with a price.
    """
    balances = defaultdict(int)

    for transaction in transactions:
        total = sum(_to_cents(item.price) for item in transaction.items)

        participant_ids = sorted(
            {participant.id for participant in transaction.participants}
        )

        if not participant_ids:
            if total:
                raise ValueError(f"Transaction {transaction.id} has no participants.")
            continue

        balances[transaction.owner_id] += total

        share, remainder = divmod(total, len(participant_ids))

        for index, user_id in enumerate(participant_ids):
            owed = share + (index < remainder)
            balances[user_id] -= owed

    return dict(balances)


def calculate_settlements(
    balances: dict[int, int],
) -> list[dict]:
    """
    Minimize the number of transfers needed to settle net balances.

    Amounts are returned in cents.
    """
    debtors = [
        [user_id, -balance] for user_id, balance in balances.items() if balance < 0
    ]

    creditors = [
        [user_id, balance] for user_id, balance in balances.items() if balance > 0
    ]

    debtors.sort(key=lambda entry: entry[0])
    creditors.sort(key=lambda entry: entry[0])

    settlements = []
    debtor_index = 0
    creditor_index = 0

    while debtor_index < len(debtors) and creditor_index < len(creditors):
        debtor_id, debt = debtors[debtor_index]
        creditor_id, credit = creditors[creditor_index]

        amount = min(debt, credit)

        settlements.append(
            {
                "from_user_id": debtor_id,
                "to_user_id": creditor_id,
                "amount_cents": amount,
            }
        )

        debtors[debtor_index][1] -= amount
        creditors[creditor_index][1] -= amount

        if debtors[debtor_index][1] == 0:
            debtor_index += 1

        if creditors[creditor_index][1] == 0:
            creditor_index += 1

    if debtor_index != len(debtors) or creditor_index != len(creditors):
        raise ValueError("Balances do not sum to zero.")

    return settlements
