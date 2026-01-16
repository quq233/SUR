#!/bin/bash
python3 -m nuitka \
    --standalone \
    --onefile \
    --include-data-dir=webui=webui \
    --include-data-file=.env=.env \
    --output-dir=out \
    app.py