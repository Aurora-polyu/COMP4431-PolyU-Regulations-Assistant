# Handbook MCP server

`mcp_server.py` lets an AI agent search the PolyU Student Handbook. It runs on your own computer over stdio, so nothing is hosted, no student data is stored and no model API key is needed.

| Tool | Input | Returns |
|---|---|---|
| `search_handbook` | `query`, a question in plain words | The 5 most relevant passages: `chunk_id`, `section`, `printed_page`, `pdf_page`, `text` |
| `get_section` | `section`, a section id such as `4.H`, or `4` for a whole chapter | Every passage of that section, in handbook order. An unknown id returns an error listing valid ids nearby. |

Both tools are read-only. Their descriptions tell the agent to cite the section and page inline and to end with a **Sources** list. Each line of that list gives the section, the printed page, the PDF page and a short exact quote. The descriptions also tell the agent to point the student to the official handbook and the responsible office.

## Before you start

1. Follow the setup in the [README](../README.md): create `.venv`, run `pip install -r requirements.txt`, and build the index into `handbook-index/`. Building the index also downloads the embedding model.
2. Find the two absolute paths you will paste below. Run this from the project folder:

   ```bash
   echo "$PWD/.venv/bin/python"; echo "$PWD"
   ```

   On Windows the Python path is `<project>\.venv\Scripts\python.exe`.

In every example, replace `/ABS/PATH/TO/GP` with your project folder. The config must use absolute paths and the venv's Python, because the client starts the server from its own folder with its own environment. The server loads the model at startup, which takes about 10 seconds.

## Claude Desktop

1. Open Claude > Settings > Developer > **Edit Config**. This opens `claude_desktop_config.json`:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
2. Add the server inside `mcpServers`. Keep any servers already there.

   ```json
   {
     "mcpServers": {
       "polyu-handbook": {
         "command": "/ABS/PATH/TO/GP/.venv/bin/python",
         "args": ["/ABS/PATH/TO/GP/mcp_server.py"],
         "env": { "RETRIEVAL_INDEX_DIR": "/ABS/PATH/TO/GP/handbook-index" }
       }
     }
   }
   ```

3. Quit Claude Desktop completely and open it again.
4. Ask "How do I defer my study?" Claude should call `search_handbook` and cite section 4.H.

If the server doesn't appear, read its log at `~/Library/Logs/Claude/mcp-server-polyu-handbook.log` (Windows: `%APPDATA%\Claude\logs`).

## Claude Code

Run this once, from any folder:

```bash
claude mcp add --transport stdio --scope user --env RETRIEVAL_INDEX_DIR=/ABS/PATH/TO/GP/handbook-index polyu-handbook -- /ABS/PATH/TO/GP/.venv/bin/python /ABS/PATH/TO/GP/mcp_server.py
```

- `--scope user` makes the server available in every project. Leave it out to add it to the current project only.
- Everything after `--` is the command that starts the server.
- Check that it connected with `claude mcp list`, or with `/mcp` inside a session.

## Codex

`codex mcp add` has no option for the startup timeout, and Codex waits only 10 seconds by default, so add the server to `~/.codex/config.toml` by hand:

```toml
[mcp_servers.polyu-handbook]
command = "/ABS/PATH/TO/GP/.venv/bin/python"
args = ["/ABS/PATH/TO/GP/mcp_server.py"]
startup_timeout_sec = 60

[mcp_servers.polyu-handbook.env]
RETRIEVAL_INDEX_DIR = "/ABS/PATH/TO/GP/handbook-index"
```

Check it with `codex mcp get polyu-handbook`, or with `/mcp` inside Codex.

## Test with MCP Inspector

MCP Inspector (it needs Node.js) lets you call the tools by hand. Start it with the venv's Python:

```bash
RETRIEVAL_INDEX_DIR="$PWD/handbook-index" npx @modelcontextprotocol/inspector@0.17.2 "$PWD/.venv/bin/python" "$PWD/mcp_server.py"
```

It opens in your browser. Click **Connect**, then **Tools > List Tools**, and run `search_handbook` with "How do I defer my study?"

Don't use `mcp dev mcp_server.py`. It runs the server in a temporary environment that contains only the `mcp` package, so the retriever's imports fail.

The same check works without the browser:

```bash
RETRIEVAL_INDEX_DIR="$PWD/handbook-index" npx @modelcontextprotocol/inspector@0.17.2 --cli "$PWD/.venv/bin/python" "$PWD/mcp_server.py" --method tools/list
```

## Troubleshooting

| Problem | Fix |
|---|---|
| The server fails to start or the client times out | Run `/ABS/PATH/TO/GP/.venv/bin/python /ABS/PATH/TO/GP/mcp_server.py` in a terminal. It should print `Ready.` to stderr after about 10 seconds; press Ctrl+C to stop it. In Codex, raise `startup_timeout_sec`. |
| An error about the index or manifest | `RETRIEVAL_INDEX_DIR` must be the absolute path to `handbook-index`. Rebuild the index if `data/chunks.jsonl` changed. |
| `ModuleNotFoundError` | `command` isn't the venv's Python. |

The server writes logs only to stderr, because stdout carries the MCP protocol. Don't add `print` calls to `mcp_server.py`.
