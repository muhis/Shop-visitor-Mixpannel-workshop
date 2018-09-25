from weighted_random import random_choice
import requests
import random
import uuid
import json
import logging
from ipaddress import IPv4Address, AddressValueError
from mixpanel import Mixpanel
from constants import *
from typing import List, ClassVar, Any, Optional
import sys
import threading
from random_user import generate_random_user_properties
# Logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


def init_mixpannel_clients(mxp_tokens: List[str]) -> List[Mixpanel]:
    """
    Return a list of mixpannel clients.
    """
    projects: List[Mixpanel] = []
    logger.info('Found %s Mixpannel tokens.', len(mxp_tokens))
    for project_token in mxp_tokens:
        mp = Mixpanel(project_token)
        projects.append(mp)
    logger.info('%s Mixpannel projects ready to go.', len(projects))
    return projects


MXP_PROJECTS = init_mixpannel_clients(mxp_tokens=MIXPANNEL_TOKENS)


def generate_random_ip() ->str:
    """
    Generate random IP address. Copied from
    https://codereview.stackexchange.com/questions/200337/random-ip-address-generator
    with some changes to generate valid looking IP addresses.
    """
    while (True):
        trials: int = 0
        try:
            trials += 1
            # instances an IPv4Address object from those bits
            # generates an integer with 32 random bits
            bits = random.getrandbits(32)
            addr = IPv4Address(bits)
        except AddressValueError:
            continue
        if not addr.is_private or not addr.is_reserved:
            break
    ip_address = str(addr)
    logger.info('Generated %s IP address after %s attempt', ip_address, trials)
    return ip_address


class BaseShopper(object):
    def __init__(self):
        self.uuid = str(uuid.uuid4())  # type: ignore
        random_device_os = random.choice(DEVICE_OS_CHOICES)
        self.user_agent: str = RANDOM_AGENT.random_agent(*random_device_os)
        self.ip_address: str = generate_random_ip()
        self.base_properties: dict = {
            'uuid': self.uuid,
            'user_agent': self.user_agent,
            'ip': self.ip_address,
        }
        self.properties = self.base_properties

    def visit(self, end_point: str, extra: Optional[dict] = None):
        """
        Send mixpannel API a visit metric.
        """
        properties_to_send: dict
        if extra:
            properties_to_send = {**self.properties, **extra}
        else:
            properties_to_send = self.properties
        for project in MXP_PROJECTS:
            project.track(self.uuid, end_point, properties=properties_to_send)


class UnregisteredShopper(BaseShopper):
    pass


class User(BaseShopper):
    """
    A registered customer.
    """

    def __init__(self, properties: Optional[dict] = None) -> None:
        if not properties:
            super().__init__()
        else:
            self.uuid = properties['uuid']
            self.user_agent = properties['user_agent']
            self.ip_address = properties['ip']
        self.user_properties: dict = generate_random_user_properties()
        properties = properties or self.base_properties
        self.properties: dict = {
            **self.user_properties, **properties
        }
        self.add_user_to_all_projects(properties=self.properties)
        users_pool.append(self)

    def _people_set(self, mxp_project: Mixpanel, properties: dict):
        mxp_project.people_set(self.uuid, properties)

    def add_user_to_all_projects(self, properties: dict):
        mxp_project: Optional[Mixpanel] = None
        for mxp_project in MXP_PROJECTS:
            self._people_set(
                mxp_project=mxp_project,
                properties=properties
            )

    @classmethod
    def register_requester(cls, requester: UnregisteredShopper):
        return cls(properties=requester.base_properties)


users_pool: List[User] = []


class Visit(object):
    """
    Simple customer of the website. This might be a registered user or a random unregistered user.
    """
    user_journy: List[str] = []
    user_cart: List[str] = []

    def start(self) -> None:
        self.requester = self.choose_requester()
        self._visit_main_page()

    def choose_requester(self) -> BaseShopper:
        """
        Return a Shopper object
        """
        self.is_registered = random_bool()
        requester: BaseShopper
        if self.is_registered and users_pool:
            requester = random.choice(users_pool)  # type: ignore
        else:
            requester = UnregisteredShopper()
        return requester

    def _visit_main_page(self):
        """
        In main page, the user might visit an item page or drop.
        """
        self.requester.visit('main page')
        self._visit_item_page()

    def _visit_item_page(self):
        """
        In an item page, users can:
        1. Add the item into the cart.
        2. Return to main page.
        3. Drop.
        """
        requester_progressed = random_choice([(True, 70), (False, 30)])
        if requester_progressed:
            product = random_choice(SHOP_PRODUCTS)
            self.requester.visit(
                'Visit item page',
                extra={
                    'item name': product
                }
            )
            self._add_item_to_cart(product)

        else:
            requester_progressed = random_bool()
            if requester_progressed:
                # Let us assume that they need to go to home page.
                self._visit_main_page()

    def _add_item_to_cart(self, item: str):
        add_item_to_cart = random_choice([(True, 70), (False, 30)])
        if add_item_to_cart:
            self.requester.visit(
                'Add item to cart',
                extra={
                    'item name': item
                }
            )
            self.user_cart.append(item)
        else:
            continue_to_checkout = random_choice([(True, 70), (False, 30)])
            if continue_to_checkout:
                self._visit_checkout()
            else:
                user_drop = random_bool()
                if not user_drop:
                    self._visit_main_page()

    def _visit_checkout(self):
        if not self.user_cart:
            return
        requester_progressed = random_choice([(True, 70), (False, 30)])
        if requester_progressed:
            self._visit_register()
            self.requester.visit('Checkout', extra={'items': self.user_cart})
            self.user_cart = []

    def _visit_register(self):
        if self.is_registered or type(self.requester) == User:
            return
        user_registered = random_choice([(True, 70), (False, 30)])
        if user_registered:
            self.requester.visit('Register', extra={'items': self.user_cart})
            self.requester = User.register_requester(self.requester)


def random_bool() -> bool:
    return random.choice([True, False])


def start_a_visit():
    vi = Visit()
    vi.start()


def start_script():
    for _number in range(1000):
        try:
            threading.Thread(target=start_a_visit).start()
        except Exception as err:
            logger.exception(err)


if __name__ == '__main__':
    start_script()
