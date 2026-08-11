"""
E.V.I.E. - Spotify Search and Playback Resolution

Phase 9F
Last Edited: August 10, 2026

Purpose:
    Search Spotify and safely resolve human-readable music requests
    into real Spotify URIs before playback.

Capabilities:
    - media.search
    - media.play
    - media.play_query
    - media.queue_query
"""

from __future__ import annotations

from .api import (
    spotify_get,
    spotify_put,
)

from .playback import (
    spotify_queue_uri,
)


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

def spotify_search(
    account_id: str,
    query: str,
    search_type: str = "track",
    limit: int = 10,
):
    query = (
        str(
            query
        )
        .strip()
    )


    if not query:

        raise ValueError(
            "Spotify search query cannot be empty."
        )


    search_type = (
        str(
            search_type
        )
        .strip()
        .lower()
    )


    allowed_types = {
        "track",
        "artist",
        "album",
        "playlist",
        "show",
        "episode",
    }


    if (
        search_type
        not in allowed_types
    ):

        raise ValueError(
            (
                "Unsupported Spotify search type: "
                f"{search_type}"
            )
        )


    result = spotify_get(
        account_id,
        "/search",
        params={
            "q":
                query,

            "type":
                search_type,

            "limit":
                max(
                    1,
                    min(
                        50,
                        int(
                            limit
                        ),
                    ),
                ),
        },
    )


    key = (
        search_type
        + "s"
    )


    container = (
        result.get(
            key,
            {}
        )
        or {}
    )


    return (
        container.get(
            "items",
            []
        )
        or []
    )


# ---------------------------------------------------------------------------
# Play URI
# ---------------------------------------------------------------------------

def spotify_play_uri(
    account_id: str,
    uri: str,
    device_id: str | None = None,
):
    uri = (
        str(
            uri
        )
        .strip()
    )


    if not uri:

        raise ValueError(
            "Spotify URI is required."
        )


    params = {}


    if device_id:

        params[
            "device_id"
        ] = device_id


    if uri.startswith(
        (
            "spotify:track:",
            "spotify:episode:",
        )
    ):

        body = {
            "uris":
                [
                    uri
                ]
        }


    else:

        body = {
            "context_uri":
                uri
        }


    spotify_put(
        account_id,
        "/me/player/play",
        params=
            params,

        json_body=
            body,
    )


    return {
        "action":
            "play",

        "uri":
            uri,

        "device_id":
            device_id,
    }


# ---------------------------------------------------------------------------
# Normalize Track Result
# ---------------------------------------------------------------------------

def _track_summary(
    track: dict,
):
    artists = [
        str(
            artist.get(
                "name",
                "",
            )
        )

        for artist
        in (
            track.get(
                "artists",
                []
            )
            or []
        )

        if artist.get(
            "name"
        )
    ]


    album = (
        track.get(
            "album",
            {}
        )
        or {}
    )


    return {
        "id":
            track.get(
                "id",
                "",
            ),

        "uri":
            track.get(
                "uri",
                "",
            ),

        "name":
            track.get(
                "name",
                "",
            ),

        "artists":
            artists,

        "artist":
            ", ".join(
                artists
            ),

        "album":
            album.get(
                "name",
                "",
            ),

        "duration_ms":
            track.get(
                "duration_ms"
            ),

        "explicit":
            track.get(
                "explicit",
                False,
            ),
    }


# ---------------------------------------------------------------------------
# Search First Track
# ---------------------------------------------------------------------------

def spotify_find_track(
    account_id: str,
    query: str,
):
    results = spotify_search(
        account_id=
            account_id,

        query=
            query,

        search_type=
            "track",

        limit=
            5,
    )


    if not results:

        raise RuntimeError(
            (
                "Spotify did not find a track for: "
                f"{query}"
            )
        )


    return results[
        0
    ]


# ---------------------------------------------------------------------------
# Play Query
# ---------------------------------------------------------------------------

def spotify_play_query(
    account_id: str,
    query: str,
    device_id: str | None = None,
):
    track = spotify_find_track(
        account_id=
            account_id,

        query=
            query,
    )


    uri = (
        track.get(
            "uri",
            ""
        )
    )


    if not uri:

        raise RuntimeError(
            "Spotify search result had no URI."
        )


    spotify_play_uri(
        account_id=
            account_id,

        uri=
            uri,

        device_id=
            device_id,
    )


    summary = (
        _track_summary(
            track
        )
    )


    summary[
        "action"
    ] = "play_query"


    summary[
        "query"
    ] = query


    summary[
        "device_id"
    ] = device_id


    return summary


# ---------------------------------------------------------------------------
# Queue Query
# ---------------------------------------------------------------------------

def spotify_queue_query(
    account_id: str,
    query: str,
    device_id: str | None = None,
):
    track = spotify_find_track(
        account_id=
            account_id,

        query=
            query,
    )


    uri = (
        track.get(
            "uri",
            ""
        )
    )


    if not uri:

        raise RuntimeError(
            "Spotify search result had no URI."
        )


    spotify_queue_uri(
        account_id=
            account_id,

        uri=
            uri,

        device_id=
            device_id,
    )


    summary = (
        _track_summary(
            track
        )
    )


    summary[
        "action"
    ] = "queue_query"


    summary[
        "query"
    ] = query


    summary[
        "device_id"
    ] = device_id


    return summary