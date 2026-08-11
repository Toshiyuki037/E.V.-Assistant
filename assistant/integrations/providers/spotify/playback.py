"""
E.V.I.E. - Spotify Playback

Phase 9F
Last Edited: August 10, 2026

Purpose:
    Complete Spotify playback-control implementation.

Capabilities:
    - current playback
    - currently playing
    - devices
    - pause / resume
    - next / previous
    - seek
    - volume
    - shuffle
    - repeat
    - queue
    - transfer playback
"""

from __future__ import annotations

from .api import (
    spotify_get,
    spotify_post,
    spotify_put,
)


# ---------------------------------------------------------------------------
# Read Playback
# ---------------------------------------------------------------------------

def spotify_current_playback(
    account_id: str,
):
    return spotify_get(
        account_id,
        "/me/player",
    )


def spotify_currently_playing(
    account_id: str,
):
    return spotify_get(
        account_id,
        "/me/player/currently-playing",
    )


def spotify_devices(
    account_id: str,
):
    result = spotify_get(
        account_id,
        "/me/player/devices",
    )


    return (
        result.get(
            "devices",
            []
        )
        or []
    )


# ---------------------------------------------------------------------------
# Device Params
# ---------------------------------------------------------------------------

def _device_params(
    device_id: str | None,
):
    params = {}


    if device_id:

        params[
            "device_id"
        ] = str(
            device_id
        )


    return params


# ---------------------------------------------------------------------------
# Pause
# ---------------------------------------------------------------------------

def spotify_pause(
    account_id: str,
    device_id: str | None = None,
):
    spotify_put(
        account_id,
        "/me/player/pause",
        params=
            _device_params(
                device_id
            ),
    )


    return {
        "action":
            "pause",

        "paused":
            True,

        "device_id":
            device_id,
    }


# ---------------------------------------------------------------------------
# Resume
# ---------------------------------------------------------------------------

def spotify_resume(
    account_id: str,
    device_id: str | None = None,
):
    spotify_put(
        account_id,
        "/me/player/play",
        params=
            _device_params(
                device_id
            ),
    )


    return {
        "action":
            "resume",

        "playing":
            True,

        "device_id":
            device_id,
    }


# ---------------------------------------------------------------------------
# Next
# ---------------------------------------------------------------------------

def spotify_next(
    account_id: str,
    device_id: str | None = None,
):
    spotify_post(
        account_id,
        "/me/player/next",
        params=
            _device_params(
                device_id
            ),
    )


    return {
        "action":
            "next",

        "skipped":
            "next",

        "device_id":
            device_id,
    }


# ---------------------------------------------------------------------------
# Previous
# ---------------------------------------------------------------------------

def spotify_previous(
    account_id: str,
    device_id: str | None = None,
):
    spotify_post(
        account_id,
        "/me/player/previous",
        params=
            _device_params(
                device_id
            ),
    )


    return {
        "action":
            "previous",

        "skipped":
            "previous",

        "device_id":
            device_id,
    }


# ---------------------------------------------------------------------------
# Volume
# ---------------------------------------------------------------------------

def spotify_set_volume(
    account_id: str,
    volume_percent: int,
    device_id: str | None = None,
):
    volume_percent = max(
        0,
        min(
            100,
            int(
                volume_percent
            ),
        ),
    )


    params = {
        "volume_percent":
            volume_percent,
    }


    if device_id:

        params[
            "device_id"
        ] = device_id


    spotify_put(
        account_id,
        "/me/player/volume",
        params=
            params,
    )


    return {
        "action":
            "volume",

        "volume_percent":
            volume_percent,

        "device_id":
            device_id,
    }


# ---------------------------------------------------------------------------
# Seek
# ---------------------------------------------------------------------------

def spotify_seek(
    account_id: str,
    position_ms: int,
    device_id: str | None = None,
):
    position_ms = max(
        0,
        int(
            position_ms
        ),
    )


    params = {
        "position_ms":
            position_ms,
    }


    if device_id:

        params[
            "device_id"
        ] = device_id


    spotify_put(
        account_id,
        "/me/player/seek",
        params=
            params,
    )


    return {
        "action":
            "seek",

        "position_ms":
            position_ms,

        "device_id":
            device_id,
    }


# ---------------------------------------------------------------------------
# Shuffle
# ---------------------------------------------------------------------------

def spotify_set_shuffle(
    account_id: str,
    state: bool,
    device_id: str | None = None,
):
    params = {
        "state":
            "true"
            if bool(
                state
            )
            else "false",
    }


    if device_id:

        params[
            "device_id"
        ] = device_id


    spotify_put(
        account_id,
        "/me/player/shuffle",
        params=
            params,
    )


    return {
        "action":
            "shuffle",

        "shuffle":
            bool(
                state
            ),

        "device_id":
            device_id,
    }


# ---------------------------------------------------------------------------
# Repeat
# ---------------------------------------------------------------------------

def spotify_set_repeat(
    account_id: str,
    state: str,
    device_id: str | None = None,
):
    state = (
        str(
            state
        )
        .strip()
        .lower()
    )


    aliases = {
        "song":
            "track",

        "track":
            "track",

        "one":
            "track",

        "playlist":
            "context",

        "album":
            "context",

        "context":
            "context",

        "all":
            "context",

        "none":
            "off",

        "false":
            "off",

        "off":
            "off",
    }


    normalized = (
        aliases.get(
            state
        )
    )


    if normalized is None:

        raise ValueError(
            (
                "Spotify repeat state must be "
                "track, context, or off."
            )
        )


    params = {
        "state":
            normalized,
    }


    if device_id:

        params[
            "device_id"
        ] = device_id


    spotify_put(
        account_id,
        "/me/player/repeat",
        params=
            params,
    )


    return {
        "action":
            "repeat",

        "repeat_state":
            normalized,

        "device_id":
            device_id,
    }


# ---------------------------------------------------------------------------
# Queue URI
# ---------------------------------------------------------------------------

def spotify_queue_uri(
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


    params = {
        "uri":
            uri,
    }


    if device_id:

        params[
            "device_id"
        ] = device_id


    spotify_post(
        account_id,
        "/me/player/queue",
        params=
            params,
    )


    return {
        "action":
            "queue",

        "uri":
            uri,

        "device_id":
            device_id,
    }


# ---------------------------------------------------------------------------
# Transfer Playback
# ---------------------------------------------------------------------------

def spotify_transfer_playback(
    account_id: str,
    device_id: str,
    play: bool = False,
):
    device_id = (
        str(
            device_id
        )
        .strip()
    )


    if not device_id:

        raise ValueError(
            "Spotify device_id is required."
        )


    spotify_put(
        account_id,
        "/me/player",
        json_body={
            "device_ids":
                [
                    device_id
                ],

            "play":
                bool(
                    play
                ),
        },
    )


    return {
        "action":
            "transfer",

        "device_id":
            device_id,

        "play":
            bool(
                play
            ),
    }