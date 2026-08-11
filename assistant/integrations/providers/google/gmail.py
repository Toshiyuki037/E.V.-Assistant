"""
E.V.I.E. - Gmail Integration

Created: August 10, 2026
Last Edited: August 10, 2026
Author: Max Maehara

Purpose:
    Provides Gmail read/search and send capabilities.

Capabilities:
    - email.search
    - email.send
"""

from __future__ import annotations

import base64

from email.message import (
    EmailMessage,
)

from googleapiclient.errors import (
    HttpError,
)

from assistant.integrations.connections import (
    get_account,
)

from assistant.integrations.models import (
    Message,
)

from .auth import (
    build_google_service,
)


# ---------------------------------------------------------------------------
# Gmail Availability
# ---------------------------------------------------------------------------

def ensure_gmail_available(
    account_id: str,
):
    account = get_account(
        "google",
        account_id,
    )


    if account is None:

        raise RuntimeError(
            (
                "Google account is not connected: "
                f"{account_id}"
            )
        )


    gmail_available = (
        account.metadata.get(
            "gmail_available"
        )
    )


    if gmail_available is False:

        raise RuntimeError(
            (
                "Gmail is not enabled for this Google account: "
                f"{account_id}."
            )
        )


# ---------------------------------------------------------------------------
# Header Lookup
# ---------------------------------------------------------------------------

def get_header(
    payload: dict,
    name: str,
):
    target = (
        name.lower()
    )


    for header in (
        payload.get(
            "headers",
            []
        )
        or []
    ):

        if (
            str(
                header.get(
                    "name",
                    ""
                )
            ).lower()
            == target
        ):

            return str(
                header.get(
                    "value",
                    "",
                )
            )


    return ""


# ---------------------------------------------------------------------------
# Decode Gmail Body
# ---------------------------------------------------------------------------

def decode_body_data(
    data: str,
):
    if not data:

        return ""


    try:

        padded = (
            data
            + "="
            * (
                -len(
                    data
                )
                % 4
            )
        )


        decoded = (
            base64.urlsafe_b64decode(
                padded.encode(
                    "utf-8"
                )
            )
        )


        return decoded.decode(
            "utf-8",
            errors="replace",
        )


    except Exception:

        return ""


# ---------------------------------------------------------------------------
# Extract Body
# ---------------------------------------------------------------------------

def extract_body(
    payload: dict,
):
    mime_type = (
        payload.get(
            "mimeType",
            "",
        )
    )


    body = (
        payload.get(
            "body",
            {}
        )
        or {}
    )


    data = body.get(
        "data"
    )


    if (
        mime_type
        == "text/plain"
        and data
    ):

        return decode_body_data(
            data
        )


    parts = (
        payload.get(
            "parts",
            []
        )
        or []
    )


    for part in parts:

        if (
            part.get(
                "mimeType"
            )
            == "text/plain"
        ):

            result = extract_body(
                part
            )


            if result:

                return result


    if data:

        return decode_body_data(
            data
        )


    for part in parts:

        result = extract_body(
            part
        )


        if result:

            return result


    return ""


# ---------------------------------------------------------------------------
# Search Gmail
# ---------------------------------------------------------------------------

def google_gmail_search(
    account_id: str,
    query: str,
    max_results: int = 20,
):
    ensure_gmail_available(
        account_id
    )


    service = build_google_service(
        account_id,
        "gmail",
        "v1",
    )


    try:

        response = (
            service.users()
            .messages()
            .list(
                userId=
                    "me",

                q=
                    query,

                maxResults=
                    int(
                        max_results
                    ),
            )
            .execute()
        )


    except HttpError as error:

        status_code = getattr(
            error.resp,
            "status",
            None,
        )


        raise RuntimeError(
            (
                "Gmail request failed for "
                f"{account_id}. "
                f"HTTP status: {status_code}"
            )
        ) from error


    references = (
        response.get(
            "messages",
            []
        )
        or []
    )


    messages = []


    for reference in references:

        message_id = (
            reference.get(
                "id"
            )
        )


        if not message_id:

            continue


        raw = (
            service.users()
            .messages()
            .get(
                userId=
                    "me",

                id=
                    message_id,

                format=
                    "full",
            )
            .execute()
        )


        payload = (
            raw.get(
                "payload",
                {}
            )
            or {}
        )


        recipients = (
            get_header(
                payload,
                "To",
            )
        )


        messages.append(
            Message(
                id=str(
                    raw.get(
                        "id",
                        "",
                    )
                ),

                provider=
                    "google",

                account_id=
                    account_id,

                sender=
                    get_header(
                        payload,
                        "From",
                    ),

                recipients=[
                    value.strip()

                    for value
                    in recipients.split(
                        ","
                    )

                    if value.strip()
                ],

                subject=
                    get_header(
                        payload,
                        "Subject",
                    ),

                body=
                    extract_body(
                        payload
                    ),

                timestamp=
                    get_header(
                        payload,
                        "Date",
                    ),

                conversation_id=str(
                    raw.get(
                        "threadId",
                        "",
                    )
                ),

                metadata={
                    "snippet":
                        raw.get(
                            "snippet",
                            "",
                        ),

                    "label_ids":
                        raw.get(
                            "labelIds",
                            [],
                        ),
                },
            )
        )


    return messages


# ---------------------------------------------------------------------------
# Send Gmail
# ---------------------------------------------------------------------------

def google_gmail_send(
    account_id: str,
    to: str,
    subject: str,
    body: str,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
):
    """
    Sends an email through the connected Gmail account.

    This is intentionally a write action and should be gated by the
    Phase 6/7 approval system when exposed to natural-language tools.
    """

    ensure_gmail_available(
        account_id
    )


    to = (
        str(
            to
        )
        .strip()
    )


    subject = (
        str(
            subject
        )
        .strip()
    )


    if not to:

        raise ValueError(
            "Email recipient is required."
        )


    message = EmailMessage()


    message[
        "To"
    ] = to


    message[
        "Subject"
    ] = subject


    account = get_account(
        "google",
        account_id,
    )


    if (
        account is not None
        and account.email
    ):

        message[
            "From"
        ] = account.email


    if cc:

        message[
            "Cc"
        ] = ", ".join(
            cc
        )


    if bcc:

        message[
            "Bcc"
        ] = ", ".join(
            bcc
        )


    message.set_content(
        str(
            body
        )
    )


    encoded = (
        base64.urlsafe_b64encode(
            message.as_bytes()
        )
        .decode(
            "utf-8"
        )
    )


    service = build_google_service(
        account_id,
        "gmail",
        "v1",
    )


    result = (
        service.users()
        .messages()
        .send(
            userId=
                "me",

            body={
                "raw":
                    encoded,
            },
        )
        .execute()
    )


    return {
        "message_id":
            result.get(
                "id",
                "",
            ),

        "thread_id":
            result.get(
                "threadId",
                "",
            ),

        "to":
            to,

        "subject":
            subject,

        "sent":
            True,
    }