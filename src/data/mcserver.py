import re
from enum import StrEnum
from typing import Any, TypedDict

VERSION_REGEX = re.compile(
    r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
)


class MinecraftVersion(TypedDict):
    major: int
    minor: int
    patch: int


class MCServerConfig(TypedDict):
    cfapikey: str  # Curseforge api key
    routerUrl: str  # Url to mc-router
    hostUrl: str  # Base url for mcservers
    dockerSocket: str  # a docker socket. defaults to `/var/run/docker.sock`
    dockerNetwork: str  # Name identifter for docker network
    extraEnv: dict[str, Any]


#
class ServerTags(StrEnum):
    latest = "latest"
    java8 = "java8"
    java8_jdk = "java8-jdk"
    java8_multiarch = "java8-multiarch"
    java8_openj9 = "java8-openj9"
    java8_graalvm_ce = "java8-graalvm-ce"
    java11 = "java11"
    java11_jdk = "java11-jdk"
    java11_openj9 = "java11-openj9"
    java17 = "java17"
    java17_jdk = "java17-jdk"
    java17_openj9 = "java17-openj9"
    java17_graalvm_ce = "java17-graalvm-ce"
    java17_alpine = "java17-alpine"
    java19 = "java19"


class MinecraftVersions(StrEnum):
    # 1.19
    v_1_19_4 = "1.19.4"
    v_1_19_3 = "1.19.3"
    v_1_19_2 = "1.19.2"
    v_1_19_1 = "1.19.1"
    v_1_19 = "1.19"
    # 1.18
    v_1_18_2 = "1.18.2"
    v_1_18_1 = "1.18.1"
    v_1_18 = "1.18"
    # 1.17
    v_1_17_1 = "1.17.1"
    v_1_17 = "1.17"
    # 1.6
    v_1_16_5 = "1.16.5"
    v_1_16_4 = "1.16.4"
    v_1_16_3 = "1.16.3"
    v_1_16_2 = "1.16.2"
    v_1_16_1 = "1.16.1"
    v_1_16 = "1.16"
    # 1.15
    v_1_15_2 = "1.15.2"
    v_1_15_1 = "1.15.1"
    v_1_15 = "1.15"
    # 1.14
    v_1_14_4 = "1.14.4"
    v_1_14_3 = "1.14.3"
    v_1_14_2 = "1.14.2"
    v_1_14_1 = "1.14.1"
    v_1_14 = "1.14"
    # 1.13
    v_1_13_2 = "1.13.2"
    v_1_13_1 = "1.13.1"
    v_1_13 = "1.13"
    #1.12
    v_1_12_2 = "1.12.2"
    v_1_12_1 = "1.12.1"
    v_1_12 = "1.12"
    # 1.11
    v_1_11_2 = "1.11.2"
    v_1_11_1 = "1.11.1"
    v_1_11 = "1.11"
    # 1.10
    v_1_10_2 = "1.10.2"
    v_1_10_1 = "1.10.1"
    v_1_10 = "1.10"
    # 1.9
    v_1_9_4 = "1.9.4"
    v_1_9_3 = "1.9.3"
    v_1_9_2 = "1.9.2"
    v_1_9_1 = "1.9.1"
    v_1_9 = "1.9"
    # 1.8
    v_1_8_9 = "1.8.9"
    v_1_8_8 = "1.8.8"
    v_1_8_7 = "1.8.7"
    v_1_8_6 = "1.8.6"
    v_1_8_5 = "1.8.5"
    v_1_8_4 = "1.8.4"
    v_1_8_3 = "1.8.3"
    v_1_8_2 = "1.8.2"
    v_1_8_1 = "1.8.1"
    v_1_8 = "1.8"
    # 1.7
    v_1_7_10 = "1.7.10"
    # unsupported
    v_1_7_9 = "1.7.9"
    v_1_7_8 = "1.7.8"
    v_1_7_7 = "1.7.7"
    v_1_7_6 = "1.7.6"
    v_1_7_5 = "1.7.5"
    v_1_7_4 = "1.7.4"
    v_1_7_3 = "1.7.3"
    v_1_7_2 = "1.7.2"
    v_1_6_4 = "1.6.4"
    v_1_6_2 = "1.6.2"
    v_1_6_1 = "1.6.1"
    v_1_5_2 = "1.5.2"
    v_1_5_1 = "1.5.1"
    v_1_4_7 = "1.4.7"
    v_1_4_5 = "1.4.5"
    v_1_4_6 = "1.4.6"
    v_1_4_4 = "1.4.4"
    v_1_4_2 = "1.4.2"
    v_1_3_2 = "1.3.2"
    v_1_3_1 = "1.3.1"
    v_1_2_5 = "1.2.5"
    v_1_2_4 = "1.2.4"
    v_1_2_3 = "1.2.3"
    v_1_2_2 = "1.2.2"
    v_1_2_1 = "1.2.1"
    v_1_1 = "1.1"
    v_1_0 = "1.0"


def version_parse(value: str) -> MinecraftVersion | None:
    if match := VERSION_REGEX.match(value):
        return match.groupdict()

    return None
