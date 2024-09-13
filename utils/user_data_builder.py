# user data builder, it checks if the user_id is in the database, if not, it creates a new user, an auth token should be generated.

from config import Session, User
import json

def build_user_data(user_id: str, email: str, name: str, nickname: str, last_ip: str, logins_count: int, created_at: str, updated_at: str, last_login: str, email_verified: bool):
    return {
        "user_id": user_id,
        "email": email,
        "name": name,
        "nickname": nickname,
        "last_ip": last_ip,
        "logins_count": logins_count,
        "created_at": created_at,
        "updated_at": updated_at,
        "last_login": last_login,
        "email_verified": email_verified
    }

def get_user_data(user_id: str):
    session = Session()
    user = session.query(User).filter(User.user_id == user_id).first()
    session.close()
    return user


def create_user_data(user_id: str, email: str, name: str, nickname: str, last_ip: str, logins_count: int, created_at: str, updated_at: str, last_login: str, email_verified: bool):
    session = Session()
    user = User(user_id=user_id, email=email, name=name, nickname=nickname, last_ip=last_ip, logins_count=logins_count, created_at=created_at, updated_at=updated_at, last_login=last_login, email_verified=email_verified)
    session.add(user)
    session.commit()
    session.close()
    return user

def load_json_file(file_path: str):
    with open(file_path, 'r') as file:
        return json.load(file)


# TODO: Check if the user is already in the database, if not, create a new user
def main():
    users = load_json_file('users.json')
    for user in users:
        user_data = build_user_data(user['user_id'], user['email'], user['name'], user['nickname'], user['last_ip'], user['logins_count'], user['created_at'], user['updated_at'], user['last_login'], user['email_verified'])
        create_user_data(user_data)


# Usage
main()




