---
description: QuickServe is meant to be configurable, to suit your limitations, and needs.
---

# Configuration

### Config File

The main configuration file is located at `<QS-FOLDER>/config.toml` . To find you `<QS-FOLDER>` see [QuickServe Folder](quickserve-folder.md). The file uses the [TOML](https://toml.io/) syntax.

### Sections

The configuration file is broken down into three main sections:

#### web

Configuration related to the QuickServe website, and websockets.

<table><thead><tr><th width="154.82421875">Setting</th><th>Default</th><th>Description</th></tr></thead><tbody><tr><td>secret_key</td><td>"secret-key-change-in-production"</td><td>Secret key used by Flask, see the <a href="https://flask.palletsprojects.com/en/stable/config/#SECRET_KEY">Flask documentation</a> for more information.</td></tr><tr><td>websocket_port</td><td>5000</td><td>The port used by the main QuickServe websocket for things such as the controller interface.</td></tr><tr><td>websocket_host</td><td>"0.0.0.0"</td><td>The host used by the main QuickServe websocket for things such as the controller interface.</td></tr></tbody></table>

### driver

Configuration related to the QuickServe driver **(NOT CURRENTLY USED)**.

### **database**

Configuration related to QuickServe's internal database.

<table><thead><tr><th width="155.43359375">Setting</th><th>Default</th><th>Description</th></tr></thead><tbody><tr><td>file_path</td><td>"/opt/quickserve/database.db"</td><td>The path to the internal QuickServe database.</td></tr></tbody></table>
