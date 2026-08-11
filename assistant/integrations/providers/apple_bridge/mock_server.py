"""
E.V.I.E. - Mock Apple Bridge

Created: August 10, 2026
Author: Max Maehara

Purpose:
    Development-only mock implementation of the Phase 9H Apple bridge.

This server allows E.V.I.E.'s Windows-side bridge client, capability
registry, account router, and aggregator to be tested before the native
Swift bridge exists.

Never expose this development server publicly.
"""

from __future__ import annotations

import json

from http.server import (
    BaseHTTPRequestHandler,
    ThreadingHTTPServer,
)


HOST = "127.0.0.1"

PORT = 8765

TEST_TOKEN = (
    "phase9-apple-bridge-test-token"
)


# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------

class AppleBridgeMockHandler(
    BaseHTTPRequestHandler
):

    def _send_json(
        self,
        status_code: int,
        payload: dict,
    ):
        data = json.dumps(
            payload,
            ensure_ascii=False,
        ).encode(
            "utf-8"
        )


        self.send_response(
            status_code
        )


        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8",
        )


        self.send_header(
            "Content-Length",
            str(
                len(
                    data
                )
            ),
        )


        self.end_headers()


        self.wfile.write(
            data
        )


    def _authorized(
        self,
    ):
        header = (
            self.headers.get(
                "Authorization",
                "",
            )
        )


        expected = (
            f"Bearer {TEST_TOKEN}"
        )


        return (
            header
            == expected
        )


    def do_GET(
        self,
    ):
        if not self._authorized():

            self._send_json(
                401,
                {
                    "success":
                        False,

                    "error":
                        "unauthorized",
                },
            )

            return


        if self.path == "/health":

            self._send_json(
                200,
                {
                    "success":
                        True,

                    "bridge":
                        "EVIE Apple Bridge",

                    "version":
                        "0.1.0",

                    "platform":
                        "mock",

                    "capabilities":
                        [
                            "health",
                        ],
                },
            )

            return


        self._send_json(
            404,
            {
                "success":
                    False,

                "error":
                    "not_found",
            },
        )


    def log_message(
        self,
        format,
        *args,
    ):
        return


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    server = ThreadingHTTPServer(
        (
            HOST,
            PORT,
        ),
        AppleBridgeMockHandler,
    )


    print(
        "E.V.I.E. Mock Apple Bridge"
    )

    print(
        "--------------------------"
    )


    print(
        f"Listening: http://{HOST}:{PORT}"
    )


    print(
        "Press Ctrl+C to stop."
    )


    try:

        server.serve_forever()


    except KeyboardInterrupt:

        pass


    finally:

        server.server_close()