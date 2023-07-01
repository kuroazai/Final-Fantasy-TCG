import random
from dataclasses import dataclass, field


@dataclass(order=True, frozen=False)
class Card:
    sort_index: str = field(init=True, repr=False)
    name: str
    text: str
    group: str
    element: str
    cost: int
    serial: str
    job : str
    power: int
    catagory: str
    boxset: str
    code: str
    card_img: str
    state: str
    quantity: int
    card_limit: int

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def _post_init__(self):
        object.__setattr__(self, 'sort_index', self.name)

    def __str__(self):
        return f'Name: {self.name} \nType: {self.group} \nCost:{self.cost}  Element:{self.element} \nEffect:{self.text}'

    def update_power(self, deduction: int):
        self.power -= deduction

    def update_state(self, state: str):
        self.state = state

    def update_quantity(self, quantity: int):
        if quantity < 3:
            self.quantity += quantity
        else:
            self.quantity = 3


@dataclass
class CardDeck:
    cards: list = field(default_factory=list)

    def draw(self, number: int):
        # draw n number of cards from top of the deck and pop from list
        drawn_cards = []
        for _ in range(number):
            drawn_cards.append(self.cards.pop(0))
        return drawn_cards

    def add_card_to_hand(self, card):
        self.cards.append(card)

    def remove_card_to_grave(self, card):
        self.cards.remove(card)

    def remove_card_to_banish(self, card):
        self.cards.append(card)

    def shuffle(self):
        random.shuffle(self.cards)

    def __iter__(self):
        return iter(self.cards)

    def __getitem__(self, item):
        return self.cards[item]

    def __len__(self):
        return len(self.cards)
