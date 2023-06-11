from typing import Any, TypedDict

from pydantic import BaseModel


class BaseDockerModel(BaseModel):
    """Base curseforge models"""


class Port(BaseDockerModel):
    PrivatePort: int
    PublicPort: int
    Type: str


class Mount(BaseDockerModel):
    ...


class Image(BaseDockerModel):
    Containers: int
    Created: int
    Id: str
    Labels: dict[str, Any] | None
    ParentId: str
    RepoDigests: list[str] | None
    RepoTags: list[str]
    SharedSize: int
    Size: int
    VirtualSize: int

    def __repr__(self) -> str:
        return f"<Id={self.Id} RepoTags=[{' ,'.join(self.RepoTags)}]>"

    def __str__(self) -> str:
        return self.__repr__()


class Container(BaseDockerModel):
    Id: str
    Names: list[str]
    Image: str
    ImageID: str
    Command: str
    Created: int
    Ports: list[Port]
    SizeRw: int
    SizeRootFs: int
    Labels: dict[str, str]
    State: str
    Status: str
    HostConfig: dict[str, str]
    NetworkSettings: dict[str, Any]
    Mounts: dict[str, Any]


# Typed dicts


class CreateContainerConfig(TypedDict):
    Image: str
    Env: list[str]
    HostConfig: dict[str, Any]
    NetworkingConfig: dict[str, dict]
