import datetime

from CTFd.models import db
from ..models import WhaleConfig, WhaleContainer, WhaleRedirectTemplate


class DBConfig(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        configs = WhaleConfig.query.all()
        for c in configs:
            self[str(c.key)] = str(c.value)

    def get(self, k, default=""):
        if k not in self:
            self[k] = default
        return super().__getitem__(k)

    def __getitem__(self, item):
        return self.get(item)

    def __setitem__(self, key, value):
        DBConfig.set_config(key, value)
        super().__setitem__(key, value)

    @staticmethod
    def get_config(key, default=""):
        result = WhaleConfig.query.filter_by(key=key).first()
        if not result:
            DBConfig.set_config(key, default)
            return default
        return result.value

    @staticmethod
    def set_config(key, value):
        DBConfig.set_all_configs({key: value})

    @staticmethod
    def get_all_configs():
        return DBConfig()

    @staticmethod
    def set_all_configs(configs):
        for c in configs.items():
            q = db.session.query(WhaleConfig)
            q = q.filter(WhaleConfig.key == c[0])
            record = q.one_or_none()

            if record:
                record.value = c[1]
                db.session.commit()
            else:
                config = WhaleConfig(key=c[0], value=c[1])
                db.session.add(config)
                db.session.commit()


class DBContainer:
    @staticmethod
    def create_container_record(user_id, challenge_id, port=0, container_type="challenge"):
        container = WhaleContainer(
            user_id=user_id, challenge_id=challenge_id, port=port, container_type=container_type)
        db.session.add(container)
        db.session.commit()

        return container

    @staticmethod
    def get_current_containers(user_id, container_type="challenge"):
        q = db.session.query(WhaleContainer)
        q = q.filter(WhaleContainer.user_id == user_id)
        q = q.filter(WhaleContainer.container_type == container_type)
        return q.first()

    @staticmethod
    def get_container_by_port(port):
        q = db.session.query(WhaleContainer)
        q = q.filter(WhaleContainer.port == port)
        return q.first()

    @staticmethod
    def remove_container_record(user_id, container_type="challenge"):
        q = db.session.query(WhaleContainer)
        q = q.filter(WhaleContainer.user_id == user_id)
        q = q.filter(WhaleContainer.container_type == container_type)
        q.delete()
        db.session.commit()

    @staticmethod
    def get_all_expired_container():
        timeout = int(DBConfig.get_config("docker_timeout", "3600"))

        try:
            # Try using the model with container_type
            q = db.session.query(WhaleContainer)
            q = q.filter(
                WhaleContainer.start_time <
                datetime.datetime.now() - datetime.timedelta(seconds=timeout)
            )
            return q.all()
        except Exception as e:
            # If that fails, try a direct SQL query
            try:
                from sqlalchemy import text
                result = db.engine.execute(text(
                    "SELECT id, user_id, challenge_id, start_time, renew_count, status, uuid, port, flag "
                    "FROM whale_container "
                    "WHERE start_time < DATE_SUB(NOW(), INTERVAL :timeout SECOND)"
                ), {"timeout": timeout})

                # Convert to WhaleContainer objects
                containers = []
                for row in result:
                    container = WhaleContainer(
                        user_id=row[1],
                        challenge_id=row[2],
                        port=row[7]
                    )
                    container.id = row[0]
                    container.start_time = row[3]
                    container.renew_count = row[4]
                    container.status = row[5]
                    container.uuid = row[6]
                    container.flag = row[8]
                    # Set default container_type
                    container.container_type = "challenge"
                    containers.append(container)
                return containers
            except Exception as inner_e:
                # If all else fails, return an empty list
                print(f"[CTFd-Whale] Error getting expired containers: {str(e)} -> {str(inner_e)}")
                return []

    @staticmethod
    def get_all_alive_container():
        timeout = int(DBConfig.get_config("docker_timeout", "3600"))

        try:
            # Try using the model with container_type
            q = db.session.query(WhaleContainer)
            q = q.filter(
                WhaleContainer.start_time >=
                datetime.datetime.now() - datetime.timedelta(seconds=timeout)
            )
            return q.all()
        except Exception as e:
            # If that fails, try a direct SQL query
            try:
                from sqlalchemy import text
                result = db.engine.execute(text(
                    "SELECT id, user_id, challenge_id, start_time, renew_count, status, uuid, port, flag "
                    "FROM whale_container "
                    "WHERE start_time >= DATE_SUB(NOW(), INTERVAL :timeout SECOND)"
                ), {"timeout": timeout})

                # Convert to WhaleContainer objects
                containers = []
                for row in result:
                    container = WhaleContainer(
                        user_id=row[1],
                        challenge_id=row[2],
                        port=row[7]
                    )
                    container.id = row[0]
                    container.start_time = row[3]
                    container.renew_count = row[4]
                    container.status = row[5]
                    container.uuid = row[6]
                    container.flag = row[8]
                    # Set default container_type
                    container.container_type = "challenge"
                    containers.append(container)
                return containers
            except Exception as inner_e:
                # If all else fails, return an empty list
                print(f"[CTFd-Whale] Error getting alive containers: {str(e)} -> {str(inner_e)}")
                return []

    @staticmethod
    def get_all_container():
        try:
            # Try using the model with container_type
            q = db.session.query(WhaleContainer)
            return q.all()
        except Exception as e:
            # If that fails, try a direct SQL query without container_type
            try:
                from sqlalchemy import text
                result = db.engine.execute(text(
                    "SELECT id, user_id, challenge_id, start_time, renew_count, status, uuid, port, flag "
                    "FROM whale_container"
                ))
                # Convert to WhaleContainer objects
                containers = []
                for row in result:
                    container = WhaleContainer(
                        user_id=row[1],
                        challenge_id=row[2],
                        port=row[7]
                    )
                    container.id = row[0]
                    container.start_time = row[3]
                    container.renew_count = row[4]
                    container.status = row[5]
                    container.uuid = row[6]
                    container.flag = row[8]
                    # Set default container_type
                    container.container_type = "challenge"
                    containers.append(container)
                return containers
            except Exception as inner_e:
                # If all else fails, return an empty list
                print(f"[CTFd-Whale] Error getting containers: {str(e)} -> {str(inner_e)}")
                return []

    @staticmethod
    def get_all_alive_container_page(page_start, page_end):
        timeout = int(DBConfig.get_config("docker_timeout", "3600"))

        try:
            # Try using the model with container_type
            q = db.session.query(WhaleContainer)
            q = q.filter(
                WhaleContainer.start_time >=
                datetime.datetime.now() - datetime.timedelta(seconds=timeout)
            )
            q = q.slice(page_start, page_end)
            return q.all()
        except Exception as e:
            # If that fails, try a direct SQL query
            try:
                from sqlalchemy import text
                result = db.engine.execute(text(
                    "SELECT id, user_id, challenge_id, start_time, renew_count, status, uuid, port, flag "
                    "FROM whale_container "
                    "WHERE start_time >= DATE_SUB(NOW(), INTERVAL :timeout SECOND) "
                    "LIMIT :offset, :limit"
                ), {"timeout": timeout, "offset": page_start, "limit": page_end - page_start})

                # Convert to WhaleContainer objects
                containers = []
                for row in result:
                    container = WhaleContainer(
                        user_id=row[1],
                        challenge_id=row[2],
                        port=row[7]
                    )
                    container.id = row[0]
                    container.start_time = row[3]
                    container.renew_count = row[4]
                    container.status = row[5]
                    container.uuid = row[6]
                    container.flag = row[8]
                    # Set default container_type
                    container.container_type = "challenge"
                    containers.append(container)
                return containers
            except Exception as inner_e:
                # If all else fails, return an empty list
                print(f"[CTFd-Whale] Error getting paged containers: {str(e)} -> {str(inner_e)}")
                return []

    @staticmethod
    def get_all_alive_container_count():
        timeout = int(DBConfig.get_config("docker_timeout", "3600"))

        try:
            # Try using the model with container_type
            q = db.session.query(WhaleContainer)
            q = q.filter(
                WhaleContainer.start_time >=
                datetime.datetime.now() - datetime.timedelta(seconds=timeout)
            )
            return q.count()
        except Exception as e:
            # If that fails, try a direct SQL query
            try:
                from sqlalchemy import text
                result = db.engine.execute(text(
                    "SELECT COUNT(*) FROM whale_container "
                    "WHERE start_time >= DATE_SUB(NOW(), INTERVAL :timeout SECOND)"
                ), {"timeout": timeout})

                # Get the count from the result
                for row in result:
                    return row[0]
                return 0
            except Exception as inner_e:
                # If all else fails, return 0
                print(f"[CTFd-Whale] Error getting container count: {str(e)} -> {str(inner_e)}")
                return 0


class DBRedirectTemplate:
    @staticmethod
    def get_all_templates():
        return WhaleRedirectTemplate.query.all()

    @staticmethod
    def create_template(name, access_template, frp_template):
        if WhaleRedirectTemplate.query.filter_by(key=name).first():
            return  # already existed
        db.session.add(WhaleRedirectTemplate(
            name, access_template, frp_template
        ))
        db.session.commit()

    @staticmethod
    def delete_template(name):
        WhaleRedirectTemplate.query.filter_by(key=name).delete()
        db.session.commit()
