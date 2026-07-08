import os

import uvicorn

from backend.app.bootstrap import bootstrap_application


def should_bootstrap_before_run() -> bool:
    return (os.getenv("BOOTSTRAP_BEFORE_RUN", "1").strip().lower()) not in {"0", "false", "no"}


if __name__ == "__main__":
    if should_bootstrap_before_run():
        bootstrap_application()
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
