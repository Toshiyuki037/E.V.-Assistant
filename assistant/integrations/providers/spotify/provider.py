"""
E.V.I.E. - Spotify Provider Registration

Phase 9F
Last Edited: August 10, 2026
"""

from __future__ import annotations

from assistant.integrations.registry import (
    register_integration_capability,
)

from .auth import (
    connect_spotify_account,
    disconnect_spotify_account,
)

from .playback import (
    spotify_current_playback,
    spotify_currently_playing,
    spotify_devices,
    spotify_next,
    spotify_pause,
    spotify_previous,
    spotify_queue_uri,
    spotify_resume,
    spotify_seek,
    spotify_set_repeat,
    spotify_set_shuffle,
    spotify_set_volume,
    spotify_transfer_playback,
)

from .search import (
    spotify_play_query,
    spotify_play_uri,
    spotify_queue_query,
    spotify_search,
)


# ---------------------------------------------------------------------------
# Unified Media Control
# ---------------------------------------------------------------------------

def spotify_media_control(
    account_id: str,
    action: str,
    device_id: str | None = None,
    query: str | None = None,
    uri: str | None = None,
    volume_percent: int | None = None,
    position_ms: int | None = None,
    state=None,
    play: bool = False,
):
    """
    Unified natural-language-friendly Spotify control gateway.

    Supported actions:
        next
        previous
        pause
        resume
        play
        play_query
        queue
        queue_query
        volume
        seek
        shuffle
        repeat
        transfer
    """

    action = (
        str(
            action
        )
        .strip()
        .lower()
        .replace(
            "-",
            "_",
        )
        .replace(
            " ",
            "_",
        )
    )


    aliases = {
        "skip":
            "next",

        "skip_next":
            "next",

        "next_track":
            "next",

        "back":
            "previous",

        "go_back":
            "previous",

        "previous_track":
            "previous",

        "unpause":
            "resume",

        "start":
            "resume",

        "play_song":
            "play_query",

        "play_track":
            "play_query",

        "queue_song":
            "queue_query",

        "add_to_queue":
            "queue_query",

        "set_volume":
            "volume",

        "set_shuffle":
            "shuffle",

        "set_repeat":
            "repeat",

        "transfer_playback":
            "transfer",
    }


    action = (
        aliases.get(
            action,
            action,
        )
    )


    # -----------------------------------------------------------------------
    # Navigation
    # -----------------------------------------------------------------------

    if action == "next":

        return spotify_next(
            account_id=
                account_id,

            device_id=
                device_id,
        )


    if action == "previous":

        return spotify_previous(
            account_id=
                account_id,

            device_id=
                device_id,
        )


    # -----------------------------------------------------------------------
    # Pause / Resume
    # -----------------------------------------------------------------------

    if action == "pause":

        return spotify_pause(
            account_id=
                account_id,

            device_id=
                device_id,
        )


    if action == "resume":

        return spotify_resume(
            account_id=
                account_id,

            device_id=
                device_id,
        )


    # -----------------------------------------------------------------------
    # Play
    # -----------------------------------------------------------------------

    if action == "play":

        if query:

            return spotify_play_query(
                account_id=
                    account_id,

                query=
                    query,

                device_id=
                    device_id,
            )


        if uri:

            return spotify_play_uri(
                account_id=
                    account_id,

                uri=
                    uri,

                device_id=
                    device_id,
            )


        return spotify_resume(
            account_id=
                account_id,

            device_id=
                device_id,
        )


    if action == "play_query":

        if not query:

            raise ValueError(
                "media.control play_query requires query."
            )


        return spotify_play_query(
            account_id=
                account_id,

            query=
                query,

            device_id=
                device_id,
        )


    # -----------------------------------------------------------------------
    # Queue
    # -----------------------------------------------------------------------

    if action == "queue":

        if query:

            return spotify_queue_query(
                account_id=
                    account_id,

                query=
                    query,

                device_id=
                    device_id,
            )


        if not uri:

            raise ValueError(
                "media.control queue requires query or uri."
            )


        return spotify_queue_uri(
            account_id=
                account_id,

            uri=
                uri,

            device_id=
                device_id,
        )


    if action == "queue_query":

        if not query:

            raise ValueError(
                "media.control queue_query requires query."
            )


        return spotify_queue_query(
            account_id=
                account_id,

            query=
                query,

            device_id=
                device_id,
        )


    # -----------------------------------------------------------------------
    # Volume
    # -----------------------------------------------------------------------

    if action == "volume":

        if volume_percent is None:

            raise ValueError(
                "media.control volume requires volume_percent."
            )


        return spotify_set_volume(
            account_id=
                account_id,

            volume_percent=
                volume_percent,

            device_id=
                device_id,
        )


    # -----------------------------------------------------------------------
    # Seek
    # -----------------------------------------------------------------------

    if action == "seek":

        if position_ms is None:

            raise ValueError(
                "media.control seek requires position_ms."
            )


        return spotify_seek(
            account_id=
                account_id,

            position_ms=
                position_ms,

            device_id=
                device_id,
        )


    # -----------------------------------------------------------------------
    # Shuffle
    # -----------------------------------------------------------------------

    if action == "shuffle":

        if state is None:

            raise ValueError(
                "media.control shuffle requires state."
            )


        if isinstance(
            state,
            str,
        ):

            state = (
                state
                .strip()
                .lower()
                in {
                    "true",
                    "on",
                    "yes",
                    "1",
                    "enable",
                    "enabled",
                }
            )


        return spotify_set_shuffle(
            account_id=
                account_id,

            state=
                bool(
                    state
                ),

            device_id=
                device_id,
        )


    # -----------------------------------------------------------------------
    # Repeat
    # -----------------------------------------------------------------------

    if action == "repeat":

        if state is None:

            raise ValueError(
                "media.control repeat requires state."
            )


        return spotify_set_repeat(
            account_id=
                account_id,

            state=
                str(
                    state
                ),

            device_id=
                device_id,
        )


    # -----------------------------------------------------------------------
    # Transfer
    # -----------------------------------------------------------------------

    if action == "transfer":

        if not device_id:

            raise ValueError(
                "media.control transfer requires device_id."
            )


        return spotify_transfer_playback(
            account_id=
                account_id,

            device_id=
                device_id,

            play=
                bool(
                    play
                ),
        )


    raise ValueError(
        (
            "Unsupported Spotify media action: "
            f"{action}"
        )
    )


