# assistant/integrations/providers/google/contacts.py

"""
E.V.I.E. - Google Contacts Integration

Phase 9C
"""

from __future__ import annotations

from assistant.integrations.models import (
    Person,
)

from .auth import (
    build_google_service,
)


def google_contacts(
    account_id: str,
    page_size: int = 100,
):
    service = build_google_service(
        account_id,
        "people",
        "v1",
    )


    response = (
        service.people()
        .connections()
        .list(
            resourceName=
                "people/me",

            pageSize=int(
                page_size
            ),

            personFields=(
                "names,"
                "emailAddresses,"
                "phoneNumbers"
            ),
        )
        .execute()
    )


    connections = (
        response.get(
            "connections",
            []
        )
        or []
    )


    people = []


    for raw in connections:

        names = (
            raw.get(
                "names",
                []
            )
            or []
        )


        emails = (
            raw.get(
                "emailAddresses",
                []
            )
            or []
        )


        phones = (
            raw.get(
                "phoneNumbers",
                []
            )
            or []
        )


        display_name = ""


        if names:

            display_name = (
                names[
                    0
                ].get(
                    "displayName",
                    ""
                )
            )


        people.append(
            Person(
                id=str(
                    raw.get(
                        "resourceName",
                        ""
                    )
                ),

                display_name=
                    display_name,

                emails=[
                    item.get(
                        "value"
                    )

                    for item
                    in emails

                    if item.get(
                        "value"
                    )
                ],

                phone_numbers=[
                    item.get(
                        "value"
                    )

                    for item
                    in phones

                    if item.get(
                        "value"
                    )
                ],

                provider_ids={
                    "google":
                        str(
                            raw.get(
                                "resourceName",
                                ""
                            )
                        )
                },

                metadata={},
            )
        )


    return people


def search_google_contacts(
    account_id: str,
    query: str,
    page_size: int = 250,
):
    query = (
        query
        .strip()
        .lower()
    )


    if not query:

        return []


    people = google_contacts(
        account_id,
        page_size=page_size,
    )


    matches = []


    for person in people:

        haystack = " ".join(
            [
                person.display_name,
                *person.emails,
                *person.phone_numbers,
            ]
        ).lower()


        if query in haystack:

            matches.append(
                person
            )


    return matches