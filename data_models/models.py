from dataclasses import dataclass, field


@dataclass(order=True, frozen=True)
class Card:
    sort_index: str = field(init=False, repr=False)
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

    def _post_init__(self):
        object.__setattr__(self, 'sort_index', self.name)

    def __str__(self):
        return f'Name: {self.name} \nType: {self.group} \nCost:{self.cost}  Element:{self.element} \nEffect:{self.text}'