# ---------------------------------------------------------------------------
# Provider Registration
# ---------------------------------------------------------------------------

def load_spotify_provider():

    # -----------------------------------------------------------------------
    # Account
    # -----------------------------------------------------------------------

    register_integration_capability(
        provider=
            "spotify",

        name=
            "account.connect",

        function=
            connect_spotify_account,

        risk=
            "medium",

        sensitivity=
            "personal",

        description=
            "Connects a Spotify account using OAuth PKCE.",
    )


    register_integration_capability(
        provider=
            "spotify",

        name=
            "account.disconnect",

        function=
            disconnect_spotify_account,

        risk=
            "high",

        sensitivity=
            "personal",

        description=
            "Disconnects a Spotify account.",
    )


    # -----------------------------------------------------------------------
    # Reads
    # -----------------------------------------------------------------------

    register_integration_capability(
        provider=
            "spotify",

        name=
            "media.read",

        function=
            spotify_current_playback,

        risk=
            "low",

        sensitivity=
            "personal",

        description=
            "Reads Spotify playback state.",
    )


    register_integration_capability(
        provider=
            "spotify",

        name=
            "media.current",

        function=
            spotify_currently_playing,

        risk=
            "low",

        sensitivity=
            "personal",

        description=
            "Reads the currently playing Spotify item.",
    )


    register_integration_capability(
        provider=
            "spotify",

        name=
            "media.devices",

        function=
            spotify_devices,

        risk=
            "low",

        sensitivity=
            "personal",

        description=
            "Lists Spotify Connect devices.",
    )


    register_integration_capability(
        provider=
            "spotify",

        name=
            "media.search",

        function=
            spotify_search,

        risk=
            "low",

        sensitivity=
            "public",

        description=
            "Searches the Spotify catalog.",
    )


    # -----------------------------------------------------------------------
    # Unified Control
    # -----------------------------------------------------------------------

    register_integration_capability(
        provider=
            "spotify",

        name=
            "media.control",

        function=
            spotify_media_control,

        risk=
            "low",

        sensitivity=
            "personal",

        description=(
            "Controls Spotify playback. "
            "Actions include next, previous, pause, resume, play, "
            "play_query, queue, queue_query, volume, seek, shuffle, "
            "repeat, and transfer."
        ),
    )


    # -----------------------------------------------------------------------
    # Compatibility Capabilities
    # -----------------------------------------------------------------------

    register_integration_capability(
        provider="spotify",
        name="media.pause",
        function=spotify_pause,
        risk="low",
        sensitivity="personal",
        description="Pauses Spotify playback.",
    )


    register_integration_capability(
        provider="spotify",
        name="media.resume",
        function=spotify_resume,
        risk="low",
        sensitivity="personal",
        description="Resumes Spotify playback.",
    )


    register_integration_capability(
        provider="spotify",
        name="media.next",
        function=spotify_next,
        risk="low",
        sensitivity="personal",
        description="Skips to the next Spotify item.",
    )


    register_integration_capability(
        provider="spotify",
        name="media.previous",
        function=spotify_previous,
        risk="low",
        sensitivity="personal",
        description="Skips to the previous Spotify item.",
    )


    register_integration_capability(
        provider="spotify",
        name="media.volume",
        function=spotify_set_volume,
        risk="low",
        sensitivity="personal",
        description="Changes Spotify playback volume.",
    )


    register_integration_capability(
        provider="spotify",
        name="media.seek",
        function=spotify_seek,
        risk="low",
        sensitivity="personal",
        description="Seeks Spotify playback.",
    )


    register_integration_capability(
        provider="spotify",
        name="media.shuffle",
        function=spotify_set_shuffle,
        risk="low",
        sensitivity="personal",
        description="Enables or disables Spotify shuffle.",
    )


    register_integration_capability(
        provider="spotify",
        name="media.repeat",
        function=spotify_set_repeat,
        risk="low",
        sensitivity="personal",
        description="Changes Spotify repeat mode.",
    )


    register_integration_capability(
        provider="spotify",
        name="media.queue",
        function=spotify_queue_uri,
        risk="low",
        sensitivity="personal",
        description="Adds a Spotify URI to the playback queue.",
    )


    register_integration_capability(
        provider="spotify",
        name="media.transfer",
        function=spotify_transfer_playback,
        risk="low",
        sensitivity="personal",
        description="Transfers Spotify playback between devices.",
    )


    register_integration_capability(
        provider="spotify",
        name="media.play",
        function=spotify_play_uri,
        risk="low",
        sensitivity="personal",
        description="Starts Spotify playback for a Spotify URI.",
    )


    register_integration_capability(
        provider="spotify",
        name="media.play_query",
        function=spotify_play_query,
        risk="low",
        sensitivity="personal",
        description="Searches for a track and immediately plays it.",
    )


    register_integration_capability(
        provider="spotify",
        name="media.queue_query",
        function=spotify_queue_query,
        risk="low",
        sensitivity="personal",
        description="Searches for a track and adds it to the queue.",
    )