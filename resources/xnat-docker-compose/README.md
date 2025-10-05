# Bundled XNAT docker-compose files

This directory contains a minimal docker-compose configuration for bringing up
an XNAT instance in environments without access to the upstream
`xnat-docker-compose` repository. The configuration mirrors the default admin
credentials (`admin` / `admin`) and publishes the application on
`http://localhost`.

The compose definition is intentionally lightweight and is only meant for local
smoke testing. For production-like setups, clone the upstream repository and
customize the stack as needed.
