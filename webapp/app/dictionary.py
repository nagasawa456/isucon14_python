from .models import Chair, User, Owner


unsent_by_ride: dict[str, list[dict[str, str]]] = {}
latest_status_by_ride: dict[str, str] = {}  

chairs_by_token: dict[str, Chair] = {}
users_by_token: dict[str, User] = {}
owners_by_token: dict[str, Owner] = {}