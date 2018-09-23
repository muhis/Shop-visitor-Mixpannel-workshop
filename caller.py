import random
import uuid
import json
from ipaddress import IPv4Address, AddressValueError
from mixpanel import Mixpanel
from random_useragent.random_useragent import Randomize
from typing import List, ClassVar, Any, Optional

MIXPANNEL_TOKENS: List[str] = []
RANDOM_USERS_URL: str = 'https://randomuser.me/api/'
RANDOM_AGENT: Randomize = Randomize()


def init_mixpannel_clients(mxp_tokens: List[str]) -> List[Mixpanel]:
    """
    Return a list of mixpannel clients.
    """
    projects: List[Mixpanel]
    for project_token in mxp_tokens:
        mp = Mixpanel(project_token)
        projects.append(mp)
    return projects


MXP_PROJECTS = init_mixpannel_clients(mxp_token=MIXPANNEL_TOKENS)


def generate_random_ip() ->str:
    """
    Generate random IP address. Copied from
    https://codereview.stackexchange.com/questions/200337/random-ip-address-generator
    with some changes to generate valid looking IP addresses.
    """
    bits = random.getrandbits(32)  # generates an integer with 32 random bits
    while (True):
        try:
            # instances an IPv4Address object from those bits
            addr = IPv4Address(bits)
        except AddressValueError:
            continue
        if not addr.is_private:
            break
    return str(addr)  # get the IPv4Address object's string representation


class BaseShopper(object):
    def __init__(self):
        self.uuid = str(uuid.uuid4())  # type: ignore
        self.user_agent: str = str(RANDOM_AGENT.random_agent)
        self.ip_address: str = generate_random_ip()
        self.base_properties: dict = {
            'uuid': self.uuid,
            'user_agent': self.user_agent,
            'ip': self.ip_address,
        }
        self.properties = self.base_properties

    def visit(self, end_point: str, client: Mixpanel):
        """
        Send mixpannel API a visit metric.
        """
        client.track(self.uuid, end_point, properties=self.properties)


class UnregisteredShopper(BaseShopper):
    pass


class User(BaseShopper):
    """
    A registered customer.
    """

    def __init__(self):
        super()
        self.user_properties: dict = json.loads(
            requests.get(url=RANDOM_USERS_URL)
        )
        properties: dict = {
            **self.user_properties, **self.base_properties
        }
        self.add_user_to_all_projects(properties=properties)

    def _people_set(self, mxp_project: Mixpanel, properties: dict):
        mxp_project.people_set(self.uuid, properties)

    def add_user_to_all_projects(self, properties: dict):
        mxp_project: Optional[Mixpanel] = None
        for mxp_project in MXP_PROJECTS:
            self._people_set(
                mxp_project=mxp_project,
                properties=properties
            )


users: List[User] = []


class Visit(object):
    """
    Simple customer of the website. This might be a registered user or a random unregistered user.
    """

    def start(self) -> None:
        self.choose_requester()

    def choose_requester(self) -> BaseShopper:
        """
        Return a Shopper object 
        """
        self.is_registered = random.choice([True, False])
        if self.is_registered and users:
            requester = random.choice[users]  # type: ignore
        else:
            requester = UnregisteredShopper()  # type: ignore
        return requester  # type: ignore
