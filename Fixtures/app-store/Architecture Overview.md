# Architecture Overview

This sample uses a plain Markdown table so the screenshot set shows structured content clearly.

| Root | Region | Purpose |
| --- | --- | --- |
| bootstrap/state | ca-central-1 | Stores Terraform state, locking, and encryption material |
| staging/mx-central-1 | mx-central-1 | Hosts the staging environment in Mexico |
| production/mx-central-1 | mx-central-1 | Runs the primary production stack |
| recovery/ca-central-1 | ca-central-1 | Holds disaster recovery support services |

The viewer keeps tables readable without switching to a web view.
