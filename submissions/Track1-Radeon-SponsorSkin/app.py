#!/usr/bin/env python3
"""Launch the Radeon SponsorSkin local development UI."""

from __future__ import annotations

import os

from sponsorskin.ui import SPONSORSKIN_CSS, build_app


def main() -> None:
    demo = build_app()
    demo.queue(default_concurrency_limit=1).launch(
        server_name=os.getenv("SPONSORSKIN_SERVER_NAME", "127.0.0.1"),
        server_port=int(os.getenv("SPONSORSKIN_SERVER_PORT", "7860")),
        show_error=True,
        css=SPONSORSKIN_CSS,
    )


if __name__ == "__main__":
    main()
