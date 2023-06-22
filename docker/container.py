import dataclasses
import subprocess
import time
import typing
from contextlib import contextmanager
from copy import copy
from typing import Mapping

from docker.postgres import get_free_port


def _to_args(arg_type, arguments):
    ret = []
    for arg in arguments:
        ret.append(arg_type)
        ret.append(arg)
    return ret


@dataclasses.dataclass(frozen=True, kw_only=True)
class ConnectionParams:
    db: str
    user: str
    password: str
    port: int


@dataclasses.dataclass(frozen=True, kw_only=True)
class WaitRules:
    interval: int
    retries: int


def copied(method):
    def new_method(inst, *args, **options):
        # noinspection PyProtectedMember
        copy_inst = copy(inst)
        return method(copy_inst, *args, **options)
    return new_method


def argument(arg) -> "ClassMethod":
    def method(inst):
        c_inst = copy(inst)
        c_inst.args.append(arg)
        return c_inst
    return method


ClassMethod = typing.Callable[[], typing.Any]


class Image:

    image_name = None
    args = typing.List

    def __init__(self, image):
        self.image_name = image
        self.args = list()

    def __copy__(self):
        d = self.__class__(self.image_name)
        d.args = copy(self.args)
        return d

    interactive = argument("-it")
    daemon = argument("-d")

    @copied
    def env(self, **env):
        for name, value in env.items():
            self.args.append("-e")
            self.args.append(f"{name}={value}")
        return self

    @copied
    def port(self, source, target):
        self.args.append("-p")
        self.args.append(f"{source}:{target}")
        return self

    def run(self):
        args = ["docker", "run"]
        args.extend(self.args)
        args.append(self.image_name)
        return args


class Container:

    container_id = None
    args = typing.List

    def __init__(self, container_id):
        self.container_id = container_id
        self.args = list()

    def _copy(self):
        d = self.__class__(self.container_id)
        d.args = copy(self.args)
        return d

    def stop(self):
        args = ["docker", "stop"]
        args.extend(self.args)
        args.append(self.container_id)
        return args

    def execute(self, command):
        args = ["docker", "exec"]
        args.extend(self.args)
        args.append(self.container_id)
        args.append(command)
        return args


class PostgreContainer:

    container_id: str
    environment: Mapping
    p = None
    wait_rules: WaitRules = WaitRules(interval=5, retries=5)
    params: ConnectionParams = None

    def __init__(self, params=None):
        self.params = params

    def run(self):
        params = self.params
        psdc = (Image("postgres:latest").daemon()
                                        .env(POSTGRES_USER=params.user,
                                             POSTGRES_PASSWORD=params.password,
                                             POSTGRES_DB=params.db)
                                        .port(params.port, "5432"))

        self.p = subprocess.Popen(psdc.run(),
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
        self._register_container()
        self._wait()

    def _register_container(self):
        stdout, stderr = self.p.communicate()
        if stderr:
            raise RuntimeError("Error run container")
        self.container_id = stdout.decode().strip("\n")

    def _wait(self):
        wait_rules = self.wait_rules
        psda = Container(self.container_id)

        for retrie in range(wait_rules.retries):
            self.p = subprocess.Popen(psda.execute("/usr/bin/pg_isready"),
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE)

            stdout, stderr = self.p.communicate()
            if stderr:
                raise RuntimeError(stderr)
            if self.p.returncode:
                time.sleep(wait_rules.interval)

    def stop(self):
        p = subprocess.Popen(Container(self.container_id).stop(),
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        if stderr:
            raise RuntimeError("Postgres container removed with error")


@contextmanager
def temporary_postgres(
        *,
        port=None,
        user="test",
        db_name="test",
        password="test"
):
    if port is None:
        port = get_free_port()

    params = ConnectionParams(db=db_name, port=port, user=user, password=password)
    c = PostgreContainer(params)
    c.run()
    try:
        yield params
    finally:
        c.stop()
