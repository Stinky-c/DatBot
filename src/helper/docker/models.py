from typing import Any

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
    Id: str
    ParentId: str
    RepoTags: list[str]
    RepoDigests: list[str] | None
    Created: int
    Size: int
    SharedSize: int
    VirtualSize: int
    Labels: dict[str, Any] | None
    Containers: int

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
