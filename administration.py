#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This is just a module for administration purpose.
The idea is to leave PyFunceble run this script in order to get less headache
while debugging environnements.

Authors:
    - @Funilrys, Nissar Chababy <contactTAfunilrysTODcom>

Contributors:
    Let's contribute !

    @GitHubUsername, Name, Email (optional)
"""
# pylint:disable=bad-continuation

from PyFunceble import test as domain_availability_check
from PyFunceble.check import Check
from ultimate_hosts_blacklist_the_whitelist import clean_list_with_official_whitelist

from update import Helpers, Settings, path, strftime

INFO = {}


PYFUNCEBLE_CONFIGURATION = {"no_whois": True}
PYFUNCEBLE_CONFIGURATION_VOLATILE = {"no_whois": True, "no_special": True}


def get_administration_file():
    """
    Get the administation file content.
    """

    if path.isfile(Settings.repository_info):
        content = Helpers.File(Settings.repository_info).read()
        INFO.update(Helpers.Dict().from_json(content))
    else:
        raise Exception("Unable to find the administration file.")


def update_adminisation_file():
    """
    Update what should be updated.
    """

    INFO.update({"currently_under_test": str(int(False)), "last_test": strftime("%s")})


def save_administration_file():
    """
    Save the current state of the administration file content.
    """

    Helpers.Dict(INFO).to_json(Settings.repository_info)


def _is_special_pyfunceble(element):
    """
    Check if the given element is a SPECIAL.
    """

    if ".blogspot." in element:
        return True

    should_endswith = [
        ".doubleclick.net",
        ".liveadvert.com",
        ".skyrock.com",
        ".tumblr.com",
        ".wordpress.com",
    ]

    for marker in should_endswith:
        if element.endswith(marker):
            return True

    return False


def generate_extra_files():  # pylint: disable=too-many-branches
    """
    Update/Create `clean.list`, `volatile.list` and `whitelisted.list`.
    """

    if bool(int(INFO["clean_original"])):  # pylint: disable=too-many-nested-blocks
        clean_list = temp_clean_list = volatile_list = []

        list_special_content = Helpers.Regex(
            Helpers.File(Settings.file_to_test).to_list(), r"ALL\s"
        ).matching_list()

        active = Settings.current_directory + "output/domains/ACTIVE/list"
        inactive = Settings.current_directory + "output/domains/INACTIVE/list"

        if path.isfile(active):
            temp_clean_list.extend(
                Helpers.Regex(Helpers.File(active).to_list(), r"^#").not_matching_list()
                + list_special_content
            )

        if path.isfile(inactive):
            for element in Helpers.Regex(
                Helpers.File(inactive).to_list(), r"^#"
            ).not_matching_list():
                if (
                    element
                    and _is_special_pyfunceble(element)
                    and domain_availability_check(
                        element, config=PYFUNCEBLE_CONFIGURATION_VOLATILE
                    ).lower()
                    == "active"
                ):
                    if not Check(element).is_subdomain():
                        if (
                            element.startswith("www.")
                            and domain_availability_check(
                                element[4:], config=PYFUNCEBLE_CONFIGURATION_VOLATILE
                            ).lower()
                            == "active"
                        ):
                            volatile_list.append(element[4:])
                        else:
                            if (
                                domain_availability_check(
                                    "www.{}".format(element),
                                    config=PYFUNCEBLE_CONFIGURATION_VOLATILE,
                                ).lower()
                                == "active"
                            ):
                                volatile_list.append("www.{}".format(element))
                    volatile_list.append(element)

        temp_clean_list = Helpers.List(temp_clean_list).format()
        volatile_list = Helpers.List(volatile_list).format()

        for element in temp_clean_list:
            if element:
                if (
                    not Check(element).is_subdomain()
                    and Check(element).is_domain_valid()
                ):
                    if (
                        element.startswith("www.")
                        and domain_availability_check(
                            element[4:], config=PYFUNCEBLE_CONFIGURATION
                        ).lower()
                        == "active"
                    ):
                        clean_list.append(element[4:])
                    else:
                        if (
                            domain_availability_check(
                                "www.{}".format(element),
                                config=PYFUNCEBLE_CONFIGURATION,
                            ).lower()
                            == "active"
                        ):
                            clean_list.append("www.{}".format(element))
                clean_list.append(element)

        clean_list = Helpers.List(clean_list).format()
        whitelisted = clean_list_with_official_whitelist(clean_list)

        volatile_list.extend(clean_list)
        volatile_list = Helpers.List(volatile_list).format()

        Helpers.File(Settings.clean_list_file).write(
            "\n".join(clean_list), overwrite=True
        )

        Helpers.File(Settings.whitelisted_list_file).write(
            "\n".join(whitelisted), overwrite=True
        )

        Helpers.File(Settings.volatile_list_file).write(
            "\n".join(volatile_list), overwrite=True
        )

        Helpers.File("whitelisting.py").delete()


if __name__ == "__main__":
    get_administration_file()
    update_adminisation_file()
    save_administration_file()

    generate_extra_files()
